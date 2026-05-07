"""
PRAHARI Vendor History Lookup
============================
Two data sources:
  1. CPPP (Central Public Procurement Portal) — debarred vendor list
     https://eprocure.gov.in/mmp/latestdebarredvendor
  2. GeM (Government e-Marketplace) — public seller directory search

Both are attempted on every lookup; failures are caught and degraded
gracefully so a network issue never blocks the evaluation pipeline.

Results are cached in-process with a 24-hour TTL to avoid hammering
public portals on every bidder check.
"""

from __future__ import annotations

import asyncio
import re
import time
import unicodedata
from difflib import SequenceMatcher
from typing import Dict, List, Optional

import httpx

# ── constants ──────────────────────────────────────────────────────────────────
CPPP_DEBARMENT_URL = "https://eprocure.gov.in/mmp/latestdebarredvendor"
GEM_SEARCH_URL     = "https://mkp.gem.gov.in/api/public/cat/search"
GEM_SELLER_URL     = "https://mkp.gem.gov.in/api/public/sellers"

_HTTP_TIMEOUT  = 15.0   # seconds
_CACHE_TTL     = 86_400  # 24 hours
_FUZZY_THRESH  = 0.72    # SequenceMatcher ratio threshold for name match

# ── in-memory cache ────────────────────────────────────────────────────────────
_debarment_cache: Dict = {}    # {list: [...], fetched_at: float}
_gem_cache: Dict[str, Dict] = {}   # {query_key: {result, fetched_at}}
_lookup_cache: Dict[str, Dict] = {}  # {bidder_key: full_result}


# ── text helpers ───────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    """Lower-case, strip accents, collapse whitespace."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


def _fuzzy_match(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalise(a), _normalise(b)).ratio()


def _pan_match(pan_a: Optional[str], pan_b: Optional[str]) -> bool:
    if not pan_a or not pan_b:
        return False
    return pan_a.strip().upper() == pan_b.strip().upper()


# ── CPPP debarment fetcher ─────────────────────────────────────────────────────

async def _fetch_cppp_debarment_list() -> List[Dict]:
    """
    Fetch and parse the CPPP debarred-vendor HTML table.
    Returns a list of dicts with keys: name, pan, address, debarred_from, debarred_till, reason.
    Caches result for 24 hours.
    """
    now = time.time()
    if _debarment_cache.get("fetched_at", 0) + _CACHE_TTL > now and _debarment_cache.get("list"):
        return _debarment_cache["list"]

    print("⏳ Fetching CPPP debarment list…")
    vendors: List[Dict] = []

    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(
                CPPP_DEBARMENT_URL,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PRAHARI/1.0; +https://crpf.gov.in)"},
            )
            resp.raise_for_status()
            html = resp.text

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # The page has a table; try to find it generically
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            # Detect header row
            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
            if not any(h in headers for h in ["vendor", "firm", "company", "name", "pan"]):
                continue
            # Map column indices
            col = {h: i for i, h in enumerate(headers)}
            name_idx = next((col[k] for k in ("vendor name", "name", "firm name", "company") if k in col), 0)
            pan_idx  = next((col[k] for k in ("pan", "pan no", "pan number") if k in col), None)
            from_idx = next((col[k] for k in ("debarred from", "from date", "from") if k in col), None)
            till_idx = next((col[k] for k in ("debarred till", "till date", "till", "to") if k in col), None)
            reason_idx = next((col[k] for k in ("reason", "remarks", "description") if k in col), None)

            for row in rows[1:]:
                cells = [td.get_text(separator=" ", strip=True) for td in row.find_all(["td", "th"])]
                if not cells or len(cells) <= name_idx:
                    continue
                vendors.append({
                    "name":          cells[name_idx] if name_idx < len(cells) else "",
                    "pan":           cells[pan_idx]  if pan_idx  is not None and pan_idx  < len(cells) else "",
                    "debarred_from": cells[from_idx] if from_idx is not None and from_idx < len(cells) else "",
                    "debarred_till": cells[till_idx] if till_idx is not None and till_idx < len(cells) else "",
                    "reason":        cells[reason_idx] if reason_idx is not None and reason_idx < len(cells) else "",
                })
            if vendors:
                break

        print(f"✓ CPPP debarment list fetched: {len(vendors)} entries")

    except Exception as e:
        print(f"⚠ CPPP fetch failed: {e} — debarment check will be skipped")

    _debarment_cache["list"] = vendors
    _debarment_cache["fetched_at"] = time.time()
    return vendors


async def check_cppp_debarment(
    company_name: str,
    pan: Optional[str] = None,
    gstin: Optional[str] = None,
) -> Dict:
    """
    Check whether a vendor appears on the CPPP debarment list.
    Returns: {is_debarred, match_type, match_entry, source}
    """
    vendors = await _fetch_cppp_debarment_list()

    # Derive PAN from GSTIN if not supplied (GSTIN chars 3–12 = PAN)
    derived_pan = pan
    if not derived_pan and gstin and len(gstin) == 15:
        derived_pan = gstin[2:12].upper()

    for v in vendors:
        # Exact PAN match
        if derived_pan and _pan_match(derived_pan, v.get("pan")):
            return {
                "is_debarred": True,
                "match_type":  "PAN",
                "match_entry": v,
                "source":      "CPPP",
            }
        # Fuzzy name match
        if company_name and v.get("name"):
            ratio = _fuzzy_match(company_name, v["name"])
            if ratio >= _FUZZY_THRESH:
                return {
                    "is_debarred": True,
                    "match_type":  f"name_similarity_{ratio:.2f}",
                    "match_entry": v,
                    "source":      "CPPP",
                }

    if not vendors:
        return {"is_debarred": None, "source": "CPPP", "note": "Debarment list unavailable"}

    return {"is_debarred": False, "source": "CPPP"}


