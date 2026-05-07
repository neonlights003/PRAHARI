import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '@/components/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import {
  Upload, FileText, Trash2, Plus, Loader2, CheckCircle, XCircle,
  Clock, AlertTriangle, ArrowLeft, ArrowRight, Shield, ChevronDown, ChevronUp,
} from 'lucide-react'

const API = 'http://127.0.0.1:8000'

const DOCUMENT_TYPES = [
  'Audited Balance Sheet',
  'Profit & Loss Statement',
  'CA Certificate – Turnover',
  'CA Certificate – Net Worth',
  'Work Order',
  'Completion Certificate',
  'Experience Certificate',
  'GST Registration Certificate',
  'PAN Card',
  'EMD / Bid Security',
  'Integrity Pact',
  'Power of Attorney',
  'Bank Solvency Certificate',
  'Affidavit / Self-declaration',
  'ISO / Quality Certificate',
  'Other',
]

interface UploadRow { docType: string; file: File | null }
interface Tender { id: number; name: string; state?: string; sector?: string }

interface AuthDoc {
  filename: string
  document_type: string
  authenticity_score: number
  tamper_risk_level: string
  flags: string[]
  language?: string
}

interface VerdictRow {
  criterion_id: string
  criterion_name?: string
  verdict: string
  confidence_score: number
  extracted_value_text?: string
  evidence_quote?: string
  reasoning?: string
}

interface Assessment {
  overall_assessment: string
  project_name: string
  company_name: string
  summary: { eligible: number; not_eligible: number; manual_review: number; total_criteria: number; avg_confidence: number }
  documents: AuthDoc[]
  verdicts: VerdictRow[]
  disclaimer: string
}

// ── helpers ───────────────────────────────────────────────────────────────────

function verdictBadge(v: string) {
  if (v === 'Eligible')     return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium"><CheckCircle className="h-3 w-3" />Eligible</span>
  if (v === 'Not_Eligible') return <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium"><XCircle className="h-3 w-3" />Not Eligible</span>
  return                          <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium"><Clock className="h-3 w-3" />Needs Review</span>
}

