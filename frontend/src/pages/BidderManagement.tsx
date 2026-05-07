import { Header } from '@/components/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import {
  ArrowLeft, Plus, Upload, Trash2, ChevronDown, ChevronUp,
  Loader2, AlertTriangle, CheckCircle, XCircle, Shield,
  FileText, RefreshCw, Play, User, Building2, Mail,
  Hash, X, BarChart3, Sparkles, ClipboardList
} from 'lucide-react'
import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, type Bidder, type BidderDocument } from '@/lib/api'

// ── constants ─────────────────────────────────────────────────────────────────

const DOCUMENT_TYPES = [
  'Audited Balance Sheet',
  'CA Certificate (Annual Turnover)',
  'CA Certificate (Net Worth)',
  'Work Order / Contract Copy',
  'Completion Certificate',
  'GST Registration Certificate',
  'PAN Card Copy',
  'ISO 9001 Certificate',
  'MSME / Udyam Certificate',
  'Company Registration Certificate',
  'Power of Attorney',
  'EMD / Bid Security Document',
  'Bank Solvency Certificate',
  'Experience Certificate',
  'Personnel CV / Qualification',
  'Other',
]

// ── helpers ───────────────────────────────────────────────────────────────────

function AuthBadge({ score, risk }: { score?: number | null; risk?: string | null }) {
  if (score == null) return <span className="text-[11px] text-muted-foreground">Scoring…</span>
  const pct = Math.round(score * 100)
  const level = risk ?? (score >= 0.7 ? 'Low' : score >= 0.4 ? 'Medium' : 'High')
  const cls = level === 'Low'
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : level === 'Medium'
    ? 'bg-amber-50 text-amber-700 border-amber-200'
    : 'bg-red-50 text-red-600 border-red-200'
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded border ${cls}`}>
      <Shield className="h-3 w-3" />
      {pct}% authentic · {level} risk
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending:                  'bg-muted text-muted-foreground',
    evaluating:               'bg-blue-50 text-blue-600',
    evaluated:                'bg-emerald-50 text-emerald-700',
    manual_review_required:   'bg-amber-50 text-amber-700',
    evaluation_failed:        'bg-red-50 text-red-600',
  }
  return (
    <span className={`text-[11px] font-medium px-2 py-0.5 rounded capitalize ${map[status] ?? 'bg-muted text-muted-foreground'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  )
}

// ── NitCriteriaCard ───────────────────────────────────────────────────────────