# ── GeM seller lookup ──────────────────────────────────────────────────────────

async def lookup_gem_history(
    company_name: str,
    gstin: Optional[str] = None,
) -> Dict:
    """
    Search the GeM public seller directory for a vendor.
    Returns: {found, seller_count, categories, rating, source, raw}
    """
    cache_key = _normalise(company_name)[:50] + (gstin or "")
    cached = _gem_cache.get(cache_key)
    if cached and cached.get("fetched_at", 0) + _CACHE_TTL > time.time():
        return cached["result"]

    result: Dict = {"found": False, "source": "GeM", "sellers": []}

    try:
        params: Dict = {"search_type": "seller", "q": company_name, "page_no": 1, "page_size": 5}
        if gstin:
            params["gstin"] = gstin

        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, follow_redirects=True) as client:
            # Try public search API
            resp = await client.get(
                GEM_SEARCH_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PRAHARI/1.0)", "Accept": "application/json"},
            )

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    sellers = data.get("data", data.get("results", data.get("sellers", [])))
                    if isinstance(sellers, list) and sellers:
                        result["found"] = True
                        result["sellers"] = [
                            {
                                "name":       s.get("seller_name") or s.get("name", ""),
                                "gstin":      s.get("gstin", ""),
                                "rating":     s.get("rating") or s.get("seller_rating"),
                                "categories": s.get("categories", []),
                                "orders":     s.get("total_orders") or s.get("order_count"),
                                "registered": s.get("registration_date") or s.get("joined_date"),
                            }
                            for s in sellers[:5]
                        ]
                except Exception:
                    pass

    except httpx.TimeoutException:
        result["note"] = "GeM API timed out"
    except Exception as e:
        result["note"] = f"GeM lookup failed: {str(e)[:80]}"

    _gem_cache[cache_key] = {"result": result, "fetched_at": time.time()}
    return result


# ── Combined vendor lookup ─────────────────────────────────────────────────────

def _compute_risk(debarment: Dict, gem: Dict, company_name: str) -> Dict:
    """Derive a risk level and summary from the two source results."""
    if debarment.get("is_debarred") is True:
        return {
            "level":   "CRITICAL",
            "color":   "red",
            "summary": f"DEBARRED on CPPP (match: {debarment.get('match_type')}). Do not award contract.",
        }

    flags = []
    if debarment.get("is_debarred") is None:
        flags.append("CPPP check unavailable — verify manually")
    if not gem.get("found") and gem.get("note") is None:
        flags.append("Not found on GeM seller registry")

    if flags:
        return {"level": "MEDIUM", "color": "amber", "summary": "; ".join(flags), "flags": flags}

    return {
        "level":   "LOW",
        "color":   "green",
        "summary": "No debarment found. Vendor present on GeM." if gem.get("found") else "No debarment found.",
    }


async def full_vendor_lookup(
    company_name: str,
    gstin: Optional[str] = None,
    pan: Optional[str] = None,
) -> Dict:
    """
    Run CPPP debarment check + GeM history lookup in parallel.
    Returns a unified risk report.
    """
    cache_key = f"{_normalise(company_name)[:40]}|{gstin or ''}|{pan or ''}"
    cached = _lookup_cache.get(cache_key)
    if cached and cached.get("fetched_at", 0) + _CACHE_TTL > time.time():
        return cached

    debarment, gem = await asyncio.gather(
        check_cppp_debarment(company_name, pan=pan, gstin=gstin),
        lookup_gem_history(company_name, gstin=gstin),
    )

    risk = _compute_risk(debarment, gem, company_name)

    result = {
        "company_name": company_name,
        "gstin":        gstin,
        "pan":          pan,
        "debarment":    debarment,
        "gem":          gem,
        "risk":         risk,
        "fetched_at":   time.time(),
    }
    _lookup_cache[cache_key] = result
    return result


async def bulk_vendor_lookup(bidders: List[Dict]) -> List[Dict]:
    """Run full_vendor_lookup for all bidders concurrently."""
    tasks = [
        full_vendor_lookup(
            company_name=b.get("company_name", ""),
            gstin=b.get("gstin"),
            pan=b.get("pan"),
        )
        for b in bidders
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for b, r in zip(bidders, results):
        if isinstance(r, Exception):
            out.append({"bidder_id": b["id"], "company_name": b.get("company_name"), "error": str(r)})
        else:
            out.append({"bidder_id": b["id"], **r})
    return out


def invalidate_cache(company_name: str = None) -> None:
    """Clear cached lookup results (optionally for one company only)."""
    if company_name:
        key = _normalise(company_name)[:40]
        for k in list(_lookup_cache.keys()):
            if k.startswith(key):
                del _lookup_cache[k]
    else:
        _lookup_cache.clear()
        _gem_cache.clear()
        _debarment_cache.clear()
        print("✓ Vendor lookup cache cleared")
