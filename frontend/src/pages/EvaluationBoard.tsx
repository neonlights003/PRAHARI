import { Header } from '@/components/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { PDFViewerModal } from '@/components/PDFViewerModal'
import {
  ArrowLeft, Loader2, RefreshCw, AlertTriangle, CheckCircle,
  XCircle, Clock, Shield, BarChart3, FileText, ChevronDown, ChevronUp,
  Play, ShieldAlert, Hash, ClipboardList, Users, MessageSquare, Send, Trash2,
  Lock, TrendingUp, RefreshCcw, Download, Search, Building2, AlertOctagon, BookOpen,
  PenLine, CheckCircle2
} from 'lucide-react'
import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  api,
  type Verdict,
  type CollusionAlert,
  type AuditEvent,
  type Bidder,
} from '@/lib/api'
import { ChatMessageFormatter } from '@/components/ChatMessageFormatter'

// ── colour helpers ────────────────────────────────────────────────────────────

// Hindi label shown alongside the verdict for CRPF officers
const verdictHindi: Record<string, string> = {
  Eligible:     'योग्य',
  Not_Eligible: 'अयोग्य',
  Manual_Review:'समीक्षा',
}

function verdictColor(verdict: string, _conf: number) {
  if (verdict === 'Eligible')     return { bg: 'bg-emerald-100 dark:bg-emerald-900/40', text: 'text-emerald-700 dark:text-emerald-300', border: 'border-emerald-300 dark:border-emerald-700' }
  if (verdict === 'Not_Eligible') return { bg: 'bg-red-100 dark:bg-red-900/40',     text: 'text-red-700 dark:text-red-300',     border: 'border-red-300 dark:border-red-700' }
  return                               { bg: 'bg-amber-100 dark:bg-amber-900/40',   text: 'text-amber-700 dark:text-amber-300', border: 'border-amber-300 dark:border-amber-700' }
}

function confBar(score: number) {
  const pct = Math.round(score * 100)
  const color = score >= 0.9 ? 'bg-emerald-500' : score >= 0.6 ? 'bg-amber-400' : 'bg-red-400'
  return (
    <div className="w-full mt-1">
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-muted-foreground">{pct}%</span>
    </div>
  )
}

