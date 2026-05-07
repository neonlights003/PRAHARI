const API_BASE_URL = '/api'
const PRAHARI_API = (import.meta as any).env.VITE_API_URL || 'http://127.0.0.1:8000/api'

function adminHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = localStorage.getItem('adminToken')
  return token
    ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, ...extra }
    : { 'Content-Type': 'application/json', ...extra }
}

export interface DPR {
  id: number
  filename: string
  original_filename: string
  filepath: string
  upload_ts: string
  summary_json: any | null
  project_id?: number
  client_id?: number
  client_email?: string
  admin_feedback?: string
  feedback_timestamp?: string
  validation_flags?: {
    hasFlags: boolean
    flags: Array<{
      type: string
      message: string
      severity: string
    }>
  }
}

export interface Message {
  id: number
  dpr_id: number
  role: string
  text: string
  timestamp: string
}

export interface UploadResponse {
  id: number
  filename: string
  message: string
}

export interface Comparison {
  id: number
  name: string
  created_ts: string
  dprs?: DPR[]
  dpr_count?: number
}

export interface ComparisonMessage {
  id: number
  comparison_id: number
  role: string
  text: string
  timestamp: string
}

export interface Project {
  id: number
  name: string
  state: string
  scheme: string
  sector: string
  created_at: string
  dpr_count?: number
  signed_by?: string
  signed_at?: string
}

// ── PRAHARI types ──────────────────────────────────────────────────────────────

export interface Bidder {
  id: number
  project_id: number
  company_name: string
  gstin?: string
  pan?: string
  contact_email?: string
  status: string
  created_at: string
}

export interface BidderDocument {
  id: number
  bidder_id: number
  document_type: string
  original_filename: string
  uploaded_file_ref?: string
  cloudinary_url?: string
  authenticity_score?: number
  tamper_risk_level?: string
  metadata_flags?: any
  language_detected?: string
  upload_ts: string
}

export interface Verdict {
  id: number
  bidder_id: number
  company_name: string
  criterion_id: string
  verdict: 'Eligible' | 'Not_Eligible' | 'Manual_Review'
  confidence_score: number
  extracted_value_text?: string
  threshold_value?: number
  evidence_quote?: string
  evidence_page?: number
  reasoning?: string
  tamper_risk_score?: number
  human_override: boolean
  override_verdict?: string
  override_justification?: string
  created_at: string
}

export interface CollusionAlert {
  id: number
  project_id: number
  alert_type: string
  bidder_ids: number[]
  description: string
  confidence_score: number
  officer_disposition: string
  disposition_notes?: string
  created_at: string
}

export interface AuditEvent {
  event_id: string
  event_type: string
  project_id?: number
  bidder_id?: number
  criterion_id?: string
  payload_hash: string
  model_version?: string
  confidence_score?: number
  language_detected?: string
  officer_id?: number
  created_at: string
}

export interface TenderCriteria {
  tender_metadata: any
  criteria: any[]
  document_checklist: any[]
  self_audit: any
  market_benchmark_flags: any[]
  summary: any
}

