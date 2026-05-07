import { FileText, Moon, Sun, CheckCircle2, LogOut, Sparkles } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Button } from './ui/Button'
import { useState, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { useRole } from '../contexts/RoleContext'
import { api } from '@/lib/api'
import { ProjectSelectionModal } from './ProjectSelectionModal'
import { Card } from './ui/Card'
import { LanguageDropdown } from './LanguageDropdown'

export function Header() {
  const [isDark, setIsDark] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useRole()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Project Selection & Upload State
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [processing, setProcessing] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)

  useEffect(() => {
    // Check localStorage first, then check current state
    const savedTheme = localStorage.getItem('theme')
    const isDarkMode = savedTheme === 'dark' || (!savedTheme && document.documentElement.classList.contains('dark'))

    if (isDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    setIsDark(isDarkMode)
  }, [])

  const toggleDarkMode = () => {
    const newDarkMode = !isDark
    document.documentElement.classList.toggle('dark')
    setIsDark(newDarkMode)
    // Save preference to localStorage
    localStorage.setItem('theme', newDarkMode ? 'dark' : 'light')
  }

  const isActive = (path: string) => location.pathname === path

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Please upload a PDF file')
      return
    }

    setPendingFile(file)
    setIsProjectModalOpen(true)

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleProjectSelect = async (projectId: number) => {
    if (!pendingFile) return

    setIsProjectModalOpen(false)
    setUploading(true)
    setProcessing(false)
    setUploadSuccess(false)
    setUploadProgress(0)

    try {
      const result = await api.uploadDPR(pendingFile, projectId, (progress) => {
        setUploadProgress(progress)
        if (progress === 100) {
          setProcessing(true)
        }
      })

      setUploadSuccess(true)
      // Small delay to show success message before redirect
      setTimeout(() => {
        setUploading(false)
        navigate(`/admin/documents/${result.id}`)
      }, 1500)
    } catch (err) {
      console.error('Upload error:', err)
      alert('Failed to upload file. Please try again.')
      setUploading(false)
    } finally {
      setPendingFile(null)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur-md">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link to="/admin" className="flex items-center gap-2.5 group">
            <div className="h-9 w-9 rounded-lg gradient-primary flex items-center justify-center group-hover:shadow-glow transition-all duration-300">
              <FileText className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-heading font-semibold text-foreground">PRAHARI</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/admin"
              className={cn(
                'px-3.5 py-2 text-sm font-medium transition-all duration-200 rounded-lg',
                isActive('/admin')
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
            >
              Home
            </Link>
            <Link
              to="/admin/projects"
              className={cn(
                'px-3.5 py-2 text-sm font-medium transition-all duration-200 rounded-lg',
                isActive('/admin/projects') || location.pathname.startsWith('/admin/projects/')
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
            >
              Tenders
            </Link>
            <Link
              to="/admin/comparisons"
              className={cn(
                'px-3.5 py-2 text-sm font-medium transition-all duration-200 rounded-lg',
                isActive('/admin/comparisons') || location.pathname.startsWith('/admin/comparison-chat/')
                  ? 'text-primary bg-primary/10'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
            >
              Evaluations
            </Link>
          </nav>

          <div className="flex items-center gap-2.5">
            <LanguageDropdown />
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg hover:bg-muted/50 transition-colors"
              aria-label="Toggle dark mode"
            >
              {isDark ? (
                <Sun className="h-4.5 w-4.5 text-muted-foreground" />
              ) : (
                <Moon className="h-4.5 w-4.5 text-muted-foreground" />
              )}
            </button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
            >
              <LogOut className="h-3.5 w-3.5 mr-1.5" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <ProjectSelectionModal
        isOpen={isProjectModalOpen}
        onClose={() => {
          setIsProjectModalOpen(false)
          setPendingFile(null)
        }}
        onSelect={handleProjectSelect}
      />

      {/* Upload Progress Modal */}
      {uploading && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4 animate-fade-in">
          <Card className="w-full max-w-md p-8 shadow-2xl border-primary/20 animate-scale-in">
            <div className="text-center">
              {uploadSuccess ? (
                <div className="animate-fade-up">
                  <div className="mb-4 flex justify-center">
                    <div className="h-16 w-16 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center shadow-glow animate-scale-in">
                      <CheckCircle2 className="h-8 w-8 text-white" />
                    </div>
                  </div>
                  <h3 className="text-lg font-heading font-semibold mb-2 text-green-600">Upload Complete!</h3>
                  <p className="text-muted-foreground">Redirecting to analysis...</p>
                </div>
              ) : (
                <>
                  <div className="mb-4">
                    <div className="w-16 h-16 mx-auto border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                  </div>
                  <h3 className="text-lg font-heading font-semibold mb-2">
                    {processing ? 'Processing Document...' : 'Uploading...'}
                  </h3>
                  <p className="text-muted-foreground mb-4">
                    {processing
                      ? 'Analyzing content with AI. This may take a moment.'
                      : 'Please wait while we process your document'}
                  </p>
                  <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                    <div
                      className="gradient-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                  <p className="text-sm text-muted-foreground mt-2 font-medium">
                    {processing ? '100%' : `${Math.round(uploadProgress)}%`}
                  </p>
                </>
              )}
            </div>
          </Card>
        </div>
      )}
    </>
  )
}