function tamperBadge(level?: string) {
  if (!level || level === 'unknown') return null
  const map: Record<string, string> = { Low: 'text-emerald-600 bg-emerald-50', Medium: 'text-amber-600 bg-amber-50', High: 'text-red-600 bg-red-50' }
  return <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${map[level] ?? ''}`}>{level} risk</span>
}

// ── VerdictCell ───────────────────────────────────────────────────────────────

function VerdictCell({ verdict, docUrl }: { verdict: Verdict | undefined; docUrl?: string }) {
  const [open, setOpen] = useState(false)
  const [showPDF, setShowPDF] = useState(false)
  if (!verdict) return <td className="border border-border/30 p-2 text-center text-muted-foreground text-xs">—</td>

  const effective = verdict.human_override ? verdict.override_verdict! : verdict.verdict
  const c = verdictColor(effective, verdict.confidence_score)

  return (
    <td className={`border border-border/30 p-2 align-top min-w-[120px] ${c.bg}`}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full text-left"
        title={verdict.reasoning ?? ''}
      >
        <div className={`flex items-center gap-1 font-medium text-xs ${c.text}`}>
          {effective === 'Eligible'     && <CheckCircle className="h-3 w-3 shrink-0" />}
          {effective === 'Not_Eligible' && <XCircle     className="h-3 w-3 shrink-0" />}
          {effective === 'Manual_Review'&& <Clock       className="h-3 w-3 shrink-0" />}
          <span className="truncate">{effective.replace('_', ' ')}</span>
          {verdictHindi[effective] && (
            <span className="ml-1 text-[9px] opacity-60 font-normal">{verdictHindi[effective]}</span>
          )}
          {open ? <ChevronUp className="h-3 w-3 ml-auto" /> : <ChevronDown className="h-3 w-3 ml-auto" />}
        </div>
        {confBar(verdict.confidence_score)}
        {verdict.human_override && (
          <span className="text-[10px] text-purple-600 font-medium">Officer override</span>
        )}
      </button>

      {open && (
        <div className="mt-2 space-y-1 text-[11px] text-muted-foreground border-t border-border/40 pt-2">
          {verdict.extracted_value_text && (
            <p><span className="font-medium text-foreground">Found:</span> {verdict.extracted_value_text}</p>
          )}
          {verdict.reasoning && <p>{verdict.reasoning}</p>}
          {verdict.evidence_quote && (
            <div className="space-y-1">
              <blockquote className="border-l-2 border-primary/40 pl-2 italic">
                "{verdict.evidence_quote.slice(0, 120)}{verdict.evidence_quote.length > 120 ? '…' : ''}"
                {verdict.evidence_page != null && <span className="not-italic"> (p.{verdict.evidence_page})</span>}
              </blockquote>
              {docUrl && (
                <button
                  onClick={e => { e.stopPropagation(); setShowPDF(true) }}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
                >
                  <BookOpen className="h-3 w-3" />
                  View in PDF
                </button>
              )}
            </div>
          )}
          {verdict.tamper_risk_score != null && tamperBadge(
            verdict.tamper_risk_score < 0.3 ? 'Low' : verdict.tamper_risk_score < 0.65 ? 'Medium' : 'High'
          )}
          {verdict.human_override && verdict.override_justification && (
            <p className="text-purple-700"><span className="font-medium">Override reason:</span> {verdict.override_justification}</p>
          )}
        </div>
      )}

      {showPDF && docUrl && (
        <PDFViewerModal
          url={docUrl}
          initialPage={verdict.evidence_page ?? 1}
          evidenceQuote={verdict.evidence_quote}
          title={`Bidder document — p.${verdict.evidence_page ?? 1}`}
          onClose={() => setShowPDF(false)}
        />
      )}
    </td>
  )
}

// ── ConfidenceHeatmap ─────────────────────────────────────────────────────────

function ConfidenceHeatmap({ verdicts, bidders, bidderDocUrls, criteriaMap }: {
  verdicts: Verdict[]
  bidders: Bidder[]
  bidderDocUrls: Record<number, string>
  criteriaMap: Record<string, { mandatory: boolean; category: string }>
}) {
  const criteriaIds = [...new Set(verdicts.map(v => v.criterion_id))].sort()
  const lookup: Record<string, Record<string, Verdict>> = {}
  for (const v of verdicts) {
    if (!lookup[v.bidder_id]) lookup[v.bidder_id] = {}
    lookup[v.bidder_id][v.criterion_id] = v
  }

  if (!criteriaIds.length || !bidders.length) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-40" />
        <p className="font-medium">No evaluation data yet</p>
        <p className="text-sm mt-1">Run evaluation to populate the heatmap</p>
      </div>
    )
  }

  const eligiblePct = (bidderId: number) => {
    const bvs = verdicts.filter(v => v.bidder_id === bidderId)
    if (!bvs.length) return null
    return Math.round(bvs.filter(v => (v.human_override ? v.override_verdict : v.verdict) === 'Eligible').length / bvs.length * 100)
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr>
            <th className="border border-border/30 bg-muted/50 p-2 text-left font-semibold sticky left-0 z-10 min-w-[160px]">
              Bidder
            </th>
            {criteriaIds.map(cid => {
              const meta = criteriaMap[cid]
              const isMandatory = meta ? meta.mandatory : true
              return (
                <th key={cid} className="border border-border/30 bg-muted/50 p-2 text-center font-mono font-medium min-w-[120px]">
                  <div className="flex flex-col items-center gap-0.5">
                    <span>{cid}</span>
                    <span className={`text-[9px] font-semibold px-1 rounded ${isMandatory ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                      {isMandatory ? 'M' : 'O'}
                    </span>
                  </div>
                </th>
              )
            })}
            <th className="border border-border/30 bg-muted/50 p-2 text-center font-semibold min-w-[80px]">
              Eligible %
            </th>
          </tr>
        </thead>
        <tbody>
          {bidders.map(b => {
            const pct = eligiblePct(b.id)
            return (
              <tr key={b.id}>
                <td className="border border-border/30 p-2 sticky left-0 bg-background z-10">
                  <div className="font-medium truncate max-w-[150px]" title={b.company_name}>{b.company_name}</div>
                  <div className="text-[10px] text-muted-foreground capitalize">{b.status.replace(/_/g, ' ')}</div>
                </td>
                {criteriaIds.map(cid => (
                  <VerdictCell key={cid} verdict={lookup[b.id]?.[cid]} docUrl={bidderDocUrls[b.id]} />
                ))}
                <td className="border border-border/30 p-2 text-center font-bold">
                  {pct == null ? '—' : (
                    <span className={pct >= 75 ? 'text-emerald-600' : pct >= 50 ? 'text-amber-600' : 'text-red-600'}>
                      {pct}%
                    </span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {/* Legend */}
      <div className="flex gap-4 mt-4 text-xs flex-wrap">
        {[
          { label: 'Eligible', bg: 'bg-emerald-100', text: 'text-emerald-700' },
          { label: 'Not Eligible', bg: 'bg-red-100', text: 'text-red-700' },
          { label: 'Manual Review', bg: 'bg-amber-100', text: 'text-amber-700' },
          { label: 'Not evaluated', bg: 'bg-muted', text: 'text-muted-foreground' },
        ].map(l => (
          <span key={l.label} className="flex items-center gap-1.5">
            <span className={`h-3 w-5 rounded ${l.bg} inline-block`} />
            <span className={l.text}>{l.label}</span>
          </span>
        ))}
        <span className="text-muted-foreground ml-2">Click any cell for details</span>
        <span className="flex items-center gap-1 ml-4">
          <span className="text-[9px] font-semibold px-1 rounded bg-red-100 text-red-700">M</span>
          <span className="text-muted-foreground">Mandatory</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="text-[9px] font-semibold px-1 rounded bg-blue-100 text-blue-700">O</span>
          <span className="text-muted-foreground">Optional</span>
        </span>
      </div>
    </div>
  )
}

// ── CollusionPanel ────────────────────────────────────────────────────────────

function CollusionPanel({ alerts, risk }: { alerts: CollusionAlert[]; risk: string }) {
  const riskColor = risk === 'High' ? 'text-red-600' : risk === 'Medium' ? 'text-amber-600' : 'text-emerald-600'
  const sevColor = (s: number) => s >= 0.85 ? 'border-red-400 bg-red-50' : s >= 0.60 ? 'border-amber-400 bg-amber-50' : 'border-muted bg-muted/30'

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <ShieldAlert className="h-5 w-5 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Overall integrity risk:</span>
        <span className={`font-bold text-sm ${riskColor}`}>{risk || 'Not assessed'}</span>
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Shield className="h-10 w-10 mx-auto mb-2 opacity-40" />
          <p className="font-medium">No collusion alerts</p>
          <p className="text-sm mt-1">Run detection to check cross-bidder integrity</p>
        </div>
      ) : (
        alerts.map(a => (
          <Card key={a.id} className={`p-4 border-l-4 ${sevColor(a.confidence_score)}`}>
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-mono bg-muted px-1.5 py-0.5 rounded">{a.alert_type.replace(/_/g, ' ')}</span>
                  <span className="text-xs text-muted-foreground">{Math.round(a.confidence_score * 100)}% confidence</span>
                  {a.officer_disposition !== 'pending' && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 capitalize">{a.officer_disposition}</span>
                  )}
                </div>
                <p className="text-sm mt-1.5 font-medium">{a.description}</p>
                {a.disposition_notes && (
                  <p className="text-xs text-muted-foreground mt-1">Officer note: {a.disposition_notes}</p>
                )}
              </div>
            </div>
          </Card>
        ))
      )}
    </div>
  )
}

