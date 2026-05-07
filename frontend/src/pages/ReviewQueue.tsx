import { Header } from '@/components/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import {
  ArrowLeft, CheckCircle, XCircle, Clock, FileText,
  Loader2, AlertTriangle, ChevronDown, ChevronUp,
  User, RefreshCw, ClipboardCheck
} from 'lucide-react'
import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, type Verdict, type Bidder } from '@/lib/api'

// ── helpers ──────────────────────────────────────────────────────────────────

function confLabel(score: number) {
  const pct = Math.round(score * 100)
  const color = score >= 0.9 ? 'text-emerald-600' : score >= 0.6 ? 'text-amber-600' : 'text-red-500'
  return <span className={`font-mono font-medium ${color}`}>{pct}%</span>
}

function tamperBadge(score?: number | null) {
  if (score == null) return null
  const level = score < 0.3 ? 'Low' : score < 0.65 ? 'Medium' : 'High'
  const cls = level === 'Low' ? 'bg-emerald-50 text-emerald-700' : level === 'Medium' ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-600'
  return <span className={`text-[11px] font-medium px-2 py-0.5 rounded ${cls}`}>Tamper risk: {level}</span>
}

function critTypeBadge(type?: string) {
  if (!type) return null
  return (
    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-muted text-muted-foreground capitalize">
      {type.replace(/_/g, ' ')}
    </span>
  )
}

// ── ReviewItem ────────────────────────────────────────────────────────────────

interface ReviewItemProps {
  verdict: Verdict
  criterion: any
  bidderName: string
  onSubmit: (verdictId: number, decision: 'Eligible' | 'Not_Eligible', justification: string) => Promise<void>
  isLast: boolean
}

