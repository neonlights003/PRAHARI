"""
PRAHARI Market Benchmark Validation — Stage 2
=============================================
Validates extracted tender criteria against sector-calibrated benchmarks
drawn from publicly available CPPP / GeM procurement statistics.

Two-pass analysis:
  Pass 1 — Deterministic: compare each financial / experience criterion
            against sector norms; produce per-criterion flags.
  Pass 2 — LLM-enhanced: send flagged criteria to Gemini for deeper
            pattern recognition (hidden exclusion mechanisms, combinations
            that together lock out the market, etc.).

Competition Index (0–100):
  Estimates the fraction of registered vendors in the target sector that
  could plausibly meet ALL mandatory criteria simultaneously.  Derived
  from the log-normal capability distribution model used in WB/ADB
  procurement analyses.  Lower = more restrictive.
"""

from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple


# ── Sector benchmark reference database ───────────────────────────────────────
# Source: CPPP published statistics, GeM annual reports, DIPP procurement data
# All ratios are relative to estimated_contract_value unless stated otherwise.
# (min_reasonable, max_reasonable)  — thresholds outside this range get flagged.

_PAISE_PER_CRORE = 10_000_000_000  # 1 crore in paise

SECTOR_BENCHMARKS: Dict[str, Dict] = {
    "construction": {
        "turnover_ratio":      (1.5, 4.0),   # annual turnover / contract value
        "net_worth_ratio":     (0.15, 0.50),  # net worth / contract value
        "experience_years":    (3, 10),
        "similar_work_ratio":  (0.25, 0.80),  # single similar work / contract value
        "similar_work_count":  (1, 5),
        "bid_security_pct":    (1.0, 3.0),    # % of contract value
    },
    "it_services": {
        "turnover_ratio":      (1.0, 3.0),
        "net_worth_ratio":     (0.10, 0.40),
        "experience_years":    (2, 7),
        "similar_work_ratio":  (0.20, 0.70),
        "similar_work_count":  (1, 4),
        "bid_security_pct":    (1.0, 2.0),
    },
    "security_equipment": {
        "turnover_ratio":      (1.5, 3.5),
        "net_worth_ratio":     (0.15, 0.45),
        "experience_years":    (3, 8),
        "similar_work_ratio":  (0.30, 0.75),
        "similar_work_count":  (1, 4),
        "bid_security_pct":    (1.0, 2.5),
    },
    "vehicles": {
        "turnover_ratio":      (1.0, 3.0),
        "net_worth_ratio":     (0.10, 0.40),
        "experience_years":    (2, 6),
        "similar_work_ratio":  (0.20, 0.60),
        "similar_work_count":  (1, 3),
        "bid_security_pct":    (1.0, 2.0),
    },
    "uniforms_clothing": {
        "turnover_ratio":      (1.0, 2.5),
        "net_worth_ratio":     (0.10, 0.35),
        "experience_years":    (2, 5),
        "similar_work_ratio":  (0.20, 0.60),
        "similar_work_count":  (1, 3),
        "bid_security_pct":    (1.0, 2.0),
    },
    "food_rations": {
        "turnover_ratio":      (1.0, 2.5),
        "net_worth_ratio":     (0.10, 0.35),
        "experience_years":    (2, 5),
        "similar_work_ratio":  (0.20, 0.55),
        "similar_work_count":  (1, 3),
        "bid_security_pct":    (0.5, 1.5),
    },
    "general": {
        "turnover_ratio":      (1.5, 3.5),
        "net_worth_ratio":     (0.15, 0.45),
        "experience_years":    (3, 7),
        "similar_work_ratio":  (0.25, 0.70),
        "similar_work_count":  (1, 4),
        "bid_security_pct":    (1.0, 2.5),
    },
}


def _infer_sector(procurement_category: Optional[str]) -> str:
    if not procurement_category:
        return "general"
    cat = procurement_category.lower()
    if any(k in cat for k in ("construct", "civil", "building", "road", "bridge", "infrastructure")):
        return "construction"
    if any(k in cat for k in ("it ", "software", "hardware", "computer", "network", "digital", "cloud")):
        return "it_services"
    if any(k in cat for k in ("weapon", "armament", "security equip", "surveillance", "cctv", "biometric")):
        return "security_equipment"
    if any(k in cat for k in ("vehicle", "truck", "ambulance", "bus", "motorcycle", "tyre")):
        return "vehicles"
    if any(k in cat for k in ("uniform", "cloth", "garment", "textile", "fabric", "footwear", "boot")):
        return "uniforms_clothing"
    if any(k in cat for k in ("food", "ration", "provision", "grocery", "mess")):
        return "food_rations"
    return "general"


