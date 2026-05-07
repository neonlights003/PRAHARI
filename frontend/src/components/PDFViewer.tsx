import { useState, useEffect, useRef, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/esm/Page/TextLayer.css'
import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
import { ChevronLeft, ChevronRight, Loader2, ZoomIn, ZoomOut, FileX, Maximize2, Minimize2, X, Search } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

// Inline styles for text layer - using actual react-pdf class names
const textLayerStyles = `
/* Target both old and new react-pdf class naming conventions */
.textLayer,
.react-pdf__Page__textContent {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow: hidden;
    line-height: 1.0;
    user-select: text;
    pointer-events: auto;
}

.textLayer span,
.react-pdf__Page__textContent span {
    color: transparent;
    position: absolute;
    white-space: pre;
    transform-origin: 0% 0%;
    cursor: text;
}

.textLayer span::selection,
.react-pdf__Page__textContent span::selection {
    background: rgba(0, 0, 255, 0.3);
}

/* Highlighted text - subtle yellow background */
mark.pdf-highlight {
    background-color: rgba(255, 235, 59, 0.25) !important;
    color: transparent !important;
    padding: 2px 0 !important;
    border-radius: 2px !important;
}
`

interface PDFViewerProps {
    pdfUrl: string
    initialPage?: number
    onPageChange?: (page: number) => void
    className?: string
    onClose?: () => void
    highlightText?: string | null
}

export function PDFViewer({ pdfUrl, initialPage = 1, onPageChange, className = '', onClose, highlightText }: PDFViewerProps) {
    const [numPages, setNumPages] = useState<number>(0)
    const [currentPage, setCurrentPage] = useState<number>(1)
    const [scale, setScale] = useState<number>(1.0)
    const [error, setError] = useState<string | null>(null)
    const [pageInput, setPageInput] = useState<string>('1')
    const [isMaximized, setIsMaximized] = useState<boolean>(false)
    const [highlightStatus, setHighlightStatus] = useState<'none' | 'searching' | 'found' | 'not-found'>('none')
    const pageContainerRef = useRef<HTMLDivElement>(null)

    // Update page when initialPage changes
    useEffect(() => {
        if (initialPage > 0 && initialPage <= numPages) {
            goToPage(initialPage)
        }
    }, [initialPage, numPages])

    // Highlight text when highlightText changes
    useEffect(() => {
        if (!highlightText || !pageContainerRef.current) {
            setHighlightStatus('none')
            return
        }

        // Wait for page to render with text layer
        const timeoutId = setTimeout(() => {
            highlightTextInPage(highlightText)
        }, 500)

        return () => {
            clearTimeout(timeoutId)
        }
    }, [highlightText, currentPage, scale])

    // Fuzzy highlighting using alphanumeric matching and mark tags
    const highlightTextInPage = useCallback((searchText: string) => {
        if (!pageContainerRef.current || !searchText) return

        setHighlightStatus('searching')

        // Find text layer
        const textLayer = pageContainerRef.current.querySelector('.react-pdf__Page__textContent') ||
            pageContainerRef.current.querySelector('[class*="textLayer"]')

        if (!textLayer) {
            setHighlightStatus('not-found')
            return
        }

        // Remove existing highlights
        textLayer.querySelectorAll('mark.pdf-highlight').forEach(mark => {
            const parent = mark.parentNode
            if (parent) {
                parent.replaceChild(document.createTextNode(mark.textContent || ''), mark)
                parent.normalize()
            }
        })

        // Get all text content from text nodes
        const walker = document.createTreeWalker(
            textLayer,
            NodeFilter.SHOW_TEXT,
            null
        )

        const textNodes: Text[] = []
        let node
        while (node = walker.nextNode()) {
            if (node.textContent && node.textContent.trim()) {
                textNodes.push(node as Text)
            }
        }

        // Build full text and track node positions
        let fullText = ''
        const nodeMap: { node: Text; start: number; end: number }[] = []

        textNodes.forEach(textNode => {
            const start = fullText.length
            const text = textNode.textContent || ''
            fullText += text
            nodeMap.push({ node: textNode, start, end: fullText.length })
        })

        // FUZZY MATCHING: Strip to alphanumeric only
        const toAlphanumeric = (text: string) => text.toLowerCase().replace(/[^a-z0-9]/g, '')

        const searchAlpha = toAlphanumeric(searchText)
        const fullTextAlpha = toAlphanumeric(fullText)

        const alphaIndex = fullTextAlpha.indexOf(searchAlpha)

        if (alphaIndex === -1) {
            setHighlightStatus('not-found')
            return
        }

        // Map alphanumeric position back to original position
        let alphaCount = 0
        let originalStart = -1
        let originalEnd = -1

        for (let i = 0; i < fullText.length; i++) {
            if (/[a-zA-Z0-9]/.test(fullText[i])) {
                if (alphaCount === alphaIndex && originalStart === -1) {
                    originalStart = i
                }
                if (alphaCount === alphaIndex + searchAlpha.length - 1) {
                    originalEnd = i + 1
                    break
                }
                alphaCount++
            }
        }

        if (originalStart === -1 || originalEnd === -1) {
            setHighlightStatus('not-found')
            return
        }

        // Highlight the text nodes in range using mark tags
        let highlighted = false
        nodeMap.forEach(({ node, start, end }) => {
            if (start < originalEnd && end > originalStart) {
                const nodeStart = Math.max(0, originalStart - start)
                const nodeEnd = Math.min(node.textContent!.length, originalEnd - start)

                if (nodeStart < nodeEnd) {
                    const before = node.textContent!.substring(0, nodeStart)
                    const match = node.textContent!.substring(nodeStart, nodeEnd)
                    const after = node.textContent!.substring(nodeEnd)

                    const fragment = document.createDocumentFragment()
                    if (before) fragment.appendChild(document.createTextNode(before))

                    const mark = document.createElement('mark')
                    mark.className = 'pdf-highlight'
                    mark.textContent = match
                    fragment.appendChild(mark)

                    if (after) fragment.appendChild(document.createTextNode(after))

                    node.parentNode?.replaceChild(fragment, node)
                    highlighted = true
                }
            }
        })

        if (highlighted) {
            setHighlightStatus('found')
            // Scroll to first highlight
            const firstMark = textLayer.querySelector('mark.pdf-highlight')
            if (firstMark) {
                firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' })
            }
        } else {
            setHighlightStatus('not-found')
        }
    }, [])

    function goToPage(pageNumber: number) {
        if (pageNumber < 1) pageNumber = 1
        if (numPages > 0 && pageNumber > numPages) pageNumber = numPages

        setCurrentPage(pageNumber)
        setPageInput(String(pageNumber))

        if (onPageChange) {
            onPageChange(pageNumber)
        }
    }

    function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
        setNumPages(numPages)
        setError(null)
        goToPage(initialPage || 1)
    }

    function onDocumentLoadError(error: Error) {
        setError(`Failed to load PDF: ${error.message}`)
    }

    function handlePrevPage() { goToPage(currentPage - 1) }
    function handleNextPage() { goToPage(currentPage + 1) }

    function handlePageInputChange(e: React.ChangeEvent<HTMLInputElement>) {
        setPageInput(e.target.value)
    }

    function handlePageInputSubmit(e: React.FormEvent | React.KeyboardEvent) {
        e.preventDefault()
        const pageNum = parseInt(pageInput, 10)
        if (!isNaN(pageNum)) {
            goToPage(pageNum)
        } else {
            setPageInput(String(currentPage))
        }
    }

    function handleZoomIn() { setScale(prev => Math.min(prev + 0.2, 2.0)) }
    function handleZoomOut() { setScale(prev => Math.max(prev - 0.2, 0.5)) }
    function toggleMaximize() { setIsMaximized(prev => !prev) }

    const renderHighlightStatus = () => {
        if (!highlightText || highlightStatus === 'none') return null

        return (
            <div className={`flex items-center gap-1 text-xs px-2 py-1 rounded ${highlightStatus === 'searching' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' :
                highlightStatus === 'found' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                    'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
                }`}>
                <Search className="h-3 w-3" />
                {highlightStatus === 'searching' && 'Searching...'}
                {highlightStatus === 'found' && 'Evidence found'}
                {highlightStatus === 'not-found' && 'Evidence not found on page'}
            </div>
        )
    }

    const pdfContent = (
        <Card className={`flex flex-col ${isMaximized ? 'h-full' : className}`}>
            <style>{textLayerStyles}</style>

            <div className="border-b p-3 flex items-center justify-between bg-muted/30">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                    {onClose && (
                        <Button variant="ghost" size="sm" onClick={onClose} className="h-7 w-7 p-0 mr-1" title="Close">
                            <X className="h-4 w-4" />
                        </Button>
                    )}
                    <h3 className="font-semibold text-sm whitespace-nowrap">PDF Viewer</h3>
                    {numPages > 0 && (
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                            Page {currentPage} of {numPages}
                        </span>
                    )}
                    {renderHighlightStatus()}
                </div>

                <div className="flex items-center gap-1">
                    {numPages > 0 && (
                        <>
                            <Button variant="ghost" size="sm" onClick={handleZoomOut} disabled={scale <= 0.5} className="h-7 w-7 p-0" title="Zoom out">
                                <ZoomOut className="h-3.5 w-3.5" />
                            </Button>
                            <span className="text-xs text-muted-foreground px-2">{Math.round(scale * 100)}%</span>
                            <Button variant="ghost" size="sm" onClick={handleZoomIn} disabled={scale >= 2.0} className="h-7 w-7 p-0" title="Zoom in">
                                <ZoomIn className="h-3.5 w-3.5" />
                            </Button>
                        </>
                    )}
                    <Button variant="ghost" size="sm" onClick={toggleMaximize} className="h-7 w-7 p-0 ml-1" title={isMaximized ? "Minimize" : "Maximize"}>
                        {isMaximized ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
                    </Button>
                </div>
            </div>

            <div className="flex-1 overflow-auto bg-gray-100 dark:bg-gray-900">
                <div className="min-h-full flex items-center justify-center p-4">
                    {error ? (
                        <div className="flex flex-col items-center gap-3 text-center max-w-md">
                            <FileX className="h-12 w-12 text-red-500" />
                            <div>
                                <p className="font-semibold text-sm mb-1">PDF Load Error</p>
                                <p className="text-xs text-muted-foreground mb-2">{error}</p>
                            </div>
                        </div>
                    ) : (
                        <div ref={pageContainerRef} className="bg-white dark:bg-gray-800 shadow-lg relative">
                            <Document
                                file={pdfUrl}
                                onLoadSuccess={onDocumentLoadSuccess}
                                onLoadError={onDocumentLoadError}
                                loading={
                                    <div className="flex flex-col items-center gap-3 p-8">
                                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                        <p className="text-sm text-muted-foreground">Loading PDF...</p>
                                    </div>
                                }
                            >
                                <Page
                                    pageNumber={currentPage}
                                    scale={scale}
                                    renderTextLayer={true}
                                    renderAnnotationLayer={false}
                                    loading={
                                        <div className="flex items-center justify-center p-8">
                                            <Loader2 className="h-6 w-6 animate-spin text-primary" />
                                        </div>
                                    }
                                    onRenderSuccess={() => {
                                        if (highlightText) {
                                            setTimeout(() => {
                                                highlightTextInPage(highlightText)
                                            }, 300)
                                        }
                                    }}
                                />
                            </Document>
                        </div>
                    )}
                </div>
            </div>

            {numPages > 0 && (
                <div className="border-t p-3 flex items-center justify-between bg-muted/30">
                    <Button variant="outline" size="sm" onClick={handlePrevPage} disabled={currentPage <= 1} className="h-8">
                        <ChevronLeft className="h-4 w-4 mr-1" /> Prev
                    </Button>

                    <form onSubmit={handlePageInputSubmit} className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Page</span>
                        <input
                            type="number"
                            min={1}
                            max={numPages}
                            value={pageInput}
                            onChange={handlePageInputChange}
                            onKeyPress={(e) => { if (e.key === 'Enter') handlePageInputSubmit(e) }}
                            onBlur={handlePageInputSubmit}
                            className="w-14 h-8 text-center text-sm border border-input rounded px-2"
                        />
                        <span className="text-xs text-muted-foreground">of {numPages}</span>
                    </form>

                    <Button variant="outline" size="sm" onClick={handleNextPage} disabled={currentPage >= numPages} className="h-8">
                        Next <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                </div>
            )}
        </Card>
    )

    if (isMaximized) {
        return (
            <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 animate-in fade-in duration-200">
                <div className="w-full h-full max-w-7xl">{pdfContent}</div>
            </div>
        )
    }

    return pdfContent
}