export const api = {
  async getProjects(): Promise<Project[]> {
    const response = await fetch(`${API_BASE_URL}/projects`)
    if (!response.ok) throw new Error('Failed to fetch projects')
    const data = await response.json()
    return data.projects || []
  },

  async createProject(project: Omit<Project, 'id' | 'created_at' | 'dpr_count'>): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(project),
    })
    if (!response.ok) throw new Error('Failed to create project')
    return response.json()
  },

  async deleteProject(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to delete project')
  },

  async getProject(id: number): Promise<Project> {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`)
    if (!response.ok) throw new Error('Failed to fetch project')
    return response.json()
  },

  async getProjectDPRs(projectId: number): Promise<DPR[]> {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/dprs`)
    if (!response.ok) throw new Error('Failed to fetch project DPRs')
    const data = await response.json()
    return data.dprs || []
  },

  async compareAllProjectDPRs(projectId: number): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/compare-all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Comparison failed' }))
      throw new Error(error.detail || 'Failed to compare DPRs')
    }
    return response.json()
  },

  async getDPRs(): Promise<DPR[]> {
    const response = await fetch(`${API_BASE_URL}/dprs`)
    if (!response.ok) throw new Error('Failed to fetch DPRs')
    const data = await response.json()
    return data.dprs || []
  },

  async getDPR(id: number): Promise<DPR> {
    const response = await fetch(`${API_BASE_URL}/dpr/${id}`)
    if (!response.ok) throw new Error('Failed to fetch DPR')
    return response.json()
  },

  async uploadDPR(file: File, projectId?: number, onProgress?: (progress: number) => void): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) {
      formData.append('project_id', projectId.toString())
    }

    const xhr = new XMLHttpRequest()

    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100
          onProgress(progress)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText))
        } else {
          reject(new Error('Upload failed'))
        }
      })

      xhr.addEventListener('error', () => reject(new Error('Upload failed')))
      xhr.open('POST', `${API_BASE_URL}/upload-dpr`)
      xhr.send(formData)
    })
  },

  async sendChatMessage(dprId: number, message: string): Promise<Message> {
    const response = await fetch(`${API_BASE_URL}/dpr/${dprId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    })
    if (!response.ok) throw new Error('Failed to send message')
    const data = await response.json()
    return {
      id: data.message_id,
      dpr_id: dprId,
      role: 'assistant',
      text: data.reply,
      timestamp: new Date().toISOString(),
    }
  },

  async getChatHistory(dprId: number): Promise<Message[]> {
    const response = await fetch(`${API_BASE_URL}/dpr/${dprId}/chat/history`)
    if (!response.ok) throw new Error('Failed to fetch chat history')
    const data = await response.json()
    return data.messages || []
  },

  async clearChatHistory(dprId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/dpr/${dprId}/chat`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to clear chat history')
  },

  async deleteDPR(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/dpr/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to delete DPR')
  },

  async updateDPRFeedback(dprId: number, feedback: string): Promise<void> {
    const formData = new FormData()
    formData.append('feedback', feedback)

    const response = await fetch(`${API_BASE_URL}/dprs/${dprId}/feedback`, {
      method: 'PUT',
      body: formData,
    })
    if (!response.ok) throw new Error('Failed to update feedback')
  },

  async updateDPRStatus(dprId: number, status: string): Promise<void> {
    const formData = new FormData()
    formData.append('status', status)

    const response = await fetch(`${API_BASE_URL}/dprs/${dprId}/status`, {
      method: 'PUT',
      body: formData,
    })
    if (!response.ok) throw new Error('Failed to update status')
  },


  async getComparisons(): Promise<Comparison[]> {
    const response = await fetch(`${API_BASE_URL}/comparison-chats`)
    if (!response.ok) throw new Error('Failed to fetch comparisons')
    const data = await response.json()
    return data.comparisons || []
  },

  async createComparison(name: string, dprIds: number[]): Promise<{ comparison_id: number; name: string }> {
    const response = await fetch(`${API_BASE_URL}/comparison-chats`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, dpr_ids: dprIds }),
    })
    if (!response.ok) throw new Error('Failed to create comparison')
    return response.json()
  },

  async getComparison(id: number): Promise<Comparison> {
    const response = await fetch(`${API_BASE_URL}/comparison-chat/${id}`)
    if (!response.ok) throw new Error('Failed to fetch comparison')
    return response.json()
  },

  async deleteComparison(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/comparison-chat/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to delete comparison')
  },

  async sendComparisonMessage(comparisonId: number, message: string): Promise<ComparisonMessage> {
    const response = await fetch(`${API_BASE_URL}/comparison-chat/${comparisonId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    })
    if (!response.ok) throw new Error('Failed to send message')
    const data = await response.json()
    return {
      id: data.message_id || 0,
      comparison_id: comparisonId,
      role: 'assistant',
      text: data.reply,
      timestamp: new Date().toISOString(),
    }
  },

  async getComparisonChatHistory(comparisonId: number): Promise<ComparisonMessage[]> {
    const response = await fetch(`${API_BASE_URL}/comparison-chat/${comparisonId}/chat/history`)
    if (!response.ok) throw new Error('Failed to fetch comparison chat history')
    const data = await response.json()
    return data.messages || []
  },

  async clearComparisonChatHistory(comparisonId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/comparison-chat/${comparisonId}/chat`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to clear comparison chat history')
  },

  async addDPRToComparison(comparisonId: number, dprId: number): Promise<Comparison> {
    const response = await fetch(`${API_BASE_URL}/comparison-chat/${comparisonId}/add-dpr`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ dpr_id: dprId }),
    })
    if (!response.ok) throw new Error('Failed to add DPR to comparison')
    return response.json()
  },

  async removeDPRFromComparison(comparisonId: number, dprId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/comparison-chat/${comparisonId}/remove-dpr/${dprId}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('Failed to remove DPR from comparison')
  },

  // ── PRAHARI Tender Criteria ────────────────────────────────────────────────
  async extractTenderCriteria(projectId: number): Promise<any> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/extract-criteria`, { method: 'POST', headers: adminHeaders() })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Extraction failed') }
    return res.json()
  },

  async getTenderCriteria(projectId: number): Promise<TenderCriteria> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/criteria`)
    if (!res.ok) throw new Error('Criteria not found')
    const data = await res.json()
    return data.criteria_data
  },

  // ── PRAHARI Bidders ────────────────────────────────────────────────────────
  async getBidders(projectId: number): Promise<Bidder[]> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/bidders`)
    if (!res.ok) throw new Error('Failed to fetch bidders')
    return (await res.json()).bidders || []
  },

  async createBidder(projectId: number, data: { company_name: string; gstin?: string; pan?: string; contact_email?: string }): Promise<{ bidder_id: number }> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/bidders`, {
      method: 'POST',
      headers: adminHeaders(),
      body: JSON.stringify(data),
    })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Failed to create bidder') }
    return res.json()
  },

  async getBidder(bidderId: number): Promise<Bidder & { documents: BidderDocument[] }> {
    const res = await fetch(`${PRAHARI_API}/bidders/${bidderId}`)
    if (!res.ok) throw new Error('Failed to fetch bidder')
    return res.json()
  },

  async deleteBidder(bidderId: number): Promise<void> {
    const res = await fetch(`${PRAHARI_API}/bidders/${bidderId}`, { method: 'DELETE', headers: adminHeaders() })
    if (!res.ok) throw new Error('Failed to delete bidder')
  },

  async uploadBidderDocument(bidderId: number, file: File, documentType: string): Promise<any> {
    const form = new FormData()
    form.append('file', file)
    form.append('document_type', documentType)
    const res = await fetch(`${PRAHARI_API}/bidders/${bidderId}/documents`, { method: 'POST', body: form })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Upload failed') }
    return res.json()
  },

  async getBidderDocuments(bidderId: number): Promise<BidderDocument[]> {
    const res = await fetch(`${PRAHARI_API}/bidders/${bidderId}/documents`)
    if (!res.ok) throw new Error('Failed to fetch documents')
    return (await res.json()).documents || []
  },

  // ── PRAHARI Evaluation ─────────────────────────────────────────────────────
  async evaluateBidder(projectId: number, bidderId: number): Promise<any> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/bidders/${bidderId}/evaluate`, { method: 'POST', headers: adminHeaders() })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Evaluation failed') }
    return res.json()
  },

  async evaluateAllBidders(projectId: number): Promise<any> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/evaluate-all`, { method: 'POST', headers: adminHeaders() })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Evaluation failed') }
    return res.json()
  },

  async getVerdictsMatrix(projectId: number): Promise<Verdict[]> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/verdicts`)
    if (!res.ok) throw new Error('Failed to fetch verdicts')
    return (await res.json()).verdicts || []
  },

  async overrideVerdict(verdictId: number, overrideVerdict: string, justification: string, officerId: number): Promise<any> {
    const res = await fetch(`${PRAHARI_API}/verdicts/${verdictId}/override`, {
      method: 'PUT',
      headers: adminHeaders(),
      body: JSON.stringify({ override_verdict: overrideVerdict, justification, officer_id: officerId }),
    })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Override failed') }
    return res.json()
  },

  // ── PRAHARI Collusion ──────────────────────────────────────────────────────
  async detectCollusion(projectId: number): Promise<any> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/detect-collusion`, { method: 'POST', headers: adminHeaders() })
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || 'Detection failed') }
    return res.json()
  },

  async getCollusionAlerts(projectId: number): Promise<CollusionAlert[]> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/collusion-alerts`)
    if (!res.ok) throw new Error('Failed to fetch alerts')
    return (await res.json()).alerts || []
  },

  // ── PRAHARI Audit Trail ────────────────────────────────────────────────────
  async getAuditTrail(projectId: number): Promise<AuditEvent[]> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/audit-trail`)
    if (!res.ok) throw new Error('Failed to fetch audit trail')
    return (await res.json()).events || []
  },

  async runBenchmarkValidation(projectId: number, enhance = true): Promise<Record<string, any>> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/benchmark?enhance=${enhance}`, { method: 'POST' })
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'Benchmark validation failed') }
    return res.json()
  },

  async getVendorHistory(projectId: number): Promise<Record<string, any>> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/vendor-history`)
    if (!res.ok) throw new Error('Failed to fetch vendor history')
    return res.json()
  },

  async lookupVendor(companyName: string, gstin?: string, pan?: string): Promise<Record<string, any>> {
    const res = await fetch(`${PRAHARI_API}/vendors/lookup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_name: companyName, gstin, pan }),
    })
    if (!res.ok) throw new Error('Vendor lookup failed')
    return res.json()
  },

  downloadEvaluationReport(projectId: number): void {
    window.open(`${PRAHARI_API}/tenders/${projectId}/report`, '_blank')
  },

  async signOffTender(projectId: number, officerName: string): Promise<{ signed_by: string }> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/sign-off`, {
      method: 'POST',
      headers: adminHeaders(),
      body: JSON.stringify({ officer_name: officerName }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Sign-off failed' }))
      throw new Error(err.detail || 'Sign-off failed')
    }
    return res.json()
  },

  async getCriteriaWeights(projectId: number): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/compliance-weights`)
    if (!res.ok) throw new Error('Failed to fetch criteria weights')
    return res.json()
  },

  async updateCriteriaWeights(projectId: number, weights: Record<string, number>): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/compliance-weights`, {
      method: 'PUT',
      headers: adminHeaders(),
      body: JSON.stringify({ weights }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Update failed' }))
      throw new Error(err.detail || 'Failed to update weights')
    }
  },

  async resetCriteriaWeights(projectId: number): Promise<void> {
    const res = await fetch(`${API_BASE_URL}/projects/${projectId}/compliance-weights/reset`, {
      method: 'POST',
      headers: adminHeaders(),
    })
    if (!res.ok) throw new Error('Failed to reset weights')
  },

  async getTenderAnalytics(projectId: number, epsilon = 1.0, resetBudget = false): Promise<Record<string, any>> {
    const params = new URLSearchParams({ epsilon: String(epsilon), reset_budget: String(resetBudget) })
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/analytics?${params}`)
    if (!res.ok) throw new Error('Failed to fetch analytics')
    return res.json()
  },

  async askEvaluationQuestion(projectId: number, question: string): Promise<string> {
    const res = await fetch(`${PRAHARI_API}/tenders/${projectId}/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    })
    if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || 'Q&A request failed') }
    return (await res.json()).answer
  },

  async clearEvaluationQA(projectId: number): Promise<void> {
    await fetch(`${PRAHARI_API}/tenders/${projectId}/qa`, { method: 'DELETE' })
  },
}