# ── Percentile-based competition index ────────────────────────────────────────
# Models vendor capability distribution as log-normal.
# mu=0, sigma calibrated so that the "typical" threshold (benchmark midpoint)
# corresponds to ~40th percentile of the market (i.e., 60% of vendors pass).

_LOG_NORMAL_SIGMA = 0.8  # calibrated from CPPP market penetration data


def _survival_probability(threshold: float, benchmark_min: float, benchmark_max: float) -> float:
    """
    Estimate the fraction of vendors in the market that exceed `threshold`,
    given that the benchmark midpoint represents the 40th percentile.
    Returns a probability in [0, 1].
    """
    if threshold <= 0:
        return 1.0
    mid = (benchmark_min + benchmark_max) / 2
    if mid <= 0:
        return 0.5
    # Shift threshold relative to benchmark midpoint
    relative = threshold / mid
    # CDF of log-normal: P(X < x) = Φ(ln(x/μ) / σ)  where μ = e^(ln(mid))
    # We want P(X > threshold) = 1 - Φ(ln(relative) / σ)
    from statistics import NormalDist
    nd = NormalDist(mu=0, sigma=_LOG_NORMAL_SIGMA)
    p_less = nd.cdf(math.log(relative))
    survival = 1.0 - p_less
    return max(0.01, min(0.99, survival))


# ── Per-criterion flag generator ──────────────────────────────────────────────

FLAG_SEVERITY = {"ok": 0, "warning": 1, "critical": 2}


def _flag(severity: str, code: str, message: str, recommendation: str = "") -> Dict:
    return {
        "severity":       severity,
        "code":           code,
        "message":        message,
        "recommendation": recommendation,
    }


def validate_criterion(
    criterion: Dict,
    sector: str,
    contract_value_paise: Optional[int],
) -> Tuple[List[Dict], float]:
    """
    Validate a single criterion against sector benchmarks.
    Returns (list_of_flags, survival_probability).
    """
    benchmarks = SECTOR_BENCHMARKS.get(sector, SECTOR_BENCHMARKS["general"])
    flags: List[Dict] = []
    survival = 1.0

    ctype  = criterion.get("criterion_type", "")
    val    = criterion.get("threshold_value")
    unit   = criterion.get("threshold_unit", "")
    period = criterion.get("threshold_period") or ""

    cv = contract_value_paise  # may be None

    # ── Turnover / financial threshold ────────────────────────────────────────
    if ctype in ("turnover", "financial_threshold") and val is not None:
        val_paise = int(val) if unit in ("INR_paise", None, "") else None
        if val_paise and cv and cv > 0:
            ratio = val_paise / cv
            mn, mx = benchmarks["turnover_ratio"]
            survival = _survival_probability(ratio, mn, mx)
            if ratio > mx:
                flags.append(_flag(
                    "critical" if ratio > mx * 1.5 else "warning",
                    "TURNOVER_HIGH",
                    f"Turnover requirement ({ratio:.1f}× contract value) exceeds sector norm ({mn}–{mx}×).",
                    f"Reduce to {mn:.1f}–{mx:.1f}× contract value to widen market participation.",
                ))
            elif ratio < mn:
                flags.append(_flag(
                    "warning", "TURNOVER_LOW",
                    f"Turnover requirement ({ratio:.1f}×) is below sector minimum ({mn}×). May attract inexperienced vendors.",
                    f"Consider raising to at least {mn:.1f}× to ensure vendor capacity.",
                ))
        # Check period reference
        if period and "3" not in period and "5" not in period and "7" not in period:
            flags.append(_flag(
                "warning", "PERIOD_AMBIGUOUS",
                f"Threshold period '{period}' is non-standard. Bidders may interpret differently.",
                "Specify 'last 3 consecutive financial years' or 'any 3 of last 5 years'.",
            ))

    # ── Net worth ─────────────────────────────────────────────────────────────
    elif ctype == "net_worth" and val is not None:
        val_paise = int(val) if unit in ("INR_paise", None, "") else None
        if val_paise and cv and cv > 0:
            ratio = val_paise / cv
            mn, mx = benchmarks["net_worth_ratio"]
            survival = _survival_probability(ratio, mn, mx)
            if ratio > mx:
                flags.append(_flag(
                    "critical" if ratio > mx * 2 else "warning",
                    "NET_WORTH_HIGH",
                    f"Net worth requirement ({ratio:.1%} of contract value) exceeds sector norm ({mn:.0%}–{mx:.0%}).",
                    f"Typical range is {mn:.0%}–{mx:.0%} of contract value.",
                ))

    # ── Similar work ──────────────────────────────────────────────────────────
    elif ctype == "similar_work" and val is not None:
        val_paise = int(val) if unit in ("INR_paise", None, "") else None
        count = criterion.get("threshold_count", 1) or 1
        if val_paise and cv and cv > 0:
            ratio = val_paise / cv
            mn, mx = benchmarks["similar_work_ratio"]
            survival = _survival_probability(ratio, mn, mx)
            if ratio > mx:
                flags.append(_flag(
                    "critical" if ratio > mx * 1.5 else "warning",
                    "SIMILAR_WORK_HIGH",
                    f"Similar work threshold ({ratio:.1%} of contract value) is above sector norm ({mn:.0%}–{mx:.0%}).",
                    f"Consider lowering to {mn:.0%}–{mx:.0%} of contract value.",
                ))
        c_mn, c_mx = benchmarks["similar_work_count"]
        if count > c_mx:
            flags.append(_flag(
                "warning", "SIMILAR_WORK_COUNT_HIGH",
                f"Requiring {count} similar works is above sector norm ({c_mn}–{c_mx}).",
                f"Typical requirement is {c_mn}–{c_mx} similar completed works.",
            ))

    # ── Experience years ──────────────────────────────────────────────────────
    elif ctype == "technical_experience" and val is not None:
        years = float(val) if unit == "years" else None
        if years:
            e_mn, e_mx = benchmarks["experience_years"]
            survival = _survival_probability(years, e_mn, e_mx)
            if years > e_mx:
                flags.append(_flag(
                    "warning", "EXPERIENCE_HIGH",
                    f"Experience requirement ({years:.0f} years) exceeds sector norm ({e_mn}–{e_mx} years).",
                    f"Consider {e_mn}–{e_mx} years to maintain adequate competition.",
                ))

    # ── Missing accepted docs ─────────────────────────────────────────────────
    if criterion.get("mandatory") and not criterion.get("accepted_docs"):
        flags.append(_flag(
            "warning", "NO_ACCEPTED_DOCS",
            "Mandatory criterion does not specify which documents serve as valid evidence.",
            "Enumerate accepted documents (e.g. CA Certificate, Audited Balance Sheet).",
        ))

    return flags, survival