function ReviewItem({ verdict, criterion, bidderName, onSubmit, isLast }: ReviewItemProps) {
  const [expanded, setExpanded] = useState(true)
  const [decision, setDecision] = useState<'Eligible' | 'Not_Eligible' | null>(null)
  const [justification, setJustification] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const canSubmit = decision !== null && justification.trim().length >= 10

  const handleSubmit = async () => {
    if (!canSubmit) return
    setSubmitting(true)
    setErr(null)
    try {
      await onSubmit(verdict.id, decision!, justification.trim())
      setDone(true)
    } catch (e: any) {
      setErr(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (done) {
    return (
      <Card className={`p-4 border-emerald-300 bg-emerald-50/60 ${!isLast ? 'mb-3' : ''}`}>
        <div className="flex items-center gap-2 text-emerald-700 text-sm font-medium">
          <CheckCircle className="h-4 w-4" />
          <span>{bidderName} — {verdict.criterion_id}: overridden to <strong>{decision}</strong></span>
        </div>
      </Card>
    )
  }

  return (
    <Card className={`border-amber-300/60 ${!isLast ? 'mb-4' : ''} overflow-hidden`}>
      {/* Header row */}
      <button
        className="w-full flex items-center gap-3 p-4 text-left hover:bg-muted/30 transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        <Clock className="h-4 w-4 text-amber-500 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm">{verdict.criterion_id}</span>
            {critTypeBadge(criterion?.criterion_type)}
            {criterion?.mandatory && (
              <span className="text-[10px] bg-red-50 text-red-600 px-1.5 py-0.5 rounded font-medium">Mandatory</span>
            )}
          </div>
          <div className="text-xs text-muted-foreground mt-0.5 flex items-center gap-2 flex-wrap">
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />{bidderName}
            </span>
            <span>·</span>
            <span>AI confidence: {confLabel(verdict.confidence_score)}</span>
            {tamperBadge(verdict.tamper_risk_score)}
          </div>
        </div>
        {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground shrink-0" /> : <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />}
      </button>

      {expanded && (
        <div className="px-4 pb-5 space-y-4 border-t border-border/40">

          {/* Criterion description */}
          {criterion?.description && (
            <div className="pt-3">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Criterion</p>
              <p className="text-sm">{criterion.description}</p>
              {criterion?.source_quote && (
                <blockquote className="mt-2 text-xs border-l-2 border-muted pl-3 text-muted-foreground italic">
                  "{criterion.source_quote.slice(0, 200)}{criterion.source_quote.length > 200 ? '…' : ''}"
                  {criterion.source_page && <span className="not-italic"> — tender p.{criterion.source_page}</span>}
                </blockquote>
              )}
              {criterion?.ambiguity_flag && (
                <div className="mt-2 text-xs text-amber-700 bg-amber-50 px-2 py-1.5 rounded flex items-start gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
                  <span><strong>Ambiguity flagged:</strong> {criterion.ambiguity_note}</span>
                </div>
              )}
            </div>
          )}

          {/* Threshold */}
          {verdict.threshold_value != null && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Required Threshold</p>
              <p className="text-sm font-mono">
                {criterion?.comparison_op?.toUpperCase() ?? '≥'} {
                  criterion?.threshold_unit === 'INR_paise'
                    ? `INR ${(verdict.threshold_value / 1e10).toFixed(2)} crore`
                    : `${verdict.threshold_value} ${criterion?.threshold_unit ?? ''}`
                }
                {criterion?.threshold_period && <span className="text-muted-foreground ml-2">({criterion.threshold_period.replace(/_/g, ' ')})</span>}
              </p>
            </div>
          )}

          {/* AI finding */}
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">AI Finding</p>
            {verdict.extracted_value_text && (
              <p className="text-sm text-emerald-700 font-medium mb-1">Found: {verdict.extracted_value_text}</p>
            )}
            {verdict.reasoning && <p className="text-sm text-muted-foreground">{verdict.reasoning}</p>}
          </div>

          {/* Evidence */}
          {verdict.evidence_quote && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                Evidence Quote{verdict.evidence_page != null && ` (page ${verdict.evidence_page})`}
              </p>
              <blockquote className="text-sm border-l-2 border-primary/40 pl-3 text-muted-foreground italic">
                "{verdict.evidence_quote.slice(0, 300)}{verdict.evidence_quote.length > 300 ? '…' : ''}"
              </blockquote>
            </div>
          )}

          {/* Officer decision */}
          <div className="border-t border-border/40 pt-4 space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wide">Officer Decision</p>
            <div className="flex gap-2">
              <button
                onClick={() => setDecision('Eligible')}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${
                  decision === 'Eligible'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                    : 'border-border hover:border-emerald-300 hover:bg-emerald-50/40 text-muted-foreground'
                }`}
              >
                <CheckCircle className="h-4 w-4" /> Eligible
              </button>
              <button
                onClick={() => setDecision('Not_Eligible')}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${
                  decision === 'Not_Eligible'
                    ? 'border-red-500 bg-red-50 text-red-700'
                    : 'border-border hover:border-red-300 hover:bg-red-50/40 text-muted-foreground'
                }`}
              >
                <XCircle className="h-4 w-4" /> Not Eligible
              </button>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1 block">
                Justification <span className="text-red-500">*</span>
                <span className="font-normal ml-1">(minimum 10 characters, logged to immutable audit trail)</span>
              </label>
              <textarea
                rows={3}
                value={justification}
                onChange={e => setJustification(e.target.value)}
                placeholder="Explain your decision with reference to the document…"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              />
              {justification.length > 0 && justification.trim().length < 10 && (
                <p className="text-xs text-red-500 mt-0.5">{10 - justification.trim().length} more characters required</p>
              )}
            </div>

            {err && <p className="text-xs text-red-500">{err}</p>}

            <Button
              onClick={handleSubmit}
              disabled={!canSubmit || submitting}
              className="w-full"
            >
              {submitting
                ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Submitting…</>
                : <><ClipboardCheck className="h-4 w-4 mr-2" />Submit Override</>
              }
            </Button>
          </div>
        </div>
      )}
    </Card>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

const DEFAULT_OFFICER_ID = 1

export default function ReviewQueuePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = parseInt(id ?? '0')

  const [loading, setLoading] = useState(true)
  const [project, setProject] = useState<any>(null)
  const [pendingVerdicts, setPendingVerdicts] = useState<Verdict[]>([])
  const [resolvedCount, setResolvedCount] = useState(0)
  const [criteriaMap, setCriteriaMap] = useState<Record<string, any>>({})
  const [bidderMap, setBidderMap] = useState<Record<number, string>>({})
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const [proj, bidders, allVerdicts] = await Promise.all([
        api.getProject(projectId),
        api.getBidders(projectId),
        api.getVerdictsMatrix(projectId),
      ])

      setProject(proj)
      const bMap: Record<number, string> = {}
      for (const b of bidders) bMap[b.id] = b.company_name
      setBidderMap(bMap)

      // Only show verdicts that are still Manual_Review and not yet overridden
      const pending = allVerdicts.filter(
        v => v.verdict === 'Manual_Review' && !v.human_override
      )
      setPendingVerdicts(pending)
      setResolvedCount(
        allVerdicts.filter(v => v.verdict === 'Manual_Review' && v.human_override).length
      )

      // Load criteria map
      try {
        const cdata = await api.getTenderCriteria(projectId)
        const cMap: Record<string, any> = {}
        for (const c of cdata?.criteria ?? []) cMap[c.criterion_id] = c
        setCriteriaMap(cMap)
      } catch {
        // criteria not extracted yet — proceed without descriptions
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => { load() }, [load])

  const handleOverride = async (
    verdictId: number,
    decision: 'Eligible' | 'Not_Eligible',
    justification: string,
  ) => {
    await api.overrideVerdict(verdictId, decision, justification, DEFAULT_OFFICER_ID)
    // Decrement local pending list count — ReviewItem marks itself done visually
    setResolvedCount(c => c + 1)
  }

  const totalManual = pendingVerdicts.length + resolvedCount
  const progressPct = totalManual > 0 ? Math.round((resolvedCount / totalManual) * 100) : 100

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
      <main className="flex-1 container mx-auto px-4 py-6 max-w-4xl">

        {/* Top bar */}
        <div className="mb-6">
          <Button variant="ghost" className="mb-3 pl-0" onClick={() => navigate(`/admin/evaluations/${projectId}`)}>
            <ArrowLeft className="h-4 w-4 mr-2" /> Back to Evaluation Board
          </Button>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Clock className="h-6 w-6 text-amber-500" />
                Manual Review Queue
              </h1>
              <p className="text-muted-foreground text-sm mt-0.5">
                {project?.name ?? `Tender #${projectId}`}
              </p>
            </div>
            <Button size="sm" variant="ghost" onClick={load}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {error && (
          <Card className="p-4 mb-4 border-red-300 bg-red-50 text-red-700 text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {error}
          </Card>
        )}

        {/* Progress bar */}
        <Card className="p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Review Progress</span>
            <span className="text-sm text-muted-foreground">
              {resolvedCount} / {totalManual} resolved
            </span>
          </div>
          <div className="h-2.5 rounded-full bg-muted overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${progressPct === 100 ? 'bg-emerald-500' : 'bg-amber-400'}`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
          {progressPct === 100 && totalManual > 0 && (
            <p className="text-xs text-emerald-600 font-medium mt-2 flex items-center gap-1">
              <CheckCircle className="h-3.5 w-3.5" /> All manual reviews resolved — evaluation is complete.
            </p>
          )}
        </Card>

        {pendingVerdicts.length === 0 && (
          <Card className="p-12 text-center">
            {totalManual === 0 ? (
              <>
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-40" />
                <h3 className="text-lg font-semibold mb-1">No Manual Reviews</h3>
                <p className="text-muted-foreground text-sm">
                  All criteria were evaluated with high confidence — no officer review needed.
                </p>
              </>
            ) : (
              <>
                <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-1 text-emerald-700">All Reviews Complete</h3>
                <p className="text-muted-foreground text-sm mb-4">
                  {resolvedCount} item{resolvedCount !== 1 ? 's' : ''} reviewed and signed off.
                </p>
                <Button onClick={() => navigate(`/admin/evaluations/${projectId}`)}>
                  View Evaluation Board
                </Button>
              </>
            )}
          </Card>
        )}

        {pendingVerdicts.length > 0 && (
          <div className="space-y-0">
            <div className="text-sm text-muted-foreground mb-4">
              {pendingVerdicts.length} item{pendingVerdicts.length !== 1 ? 's' : ''} pending officer review
              <span className="ml-2 text-[11px]">— decisions are written to the immutable audit trail</span>
            </div>
            {pendingVerdicts.map((v, idx) => (
              <ReviewItem
                key={v.id}
                verdict={v}
                criterion={criteriaMap[v.criterion_id]}
                bidderName={bidderMap[v.bidder_id] ?? `Bidder ${v.bidder_id}`}
                onSubmit={handleOverride}
                isLast={idx === pendingVerdicts.length - 1}
              />
            ))}
          </div>
        )}

        {/* Bottom nav */}
        {pendingVerdicts.length > 0 && (
          <div className="mt-6 flex justify-between items-center text-sm text-muted-foreground">
            <span>{pendingVerdicts.length} remaining</span>
            <Button variant="outline" onClick={() => navigate(`/admin/evaluations/${projectId}`)}>
              Back to Board
            </Button>
          </div>
        )}

      </main>
    </div>
  )
}