function NitCriteriaCard({ projectId }: { projectId: number }) {
  const [nit, setNit] = useState<{ uploaded: boolean; filename?: string } | null>(null)
  const [criteria, setCriteria] = useState<any[] | null>(null)
  const [uploading, setUploading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.getNITStatus(projectId).then(setNit).catch(() => setNit({ uploaded: false }))
    api.getTenderCriteria(projectId).then(c => setCriteria(Array.isArray(c?.criteria) ? c.criteria : null)).catch(() => {})
  }, [projectId])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setErr(null); setUploading(true)
    try {
      await api.uploadNIT(projectId, file)
      const status = await api.getNITStatus(projectId)
      setNit(status)
    } catch (ex: any) { setErr(ex.message) }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = '' }
  }

  const handleExtract = async () => {
    setErr(null); setExtracting(true)
    try {
      const result = await api.extractTenderCriteria(projectId)
      const c = result?.criteria_data?.criteria ?? result?.criteria ?? []
      setCriteria(c)
    } catch (ex: any) { setErr(ex.message) }
    finally { setExtracting(false) }
  }

  return (
    <Card className="p-5 mb-6 border-primary/20 bg-gradient-to-br from-primary/5 to-cyan-50/50">
      <div className="flex items-center gap-2 mb-4">
        <ClipboardList className="h-5 w-5 text-primary" />
        <h2 className="font-semibold text-base">Stage 1 — Tender NIT &amp; Criteria Extraction</h2>
      </div>

      {err && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700 flex items-start gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" /> {err}
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        {/* Upload zone */}
        <div className="flex-1">
          {nit?.uploaded ? (
            <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-3 py-2">
              <CheckCircle className="h-4 w-4 shrink-0" />
              <span className="truncate font-medium">{nit.filename}</span>
            </div>
          ) : (
            <label className="flex items-center gap-2 border-2 border-dashed border-primary/30 rounded px-4 py-3 cursor-pointer hover:border-primary/60 transition-colors text-sm text-muted-foreground">
              <Upload className="h-4 w-4 shrink-0" />
              {uploading ? 'Uploading to Gemini…' : 'Upload NIT document (PDF / DOCX)'}
              <input ref={fileRef} type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={handleUpload} disabled={uploading} />
            </label>
          )}
        </div>

        {/* Re-upload link */}
        {nit?.uploaded && !criteria?.length && (
          <label className="text-xs text-muted-foreground underline cursor-pointer">
            Replace
            <input type="file" accept=".pdf,.docx,.doc" className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
        )}

        {/* Extract button */}
        {nit?.uploaded && (
          <Button size="sm" onClick={handleExtract} disabled={extracting} className="shrink-0">
            {extracting
              ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Extracting…</>
              : <><Sparkles className="h-4 w-4 mr-2" />Extract Criteria</>}
          </Button>
        )}
      </div>

      {/* Criteria list */}
      {criteria && criteria.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">
            {criteria.length} criteria extracted
          </p>
          <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
            {criteria.map((c: any, i: number) => (
              <div key={c.id ?? i} className="flex items-start gap-2 text-sm bg-white border rounded px-3 py-2">
                <span className="font-mono text-[11px] text-primary shrink-0 mt-0.5">{c.id ?? `C${String(i + 1).padStart(3, '0')}`}</span>
                <span className="text-foreground leading-snug">{c.description ?? c.name ?? JSON.stringify(c)}</span>
                {c.mandatory && <span className="ml-auto shrink-0 text-[10px] font-medium text-red-600 bg-red-50 border border-red-200 px-1.5 py-0.5 rounded">Mandatory</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

// ── AddBidderModal ────────────────────────────────────────────────────────────

function AddBidderModal({
  projectId,
  onClose,
  onCreated,
}: {
  projectId: number
  onClose: () => void
  onCreated: (id: number) => void
}) {
  const [form, setForm] = useState({ company_name: '', gstin: '', pan: '', contact_email: '' })
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async () => {
    if (!form.company_name.trim()) { setErr('Company name is required'); return }
    setSaving(true); setErr(null)
    try {
      const res = await api.createBidder(projectId, {
        company_name: form.company_name.trim(),
        gstin: form.gstin.trim() || undefined,
        pan: form.pan.trim() || undefined,
        contact_email: form.contact_email.trim() || undefined,
      })
      onCreated(res.bidder_id)
    } catch (e: any) { setErr(e.message) }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md p-6 animate-in fade-in zoom-in duration-200">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Plus className="h-5 w-5 text-primary" /> Register Bidder
          </h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-3">
          {[
            { key: 'company_name', label: 'Company Name', required: true, placeholder: 'e.g. Acme Defense Supplies Pvt. Ltd.' },
            { key: 'gstin', label: 'GSTIN', required: false, placeholder: '22AAAAA0000A1Z5' },
            { key: 'pan', label: 'PAN', required: false, placeholder: 'AAAAA0000A' },
            { key: 'contact_email', label: 'Contact Email', required: false, placeholder: 'procurement@company.com' },
          ].map(field => (
            <div key={field.key}>
              <label className="text-sm font-medium block mb-1">
                {field.label}
                {field.required && <span className="text-red-500 ml-0.5">*</span>}
              </label>
              <input
                type={field.key === 'contact_email' ? 'email' : 'text'}
                value={form[field.key as keyof typeof form]}
                onChange={set(field.key as keyof typeof form)}
                placeholder={field.placeholder}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          ))}
        </div>

        {err && (
          <p className="mt-3 text-sm text-red-600 flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4" /> {err}
          </p>
        )}

        <div className="flex gap-2 mt-5">
          <Button variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
          <Button onClick={submit} disabled={saving} className="flex-1">
            {saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Plus className="h-4 w-4 mr-2" />}
            Register
          </Button>
        </div>
      </Card>
    </div>
  )
}

// ── UploadDocModal ────────────────────────────────────────────────────────────

function UploadDocModal({
  bidderId,
  bidderName,
  onClose,
  onUploaded,
}: {
  bidderId: number
  bidderName: string
  onClose: () => void
  onUploaded: () => void
}) {
  const [docType, setDocType] = useState(DOCUMENT_TYPES[0])
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const upload = async () => {
    if (!file) { setErr('Select a document first'); return }
    setUploading(true); setErr(null)
    try {
      const res = await api.uploadBidderDocument(bidderId, file, docType)
      setResult(res)
    } catch (e: any) { setErr(e.message) }
    finally { setUploading(false) }
  }

  if (result) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <Card className="w-full max-w-md p-6 animate-in fade-in zoom-in duration-200 text-center">
          <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-lg font-bold mb-1">Document Uploaded</h3>
          <p className="text-sm text-muted-foreground mb-2">{result.original_filename}</p>
          {result.authenticity_score != null && (
            <div className="inline-flex flex-col items-center gap-1 mt-2">
              <AuthBadge score={result.authenticity_score} risk={result.tamper_risk_level} />
              {result.authenticity_flags > 0 && (
                <span className="text-xs text-amber-600">{result.authenticity_flags} flag{result.authenticity_flags !== 1 ? 's' : ''} detected</span>
              )}
            </div>
          )}
          <div className="flex gap-2 mt-5">
            <Button variant="outline" onClick={() => { setResult(null); setFile(null); setDocType(DOCUMENT_TYPES[0]) }} className="flex-1">
              Upload Another
            </Button>
            <Button onClick={() => { onUploaded(); onClose() }} className="flex-1">Done</Button>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md p-6 animate-in fade-in zoom-in duration-200">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Upload className="h-5 w-5 text-primary" /> Upload Document
          </h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          For: <span className="font-medium text-foreground">{bidderName}</span>
        </p>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1">Document Type <span className="text-red-500">*</span></label>
            <select
              value={docType}
              onChange={e => setDocType(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {DOCUMENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium block mb-1">Document <span className="text-red-500">*</span></label>
            <div
              className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 hover:bg-muted/20 transition-colors"
              onClick={() => fileRef.current?.click()}
            >
              {file ? (
                <div className="flex items-center gap-2 justify-center text-sm">
                  <FileText className="h-5 w-5 text-primary" />
                  <span className="font-medium truncate max-w-[200px]">{file.name}</span>
                  <button
                    onClick={e => { e.stopPropagation(); setFile(null) }}
                    className="text-muted-foreground hover:text-red-500"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Click to select a document</p>
                  <p className="text-xs text-muted-foreground/60 mt-0.5">PDF · DOCX · JPG · PNG · TIFF — typed or scanned</p>
                </>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.tiff,.tif"
              className="hidden"
              onChange={e => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
        </div>

        {uploading && (
          <div className="mt-3 text-sm text-muted-foreground flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            Uploading and scoring authenticity — this may take 15–30s…
          </div>
        )}

        {err && (
          <p className="mt-3 text-sm text-red-600 flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4" /> {err}
          </p>
        )}

        <div className="flex gap-2 mt-5">
          <Button variant="outline" onClick={onClose} className="flex-1" disabled={uploading}>Cancel</Button>
          <Button onClick={upload} disabled={uploading || !file} className="flex-1">
            {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
            {uploading ? 'Uploading…' : 'Upload & Score'}
          </Button>
        </div>
      </Card>
    </div>
  )
}

// ── DocumentRow ───────────────────────────────────────────────────────────────

function DocumentRow({ doc }: { doc: BidderDocument }) {
  const flags = (doc.metadata_flags?.flags ?? []) as any[]
  const hasHighFlag = flags.some((f: any) => f.severity === 'Critical' || f.severity === 'High')

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg text-xs ${hasHighFlag ? 'bg-red-50 dark:bg-red-950/20' : 'bg-muted/30'}`}>
      <FileText className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium truncate max-w-[200px]" title={doc.original_filename}>
            {doc.original_filename}
          </span>
          <span className="text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{doc.document_type}</span>
          {doc.language_detected && doc.language_detected !== 'en' && (
            <span className="text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded font-mono">{doc.language_detected}</span>
          )}
        </div>
        <div className="mt-1 flex items-center gap-2 flex-wrap">
          <AuthBadge score={doc.authenticity_score} risk={doc.tamper_risk_level} />
          {flags.length > 0 && (
            <span className="text-amber-600">{flags.length} flag{flags.length !== 1 ? 's' : ''}</span>
          )}
        </div>
        {flags.length > 0 && (
          <ul className="mt-1.5 space-y-0.5">
            {flags.slice(0, 3).map((f: any, i: number) => (
              <li key={i} className="flex items-start gap-1 text-muted-foreground">
                <AlertTriangle className={`h-3 w-3 mt-0.5 shrink-0 ${f.severity === 'High' || f.severity === 'Critical' ? 'text-red-500' : 'text-amber-500'}`} />
                <span>{f.description}</span>
              </li>
            ))}
            {flags.length > 3 && <li className="text-muted-foreground pl-4">+{flags.length - 3} more</li>}
          </ul>
        )}
      </div>
    </div>
  )
}

// ── BidderCard ────────────────────────────────────────────────────────────────

function BidderCard({
  bidder,
  onDelete,
  onEvaluate,
  onUpload,
}: {
  bidder: Bidder & { documents: BidderDocument[] }
  onDelete: (id: number) => void
  onEvaluate: (id: number) => void
  onUpload: (bidder: Bidder) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const docs = bidder.documents ?? []
  const avgAuth = docs.length > 0
    ? docs.reduce((s, d) => s + (d.authenticity_score ?? 0.5), 0) / docs.length
    : null
  const highRisk = docs.filter(d => d.tamper_risk_level === 'High').length

  const handleEvaluate = async () => {
    setEvaluating(true)
    try { await onEvaluate(bidder.id) } finally { setEvaluating(false) }
  }

  const handleDelete = async () => {
    if (!confirm(`Delete bidder "${bidder.company_name}" and all their documents?`)) return
    setDeleting(true)
    try { await onDelete(bidder.id) } finally { setDeleting(false) }
  }

  return (
    <Card className={`overflow-hidden transition-all ${highRisk > 0 ? 'border-red-300 dark:border-red-700' : ''}`}>
      {/* Card header */}
      <div className="flex items-start gap-3 p-4">
        <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
          <Building2 className="h-4.5 w-4.5 text-primary" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold">{bidder.company_name}</span>
            <StatusBadge status={bidder.status} />
            {highRisk > 0 && (
              <span className="text-[11px] bg-red-50 text-red-600 border border-red-200 px-1.5 py-0.5 rounded font-medium">
                {highRisk} high-risk doc{highRisk !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
            {bidder.gstin && <span className="flex items-center gap-1"><Hash className="h-3 w-3" />GSTIN: {bidder.gstin}</span>}
            {bidder.pan && <span className="flex items-center gap-1"><Hash className="h-3 w-3" />PAN: {bidder.pan}</span>}
            {bidder.contact_email && <span className="flex items-center gap-1"><Mail className="h-3 w-3" />{bidder.contact_email}</span>}
          </div>
          <div className="mt-1.5 flex items-center gap-3 flex-wrap">
            <span className="text-xs text-muted-foreground">{docs.length} document{docs.length !== 1 ? 's' : ''}</span>
            {avgAuth != null && <AuthBadge score={avgAuth} risk={highRisk > 0 ? 'High' : avgAuth >= 0.7 ? 'Low' : 'Medium'} />}
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <Button size="sm" variant="outline" onClick={() => onUpload(bidder)} title="Upload document">
            <Upload className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleEvaluate}
            disabled={evaluating || docs.length === 0}
            title={docs.length === 0 ? 'Upload documents first' : 'Run criterion matching'}
          >
            {evaluating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
          </Button>
          <Button size="sm" variant="ghost" className="text-red-500 hover:bg-red-50" onClick={handleDelete} disabled={deleting}>
            {deleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
          </Button>
          <button
            onClick={() => setExpanded(e => !e)}
            className="p-1.5 rounded hover:bg-muted transition-colors text-muted-foreground"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Documents panel */}
      {expanded && (
        <div className="border-t border-border/50 px-4 py-3 space-y-2 bg-muted/10">
          {docs.length === 0 ? (
            <div className="text-center py-6 text-sm text-muted-foreground">
              <FileText className="h-8 w-8 mx-auto mb-2 opacity-30" />
              No documents uploaded yet
              <br />
              <button onClick={() => onUpload(bidder)} className="text-primary hover:underline text-xs mt-1">
                Upload first document
              </button>
            </div>
          ) : (
            docs.map(d => <DocumentRow key={d.id} doc={d} />)
          )}
        </div>
      )}
    </Card>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function BidderManagementPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const projectId = parseInt(id ?? '0')

  const [project, setProject] = useState<any>(null)
  const [bidders, setBidders] = useState<(Bidder & { documents: BidderDocument[] })[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [uploadTarget, setUploadTarget] = useState<Bidder | null>(null)
  const [evaluatingAll, setEvaluatingAll] = useState(false)

  const load = useCallback(async () => {
    try {
      setLoading(true); setError(null)
      const [proj, rawBidders] = await Promise.all([
        api.getProject(projectId),
        api.getBidders(projectId),
      ])
      setProject(proj)
      const full = await Promise.all(
        rawBidders.map(async b => {
          const docs = await api.getBidderDocuments(b.id).catch(() => [])
          return { ...b, documents: docs }
        })
      )
      setBidders(full)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }, [projectId])

  useEffect(() => { load() }, [load])

  const handleBidderCreated = async () => {
    setShowAddModal(false)
    await load()
  }

  const handleDelete = async (bidderId: number) => {
    await api.deleteBidder(bidderId)
    await load()
  }

  const handleEvaluate = async (bidderId: number) => {
    await api.evaluateBidder(projectId, bidderId)
    await load()
  }

  const handleEvaluateAll = async () => {
    setEvaluatingAll(true)
    try {
      await api.evaluateAllBidders(projectId)
      await load()
    } catch (e: any) { alert(`Evaluation failed: ${e.message}`) }
    finally { setEvaluatingAll(false) }
  }

  const totalDocs = bidders.reduce((s, b) => s + b.documents.length, 0)
  const evaluated = bidders.filter(b => b.status === 'evaluated' || b.status === 'manual_review_required').length

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
          <Button variant="ghost" className="mb-3 pl-0" onClick={() => navigate(`/admin/projects/${projectId}`)}>
            <ArrowLeft className="h-4 w-4 mr-2" /> Back to Tender
          </Button>
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <User className="h-6 w-6 text-primary" /> Bidder Management
              </h1>
              <p className="text-muted-foreground text-sm mt-0.5">
                {project?.name ?? `Tender #${projectId}`}
              </p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button size="sm" variant="outline" onClick={() => navigate(`/admin/evaluations/${projectId}`)}>
                <BarChart3 className="h-4 w-4 mr-2" /> Evaluation Board
              </Button>
              {bidders.length >= 1 && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleEvaluateAll}
                  disabled={evaluatingAll || totalDocs === 0}
                >
                  {evaluatingAll ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
                  Evaluate All
                </Button>
              )}
              <Button size="sm" onClick={() => setShowAddModal(true)}>
                <Plus className="h-4 w-4 mr-2" /> Register Bidder
              </Button>
              <Button size="sm" variant="ghost" onClick={load}>
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

        {/* NIT upload + criteria extraction */}
        <NitCriteriaCard projectId={projectId} />

        {/* KPI row */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            { label: 'Bidders', value: bidders.length },
            { label: 'Documents', value: totalDocs },
            { label: 'Evaluated', value: `${evaluated}/${bidders.length}` },
          ].map(k => (
            <Card key={k.label} className="p-3 text-center">
              <div className="text-2xl font-bold">{k.value}</div>
              <div className="text-xs text-muted-foreground mt-0.5">{k.label}</div>
            </Card>
          ))}
        </div>

        {/* Tips */}
        {bidders.length === 0 && (
          <Card className="p-10 text-center mb-6">
            <User className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-40" />
            <h3 className="text-lg font-semibold mb-1">No Bidders Yet</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Register each company that submitted a bid. Then upload their supporting documents.
            </p>
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="h-4 w-4 mr-2" /> Register First Bidder
            </Button>
          </Card>
        )}

        {/* Workflow hint */}
        {bidders.length > 0 && totalDocs === 0 && (
          <Card className="p-4 mb-4 border-amber-200 bg-amber-50/60 text-amber-700 text-sm flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>Upload at least one document per bidder before running evaluation. Click the <Upload className="h-3.5 w-3.5 inline mx-0.5" /> icon on any bidder card.</span>
          </Card>
        )}

        {/* Bidder list */}
        <div className="space-y-3">
          {bidders.map(b => (
            <BidderCard
              key={b.id}
              bidder={b}
              onDelete={handleDelete}
              onEvaluate={handleEvaluate}
              onUpload={setUploadTarget}
            />
          ))}
        </div>

        {/* Status summary */}
        {evaluated > 0 && (
          <div className="mt-5 flex items-center justify-between text-sm text-muted-foreground">
            <span>{evaluated} of {bidders.length} bidders evaluated</span>
            <Button variant="outline" size="sm" onClick={() => navigate(`/admin/evaluations/${projectId}`)}>
              <BarChart3 className="h-4 w-4 mr-2" /> View Heatmap
            </Button>
          </div>
        )}
      </main>

      {showAddModal && (
        <AddBidderModal
          projectId={projectId}
          onClose={() => setShowAddModal(false)}
          onCreated={async () => handleBidderCreated()}
        />
      )}

      {uploadTarget && (
        <UploadDocModal
          bidderId={uploadTarget.id}
          bidderName={uploadTarget.company_name}
          onClose={() => setUploadTarget(null)}
          onUploaded={() => load()}
        />
      )}
    </div>
  )
}