function authBadge(score: number, risk: string) {
  const color = score >= 0.7 ? 'bg-emerald-100 text-emerald-700' : score >= 0.4 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
  return <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${color}`}><Shield className="h-3 w-3" />{(score * 100).toFixed(0)}% · {risk}</span>
}

function confBar(score: number) {
  const pct = Math.round(score * 100)
  const color = score >= 0.9 ? 'bg-emerald-500' : score >= 0.6 ? 'bg-amber-400' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[10px] text-muted-foreground">{pct}%</span>
    </div>
  )
}

function OverallBanner({ overall }: { overall: string }) {
  if (overall === 'Likely_Eligible')
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
        <CheckCircle className="h-8 w-8 text-emerald-600 shrink-0" />
        <div>
          <p className="font-semibold text-emerald-700">Likely Eligible</p>
          <p className="text-xs text-emerald-600">All criteria appear met based on uploaded documents. Proceed to official submission.</p>
        </div>
      </div>
    )
  if (overall === 'Likely_Not_Eligible')
    return (
      <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 border border-red-200">
        <XCircle className="h-8 w-8 text-red-600 shrink-0" />
        <div>
          <p className="font-semibold text-red-700">Likely Not Eligible</p>
          <p className="text-xs text-red-600">One or more mandatory criteria appear unmet. Review the details below before submitting.</p>
        </div>
      </div>
    )
  return (
    <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-50 border border-amber-200">
      <AlertTriangle className="h-8 w-8 text-amber-600 shrink-0" />
      <div>
        <p className="font-semibold text-amber-700">Needs Further Review</p>
        <p className="text-xs text-amber-600">Some criteria require manual officer verification. Address flagged items and re-check before submitting.</p>
      </div>
    </div>
  )
}

function VerdictCard({ v }: { v: VerdictRow }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-muted/40 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="font-mono text-xs text-muted-foreground w-20 shrink-0">{v.criterion_id}</span>
          <span className="text-sm font-medium truncate">{v.criterion_name || v.criterion_id}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-3">
          {verdictBadge(v.verdict)}
          {open ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </div>
      </button>
      {open && (
        <div className="px-4 pb-4 pt-1 border-t border-border/50 space-y-2 text-xs text-muted-foreground bg-muted/20">
          <div>{confBar(v.confidence_score)}<span>Confidence: {(v.confidence_score * 100).toFixed(0)}%</span></div>
          {v.extracted_value_text && <p><span className="font-medium text-foreground">Found in docs:</span> {v.extracted_value_text}</p>}
          {v.evidence_quote && (
            <blockquote className="border-l-2 border-primary/50 pl-2 italic text-foreground/70">{v.evidence_quote}</blockquote>
          )}
          {v.reasoning && <p>{v.reasoning}</p>}
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function SelfCheckPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<1 | 2 | 3>(1)

  // Step 1
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loadingTenders, setLoadingTenders] = useState(true)
  const [selectedTender, setSelectedTender] = useState<Tender | null>(null)

  // Step 2
  const [companyName, setCompanyName] = useState('')
  const [rows, setRows] = useState<UploadRow[]>([{ docType: DOCUMENT_TYPES[0], file: null }])
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Step 3
  const [result, setResult] = useState<Assessment | null>(null)

  useEffect(() => {
    fetch(`${API}/projects`)
      .then(r => r.json())
      .then(d => setTenders(d.projects ?? []))
      .catch(() => {})
      .finally(() => setLoadingTenders(false))
  }, [])

  const addRow = () => setRows(r => [...r, { docType: DOCUMENT_TYPES[0], file: null }])

  const removeRow = (i: number) => setRows(r => r.filter((_, idx) => idx !== i))

  const updateRow = (i: number, patch: Partial<UploadRow>) =>
    setRows(r => r.map((row, idx) => idx === i ? { ...row, ...patch } : row))

  const handleSubmit = async () => {
    if (!selectedTender) return
    if (!companyName.trim()) { setSubmitError('Company name is required.'); return }
    const ready = rows.filter(r => r.file)
    if (ready.length === 0) { setSubmitError('Upload at least one document.'); return }

    setSubmitting(true)
    setSubmitError(null)

    const fd = new FormData()
    fd.append('company_name', companyName.trim())
    fd.append('document_types', JSON.stringify(ready.map(r => r.docType)))
    ready.forEach(r => fd.append('files', r.file!))

    try {
      const res = await fetch(`${API}/api/self-check/${selectedTender.id}`, {
        method: 'POST',
        body: fd,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Self-check failed')
      setResult(data)
      setStep(3)
    } catch (e: any) {
      setSubmitError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const reset = () => {
    setStep(1); setSelectedTender(null); setCompanyName(''); setSubmitError(null)
    setRows([{ docType: DOCUMENT_TYPES[0], file: null }]); setResult(null)
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="max-w-3xl mx-auto px-4 py-8">
        {/* Back */}
        <Button variant="ghost" className="mb-4 pl-0" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back
        </Button>

        <h1 className="text-2xl font-bold mb-1">Pre-submission Self-Check</h1>
        <p className="text-muted-foreground text-sm mb-6">
          Upload your documents to get an instant AI-powered eligibility assessment before official submission. Results are ephemeral and carry no legal weight.
        </p>

        {/* Stepper */}
        <div className="flex items-center gap-2 mb-8">
          {(['Select Tender', 'Upload Documents', 'Assessment'].map((label, i) => {
            const n = (i + 1) as 1 | 2 | 3
            const active = step === n
            const done = step > n
            return (
              <div key={n} className="flex items-center gap-2">
                <div className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors ${
                  done   ? 'bg-primary border-primary text-primary-foreground' :
                  active ? 'border-primary text-primary' :
                           'border-muted-foreground/30 text-muted-foreground'
                }`}>
                  {done ? <CheckCircle className="h-4 w-4" /> : n}
                </div>
                <span className={`text-sm font-medium ${active ? 'text-primary' : 'text-muted-foreground'}`}>{label}</span>
                {i < 2 && <div className="flex-1 h-px bg-border w-6 mx-1" />}
              </div>
            )
          }))}
        </div>

        {/* ── Step 1: Select Tender ── */}
        {step === 1 && (
          <Card className="p-6 space-y-4">
            <h2 className="font-semibold text-lg">Choose a Tender</h2>
            {loadingTenders ? (
              <div className="flex items-center gap-2 text-muted-foreground text-sm py-4">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading tenders…
              </div>
            ) : tenders.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4">No active tenders found. Please contact the procurement office.</p>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {tenders.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setSelectedTender(t)}
                    className={`w-full text-left rounded-lg border p-4 transition-colors ${
                      selectedTender?.id === t.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50 hover:bg-muted/30'
                    }`}
                  >
                    <p className="font-medium text-sm">{t.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{[t.state, t.sector].filter(Boolean).join(' · ')}</p>
                  </button>
                ))}
              </div>
            )}
            <Button
              className="w-full mt-2"
              disabled={!selectedTender}
              onClick={() => setStep(2)}
            >
              Continue <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </Card>
        )}

        {/* ── Step 2: Upload Documents ── */}
        {step === 2 && (
          <Card className="p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-lg">Company Details & Documents</h2>
              <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">{selectedTender?.name}</span>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Company / Firm Name <span className="text-destructive">*</span></label>
              <input
                type="text"
                value={companyName}
                onChange={e => setCompanyName(e.target.value)}
                placeholder="e.g. Sharma Construction Pvt. Ltd."
                className="w-full border border-border rounded-md px-3 py-2 text-sm bg-background focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Supporting Documents</label>
              <div className="space-y-3">
                {rows.map((row, i) => (
                  <div key={i} className="flex gap-2 items-start">
                    <select
                      value={row.docType}
                      onChange={e => updateRow(i, { docType: e.target.value })}
                      className="border border-border rounded px-2 py-2 text-xs bg-background w-48 shrink-0"
                    >
                      {DOCUMENT_TYPES.map(dt => <option key={dt} value={dt}>{dt}</option>)}
                    </select>
                    <label className={`flex-1 flex items-center gap-2 border-2 border-dashed rounded-lg px-3 py-2 cursor-pointer transition-colors text-xs ${
                      row.file ? 'border-primary/50 bg-primary/5' : 'border-border hover:border-primary/40'
                    }`}>
                      {row.file ? (
                        <><FileText className="h-4 w-4 text-primary shrink-0" /><span className="truncate text-primary font-medium">{row.file.name}</span></>
                      ) : (
                        <><Upload className="h-4 w-4 text-muted-foreground shrink-0" /><span className="text-muted-foreground">Click to upload PDF</span></>
                      )}
                      <input
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={e => { const f = e.target.files?.[0]; if (f) updateRow(i, { file: f }) }}
                      />
                    </label>
                    {rows.length > 1 && (
                      <button onClick={() => removeRow(i)} className="p-2 text-muted-foreground hover:text-destructive">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={addRow}
                className="mt-2 flex items-center gap-1 text-xs text-primary hover:underline"
              >
                <Plus className="h-3.5 w-3.5" /> Add another document
              </button>
            </div>

            {submitError && (
              <div className="text-xs text-destructive bg-destructive/10 rounded px-3 py-2">{submitError}</div>
            )}

            <div className="flex gap-2 pt-1">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ArrowLeft className="h-4 w-4 mr-2" /> Back
              </Button>
              <Button className="flex-1" onClick={handleSubmit} disabled={submitting}>
                {submitting
                  ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Analysing…</>
                  : <><Shield className="h-4 w-4 mr-2" />Run Self-Check</>
                }
              </Button>
            </div>
            {submitting && (
              <p className="text-xs text-muted-foreground text-center">
                Scoring document authenticity and matching eligibility criteria — this may take 30–60 seconds.
              </p>
            )}
          </Card>
        )}

        {/* ── Step 3: Results ── */}
        {step === 3 && result && (
          <div className="space-y-5">
            <OverallBanner overall={result.overall_assessment} />

            {/* KPI row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Eligible',     value: result.summary.eligible,     color: 'text-emerald-600' },
                { label: 'Not Eligible', value: result.summary.not_eligible,  color: 'text-red-600' },
                { label: 'Needs Review', value: result.summary.manual_review, color: 'text-amber-600' },
                { label: 'Avg Confidence', value: `${(result.summary.avg_confidence * 100).toFixed(0)}%`, color: 'text-foreground' },
              ].map(k => (
                <Card key={k.label} className="p-3 text-center">
                  <p className={`text-2xl font-bold ${k.color}`}>{k.value}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{k.label}</p>
                </Card>
              ))}
            </div>

            {/* Document authenticity */}
            <Card className="p-4">
              <h3 className="font-semibold text-sm mb-3">Document Authenticity</h3>
              <div className="space-y-3">
                {result.documents.map((d, i) => (
                  <div key={i} className="flex flex-col gap-1 pb-3 border-b border-border/50 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                        <span className="text-sm font-medium truncate">{d.filename}</span>
                        <span className="text-xs text-muted-foreground">({d.document_type})</span>
                      </div>
                      {authBadge(d.authenticity_score, d.tamper_risk_level)}
                    </div>
                    {d.flags.length > 0 && (
                      <div className="flex flex-wrap gap-1 pl-6">
                        {d.flags.map((f, fi) => (
                          <span key={fi} className="text-[10px] px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">{f}</span>
                        ))}
                      </div>
                    )}
                    {d.language && <p className="text-[10px] text-muted-foreground pl-6">Language detected: {d.language}</p>}
                  </div>
                ))}
              </div>
            </Card>

            {/* Per-criterion verdicts */}
            <Card className="p-4">
              <h3 className="font-semibold text-sm mb-3">Criterion-by-Criterion Assessment</h3>
              <div className="space-y-2">
                {result.verdicts.map((v, i) => <VerdictCard key={i} v={v} />)}
              </div>
            </Card>

            {/* Disclaimer */}
            <div className="text-xs text-muted-foreground bg-muted/40 rounded-lg px-4 py-3 border border-border/50">
              <AlertTriangle className="inline h-3.5 w-3.5 mr-1 text-amber-500" />
              {result.disclaimer}
            </div>

            <Button variant="outline" className="w-full" onClick={reset}>
              Run Another Check
            </Button>
          </div>
        )}
      </main>
    </div>
  )
}
