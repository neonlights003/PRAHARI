import { Header } from '@/components/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { ArrowRight, FileText, Layers, Upload, Brain, CheckCircle, BarChart3, Clock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useLanguage } from '@/contexts/LanguageContext'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export default function IndexPage() {
  const navigate = useNavigate()
  const { t } = useLanguage()
  const [stats, setStats] = useState({
    totalProjects: 0,
    totalDocuments: 0,
    pending: 0,
    approved: 0,
    loading: true
  })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [projects, dprs] = await Promise.all([
          api.getProjects(),
          api.getDPRs()
        ])

        const totalProjects = projects.length
        const totalDocuments = dprs.length
        const pending = dprs.filter(dpr => !(dpr as any).status || (dpr as any).status === 'pending' || (dpr as any).status === 'analyzing').length
        const approved = dprs.filter(dpr => (dpr as any).status === 'accepted').length

        setStats({ totalProjects, totalDocuments, pending, approved, loading: false })
      } catch (error) {
        console.error('Failed to fetch stats:', error)
        setStats(prev => ({ ...prev, loading: false }))
      }
    }

    fetchStats()

    // Auto-refresh stats when user returns to the dashboard
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchStats()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  const workflowSteps = [
    {
      icon: Upload,
      title: 'Upload Tender',
      description: 'Officer uploads the tender PDF. PRAHARI extracts all eligibility criteria and runs a self-audit for contradictions.',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: Brain,
      title: 'Ingest Bidder Documents',
      description: 'Multi-document bundles per bidder processed in any Indic script. Authenticity scored, evidence mapped per criterion.',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: CheckCircle,
      title: 'AI Verdict + Fraud Check',
      description: 'Criterion matching engine produces Eligible / Not Eligible / Manual Review verdicts. Cross-bidder collusion analysis runs in parallel.',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: BarChart3,
      title: 'Human Review & Sign-off',
      description: 'Officer resolves Manual Review cases via the review queue, queries results in plain English, and digitally signs the final report.',
      color: 'from-orange-500 to-red-500'
    }
  ]

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative container mx-auto px-4 py-8 md:py-12 lg:py-16 overflow-hidden min-h-[calc(100vh-4rem)]">
          {/* Subtle background */}
          <div className="absolute inset-0 -z-10 bg-gradient-to-b from-muted/30 to-transparent"></div>
          <div className="absolute top-20 right-10 w-96 h-96 bg-purple/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 left-10 w-[500px] h-[500px] bg-indigo/10 rounded-full blur-3xl"></div>

          <div className="max-w-6xl mx-auto flex flex-col justify-center min-h-[calc(100vh-8rem)] space-y-12">
            {/* Text Content */}
            <div className="text-center space-y-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium border border-primary/20 animate-fade-in">
                <div className="h-2 w-2 rounded-full bg-primary animate-pulse"></div>
                CRPF AI Procurement — Procurement Officer Portal
              </div>

              <h1 className="text-5xl md:text-6xl lg:text-7xl font-heading font-bold leading-tight animate-slide-up animate-delay-100">
                Tender Eligibility Evaluation{' '}
                <span className="gradient-text">Powered by PRAHARI</span>
              </h1>

              <p className="text-lg md:text-xl text-muted-foreground leading-relaxed max-w-3xl mx-auto animate-slide-up animate-delay-200">
                Upload a tender, ingest bidder documents, and get a fully auditable eligibility verdict matrix —
                criteria extraction to collusion detection in one pipeline.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4 animate-slide-up animate-delay-300">
                <Button
                  size="lg"
                  onClick={() => navigate('/admin/projects')}
                  className="gradient-primary hover:shadow-glow transition-all duration-300 text-white border-0 hover:scale-105"
                >
                  View Tenders
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => navigate('/admin/comparisons')}
                  className="hover:scale-105 transition-all duration-300"
                >
                  Evaluation Board
                </Button>
              </div>
            </div>

            {/* Analytics Cards - Horizontal Layout */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto w-full">
              {/* Active Tenders */}
              <Card className="p-5 border-border/50 hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-card to-purple-50/50 dark:to-purple-950/20 hover:scale-105 animate-scale-in animate-delay-400">
                <div className="flex flex-col h-full justify-between space-y-3">
                  <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Layers className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Active Tenders</p>
                    <h3 className="text-2xl font-heading font-bold text-foreground">
                      {stats.loading ? '--' : stats.totalProjects}
                    </h3>
                  </div>
                </div>
              </Card>

              {/* Bid Documents */}
              <Card className="p-5 border-border/50 hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-card to-blue-50/50 dark:to-blue-950/20 hover:scale-105 animate-scale-in animate-delay-500">
                <div className="flex flex-col h-full justify-between space-y-3">
                  <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Bid Documents</p>
                    <h3 className="text-2xl font-heading font-bold text-foreground">
                      {stats.loading ? '--' : stats.totalDocuments}
                    </h3>
                  </div>
                </div>
              </Card>

              {/* Pending Review */}
              <Card className="p-5 border-border/50 hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-card to-orange-50/50 dark:to-orange-950/20 hover:scale-105 animate-scale-in animate-delay-600">
                <div className="flex flex-col h-full justify-between space-y-3">
                  <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center">
                    <Clock className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Pending Review</p>
                    <h3 className="text-2xl font-heading font-bold text-foreground">
                      {stats.loading ? '--' : stats.pending}
                    </h3>
                  </div>
                </div>
              </Card>

              {/* Evaluations Complete */}
              <Card className="p-5 border-border/50 hover:shadow-xl transition-all duration-300 bg-gradient-to-br from-card to-green-50/50 dark:to-green-950/20 hover:scale-105 animate-scale-in animate-delay-400">
                <div className="flex flex-col h-full justify-between space-y-3">
                  <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-1">Evaluations Complete</p>
                    <h3 className="text-2xl font-heading font-bold text-foreground">
                      {stats.loading ? '--' : stats.approved}
                    </h3>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="container mx-auto px-4 py-16 bg-muted/20">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl md:text-4xl lg:text-5xl font-heading font-bold mb-3">
                How It <span className="gradient-text">Works</span>
              </h2>
              <p className="text-base text-muted-foreground max-w-2xl mx-auto">
                A streamlined workflow from submission to approval
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
              {workflowSteps.map((step, index) => (
                <Card
                  key={index}
                  className="p-5 hover:shadow-lg transition-all duration-300 border-border/50"
                >
                  <div className="space-y-3">
                    <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center`}>
                      <step.icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-primary">STEP {index + 1}</span>
                      </div>
                      <h3 className="text-lg font-heading font-semibold">{step.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Quick Access Cards */}
        <section className="container mx-auto px-4 py-16">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-10">
              <h2 className="text-3xl md:text-4xl font-heading font-bold mb-2">
                Quick <span className="gradient-text">Access</span>
              </h2>
              <p className="text-base text-muted-foreground">
                Navigate to key sections of the admin dashboard
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-5">
              <Card
                className="group p-6 hover:shadow-lg transition-all duration-300 cursor-pointer border-border/50 hover:border-primary/30"
                onClick={() => navigate('/admin/projects')}
              >
                <div className="flex flex-col items-center text-center space-y-3">
                  <div className="h-14 w-14 rounded-xl gradient-primary flex items-center justify-center group-hover:shadow-glow transition-all">
                    <FileText className="h-7 w-7 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-heading font-semibold mb-1.5">Manage Tenders</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Create tenders, upload bidder documents, and track evaluation status
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-primary group-hover:translate-x-1 transition-transform" />
                </div>
              </Card>

              <Card
                className="group p-6 hover:shadow-lg transition-all duration-300 cursor-pointer border-border/50 hover:border-accent/30"
                onClick={() => navigate('/admin/comparisons')}
              >
                <div className="flex flex-col items-center text-center space-y-3">
                  <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-accent to-accent/80 flex items-center justify-center group-hover:shadow-glow transition-all">
                    <Layers className="h-7 w-7 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-heading font-semibold mb-1.5">Evaluation Board</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Confidence heatmap, verdict matrix, and NL Q&A over evaluation results
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-accent group-hover:translate-x-1 transition-transform" />
                </div>
              </Card>

              <Card
                className="group p-6 hover:shadow-lg transition-all duration-300 cursor-pointer border-border/50 hover:border-indigo/30"
              >
                <div className="flex flex-col items-center text-center space-y-3">
                  <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-indigo to-indigo-dark flex items-center justify-center group-hover:shadow-glow transition-all">
                    <Brain className="h-7 w-7 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-heading font-semibold mb-1.5">Audit Trail</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Export SHA-256 verified audit log — every decision traceable to source document and page
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-indigo group-hover:translate-x-1 transition-transform" />
                </div>
              </Card>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border/50 py-6 bg-muted/20">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-3">
            <p className="text-sm text-muted-foreground">
              © 2026{' '}
              <span className="font-heading font-semibold text-foreground">PRAHARI</span> — CRPF AI Procurement
            </p>
            <div className="flex gap-6 text-sm">
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
                {t('landing.privacy')}
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
                {t('landing.terms')}
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary transition-colors">
                {t('landing.contact')}
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