// ── AuditTrail ────────────────────────────────────────────────────────────────

function AuditTrailPanel({ events }: { events: AuditEvent[] }) {
  const typeIcon = (t: string) => {
    if (t.includes('extracted') || t.includes('criteria')) return <FileText className="h-3.5 w-3.5" />
    if (t.includes('upload')) return <FileText className="h-3.5 w-3.5" />
    if (t.includes('evaluated') || t.includes('evaluation')) return <BarChart3 className="h-3.5 w-3.5" />
    if (t.includes('collusion')) return <ShieldAlert className="h-3.5 w-3.5" />
    if (t.includes('override')) return <Shield className="h-3.5 w-3.5" />
    return <Hash className="h-3.5 w-3.5" />
  }

  return (
    <div className="space-y-2">
      {events.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <Clock className="h-10 w-10 mx-auto mb-2 opacity-40" />
          <p className="font-medium">No audit events yet</p>
        </div>
      ) : (
        events.map(e => (
          <div key={e.event_id} className="flex gap-3 text-xs group">
            <div className="flex flex-col items-center gap-1 pt-0.5">
              <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center text-muted-foreground group-hover:bg-primary/10">
                {typeIcon(e.event_type)}
              </div>
              <div className="w-px flex-1 bg-border/50 min-h-[8px]" />
            </div>
            <div className="flex-1 pb-2">
              <div className="flex items-baseline gap-2 flex-wrap">
                <span className="font-medium capitalize">{e.event_type.replace(/_/g, ' ')}</span>
                <span className="text-muted-foreground text-[10px]">
                  {new Date(e.created_at).toLocaleString()}
                </span>
                {e.confidence_score != null && (
                  <span className="text-[10px] text-muted-foreground">{Math.round(e.confidence_score * 100)}% conf</span>
                )}
              </div>
              {e.criterion_id && <div className="text-muted-foreground">{e.criterion_id}</div>}
              <div className="font-mono text-[10px] text-muted-foreground/60 truncate mt-0.5" title={e.payload_hash}>
                SHA-256: {e.payload_hash.slice(0, 20)}…
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  )
}

// ── Vendor History Panel ──────────────────────────────────────────────────────

function riskBadge(level?: string) {
  if (level === 'CRITICAL') return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-semibold"><AlertOctagon className="h-3 w-3" />CRITICAL</span>
  if (level === 'MEDIUM')   return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-semibold"><AlertTriangle className="h-3 w-3" />MEDIUM</span>
  if (level === 'LOW')      return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-semibold"><CheckCircle className="h-3 w-3" />LOW</span>
  return <span className="text-xs text-muted-foreground">—</span>
}

function VendorHistoryPanel({ projectId }: { projectId: number }) {
  const [data, setData]       = useState<Record<string, any> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)
  const [expanded, setExpanded] = useState<number | null>(null)

  const runLookup = async () => {
    setLoading(true); setError(null)
    try {
      const res = await api.getVendorHistory(projectId)
      setData(res)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const riskOrder = { CRITICAL: 0, MEDIUM: 1, LOW: 2 }
  const sortedResults = data?.results
    ? [...data.results].sort((a, b) =>
        (riskOrder[a.risk?.level as keyof typeof riskOrder] ?? 3) -
        (riskOrder[b.risk?.level as keyof typeof riskOrder] ?? 3)
      )
    : []

  return (
    <div className="space-y-5">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={runLookup}
          disabled={loading}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-primary text-primary-foreground text-sm font-medium disabled:opacity-40 hover:opacity-90"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Run Vendor Checks
        </button>
        <span className="text-xs text-muted-foreground">Checks CPPP debarment list + GeM seller registry for all bidders</span>
      </div>

      {error && <div className="text-xs text-destructive bg-destructive/10 rounded px-3 py-2">{error}</div>}

      {/* Risk summary strip */}
      {data && (
        <div className="flex gap-3 flex-wrap">
          {[
            { key: 'CRITICAL', label: 'Debarred',    cls: 'bg-red-50 border-red-200 text-red-700' },
            { key: 'MEDIUM',   label: 'Flagged',     cls: 'bg-amber-50 border-amber-200 text-amber-700' },
            { key: 'LOW',      label: 'Clear',       cls: 'bg-emerald-50 border-emerald-200 text-emerald-700' },
          ].map(k => (
            <div key={k.key} className={`flex items-center gap-2 px-4 py-2 rounded-lg border font-medium text-sm ${k.cls}`}>
              <span className="text-xl font-bold">{data.risk_summary?.[k.key] ?? 0}</span>
              <span>{k.label}</span>
            </div>
          ))}
        </div>
      )}

      {!data && !loading && (
        <div className="text-sm text-muted-foreground py-8 text-center">
          Click <strong>Run Vendor Checks</strong> to query CPPP and GeM for all registered bidders.
        </div>
      )}

      {/* Per-bidder results */}
      {sortedResults.length > 0 && (
        <div className="space-y-2">
          {sortedResults.map((r: any, i: number) => (
            <div key={i} className="border border-border rounded-lg overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-muted/30 transition-colors"
                onClick={() => setExpanded(expanded === i ? null : i)}
              >
                <div className="flex items-center gap-3">
                  <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="font-medium text-sm">{r.company_name}</span>
                  {r.gstin && <span className="text-xs text-muted-foreground font-mono hidden sm:inline">{r.gstin}</span>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {riskBadge(r.risk?.level)}
                  {expanded === i ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
                </div>
              </button>

              {expanded === i && (
                <div className="px-4 pb-4 pt-2 border-t border-border/50 bg-muted/10 space-y-3 text-xs">
                  {/* Risk summary */}
                  <p className="text-sm font-medium">{r.risk?.summary || '—'}</p>

                  {/* CPPP */}
                  <div className="space-y-1">
                    <p className="font-semibold text-foreground uppercase tracking-wide text-[10px]">CPPP Debarment Check</p>
                    {r.debarment?.is_debarred === true ? (
                      <div className="bg-red-50 border border-red-200 rounded p-2 space-y-1">
                        <p className="text-red-700 font-semibold">⚠ VENDOR IS DEBARRED</p>
                        <p>Match type: {r.debarment.match_type}</p>
                        {r.debarment.match_entry && (
                          <>
                            <p>Debarred from: {r.debarment.match_entry.debarred_from || '—'} to {r.debarment.match_entry.debarred_till || '—'}</p>
                            <p>Reason: {r.debarment.match_entry.reason || '—'}</p>
                          </>
                        )}
                      </div>
                    ) : r.debarment?.is_debarred === false ? (
                      <p className="text-emerald-700">✓ Not found on CPPP debarment list</p>
                    ) : (
                      <p className="text-muted-foreground italic">{r.debarment?.note || 'CPPP data unavailable'}</p>
                    )}
                  </div>

                  {/* GeM */}
                  <div className="space-y-1">
                    <p className="font-semibold text-foreground uppercase tracking-wide text-[10px]">GeM Seller Registry</p>
                    {r.gem?.found ? (
                      <div className="space-y-1">
                        <p className="text-emerald-700">✓ Found on GeM ({r.gem.sellers?.length ?? 0} match{r.gem.sellers?.length !== 1 ? 'es' : ''})</p>
                        {r.gem.sellers?.slice(0, 2).map((s: any, si: number) => (
                          <div key={si} className="bg-muted/40 rounded px-2 py-1">
                            <p className="font-medium">{s.name}</p>
                            {s.rating && <p>Rating: {s.rating}</p>}
                            {s.orders != null && <p>Total orders: {s.orders}</p>}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground italic">{r.gem?.note || 'Not found on GeM seller registry'}</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── DP Analytics Panel ────────────────────────────────────────────────────────

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium w-8 text-right">{value}</span>
    </div>
  )
}

function AnalyticsPanel({ projectId }: { projectId: number }) {
  const [data, setData]     = useState<Record<string, any> | null>(null)
  const [loading, setLoading] = useState(false)
  const [epsilon, setEpsilon] = useState(1.0)
  const [error, setError]   = useState<string | null>(null)

  const fetch = async (reset = false) => {
    setLoading(true); setError(null)
    try {
      const res = await api.getTenderAnalytics(projectId, epsilon, reset)
      setData(res)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const verdictColors: Record<string, string> = {
    Eligible:     'bg-emerald-500',
    Not_Eligible: 'bg-red-500',
    Manual_Review:'bg-amber-400',
  }
  const tamperColors: Record<string, string> = {
    Low:    'bg-emerald-500',
    Medium: 'bg-amber-400',
    High:   'bg-red-500',
  }

  const maxVerdict = data ? Math.max(...Object.values(data.verdict_counts ?? {}).map(Number), 1) : 1
  const maxTamper  = data ? Math.max(...Object.values(data.tamper_risk_distribution ?? {}).map(Number), 1) : 1

  return (
    <div className="space-y-5">
      {/* Controls */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-muted-foreground mb-1">Privacy budget ε (lower = stronger)</label>
          <select
            value={epsilon}
            onChange={e => setEpsilon(Number(e.target.value))}
            className="border border-border rounded px-2 py-1 text-sm bg-background"
          >
            {[0.1, 0.5, 1.0, 2.0, 5.0].map(v => (
              <option key={v} value={v}>ε = {v}</option>
            ))}
          </select>
        </div>
        <button
          onClick={() => fetch(false)}
          disabled={loading}
          className="flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-primary text-primary-foreground text-sm font-medium disabled:opacity-40 hover:opacity-90"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <TrendingUp className="h-4 w-4" />}
          Compute Analytics
        </button>
        {data && (
          <button
            onClick={() => fetch(true)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-border text-sm text-muted-foreground hover:text-foreground disabled:opacity-40"
          >
            <RefreshCcw className="h-3.5 w-3.5" /> Reset Budget
          </button>
        )}
      </div>

      {error && <div className="text-xs text-destructive bg-destructive/10 rounded px-3 py-2">{error}</div>}

      {!data && !loading && (
        <div className="text-sm text-muted-foreground py-8 text-center">
          Select an ε value and click <strong>Compute Analytics</strong> to generate privacy-preserving statistics.
        </div>
      )}

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Privacy badge */}
          <div className="md:col-span-2 flex items-start gap-2 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
            <Lock className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-blue-700 dark:text-blue-300">{data.privacy_guarantee}</p>
              <p className="text-xs text-blue-600/80 dark:text-blue-400/80 mt-0.5">{data.note}</p>
              <p className="text-xs text-blue-500 mt-1">Mechanism: <code>{data.mechanism}</code> · ε this query: {data.epsilon_used} · cumulative ε: {data.total_epsilon_spent}</p>
            </div>
          </div>

          {/* Verdict distribution */}
          <Card className="p-4">
            <p className="text-sm font-semibold mb-3">Verdict Distribution <span className="text-xs text-muted-foreground font-normal">(DP-noisy)</span></p>
            <div className="space-y-2">
              {Object.entries(data.verdict_counts ?? {}).map(([k, v]) => (
                <div key={k}>
                  <div className="flex justify-between text-xs mb-0.5">
                    <span>{k.replace('_', ' ')}</span>
                  </div>
                  <MiniBar value={Number(v)} max={maxVerdict} color={verdictColors[k] ?? 'bg-primary'} />
                </div>
              ))}
              <p className="text-xs text-muted-foreground mt-1">Eligible rate: <strong>{(data.eligible_rate * 100).toFixed(1)}%</strong></p>
            </div>
          </Card>

          {/* Confidence & Auth scores */}
          <Card className="p-4">
            <p className="text-sm font-semibold mb-3">Score Averages <span className="text-xs text-muted-foreground font-normal">(DP-noisy)</span></p>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Avg Confidence Score</span>
                  <span className="font-medium">{(data.avg_confidence_score * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div className="h-full rounded-full bg-indigo-500" style={{ width: `${(data.avg_confidence_score * 100).toFixed(1)}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Avg Authenticity Score</span>
                  <span className="font-medium">{(data.avg_authenticity_score * 100).toFixed(1)}%</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div className="h-full rounded-full bg-teal-500" style={{ width: `${(data.avg_authenticity_score * 100).toFixed(1)}%` }} />
                </div>
              </div>
              <div className="text-xs text-muted-foreground pt-1">
                Based on {data.document_count} document{data.document_count !== 1 ? 's' : ''} across {data.bidder_count} bidder{data.bidder_count !== 1 ? 's' : ''}.
              </div>
            </div>
          </Card>

          {/* Tamper risk distribution */}
          <Card className="p-4">
            <p className="text-sm font-semibold mb-3">Tamper Risk Distribution</p>
            <div className="space-y-2">
              {Object.entries(data.tamper_risk_distribution ?? {}).map(([k, v]) => (
                <div key={k}>
                  <div className="text-xs mb-0.5">{k} risk</div>
                  <MiniBar value={Number(v)} max={maxTamper} color={tamperColors[k] ?? 'bg-muted'} />
                </div>
              ))}
            </div>
          </Card>

          {/* Per-criterion pass rates */}
          <Card className="p-4">
            <p className="text-sm font-semibold mb-3">Criterion Pass Rates <span className="text-xs text-muted-foreground font-normal">(DP-noisy)</span></p>
            {Object.keys(data.criterion_pass_rates ?? {}).length === 0 ? (
              <p className="text-xs text-muted-foreground">No verdicts recorded yet.</p>
            ) : (
              <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                {Object.entries(data.criterion_pass_rates ?? {}).map(([cid, rate]) => (
                  <div key={cid}>
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="font-mono">{cid}</span>
                      <span>{((Number(rate)) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(Number(rate) * 100).toFixed(0)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}

// ── Evaluation Q&A Panel ──────────────────────────────────────────────────────

const SUGGESTED_QUESTIONS = [
  'Which bidders are fully eligible?',
  'Which criteria have the most Manual Review verdicts?',
  'Are there any high-confidence collusion alerts?',
  'Which bidder has the highest average confidence score?',
  'List all Not_Eligible verdicts with their reasons.',
  'Which bidder documents have high tamper risk?',
]

interface QAMessage { role: 'user' | 'ai'; text: string }

function EvaluationQAPanel({ projectId }: { projectId: number }) {
  const [messages, setMessages] = useState<QAMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (question: string) => {
    const q = question.trim()
    if (!q || sending) return
    setInput('')
    setError(null)
    setMessages(m => [...m, { role: 'user', text: q }])
    setSending(true)
    try {
      const answer = await api.askEvaluationQuestion(projectId, q)
      setMessages(m => [...m, { role: 'ai', text: answer }])
    } catch (e: any) {
      setError(e.message)
      setMessages(m => m.slice(0, -1))
    } finally {
      setSending(false)
    }
  }

  const clearChat = async () => {
    await api.clearEvaluationQA(projectId).catch(() => {})
    setMessages([])
    setError(null)
  }

  return (
    <div className="flex flex-col h-[560px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-muted-foreground">
          Ask anything about this tender's evaluation results, bidder eligibility, or collusion alerts.
        </p>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-destructive transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5" /> Clear
          </button>
        )}
      </div>

      {/* Suggestion chips — shown only when empty */}
      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {SUGGESTED_QUESTIONS.map(q => (
            <button
              key={q}
              onClick={() => send(q)}
              className="text-xs px-3 py-1.5 rounded-full border border-border hover:border-primary hover:text-primary transition-colors text-muted-foreground"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 mb-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <ChatMessageFormatter text={m.text} isUser={m.role === 'user'} />
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-muted text-muted-foreground px-3 py-2 rounded-lg text-xs flex items-center gap-2">
              <Loader2 className="h-3 w-3 animate-spin" /> Thinking…
            </div>
          </div>
        )}
        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded px-3 py-2">{error}</div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 border-t border-border pt-3">
        <textarea
          rows={2}
          className="flex-1 resize-none text-sm border border-border rounded-md px-3 py-2 bg-background focus:outline-none focus:ring-1 focus:ring-primary"
          placeholder="Ask about eligibility, scores, collusion alerts…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) }
          }}
        />
        <button
          onClick={() => send(input)}
          disabled={!input.trim() || sending}
          className="px-4 rounded-md bg-primary text-primary-foreground disabled:opacity-40 hover:opacity-90 transition-opacity flex items-center gap-1.5 text-sm font-medium"
        >
          {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Ask
        </button>
      </div>
    </div>
  )
}

// ── Criteria Weights Panel ────────────────────────────────────────────────────

function CriteriaWeightsPanel({ projectId }: { projectId: number }) {
  const [weights, setWeights] = useState<Record<string, number>>({})
  const [isCustom, setIsCustom] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)

  useEffect(() => {
    api.getCriteriaWeights(projectId).then(data => {
      setWeights(data.weights ?? {})
      setIsCustom(data.isCustom ?? false)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [projectId])

  const total = Object.values(weights).reduce((a, b) => a + b, 0)

  const handleChange = (key: string, val: number) => {
    setWeights(w => ({ ...w, [key]: val }))
    setDirty(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.updateCriteriaWeights(projectId, weights)
      setIsCustom(true)
      setDirty(false)
    } catch (e: any) { alert(e.message) }
    finally { setSaving(false) }
  }

  const handleReset = async () => {
    setSaving(true)
    try {
      await api.resetCriteriaWeights(projectId)
      const data = await api.getCriteriaWeights(projectId)
      setWeights(data.weights ?? {})
      setIsCustom(false)
      setDirty(false)
    } catch (e: any) { alert(e.message) }
    finally { setSaving(false) }
  }

  if (loading) return <div className="py-8 text-center text-muted-foreground text-sm"><Loader2 className="h-5 w-5 animate-spin inline mr-2" />Loading weights…</div>
  if (!Object.keys(weights).length) return <p className="text-muted-foreground text-sm py-4">No criteria weights configured for this tender.</p>

  return (
    <div className="max-w-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-sm">Criteria Importance Weights</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Adjust how much each criterion contributes to the overall compliance score.
            {isCustom && <span className="ml-2 text-amber-600 font-medium">(Custom weights active)</span>}
          </p>
        </div>
        {isCustom && (
          <Button size="sm" variant="ghost" onClick={handleReset} disabled={saving} className="text-xs text-muted-foreground">
            Reset to defaults
          </Button>
        )}
      </div>
      <div className="space-y-3">
        {Object.entries(weights).map(([key, val]) => (
          <div key={key} className="flex items-center gap-3">
            <span className="w-48 text-xs font-medium truncate capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={val}
              onChange={e => handleChange(key, parseFloat(e.target.value))}
              className="flex-1 accent-primary"
            />
            <span className="w-12 text-xs text-right tabular-nums">{Math.round(val * 100)}%</span>
          </div>
        ))}
      </div>
      <div className={`mt-2 text-xs ${Math.abs(total - 1) > 0.05 ? 'text-red-600 font-semibold' : 'text-muted-foreground'}`}>
        Total: {Math.round(total * 100)}% {Math.abs(total - 1) > 0.05 && '— weights should sum to 100%'}
      </div>
      {dirty && (
        <Button size="sm" className="mt-4" onClick={handleSave} disabled={saving || Math.abs(total - 1) > 0.05}>
          {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
          Save Weights
        </Button>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

type Tab = 'heatmap' | 'collusion' | 'audit' | 'vendors' | 'analytics' | 'qa' | 'weights'

export default function EvaluationBoardPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = parseInt(id ?? '0')

  const [tab, setTab] = useState<Tab>('heatmap')
  const [project, setProject] = useState<any>(null)
  const [bidders, setBidders] = useState<Bidder[]>([])
  const [verdicts, setVerdicts] = useState<Verdict[]>([])
  const [alerts, setAlerts] = useState<CollusionAlert[]>([])
  const [collusionRisk, setCollusionRisk] = useState('—')
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [bidderDocUrls, setBidderDocUrls] = useState<Record<number, string>>({})
  const [criteriaMap, setCriteriaMap] = useState<Record<string, { mandatory: boolean; category: string }>>({})
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showSignOff, setShowSignOff] = useState(false)
  const [officerName, setOfficerName] = useState('')
  const [signingOff, setSigningOff] = useState(false)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [proj, bids, vds, ats] = await Promise.allSettled([
        api.getProject(projectId),
        api.getBidders(projectId),
        api.getVerdictsMatrix(projectId),
        api.getAuditTrail(projectId),
      ])
      if (proj.status === 'fulfilled') setProject(proj.value)
      if (vds.status === 'fulfilled') setVerdicts(vds.value)
      if (ats.status === 'fulfilled') setAuditEvents(ats.value)

      if (bids.status === 'fulfilled') {
        setBidders(bids.value)
        // Load first document URL per bidder for PDF evidence highlighting
        const docUrlMap: Record<number, string> = {}
        await Promise.allSettled(
          bids.value.map(async (b) => {
            const docs = await api.getBidderDocuments(b.id).catch(() => [])
            const withUrl = docs.find(d => d.cloudinary_url)
            if (withUrl?.cloudinary_url) docUrlMap[b.id] = withUrl.cloudinary_url
          })
        )
        setBidderDocUrls(docUrlMap)
      }

      const alertsRes = await api.getCollusionAlerts(projectId).catch(() => [])
      setAlerts(alertsRes)

      // Load tender criteria to know which are mandatory vs preferred
      const tenderCriteria = await api.getTenderCriteria(projectId).catch(() => null)
      if (tenderCriteria?.criteria) {
        const map: Record<string, { mandatory: boolean; category: string }> = {}
        for (const c of tenderCriteria.criteria) {
          map[c.criterion_id] = {
            mandatory: c.mandatory ?? true,
            category: c.category ?? (c.mandatory ? 'Mandatory' : 'Preferred'),
          }
        }
        setCriteriaMap(map)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { load() }, [load])

  const runEvaluateAll = async () => {
    setRunning('evaluate')
    try {
      await api.evaluateAllBidders(projectId)
      await load()
    } catch (e: any) { alert(`Evaluation failed: ${e.message}`) }
    finally { setRunning(null) }
  }

  const runCollusion = async () => {
    setRunning('collusion')
    try {
      const res = await api.detectCollusion(projectId)
      setCollusionRisk(res.overall_risk ?? 'Low')
      await load()
    } catch (e: any) { alert(`Collusion detection failed: ${e.message}`) }
    finally { setRunning(null) }
  }

  const handleSignOff = async () => {
    if (!officerName.trim()) return
    setSigningOff(true)
    try {
      await api.signOffTender(projectId, officerName.trim())
      setShowSignOff(false)
      setOfficerName('')
      await load()
    } catch (e: any) { alert(`Sign-off failed: ${e.message}`) }
    finally { setSigningOff(false) }
  }

  // Summary counts
  const eligible   = verdicts.filter(v => (v.human_override ? v.override_verdict : v.verdict) === 'Eligible').length
  const notElig    = verdicts.filter(v => (v.human_override ? v.override_verdict : v.verdict) === 'Not_Eligible').length
  const manual     = verdicts.filter(v => (v.human_override ? v.override_verdict : v.verdict) === 'Manual_Review').length

  if (loading) return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </main>
    </div>
  )

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-6 max-w-screen-2xl">

        {/* Top bar */}
        <div className="mb-6">
          <Button variant="ghost" className="mb-3 pl-0" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4 mr-2" /> Back
          </Button>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold">Evaluation Board</h1>
              <p className="text-muted-foreground text-sm mt-0.5">
                {project?.name ?? `Tender #${projectId}`} · {bidders.length} bidder{bidders.length !== 1 ? 's' : ''}
              </p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate(`/admin/evaluations/${projectId}/bidders`)}
              >
                <Users className="h-4 w-4 mr-2" />
                Manage Bidders
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={runEvaluateAll}
                disabled={running !== null || bidders.length === 0}
              >
                {running === 'evaluate' ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                Evaluate All
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={runCollusion}
                disabled={running !== null || bidders.length < 2}
              >
                {running === 'collusion' ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ShieldAlert className="h-4 w-4 mr-2" />}
                Detect Collusion
              </Button>
              {manual > 0 && (
                <Button
                  size="sm"
                  onClick={() => navigate(`/admin/evaluations/${projectId}/review`)}
                  className="bg-amber-500 hover:bg-amber-600 text-white border-0"
                >
                  <ClipboardList className="h-4 w-4 mr-2" />
                  Review Queue ({manual})
                </Button>
              )}
              <Button
                size="sm"
                variant="outline"
                onClick={() => api.downloadEvaluationReport(projectId)}
                title="Download 9-stage evaluation PDF report"
              >
                <Download className="h-4 w-4 mr-2" />
                Report
              </Button>
              {project?.signed_by ? (
                <span className="inline-flex items-center gap-1 text-[11px] px-3 py-1.5 rounded-md bg-emerald-100 text-emerald-700 font-medium border border-emerald-300">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Signed by {project.signed_by}
                </span>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowSignOff(true)}
                  disabled={manual > 0}
                  title={manual > 0 ? 'Resolve all Manual Review verdicts before signing off' : 'Officer digital sign-off'}
                  className="border-emerald-400 text-emerald-700 hover:bg-emerald-50"
                >
                  <PenLine className="h-4 w-4 mr-2" />
                  Sign Off
                </Button>
              )}
              <Button size="sm" variant="ghost" onClick={load} disabled={loading}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {error && (
          <Card className="p-4 mb-4 border-red-300 bg-red-50 text-red-700 text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {error}
          </Card>
        )}

        {/* KPI row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Bidders', value: bidders.length, color: 'text-foreground' },
            { label: 'Eligible / योग्य', value: eligible, color: 'text-emerald-600' },
            { label: 'Not Eligible / अयोग्य', value: notElig, color: 'text-red-600' },
            { label: 'Manual Review / समीक्षा', value: manual, color: 'text-amber-600' },
          ].map(k => (
            <Card key={k.label} className="p-4 text-center">
              <div className={`text-3xl font-bold ${k.color}`}>{k.value}</div>
              <div className="text-xs text-muted-foreground mt-0.5">{k.label}</div>
            </Card>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-border mb-5">
          {([
            { key: 'heatmap',  label: 'Confidence Heatmap', icon: BarChart3 },
            { key: 'collusion', label: `Collusion Alerts${alerts.length ? ` (${alerts.length})` : ''}`, icon: ShieldAlert },
            { key: 'audit',     label: `Audit Trail${auditEvents.length ? ` (${auditEvents.length})` : ''}`, icon: Clock },
            { key: 'vendors',   label: 'Vendor History', icon: Building2 },
            { key: 'analytics', label: 'DP Analytics', icon: Lock },
            { key: 'qa',        label: 'Q&A Assistant', icon: MessageSquare },
            { key: 'weights',   label: 'Criteria Weights', icon: TrendingUp },
          ] as { key: Tab; label: string; icon: any }[]).map(t => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <t.icon className="h-4 w-4" />
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <Card className="p-5">
          {tab === 'heatmap' && (
            <ConfidenceHeatmap verdicts={verdicts} bidders={bidders} bidderDocUrls={bidderDocUrls} criteriaMap={criteriaMap} />
          )}
          {tab === 'collusion' && (
            <CollusionPanel alerts={alerts} risk={collusionRisk} />
          )}
          {tab === 'audit' && (
            <AuditTrailPanel events={auditEvents} />
          )}
          {tab === 'vendors' && (
            <VendorHistoryPanel projectId={projectId} />
          )}
          {tab === 'analytics' && (
            <AnalyticsPanel projectId={projectId} />
          )}
          {tab === 'qa' && (
            <EvaluationQAPanel projectId={projectId} />
          )}
          {tab === 'weights' && (
            <CriteriaWeightsPanel projectId={projectId} />
          )}
        </Card>
      </main>

      {/* ── Sign-off confirmation modal ── */}
      {showSignOff && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setShowSignOff(false)}
        >
          <div
            className="bg-background rounded-xl shadow-2xl w-full max-w-md p-6"
            onClick={e => e.stopPropagation()}
          >
            <h2 className="text-lg font-bold mb-1">Officer Digital Sign-Off</h2>
            <p className="text-sm text-muted-foreground mb-4">
              By signing off you confirm that all AI-assisted verdicts have been reviewed
              and that this evaluation report is cleared for procurement action.
              This action is recorded in the immutable audit trail.
            </p>
            <label className="block text-sm font-medium mb-1">Authorising Officer Name &amp; Designation</label>
            <input
              type="text"
              className="w-full border border-border rounded-lg px-3 py-2 text-sm bg-background mb-4 focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g. DIG (Procurement) John Smith"
              value={officerName}
              onChange={e => setOfficerName(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSignOff() }}
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setShowSignOff(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700 text-white border-0"
                onClick={handleSignOff}
                disabled={signingOff || !officerName.trim()}
              >
                {signingOff ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <PenLine className="h-4 w-4 mr-2" />}
                Confirm Sign-Off
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
