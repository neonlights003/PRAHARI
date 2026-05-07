import { useState, useCallback, useRef } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import { X, ChevronLeft, ChevronRight, ZoomIn, ZoomOut, ExternalLink, Highlighter } from 'lucide-react'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

interface PDFViewerModalProps {
  url: string
  initialPage?: number
  evidenceQuote?: string
  title?: string
  onClose: () => void
}

// ── text normalisation helpers ─────────────────────────────────────────────────

function norm(s: string): string {
  return s
    .toLowerCase()
    .replace(/[‘’“”]/g, "'") // curly quotes
    .replace(/[\s\-–—]+/g, ' ')         // dashes / whitespace → space
    .replace(/[^\w\s]/g, '')                       // strip punctuation
    .trim()
}

// Returns a 0-1 score: how well `item` overlaps with `quote`.
function overlapScore(itemStr: string, quoteNorm: string): number {
  const nItem = norm(itemStr)
  if (!nItem || nItem.length < 3) return 0

  // Direct containment is the strongest signal
  if (quoteNorm.includes(nItem)) return 1.0

  // Token overlap: what fraction of the item's significant words appear in the quote
  const tokens = nItem.split(' ').filter(t => t.length > 3)
  if (tokens.length === 0) return 0
  const matched = tokens.filter(t => quoteNorm.includes(t))
  return matched.length / tokens.length
}

// ── main component ─────────────────────────────────────────────────────────────

export function PDFViewerModal({ url, initialPage = 1, evidenceQuote, title, onClose }: PDFViewerModalProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [scale, setScale] = useState(1.2)
  const [loadError, setLoadError] = useState(false)
  const [highlightCount, setHighlightCount] = useState(0)
  const canvasRef = useRef<HTMLDivElement>(null)

  const quoteNorm = evidenceQuote ? norm(evidenceQuote) : ''

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }, [])

  const onDocumentLoadError = useCallback(() => setLoadError(true), [])

  // Called per text item — returns an HTML string; <mark> tags are injected into innerHTML
  const customTextRenderer = useCallback(
    (textItem: { str: string; itemIndex: number; pageIndex: number; pageNumber: number }) => {
      const { str } = textItem
      if (!quoteNorm || !str.trim()) return str

      const score = overlapScore(str, quoteNorm)

      if (score >= 1.0) {
        // Strong match — solid amber highlight
        return `<mark class="prahari-hl prahari-hl-strong" style="background:rgba(251,191,36,0.65);border-radius:2px;padding:0 1px;cursor:default;">${str}</mark>`
      }
      if (score >= 0.6) {
        // Partial match — lighter highlight
        return `<mark class="prahari-hl prahari-hl-partial" style="background:rgba(251,191,36,0.30);border-radius:2px;padding:0 1px;">${str}</mark>`
      }

      return str
    },
    [quoteNorm]
  )

  // After the text layer renders, count highlights and scroll to the first strong one
  const onRenderTextLayerSuccess = useCallback(() => {
    if (!canvasRef.current) return
    const marks = canvasRef.current.querySelectorAll<HTMLElement>('.prahari-hl-strong')
    setHighlightCount(marks.length)
    if (marks.length > 0) {
      marks[0].scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [])

  const prevPage = () => setCurrentPage(p => Math.max(1, p - 1))
  const nextPage = () => setCurrentPage(p => Math.min(numPages, p + 1))
  const zoomIn   = () => setScale(s => Math.min(2.5, +(s + 0.2).toFixed(1)))
  const zoomOut  = () => setScale(s => Math.max(0.5, +(s - 0.2).toFixed(1)))

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-background rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-semibold text-sm truncate">{title ?? 'Document Viewer'}</span>
            {evidenceQuote && highlightCount > 0 && (
              <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium shrink-0">
                <Highlighter className="h-3 w-3" />
                {highlightCount} match{highlightCount !== 1 ? 'es' : ''} highlighted
              </span>
            )}
            {evidenceQuote && highlightCount === 0 && numPages > 0 && (
              <span className="text-[10px] text-muted-foreground italic shrink-0">
                (scanned page — highlights unavailable)
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="p-1.5 rounded hover:bg-muted transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
            <button onClick={onClose} className="p-1.5 rounded hover:bg-muted transition-colors">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* ── Toolbar ────────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-4 py-2 bg-muted/30 border-b border-border/30 text-xs shrink-0">
          <div className="flex items-center gap-1">
            <button
              onClick={prevPage}
              disabled={currentPage <= 1}
              className="p-1.5 rounded hover:bg-muted disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </button>
            <span className="tabular-nums px-2">
              Page{' '}
              <input
                type="number"
                min={1}
                max={numPages || 1}
                value={currentPage}
                onChange={e => setCurrentPage(Math.min(numPages, Math.max(1, Number(e.target.value))))}
                className="w-10 text-center border border-border rounded px-1 py-0.5 bg-background"
              />{' '}
              / {numPages || '…'}
            </span>
            <button
              onClick={nextPage}
              disabled={currentPage >= numPages}
              className="p-1.5 rounded hover:bg-muted disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={zoomOut} className="p-1.5 rounded hover:bg-muted transition-colors">
              <ZoomOut className="h-3.5 w-3.5" />
            </button>
            <span className="tabular-nums w-12 text-center">{Math.round(scale * 100)}%</span>
            <button onClick={zoomIn} className="p-1.5 rounded hover:bg-muted transition-colors">
              <ZoomIn className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* ── PDF canvas ─────────────────────────────────────────────────── */}
        <div ref={canvasRef} className="flex-1 overflow-auto flex justify-center p-4 bg-muted/10">
          {loadError ? (
            <div className="flex flex-col items-center justify-center gap-4 py-16 text-muted-foreground">
              <p className="text-sm">Unable to load PDF inline.</p>
              <a
                href={url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm hover:opacity-90 transition-opacity"
              >
                <ExternalLink className="h-4 w-4" />
                Open PDF in new tab
              </a>
            </div>
          ) : (
            <Document
              file={url}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex items-center justify-center py-16 text-muted-foreground text-sm">
                  Loading document…
                </div>
              }
            >
              <Page
                pageNumber={currentPage}
                scale={scale}
                renderTextLayer
                renderAnnotationLayer
                customTextRenderer={evidenceQuote ? customTextRenderer : undefined}
                onRenderTextLayerSuccess={evidenceQuote ? onRenderTextLayerSuccess : undefined}
              />
            </Document>
          )}
        </div>

        {/* ── Evidence quote footer ────────────────────────────────────── */}
        {evidenceQuote && (
          <div className="shrink-0 px-4 py-2 border-t border-border/30 bg-amber-50/60 dark:bg-amber-950/20 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1 font-medium text-foreground">
              <Highlighter className="h-3 w-3 text-amber-500" />
              Evidence:
            </span>{' '}
            "{evidenceQuote}"
          </div>
        )}
      </div>
    </div>
  )
}