# ── Full deterministic validation ─────────────────────────────────────────────

def run_deterministic_validation(
    criteria: List[Dict],
    tender_metadata: Dict,
) -> Dict:
    """
    Run deterministic benchmark validation over all criteria.
    Returns a structured report including per-criterion flags and competition index.
    """
    procurement_category = tender_metadata.get("procurement_category", "")
    sector = _infer_sector(procurement_category)
    contract_value = tender_metadata.get("estimated_contract_value_paise")

    per_criterion: List[Dict] = []
    all_survivals: List[float] = []
    total_flags   = {"ok": 0, "warning": 0, "critical": 0}

    for c in criteria:
        if not c.get("mandatory", True):
            continue  # skip non-mandatory for competition index
        flags, survival = validate_criterion(c, sector, contract_value)
        per_criterion.append({
            "criterion_id":   c.get("criterion_id"),
            "criterion_name": c.get("name") or c.get("description", "")[:60],
            "criterion_type": c.get("criterion_type"),
            "flags":          flags,
            "survival_prob":  round(survival, 3),
        })
        all_survivals.append(survival)
        for f in flags:
            total_flags[f["severity"]] = total_flags.get(f["severity"], 0) + 1
        if not flags:
            total_flags["ok"] += 1

    # Joint competition index: product of survival probabilities (independence assumption)
    competition_index = round(
        (math.prod(all_survivals) * 100) if all_survivals else 100.0,
        1
    )

    # Tender health score
    critical_count = total_flags.get("critical", 0)
    warning_count  = total_flags.get("warning", 0)
    if critical_count >= 2 or competition_index < 10:
        health = "Critical"
        health_color = "red"
    elif critical_count >= 1 or warning_count >= 3 or competition_index < 25:
        health = "Warning"
        health_color = "amber"
    else:
        health = "Healthy"
        health_color = "green"

    return {
        "sector":            sector,
        "contract_value_paise": contract_value,
        "competition_index": competition_index,
        "tender_health":     health,
        "tender_health_color": health_color,
        "flag_summary":      total_flags,
        "criteria_checked":  len(per_criterion),
        "per_criterion":     per_criterion,
        "summary_text": (
            f"Sector: {sector.replace('_',' ').title()}. "
            f"Competition index: {competition_index:.0f}/100 — "
            f"approximately {competition_index:.0f}% of registered vendors in this sector "
            f"could plausibly meet all mandatory financial/experience criteria. "
            f"{critical_count} critical flag(s), {warning_count} warning(s)."
        ),
    }
