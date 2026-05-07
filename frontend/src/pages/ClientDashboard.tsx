import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useRole } from '@/contexts/RoleContext'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Upload, FileText, Download, Clock, Trash2, MessageSquare, X, CheckCircle, XCircle, AlertCircle, Search, Filter, BarChart3, ArrowRight } from 'lucide-react'
import { LanguageDropdown } from '@/components/LanguageDropdown'

interface ClientDPR {
    id: number
    client_id: number
    project_name: string
    dpr_filename: string
    original_filename: string
    status: string
    created_at: string
    admin_feedback?: string
    feedback_timestamp?: string
}

interface Project {
    id: number
    name: string
    state: string
    scheme: string
    sector: string
}

export default function ClientDashboard() {
    const navigate = useNavigate()
    const { userInfo, logoutUser } = useRole()
    const [dprs, setDprs] = useState<ClientDPR[]>([])
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(true)
    const [loadingProjects, setLoadingProjects] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [successMessage, setSuccessMessage] = useState<string | null>(null)
    const [selectedFeedback, setSelectedFeedback] = useState<ClientDPR | null>(null)
    const [searchQuery, setSearchQuery] = useState('')
    const [filterStatus, setFilterStatus] = useState<string>('all')

    // Form state
    const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [isDragging, setIsDragging] = useState(false)

    useEffect(() => {
        if (!userInfo) {
            navigate('/user/auth')
            return
        }
        fetchDPRs()
        fetchProjects()
    }, [userInfo, navigate])

    const fetchProjects = async () => {
        try {
            setLoadingProjects(true)
            const response = await fetch('http://127.0.0.1:8000/projects')
            if (!response.ok) throw new Error('Failed to fetch projects')
            const data = await response.json()
            setProjects(data.projects)
        } catch (err) {
            setError('Failed to load projects. Please try again.')
            console.error('Fetch projects error:', err)
        } finally {
            setLoadingProjects(false)
        }
    }

    const fetchDPRs = async () => {
        if (!userInfo) return

        try {
            setLoading(true)
            const response = await fetch(`http://127.0.0.1:8000/api/client/dprs?client_id=${userInfo.id}`)
            if (!response.ok) throw new Error('Failed to fetch DPRs')
            const data = await response.json()
            setDprs(data.dprs)
        } catch (err) {
            setError('Failed to load your DPRs. Please try again.')
            console.error('Fetch error:', err)
        } finally {
            setLoading(false)
        }
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                setError('Only PDF files are allowed.')
                return
            }
            setSelectedFile(file)
            setError(null)
        }
    }

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = () => {
        setIsDragging(false)
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragging(false)

        const file = e.dataTransfer.files[0]
        if (file && file.name.toLowerCase().endsWith('.pdf')) {
            setSelectedFile(file)
            setError(null)
        } else {
            setError('Only PDF files are allowed.')
        }
    }

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!userInfo) {
            setError('You must be logged in to upload DPRs.')
            return
        }

        if (!selectedProjectId) {
            setError('Please select a project.')
            return
        }

        if (!selectedFile) {
            setError('Please select a PDF file.')
            return
        }

        setUploading(true)
        setError(null)
        setSuccessMessage(null)

        try {
            const selectedProject = projects.find(p => p.id === selectedProjectId)
            if (!selectedProject) {
                throw new Error('Selected project not found')
            }

            const formData = new FormData()
            formData.append('client_id', userInfo.id.toString())
            formData.append('project_id', selectedProjectId.toString())
            formData.append('project_name', selectedProject.name)
            formData.append('file', selectedFile)

            const response = await fetch('http://127.0.0.1:8000/api/client/dprs/upload', {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Upload failed')
            }

            const result = await response.json()
            setSuccessMessage(result.message)
            setSelectedProjectId(null)
            setSelectedFile(null)

            const fileInput = document.getElementById('dpr-file') as HTMLInputElement
            if (fileInput) fileInput.value = ''

            await fetchDPRs()
        } catch (err: any) {
            setError(err.message || 'Failed to upload DPR. Please try again.')
            console.error('Upload error:', err)
        } finally {
            setUploading(false)
        }
    }

    const handleDownload = async (dpr: ClientDPR) => {
        if (!userInfo) return

        try {
            const response = await fetch(
                `http://127.0.0.1:8000/api/client/dprs/${dpr.id}/download?client_id=${userInfo.id}`
            )

            if (!response.ok) throw new Error('Failed to download file')

            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = dpr.original_filename
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch (err) {
            setError('Failed to download file. Please try again.')
            console.error('Download error:', err)
        }
    }

    const handleDelete = async (dpr: ClientDPR) => {
        if (!userInfo) return

        if (!confirm(`Are you sure you want to delete "${dpr.original_filename}"? This action cannot be undone.`)) {
            return
        }

        try {
            const url = `http://127.0.0.1:8000/api/client/dprs/${dpr.id}?client_id=${userInfo.id}`
            const response = await fetch(url, { method: 'DELETE' })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Failed to delete')
            }

            const result = await response.json()
            setSuccessMessage(result.message)
            await fetchDPRs()
        } catch (err: any) {
            setError(err.message || 'Failed to delete DPR. Please try again.')
        }
    }

    const formatDate = (dateString: string) => {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const handleLogout = () => {
        logoutUser()
        navigate('/')
    }

    // Calculate stats
    const stats = {
        total: dprs.length,
        pending: dprs.filter(d => d.status === 'pending' || d.status === 'completed').length,
        accepted: dprs.filter(d => d.status === 'accepted').length,
        rejected: dprs.filter(d => d.status === 'rejected').length
    }

    // Filter DPRs
    const filteredDPRs = dprs.filter(dpr => {
        const matchesSearch = dpr.project_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            dpr.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
        const matchesFilter = filterStatus === 'all' || dpr.status === filterStatus
        return matchesSearch && matchesFilter
    })

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
            {/* Animated Background Orbs */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-20 left-10 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-pulse"></div>
                <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
            </div>

            {/* Header */}
            <header className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-50 shadow-sm">
                <div className="container mx-auto flex h-16 items-center justify-between px-4">
                    <div className="flex items-center gap-2">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-purple-600">
                            <FileText className="h-6 w-6 text-white" />
                        </div>
                        <span className="text-xl font-heading font-bold gradient-text">PRAHARI</span>
                    </div>

                    <div className="flex items-center gap-4">
                        <LanguageDropdown />
                        <span className="text-sm text-muted-foreground hidden sm:block">
                            Welcome, <span className="font-semibold text-foreground">{userInfo?.name || 'User'}</span>
                        </span>
                        <Button variant="outline" size="sm" onClick={handleLogout}>
                            Logout
                        </Button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="relative container mx-auto px-4 py-8 max-w-7xl">
                {/* Welcome Section */}
                <div className="mb-8 animate-slide-up">
                    <h1 className="text-3xl md:text-4xl font-heading font-bold mb-2">
                        Welcome back, <span className="gradient-text">{userInfo?.name || 'User'}!</span>
                    </h1>
                    <p className="text-muted-foreground">Here's an overview of your project submissions</p>
                </div>

                {/* Self-Check Quick Access */}
                <Card
                    className="p-5 mb-8 flex items-center justify-between gap-4 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950/20 dark:to-teal-950/20 border-emerald-200 dark:border-emerald-800 cursor-pointer hover:shadow-md transition-shadow animate-slide-up"
                    onClick={() => navigate('/user/self-check')}
                >
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center shrink-0">
                            <BarChart3 className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <p className="font-semibold text-emerald-800 dark:text-emerald-200">Pre-submission Self-Check</p>
                            <p className="text-xs text-emerald-600 dark:text-emerald-400">Upload your documents for an instant AI eligibility assessment before submitting to a tender.</p>
                        </div>
                    </div>
                    <ArrowRight className="h-5 w-5 text-emerald-600 shrink-0" />
                </Card>


                {/* Upload New DPR Section */}
                <Card className="p-8 mb-8 bg-gradient-to-br from-white to-blue-50/30 dark:from-slate-900 dark:to-blue-950/10 border-2 border-dashed border-primary/30 hover:border-primary/50 transition-all animate-slide-up animate-delay-100">
                    <h2 className="text-2xl font-heading font-bold mb-6 flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                            <Upload className="h-5 w-5 text-white" />
                        </div>
                        Upload New DPR
                    </h2>

                    <form onSubmit={handleUpload} className="space-y-6">
                        {/* Project Selection */}
                        <div>
                            <label htmlFor="project-select" className="block text-sm font-semibold mb-3">
                                Select Project <span className="text-red-500">*</span>
                            </label>
                            {loadingProjects ? (
                                <div className="w-full px-4 py-3 border border-border rounded-xl bg-muted/50 text-muted-foreground">
                                    Loading projects...
                                </div>
                            ) : projects.length === 0 ? (
                                <div className="w-full px-4 py-3 border-2 border-orange-300 bg-orange-50 dark:bg-orange-950/20 rounded-xl text-orange-700 dark:text-orange-400">
                                    No projects available. Please ask an admin to create projects first.
                                </div>
                            ) : (
                                <select
                                    id="project-select"
                                    value={selectedProjectId || ''}
                                    onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                                    className="w-full px-4 py-3 border-2 border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background transition-all"
                                    required
                                    disabled={uploading}
                                >
                                    <option value="">-- Select a project --</option>
                                    {projects.map((project) => (
                                        <option key={project.id} value={project.id}>
                                            {project.name} ({project.state} - {project.scheme})
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>

                        {/* Drag and Drop File Upload */}
                        <div>
                            <label className="block text-sm font-semibold mb-3">
                                Upload DPR (PDF only) <span className="text-red-500">*</span>
                            </label>
                            <div
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${isDragging
                                    ? 'border-primary bg-primary/5 scale-105'
                                    : 'border-border hover:border-primary/50 hover:bg-muted/30'
                                    }`}
                            >
                                <input
                                    id="dpr-file"
                                    type="file"
                                    accept=".pdf"
                                    onChange={handleFileChange}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    disabled={uploading}
                                />
                                <div className="pointer-events-none">
                                    <Upload className="h-12 w-12 mx-auto mb-4 text-primary/50" />
                                    {selectedFile ? (
                                        <div className="space-y-2">
                                            <p className="text-sm font-semibold text-foreground">{selectedFile.name}</p>
                                            <p className="text-xs text-muted-foreground">
                                                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                            </p>
                                        </div>
                                    ) : (
                                        <div>
                                            <p className="text-sm font-medium mb-1">
                                                Drag and drop your PDF here, or click to browse
                                            </p>
                                            <p className="text-xs text-muted-foreground">
                                                Maximum file size: 50MB
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Error/Success Messages */}
                        {error && (
                            <div className="p-4 bg-red-50 dark:bg-red-950/20 border-2 border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 text-sm flex items-start gap-3">
                                <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                                <span>{error}</span>
                            </div>
                        )}

                        {successMessage && (
                            <div className="p-4 bg-green-50 dark:bg-green-950/20 border-2 border-green-200 dark:border-green-800 rounded-xl text-green-600 dark:text-green-400 text-sm flex items-start gap-3">
                                <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
                                <span>{successMessage}</span>
                            </div>
                        )}

                        {/* Submit Button */}
                        <Button
                            type="submit"
                            disabled={uploading}
                            className="w-full h-12 text-base font-semibold rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all"
                        >
                            {uploading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                                    Uploading...
                                </>
                            ) : (
                                <>
                                    <Upload className="h-5 w-5 mr-2" />
                                    Upload DPR
                                </>
                            )}
                        </Button>
                    </form>
                </Card>

                {/* Recent Uploads Table */}
                <Card className="p-6 animate-slide-up animate-delay-300">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center">
                            <Upload className="h-4 w-4 text-white" />
                        </div>
                        <h2 className="text-2xl font-heading font-bold">Recent Uploads</h2>
                    </div>

                    {loading ? (
                        <div className="text-center py-12">
                            <div className="w-12 h-12 mx-auto border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                            <p className="text-muted-foreground mt-4">Loading your DPRs...</p>
                        </div>
                    ) : dprs.length === 0 ? (
                        <div className="text-center py-12">
                            <FileText className="h-16 w-16 mx-auto text-muted-foreground/30 mb-4" />
                            <p className="text-lg font-medium text-muted-foreground mb-2">No uploads yet</p>
                            <p className="text-sm text-muted-foreground">Upload your first DPR document to get started</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left py-3 px-4 font-semibold text-sm text-muted-foreground">Project Name</th>
                                        <th className="text-left py-3 px-4 font-semibold text-sm text-muted-foreground">File Name</th>
                                        <th className="text-left py-3 px-4 font-semibold text-sm text-muted-foreground">Status</th>
                                        <th className="text-left py-3 px-4 font-semibold text-sm text-muted-foreground">Uploaded</th>
                                        <th className="text-center py-3 px-4 font-semibold text-sm text-muted-foreground">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {dprs.slice(0, 5).map((dpr) => (
                                        <tr key={dpr.id} className="border-b hover:bg-muted/30 transition-colors">
                                            <td className="py-4 px-4 font-medium">{dpr.project_name}</td>
                                            <td className="py-4 px-4">
                                                <span className="text-sm text-muted-foreground line-clamp-1 max-w-xs">{dpr.original_filename}</span>
                                            </td>
                                            <td className="py-4 px-4">
                                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${dpr.status === 'accepted'
                                                    ? 'bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-400'
                                                    : dpr.status === 'rejected'
                                                        ? 'bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400'
                                                        : dpr.status === 'pending'
                                                            ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-400'
                                                            : 'bg-blue-100 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400'
                                                    }`}>
                                                    {dpr.status === 'accepted' ? 'Accepted'
                                                        : dpr.status === 'rejected' ? 'Rejected'
                                                            : dpr.status === 'pending' ? 'Pending'
                                                                : 'Under Review'}
                                                </span>
                                            </td>
                                            <td className="py-4 px-4 text-sm text-muted-foreground">
                                                {new Date(dpr.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                            </td>
                                            <td className="py-4 px-4">
                                                <div className="flex items-center justify-center gap-2">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleDownload(dpr)}
                                                        className="h-8 px-2"
                                                    >
                                                        <Download className="h-4 w-4" />
                                                    </Button>
                                                    {dpr.admin_feedback && (
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            onClick={() => setSelectedFeedback(dpr)}
                                                            className="h-8 px-2"
                                                        >
                                                            <MessageSquare className="h-4 w-4" />
                                                        </Button>
                                                    )}
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={() => handleDelete(dpr)}
                                                        className="h-8 px-2 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/20"
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </Card>
            </main>

            {/* Footer */}
            <footer className="border-t bg-background/50 backdrop-blur-sm py-6 mt-12">
                <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
                    © 2025 <span className="gradient-text font-semibold">PRAHARI</span> - All rights reserved
                </div>
            </footer>

            {/* Enhanced Feedback Modal */}
            {selectedFeedback && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
                    <Card className="w-full max-w-2xl p-8 max-h-[85vh] overflow-y-auto animate-in zoom-in-95 duration-200 shadow-2xl">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-3xl font-heading font-bold flex items-center gap-3 mb-2">
                                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                                        <MessageSquare className="h-5 w-5 text-white" />
                                    </div>
                                    Admin Feedback
                                </h2>
                                <p className="text-sm text-muted-foreground">
                                    For: <span className="font-medium text-foreground">{selectedFeedback.original_filename}</span>
                                </p>
                            </div>
                            <button
                                onClick={() => setSelectedFeedback(null)}
                                className="text-muted-foreground hover:text-foreground transition-colors p-2 hover:bg-muted rounded-lg"
                            >
                                <X className="h-6 w-6" />
                            </button>
                        </div>

                        <div className="mb-6">
                            <div className="bg-gradient-to-br from-muted/50 to-muted/30 rounded-xl p-6 border border-border/50">
                                <p className="text-base leading-relaxed whitespace-pre-wrap">
                                    {selectedFeedback.admin_feedback}
                                </p>
                            </div>
                            {selectedFeedback.feedback_timestamp && (
                                <p className="text-xs text-muted-foreground mt-3 flex items-center gap-2">
                                    <Clock className="h-3.5 w-3.5" />
                                    Received on: {new Date(selectedFeedback.feedback_timestamp).toLocaleString()}
                                </p>
                            )}
                        </div>

                        <div className="flex justify-end">
                            <Button
                                onClick={() => setSelectedFeedback(null)}
                                className="px-6"
                            >
                                Close
                            </Button>
                        </div>
                    </Card>
                </div>
            )}
        </div>
    )
}