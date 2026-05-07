import { Header } from '@/components/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { EnvironmentalImpact } from '@/components/EnvironmentalImpact'
import { FinancialCharts } from '@/components/FinancialCharts'
import { ChatMessageFormatter } from '@/components/ChatMessageFormatter'
import { PDFViewer } from '@/components/PDFViewer'
import { createClickablePageLinks, createEvidencePageLink } from '@/utils/parsePageReferences'
import { formatIndianCurrency } from '@/lib/currency'
import {
  ArrowLeft,
  Download,
  Clock,
  MapPin,
  Users,
  TrendingUp,
  MessageSquare,
  Send,
  FileText,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Calendar,
  Target,
  Shield,
  Copy,
  Check,
  Trash2,
  X,
} from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { api, type DPR, type Message } from '@/lib/api'
import { useLanguage } from '@/contexts/LanguageContext'

export default function DocumentDetailPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { id } = useParams<{ id: string }>()
  const { t } = useLanguage()
  const [activeTab, setActiveTab] = useState('overview')
  const [chatMessage, setChatMessage] = useState('')
  const [chatHistory, setChatHistory] = useState<Message[]>([])
  const [document, setDocument] = useState<DPR | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatLoading, setChatLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [showClearChatConfirm, setShowClearChatConfirm] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)
  const [highlightText, setHighlightText] = useState<string | null>(null)  // NEW: Text to highlight in PDF
  const chatEndRef = useRef<HTMLDivElement>(null)
  const [isPdfCollapsed, setIsPdfCollapsed] = useState(true)
  const [isChatCollapsed, setIsChatCollapsed] = useState(true)
  const [leftWidth, setLeftWidth] = useState(50) // Percentage width of left panel
  const [isResizing, setIsResizing] = useState(false)

  // Get project_id from navigation state or document
  const projectId = (location.state as any)?.projectId || document?.project_id

  useEffect(() => {
    if (id) {
      loadDocument(parseInt(id))
      loadChatHistory(parseInt(id))
    }
  }, [id])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  async function loadDocument(dprId: number) {
    try {
      setLoading(true)
      const doc = await api.getDPR(dprId)
      setDocument(doc)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  async function loadChatHistory(dprId: number) {
    try {
      const history = await api.getChatHistory(dprId)
      setChatHistory(history)
    } catch (err) {
      console.error('Failed to load chat history:', err)
    }
  }

  function handleClearChat() {
    if (!id) return
    setShowClearChatConfirm(true)
  }

  async function confirmClearChat() {
    if (!id) return

    try {
      await api.clearChatHistory(parseInt(id))
      setChatHistory([])
      setShowClearChatConfirm(false)
    } catch (err) {
      console.error('Failed to clear chat:', err)
      // Optional: show toast error
    }
  }

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault()
    if (!chatMessage.trim() || !id || chatLoading) return

    const userMessage = chatMessage.trim()
    setChatMessage('')
    setChatLoading(true)

    const tempUserMsg: Message = {
      id: Date.now(),
      dpr_id: parseInt(id),
      role: 'user',
      text: userMessage,
      timestamp: new Date().toISOString(),
    }
    setChatHistory(prev => [...prev, tempUserMsg])

    try {
      const response = await api.sendChatMessage(parseInt(id), userMessage)
      setChatHistory(prev => [...prev, response])
    } catch (err) {
      console.error('Failed to send message:', err)
    } finally {
      setChatLoading(false)
    }
  }

  function handleDownload() {
    if (id) {
      const link = window.document.createElement('a')
      link.href = `/api/dpr/${id}/report`
      link.download = `DPR_Report_${id}_${new Date().toISOString().split('T')[0]}.pdf`
      link.click()
    }
  }

  function handleShare() {
    const url = `${window.location.origin}/documents/${id}`
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  // Updated to accept optional searchText for highlighting evidence
  function handlePageClick(page: number, searchText?: string) {
    console.log('ðŸ”— handlePageClick called:', {
      page,
      hasSearchText: !!searchText,
      searchTextPreview: searchText?.substring(0, 100),
      searchTextLength: searchText?.length
    })
    setPdfPage(page)
    setHighlightText(searchText || null)  // Set text to highlight (or clear if none)
    // Open PDF viewer if it's collapsed
    if (isPdfCollapsed) {
      console.log('ðŸ”— Opening collapsed PDF viewer')
      setIsPdfCollapsed(false)
    }
    // Note: Removed scrollIntoView to prevent page from jumping when clicking evidence links
    // The PDF viewer will update in place without scrolling the page
  }

  // Resize handler for draggable divider
  const startResize = () => {
    setIsResizing(true)
  }

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return

      const containerWidth = window.innerWidth - 100 // Account for padding
      const newLeftWidth = (e.clientX / containerWidth) * 100

      // Limit between 30% and 70%
      if (newLeftWidth >= 30 && newLeftWidth <= 70) {
        setLeftWidth(newLeftWidth)
      }
    }

    const handleMouseUp = () => {
      setIsResizing(false)
    }

    if (isResizing) {
      window.document.addEventListener('mousemove', handleMouseMove)
      window.document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      window.document.removeEventListener('mousemove', handleMouseMove)
      window.document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])

  const tabs = [
    { id: 'overview', label: t('documentDetail.overview') },
    { id: 'analysis', label: t('documentDetail.analysis') },
    { id: 'timeline', label: t('documentDetail.timeline') },
    { id: 'riskAssessment', label: t('documentDetail.riskAssessment') },
    { id: 'inconsistencies', label: t('documentDetail.inconsistencies') },
    { id: 'compliance', label: t('documentDetail.compliance') },
    { id: 'recommendations', label: t('documentDetail.recommendations') },
  ]

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
        </main>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-8">
          <Card className="p-12 text-center">
            <h2 className="text-2xl font-bold mb-2">Document Not Found</h2>
            <p className="text-muted-foreground mb-6">
              {error || 'The requested document could not be found.'}
            </p>
            <Button onClick={() => navigate(-1)}>
              <ArrowLeft className="h-4 w-4" />
              Back to Documents
            </Button>
          </Card>
        </main>
      </div>
    )
  }

  const data = document.summary_json

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-4 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex-1">
              <h1 className="text-3xl md:text-4xl font-heading font-bold mb-2">{document.original_filename}</h1>
              <p className="text-sm text-muted-foreground flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Uploaded on {new Date(document.upload_ts).toLocaleDateString()}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                onClick={handleShare}
                className="hover:bg-muted transition-colors"
              >
                {copied ? <Check className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
                {copied ? 'Copied!' : 'Share'}
              </Button>
              <Button
                variant="outline"
                onClick={handleDownload}
                className="hover:bg-muted transition-colors"
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button
                onClick={() => setIsPdfCollapsed(false)}
                className="gradient-primary text-white hover:shadow-glow transition-all"
                disabled={!isPdfCollapsed}
              >
                <FileText className="h-4 w-4 mr-2" />
                PDF
              </Button>
              <Button
                onClick={() => setIsChatCollapsed(false)}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white hover:shadow-glow transition-all"
                disabled={!isChatCollapsed}
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                Chat
              </Button>
            </div>
          </div>
        </div>



        {data && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {/* Overall Score Card */}
            {data.overallScore && (
              <div className="relative overflow-hidden rounded-xl border border-blue-200 dark:border-blue-800 bg-white dark:bg-gray-900 shadow-sm group hover:shadow-md transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-transparent to-blue-100/30 dark:from-blue-900/20 dark:to-blue-800/10 opacity-100" />
                <div className="relative p-5 flex flex-col h-full justify-between">
                  <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-medium text-sm mb-3">
                    <TrendingUp className="h-4 w-4" />
                    Overall Score
                  </div>
                  <div>
                    <div className="text-3xl font-heading font-bold text-foreground">
                      {data.overallScore}
                      <span className="text-lg text-muted-foreground font-normal ml-1">/100</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendation Card */}
            {data.recommendation && (
              <div className="relative overflow-hidden rounded-xl border border-amber-200 dark:border-amber-800 bg-white dark:bg-gray-900 shadow-sm group hover:shadow-md transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-amber-50/50 via-transparent to-amber-100/30 dark:from-amber-900/20 dark:to-amber-800/10 opacity-100" />
                <div className="relative p-5 flex flex-col h-full justify-between">
                  <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-medium text-sm mb-3">
                    {data.recommendation.toLowerCase().includes('select') || data.recommendation.toLowerCase().includes('shortlist') ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : data.recommendation.toLowerCase().includes('reject') ? (
                      <XCircle className="h-4 w-4" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    Recommendation
                  </div>
                  <div className="text-xl font-heading font-bold text-foreground leading-tight">
                    {data.recommendation}
                  </div>
                </div>
              </div>
            )}

            {/* Issuing Authority Card */}
            {data.tenderDetails?.issuingAuthority && (
              <div className="relative overflow-hidden rounded-xl border border-indigo-200 dark:border-indigo-800 bg-white dark:bg-gray-900 shadow-sm group hover:shadow-md transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/50 via-transparent to-indigo-100/30 dark:from-indigo-900/20 dark:to-indigo-800/10 opacity-100" />
                <div className="relative p-5 flex flex-col h-full justify-between">
                  <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-medium text-sm mb-3">
                    <Users className="h-4 w-4" />
                    Issuing Authority
                  </div>
                  <div className="text-lg font-heading font-bold text-foreground break-words leading-tight">
                    {data.tenderDetails.issuingAuthority}
                  </div>
                </div>
              </div>
            )}

            {/* Tender Type Card */}
            {data.tenderDetails?.tenderType && (
              <div className="relative overflow-hidden rounded-xl border border-cyan-200 dark:border-cyan-800 bg-white dark:bg-gray-900 shadow-sm group hover:shadow-md transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-50/50 via-transparent to-cyan-100/30 dark:from-cyan-900/20 dark:to-cyan-800/10 opacity-100" />
                <div className="relative p-5 flex flex-col h-full justify-between">
                  <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-medium text-sm mb-3">
                    <FileText className="h-4 w-4" />
                    Tender Type
                  </div>
                  <div className="text-lg font-heading font-bold text-foreground break-words leading-tight">
                    {data.tenderDetails.tenderType}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Calculate right panel height: 550px per open panel + 16px gap between them */}
        <div
          className="grid gap-6 relative"
          style={{
            gridTemplateColumns: isPdfCollapsed && isChatCollapsed ? '1fr' : `${leftWidth}% 4px ${100 - leftWidth}%`,
          }}
        >
          {/* Left Panel - Analysis Content */}
          <div
            style={{
              height: (isPdfCollapsed && isChatCollapsed)
                ? 'auto'
                : (!isPdfCollapsed && !isChatCollapsed)
                  ? 'calc(550px + 550px + 16px)' // Both open: 2 panels + gap
                  : '550px', // Only one open
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <Card className="flex flex-col h-full overflow-hidden">
              <div className="border-b overflow-x-auto flex-shrink-0">
                <div className="flex min-w-max">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={cn(
                        'px-4 py-3 font-medium transition-colors whitespace-nowrap',
                        activeTab === tab.id
                          ? 'text-primary border-b-2 border-primary'
                          : 'text-muted-foreground hover:text-foreground'
                      )}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-4 overflow-y-auto flex-1 text-xl">
                {activeTab === 'overview' && (
                  <OverviewTab data={data} onPageClick={handlePageClick} />
                )}

                {activeTab === 'analysis' && (
                  <AnalysisTab data={data} />
                )}

                {activeTab === 'timeline' && (
                  <TimelineTab data={data} />
                )}

                {activeTab === 'riskAssessment' && (
                  <RiskAssessmentTab data={data} onPageClick={handlePageClick} />
                )}

                {activeTab === 'inconsistencies' && (
                  <InconsistenciesTab data={data} onPageClick={handlePageClick} />
                )}


                {activeTab === 'compliance' && (() => {
                  console.log('ðŸ” Rendering ComplianceTab with projectId:', projectId, 'from location:', (location.state as any)?.projectId, 'from document:', document?.project_id)
                  return <ComplianceTab data={data} onPageClick={handlePageClick} />
                })()}

                {activeTab === 'recommendations' && (
                  <RecommendationsTab data={data} />
                )}
              </div>
            </Card>
          </div>

          {/* Draggable Resize Handle */}
          {!(isPdfCollapsed && isChatCollapsed) && (
            <div
              onMouseDown={startResize}
              className={`cursor-col-resize flex items-center justify-center group ${isResizing ? 'bg-primary' : 'hover:bg-primary/20'} transition-colors`}
              title="Drag to resize"
            >
              <div className="w-1 h-full bg-border group-hover:bg-primary transition-colors rounded-full"></div>
            </div>
          )}

          {!(isPdfCollapsed && isChatCollapsed) && (
            <div className="lg:col-span-1 flex flex-col gap-4">
              {/* PDF Viewer */}
              {!isPdfCollapsed ? (
                <div id="pdf-viewer-container" className="relative animate-in fade-in slide-in-from-right duration-300">
                  <PDFViewer
                    pdfUrl={`http://127.0.0.1:8000/dpr/${id}/pdf`}
                    initialPage={pdfPage}
                    onPageChange={(page) => setPdfPage(page)}
                    className="h-[550px]"
                    onClose={() => setIsPdfCollapsed(true)}
                    highlightText={highlightText}
                  />
                </div>
              ) : null}

              {/* Chat Window */}
              {!isChatCollapsed ? (
                <Card className="h-[550px] flex flex-col relative animate-in fade-in slide-in-from-right duration-300">
                  <div className="border-b p-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsChatCollapsed(true)}
                        className="h-7 w-7 p-0 hover:bg-background/80"
                        title="Hide Chat"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                      <MessageSquare className="h-5 w-5 text-primary" />
                      <h3 className="font-semibold">{t('documentDetail.chat')}</h3>
                    </div>
                    {chatHistory.length > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleClearChat}
                        className="text-muted-foreground hover:text-destructive h-8 w-8 p-0"
                        title={t('common.clearChat')}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>

                  <div className="flex-1 p-4 overflow-y-auto space-y-4">
                    {chatHistory.length === 0 && (
                      <div className="p-3 rounded-lg bg-muted">
                        <p className="text-sm">
                          Hello! I'm your DPR analysis assistant. Ask me anything about this document.
                        </p>
                      </div>
                    )}
                    {chatHistory.map((msg, index) => (
                      <ChatMessageFormatter key={index} text={msg.text} isUser={msg.role === 'user'} />
                    ))}
                    {chatLoading && (
                      <div className="p-3 rounded-lg bg-muted mr-8 flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm">Thinking...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  <form onSubmit={sendMessage} className="border-t p-4 flex gap-2">
                    <input
                      type="text"
                      value={chatMessage}
                      onChange={(e) => setChatMessage(e.target.value)}
                      placeholder={t('documentDetail.askQuestion')}
                      className="flex-1 px-3 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                      disabled={chatLoading}
                    />
                    <Button type="submit" disabled={chatLoading || !chatMessage.trim()}>
                      <Send className="h-4 w-4" />
                    </Button>
                  </form>
                </Card>
              ) : null}
            </div>
          )}
        </div>


      </main>

      {/* Clear Chat Confirmation Modal */}
      {showClearChatConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6 animate-in fade-in zoom-in duration-200">
            <h3 className="text-lg font-bold mb-2">{t('common.confirmClearChat')}</h3>
            <p className="text-muted-foreground mb-6">
              Are you sure you want to clear the chat history? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setShowClearChatConfirm(false)}>
                Cancel
              </Button>
              <Button
                className="bg-red-600 hover:bg-red-700 text-white"
                onClick={confirmClearChat}
              >
                Clear Chat
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

function OverviewTab({ data, onPageClick }: { data: any; onPageClick: (page: number) => void }) {
  if (!data) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No data available</p>
      </div>
    )
  }

  const tenderDetails = data.tenderDetails
  const bidderQualifications = data.bidderQualifications

  return (
    <div className="space-y-8">
      {/* Tender Name - Hero */}
      {tenderDetails?.tenderName && (
        <div className="pb-6 border-b">
          <h2 className="text-3xl font-heading font-bold text-foreground mb-2">{tenderDetails.tenderName}</h2>
          {tenderDetails?.tenderReferenceNumber && (
            <p className="text-base text-muted-foreground">Reference: {tenderDetails.tenderReferenceNumber}</p>
          )}
        </div>
      )}

      {/* Basic Information Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-heading font-semibold text-foreground border-l-4 border-primary pl-3">
          Basic Information
        </h3>

        <div className="grid md:grid-cols-2 gap-4">
          {tenderDetails?.bidderName && (
            <div className="bg-muted/30 rounded-lg p-4 border border-border">
              <div className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-2">Bidder Name</div>
              <div className="text-lg font-semibold text-foreground">{tenderDetails.bidderName}</div>
            </div>
          )}

          {tenderDetails?.projectLocation && (
            <div className="bg-muted/30 rounded-lg p-4 border border-border">
              <div className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-2 flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                Project Location
              </div>
              <div className="text-base font-semibold text-foreground">
                {[tenderDetails.projectLocation.city, tenderDetails.projectLocation.state, tenderDetails.projectLocation.country].filter(Boolean).join(', ')}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Executive Summary Section */}
      {data.executiveSummary && (
        <div className="space-y-4">
          <h3 className="text-lg font-heading font-semibold text-foreground border-l-4 border-primary pl-3">
            Executive Summary
          </h3>
          <div className="bg-muted/20 rounded-lg p-5 border border-border">
            <p className="text-base text-foreground leading-relaxed">
              {createClickablePageLinks(data.executiveSummary, onPageClick)}
            </p>
          </div>
        </div>
      )}

      {/* Methodology Assessment Section */}
      {data.technicalEvaluation?.methodologyAndApproach && (
        <div className="space-y-4">
          <h3 className="text-lg font-heading font-semibold text-foreground border-l-4 border-primary pl-3">
            Methodology Assessment
          </h3>

          <div className="space-y-4">
            {data.technicalEvaluation.methodologyAndApproach.strengths?.length > 0 && (
              <div className="bg-green-50/50 dark:bg-green-950/20 rounded-lg p-5 border border-green-200 dark:border-green-800">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                  <h4 className="text-lg font-semibold text-green-700 dark:text-green-300">Strengths</h4>
                </div>
                <ul className="space-y-2">
                  {data.technicalEvaluation.methodologyAndApproach.strengths.map((s: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
                      <span className="text-green-600 dark:text-green-400 mt-1">â€¢</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {data.technicalEvaluation.methodologyAndApproach.weaknesses?.length > 0 && (
              <div className="bg-red-50/50 dark:bg-red-950/20 rounded-lg p-5 border border-red-200 dark:border-red-800">
                <div className="flex items-center gap-2 mb-3">
                  <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                  <h4 className="text-lg font-semibold text-red-700 dark:text-red-300">Weaknesses</h4>
                </div>
                <ul className="space-y-2">
                  {data.technicalEvaluation.methodologyAndApproach.weaknesses.map((w: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
                      <span className="text-red-600 dark:text-red-400 mt-1">â€¢</span>
                      <span>{w}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Key Personnel Section */}
      {bidderQualifications?.teamComposition?.keyPersonnel?.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-primary pl-3 flex items-center gap-2">
            <Users className="h-5 w-5" />
            Key Personnel
          </h3>

          <div className="space-y-3">
            {bidderQualifications.teamComposition.keyPersonnel.map((person: any, idx: number) => (
              <div key={idx} className="bg-muted/20 rounded-lg p-4 border border-border hover:border-primary/50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-foreground mb-1">{person.name}</h4>
                    <p className="text-base text-muted-foreground mb-2">{person.role}</p>
                    <div className="flex flex-wrap gap-3 text-sm">
                      <span className="bg-primary/10 text-primary px-3 py-1 rounded">
                        {person.experienceYears} years experience
                      </span>
                      <span className="bg-muted text-muted-foreground px-3 py-1 rounded">
                        {person.qualification}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function TimelineTab({ data }: { data: any }) {
  const timeline = data?.technicalEvaluation?.projectTimeline

  if (!timeline) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No timeline data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Proposed Duration - Hero Section */}
      {timeline.proposedDuration && (
        <div className="pb-6 border-b">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center flex-shrink-0">
              <Clock className="h-8 w-8 text-white" />
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-1">Proposed Duration</div>
              <div className="text-2xl font-heading font-bold text-foreground">{timeline.proposedDuration}</div>
            </div>
          </div>
        </div>
      )}

      {/* Key Milestones Section */}
      {timeline.milestones && timeline.milestones.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-primary pl-3 flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Key Milestones
          </h3>

          <div className="space-y-4">
            {timeline.milestones.map((milestone: string, idx: number) => (
              <div key={idx} className="flex gap-4 group">
                <div className="flex flex-col items-center">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 text-white flex items-center justify-center font-heading font-bold text-base shadow-lg">
                    {idx + 1}
                  </div>
                  {idx < timeline.milestones.length - 1 && (
                    <div className="w-0.5 h-full bg-gradient-to-b from-primary/50 to-transparent mt-2"></div>
                  )}
                </div>
                <div className="flex-1 pb-6">
                  <div className="bg-muted/20 rounded-lg p-4 border border-border group-hover:border-primary/50 transition-colors">
                    <p className="text-lg text-foreground leading-relaxed">{milestone}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline Assessment */}
      {timeline.isTimelineRealistic !== undefined && (
        <div className="space-y-4">
          <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-primary pl-3">
            Timeline Assessment
          </h3>

          <div className={cn(
            'rounded-lg p-5 border-2',
            timeline.isTimelineRealistic
              ? 'bg-green-50/50 dark:bg-green-950/20 border-green-300 dark:border-green-700'
              : 'bg-red-50/50 dark:bg-red-950/20 border-red-300 dark:border-red-700'
          )}>
            <div className="flex items-start gap-3">
              {timeline.isTimelineRealistic ? (
                <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <h4 className={cn(
                  'text-lg font-semibold mb-1',
                  timeline.isTimelineRealistic
                    ? 'text-green-700 dark:text-green-300'
                    : 'text-red-700 dark:text-red-300'
                )}>
                  Timeline is {timeline.isTimelineRealistic ? 'Realistic' : 'Not Realistic'}
                </h4>
                <p className="text-base text-foreground">
                  {timeline.isTimelineRealistic
                    ? 'The proposed timeline appears achievable based on the project scope and milestones.'
                    : 'The proposed timeline may be challenging to meet based on the project requirements and complexity.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function AnalysisTab({ data }: { data: any }) {
  if (!data?.financialAnalysis) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No analysis data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold mb-4">Financial Analysis</h3>

      <FinancialCharts data={data} />
    </div>
  )
}

function RiskAssessmentTab({ data, onPageClick }: { data: any; onPageClick: (page: number, highlightText?: string) => void }) {
  if (!data?.riskAssessment && !data?.environmentalImpact) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No risk assessment data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Risk Assessment Section */}
      {data.riskAssessment && data.riskAssessment.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-primary pl-3 flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Risk Assessment
          </h3>

          <div className="space-y-4">
            {data.riskAssessment.map((risk: any, idx: number) => (
              <div
                key={idx}
                className={cn(
                  'rounded-lg border-2 p-5',
                  risk.severity === 'High'
                    ? 'border-red-300 dark:border-red-700 bg-red-50/50 dark:bg-red-950/20'
                    : risk.severity === 'Medium'
                      ? 'border-orange-300 dark:border-orange-700 bg-orange-50/50 dark:bg-orange-950/20'
                      : 'border-green-300 dark:border-green-700 bg-green-50/50 dark:bg-green-950/20'
                )}
              >
                {/* Risk Header */}
                <div className="flex items-start gap-3 mb-3">
                  <div
                    className={cn(
                      'px-3 py-1.5 rounded-md text-sm font-bold flex-shrink-0',
                      risk.severity === 'High'
                        ? 'bg-red-600 text-white'
                        : risk.severity === 'Medium'
                          ? 'bg-orange-500 text-white'
                          : 'bg-green-600 text-white'
                    )}
                  >
                    {risk.severity}
                  </div>
                  <h4 className="text-lg font-heading font-bold text-foreground flex-1">
                    {risk.riskCategory}
                  </h4>
                </div>

                {/* Risk Description */}
                <p className="text-base text-foreground leading-relaxed mb-3">
                  {createClickablePageLinks(risk.description, onPageClick)}
                </p>

                {/* Evidence Section */}
                {risk.evidence && Array.isArray(risk.evidence) && risk.evidence.length > 0 && (
                  <div className="mt-4 bg-white/50 dark:bg-gray-900/50 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-3 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Evidence
                    </p>
                    <div className="space-y-3">
                      {risk.evidence.map((ev: any, evidx: number) => (
                        <div key={evidx} className="space-y-1.5">
                          {ev.quote && (
                            <blockquote className="text-base italic text-gray-700 dark:text-gray-300 border-l-4 border-amber-400 pl-4 py-2">
                              "{ev.quote}"
                            </blockquote>
                          )}
                          {ev.pageLocation && (
                            <p className="text-sm text-muted-foreground pl-4">
                               Reference: {createEvidencePageLink(ev, onPageClick, evidx)}
                            </p>
                          )}
                            </div>
                          ))}
                        </div>
                  </div>
                )}
                  </div>
                ))}
              </div>
        </div>
      )}

          {/* Environmental Impact Section */}
          {data.environmentalImpact && (
            <div className="space-y-4">
              <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-primary pl-3">
                Environmental Impact
              </h3>
              <EnvironmentalImpact data={data.environmentalImpact} />
            </div>
          )}
        </div>
      )
      }

      function InconsistenciesTab({data, onPageClick}: {data: any; onPageClick: (page: number, highlightText?: string) => void }) {
  const inconsistencies = data?.inconsistencyDetection

      if (!inconsistencies || !inconsistencies.hasInconsistencies) {
    return (
      <div className="text-center py-12">
        <CheckCircle className="h-16 w-16 mx-auto mb-4 text-green-500" />
        <h3 className="text-xl font-heading font-semibold mb-2">No Inconsistencies Detected</h3>
        <p className="text-base text-muted-foreground">The DPR appears to be internally consistent</p>
      </div>
      )
  }

      const categoryIcons = {
        'Budget Mismatch': Target,
      'Timeline Conflict': Clock,
      'Beneficiary Discrepancy': Users,
      'Data Inconsistency': AlertCircle,
  }

      return (
      <div className="space-y-8">
        {/* Header Section */}
        <div className="pb-6 border-b">
          <div className="flex items-start gap-4">
            <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center flex-shrink-0">
              <XCircle className="h-8 w-8 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-heading font-bold text-foreground mb-2">Inconsistencies Detected</h2>
              <p className="text-base text-muted-foreground">
                Found {inconsistencies.totalInconsistenciesFound} issue(s) requiring attention
              </p>
            </div>
          </div>
        </div>

        {/* Issues List */}
        <div className="space-y-4">
          {inconsistencies.issues?.map((issue: any, idx: number) => {
            const Icon = categoryIcons[issue.category as keyof typeof categoryIcons] || AlertCircle
            return (
              <div
                key={idx}
                className={cn(
                  'rounded-lg border-2 p-5',
                  issue.severity === 'Critical'
                    ? 'border-red-300 dark:border-red-700 bg-red-50/50 dark:bg-red-950/20'
                    : issue.severity === 'High'
                      ? 'border-orange-300 dark:border-orange-700 bg-orange-50/50 dark:bg-orange-950/20'
                      : issue.severity === 'Medium'
                        ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50/50 dark:bg-yellow-950/20'
                        : 'border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-950/20'
                )}
              >
                {/* Issue Header */}
                <div className="flex items-start gap-3 mb-3">
                  <div
                    className={cn(
                      'px-3 py-1.5 rounded-md text-sm font-bold flex-shrink-0',
                      issue.severity === 'Critical'
                        ? 'bg-red-600 text-white'
                        : issue.severity === 'High'
                          ? 'bg-orange-500 text-white'
                          : issue.severity === 'Medium'
                            ? 'bg-yellow-500 text-white'
                            : 'bg-green-600 text-white'
                    )}
                  >
                    {issue.severity}
                  </div>
                  <h4 className="text-lg font-heading font-bold text-foreground flex-1">
                    {issue.category}
                  </h4>
                </div>

                {/* Issue Description */}
                <p className="text-base text-foreground leading-relaxed mb-3">
                  {createClickablePageLinks(issue.description, onPageClick)}
                </p>

                {/* Impact Section */}
                {issue.impact && (
                  <div className="mt-4 bg-white/50 dark:bg-gray-900/50 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                    <p className="text-sm font-semibold text-foreground mb-2">Impact Assessment</p>
                    <p className="text-base text-foreground italic leading-relaxed">
                      {createClickablePageLinks(issue.impact, onPageClick)}
                    </p>
                  </div>
                )}

                {/* Evidence Section */}
                {issue.evidence && Array.isArray(issue.evidence) && issue.evidence.length > 0 && (
                  <div className="mt-4 bg-white/50 dark:bg-gray-900/50 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-3 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Evidence
                    </p>
                    <div className="space-y-3">
                      {issue.evidence.map((ev: any, evidx: number) => (
                        <div key={evidx} className="space-y-1.5">
                          {ev.quote && (
                            <blockquote className="text-base italic text-gray-700 dark:text-gray-300 border-l-4 border-amber-400 pl-4 py-2">
                              "{ev.quote}"
                            </blockquote>
                          )}
                          {ev.pageLocation && (
                            <p className="text-sm text-muted-foreground pl-4">
                              ðŸ“ Reference: {createEvidencePageLink(ev, onPageClick, evidx)}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
      )
}

      function ComplianceTab({data, onPageClick}: {data: any; onPageClick: (page: number, highlightText?: string) => void }) {
  const evaluation = data?.evaluationCriteria

      if (!evaluation) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 mx-auto mb-4 text-yellow-500" />
        <p className="text-muted-foreground">Evaluation criteria data not available</p>
      </div>
      )
  }

  const scoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
      return 'text-red-600'
  }

  const formatLabel = (key: string) => {
    const specialCases: Record<string, string> = {
        'technicalFeasibilityAndDesign': 'Technical Feasibility & Design',
      'implementationSchedule': 'Implementation Schedule',
      'costEstimateAndBOQ': 'Cost Estimate & BOQ',
      'riskMitigationAndEnvironment': 'Risk Mitigation & Environment',
      'financialViability': 'Financial Viability',
      'resourceAllocationAndSite': 'Resource Allocation & Site',
    }
      if (specialCases[key]) return specialCases[key]
    return key.replace(/([A-Z])/g, ' $1').replace(/^./, (str) => str.toUpperCase()).trim()
  }

      const criteria = evaluation.criteriaBreakdown
    ? Object.keys(evaluation.criteriaBreakdown).map(key => ({
        key,
        label: formatLabel(key)
    }))
      : []

      return (
      <div className="space-y-8">
        {/* Overall Score Section */}
        <div className="space-y-4">
          <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-primary pl-3 flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Overall Evaluation Score
          </h3>

          <div className="relative overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-sm">
            {/* Subtle gradient background */}
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />

            {/* Content */}
            <div className="relative p-8">
              <div className="flex items-center justify-between gap-6">
                {/* Score Display */}
                <div className="flex-1">
                  <p className="text-sm font-medium text-muted-foreground mb-2">Compliance Score</p>
                  <div className="flex items-baseline gap-2">
                    <span className={`text-6xl font-bold ${scoreColor(evaluation.overallComplianceScore || 0)}`}>
                      {evaluation.overallComplianceScore || 0}
                    </span>
                    <span className="text-3xl font-semibold text-muted-foreground">/100</span>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    {evaluation.overallComplianceScore >= 80 ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-sm font-medium">
                        <CheckCircle className="h-4 w-4" />
                        Excellent
                      </span>
                    ) : evaluation.overallComplianceScore >= 60 ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 text-sm font-medium">
                        Good
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm font-medium">
                        Needs Improvement
                      </span>
                    )}
                  </div>
                </div>

                {/* Icon */}
                <div className="flex-shrink-0">
                  <div className="h-24 w-24 rounded-2xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg">
                    <CheckCircle className="h-12 w-12 text-white" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Criteria Breakdown */}
        <div className="space-y-4">
          <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-primary pl-3">
            Criteria Breakdown
          </h3>

          {criteria.map(({ key, label }) => {
            const item = evaluation.criteriaBreakdown?.[key]
            if (!item) return null

            return (
              <div
                key={key}
                className={cn(
                  'rounded-lg border-2 p-5',
                  item.met
                    ? 'border-green-300 dark:border-green-700 bg-green-50/50 dark:bg-green-950/20'
                    : 'border-red-300 dark:border-red-700 bg-red-50/50 dark:bg-red-950/20'
                )}
              >
                {/* Criterion Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <h4 className="text-lg font-heading font-bold text-foreground flex-1">{label}</h4>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground">Weight: {Math.round(item.weight * 100)}%</span>
                    <span className={`text-lg font-bold ${scoreColor(item.score || 0)}`}>
                      {item.score || 0}/100
                    </span>
                    {item.met ? (
                      <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-6 w-6 text-red-500 flex-shrink-0" />
                    )}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-3">
                  <div
                    className={`h-3 rounded-full transition-all ${item.score >= 80 ? 'bg-green-500' : item.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${item.score || 0}%` }}
                  />
                </div>

                {/* Findings */}
                {item.findings && (
                  <p className="text-base text-foreground leading-relaxed mb-3">
                    {createClickablePageLinks(item.findings, onPageClick)}
                  </p>
                )}

                {/* Detailed Reasoning */}
                {item.detailedReasoning && (
                  <div className="mt-4 bg-white/50 dark:bg-gray-900/50 rounded-lg p-4 border border-blue-200 dark:border-blue-700">
                    <p className="text-sm font-semibold text-foreground mb-2">Detailed Reasoning</p>
                    <p className="text-base text-foreground leading-relaxed">
                      {createClickablePageLinks(item.detailedReasoning, onPageClick)}
                    </p>
                  </div>
                )}

                {/* Evidence */}
                {item.evidence && Array.isArray(item.evidence) && item.evidence.length > 0 && (
                  <div className="mt-4 bg-white/50 dark:bg-gray-900/50 rounded-lg p-4 border border-amber-200 dark:border-amber-800">
                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-3 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Evidence
                    </p>
                    <div className="space-y-3">
                      {item.evidence.map((ev: any, evidx: number) => (
                        <div key={evidx} className="space-y-1.5">
                          {ev.quote && (
                            <blockquote className="text-base italic text-gray-700 dark:text-gray-300 border-l-4 border-amber-400 pl-4 py-2">
                              "{ev.quote}"
                            </blockquote>
                          )}
                          {ev.pageLocation && (
                            <p className="text-sm text-muted-foreground pl-4">
                              ðŸ“ Reference: {createEvidencePageLink(ev, onPageClick, evidx)}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
      )
}

      function RecommendationsTab({data}: {data: any }) {
  const recommendations = data?.smartRecommendations

      if (!recommendations) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-16 w-16 mx-auto mb-4 text-yellow-500" />
        <h3 className="text-xl font-heading font-semibold mb-2">Recommendations Not Available</h3>
        <p className="text-base text-muted-foreground">No smart recommendations have been generated for this DPR</p>
      </div>
      )
  }

      return (
      <div className="space-y-8">
        {/* Critical Actions */}
        {recommendations.criticalActions && recommendations.criticalActions.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-red-500 pl-3 flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              Critical Actions Required
            </h3>

            <div className="space-y-3">
              {recommendations.criticalActions.map((action: string, idx: number) => (
                <div
                  key={idx}
                  className="rounded-lg border-2 border-red-300 dark:border-red-700 bg-red-50/50 dark:bg-red-950/20 p-5"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-600 text-white flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <p className="text-base text-foreground leading-relaxed flex-1">{action}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Improvement Suggestions */}
        {recommendations.improvementSuggestions && recommendations.improvementSuggestions.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-yellow-500 pl-3 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-yellow-500" />
              Improvement Suggestions
            </h3>

            <div className="space-y-3">
              {recommendations.improvementSuggestions.map((suggestion: string, idx: number) => (
                <div
                  key={idx}
                  className="rounded-lg border-2 border-yellow-300 dark:border-yellow-700 bg-yellow-50/50 dark:bg-yellow-950/20 p-5"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-yellow-500 text-white flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <p className="text-base text-foreground leading-relaxed flex-1">{suggestion}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Negotiation Points */}
        {recommendations.negotiationPoints && recommendations.negotiationPoints.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-purple-500 pl-3 flex items-center gap-2">
              <Target className="h-5 w-5 text-purple-500" />
              Negotiation Points
            </h3>

            <div className="space-y-3">
              {recommendations.negotiationPoints.map((point: string, idx: number) => (
                <div
                  key={idx}
                  className="rounded-lg border-2 border-purple-300 dark:border-purple-700 bg-purple-50/50 dark:bg-purple-950/20 p-5"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-500 text-white flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <p className="text-base text-foreground leading-relaxed flex-1">{point}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Next Steps */}
        {recommendations.nextSteps && recommendations.nextSteps.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-xl font-heading font-semibold text-foreground border-l-4 border-green-500 pl-3 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Next Steps (Priority Order)
            </h3>

            <div className="space-y-3">
              {recommendations.nextSteps.map((step: string, idx: number) => (
                <div
                  key={idx}
                  className="rounded-lg border-2 border-green-300 dark:border-green-700 bg-green-50/50 dark:bg-green-950/20 p-5"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center font-bold text-sm">
                      {idx + 1}
                    </div>
                    <p className="text-base text-foreground leading-relaxed flex-1">{step}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      )
}
