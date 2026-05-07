import React, { useState, useEffect } from 'react';
import {
    Moon, Sun, FileText, ShieldAlert, CheckCircle2,
    MessageSquare, Globe, Layers, BarChart3, Clock,
    Menu, X, Send, Search, Lock, AlertTriangle
} from 'lucide-react';
import { AuthModal } from '@/components/AuthModal';
import { LanguageDropdown } from '@/components/LanguageDropdown';

const PrahariLanding: React.FC = () => {

    const [isDarkMode, setIsDarkMode] = useState(() => {
        const savedTheme = localStorage.getItem('theme')
        return savedTheme === 'dark' || savedTheme === null
    })
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
    const [chatMessage, setChatMessage] = useState("");
    const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'bot', text: string }[]>([
        { role: 'bot', text: 'Hello! I am the PRAHARI AI assistant for CRPF procurement evaluation. How can I help you today?' }
    ]);
    const [chatSending, setChatSending] = useState(false);

    // Toggle Dark Mode
    useEffect(() => {
        if (isDarkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [isDarkMode]);

    const toggleTheme = () => {
        const newDarkMode = !isDarkMode
        setIsDarkMode(newDarkMode)
        localStorage.setItem('theme', newDarkMode ? 'dark' : 'light')
    }
    const toggleChat = () => setIsChatOpen(!isChatOpen);

    const handleChatSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const q = chatMessage.trim();
        if (!q || chatSending) return;
        setChatHistory(h => [...h, { role: 'user', text: q }]);
        setChatMessage("");
        setChatSending(true);
        try {
            // Use the general Gemini Q&A endpoint (project 0 = no tender context = general assistant)
            const res = await fetch('/api/landing-chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q }),
            });
            const data = await res.json().catch(() => ({}));
            const answer = data.answer ?? "I can help you understand PRAHARI's procurement evaluation capabilities. Try asking about the 9-stage pipeline, bidder eligibility, or collusion detection.";
            setChatHistory(h => [...h, { role: 'bot', text: answer }]);
        } catch {
            setChatHistory(h => [...h, { role: 'bot', text: "I can help with questions about PRAHARI's procurement evaluation pipeline. Ask me about criteria extraction, bidder evaluation, or collusion detection." }]);
        } finally {
            setChatSending(false);
        }
    };

    return (
        <div className={`min-h-screen font-sans transition-colors duration-300 ${isDarkMode ? 'bg-slate-900 text-white' : 'bg-slate-50 text-slate-900'}`}>

            {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
          1. HEADER
      ━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
            <header className={`fixed top-0 w-full z-50 transition-all duration-300 ${isDarkMode ? 'bg-slate-900/70 border-b border-slate-800' : 'bg-white/60 border-b border-slate-200'} backdrop-blur-md`}>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        {/* Logo Area */}
                        <div className="flex items-center space-x-2">
                            <div>
                                <h1 className="text-xl font-bold tracking-tight">PRAHARI</h1>
                            </div>
                            <LanguageDropdown />
                        </div>

                        {/* Desktop Nav & Actions */}
                        <div className="hidden md:flex items-center space-x-6">
                            <nav className="flex space-x-4 text-sm font-medium opacity-80">
                                <a href="#features" className="hover:text-blue-500 transition-colors">Features</a>
                                <a href="#comparison" className="hover:text-blue-500 transition-colors">How It Works</a>
                                <a href="#states" className="hover:text-blue-500 transition-colors">Why PRAHARI</a>
                            </nav>

                            <div className="flex items-center space-x-3 pl-6 border-l border-slate-700/30">
                                {/* Theme Toggle */}
                                <button
                                    onClick={toggleTheme}
                                    className="p-2 rounded-full hover:bg-slate-200/20 transition-colors"
                                    aria-label="Toggle Theme"
                                >
                                    {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
                                </button>

                                {/* Login Button */}
                                <button
                                    onClick={() => setIsAuthModalOpen(true)}
                                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold hover:shadow-lg hover:shadow-blue-500/20 hover:scale-105 transition-all duration-300"
                                >
                                    Login
                                </button>
                            </div>
                        </div>

                        {/* Mobile Menu Button */}
                        <div className="md:hidden flex items-center">
                            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="p-2">
                                {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Mobile Menu */}
                {mobileMenuOpen && (
                    <div className={`md:hidden absolute w-full border-b ${isDarkMode ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'}`}>
                        <div className="px-4 pt-2 pb-6 space-y-4">
                            <a href="#features" className="block py-2 font-medium">Features</a>
                            <a href="#comparison" className="block py-2 font-medium">How It Works</a>
                            <a href="#states" className="block py-2 font-medium">Why PRAHARI</a>
                            <div className="flex items-center justify-between pt-4 border-t border-slate-700/30">
                                <span className="text-sm opacity-70">Theme</span>
                                <button onClick={toggleTheme} className="p-2 bg-slate-200/20 rounded-full">
                                    {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
                                </button>
                            </div>
                            <button onClick={() => setIsAuthModalOpen(true)} className="block w-full text-center py-3 rounded-lg bg-blue-600 text-white font-bold">
                                Login Portal
                            </button>
                        </div>
                    </div>
                )}
            </header>

            <main>
                {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
            2. HERO SECTION
        ━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
                <section className="relative h-screen min-h-[600px] flex items-center justify-center overflow-hidden">
                    {/* Background Gradient */}
                    <div className="absolute inset-0 z-0">
                        {/* Base light background */}
                        <div className={`absolute inset-0 ${isDarkMode ? 'bg-slate-900' : 'bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50'}`}></div>
                        {/* Large blurred purple blob - top right */}
                        <div className={`absolute top-0 right-0 w-[600px] h-[600px] ${isDarkMode ? 'bg-purple-900/40' : 'bg-purple-400/30'} rounded-full blur-3xl`}></div>
                        {/* Large blurred blue blob - bottom left */}
                        <div className={`absolute bottom-0 left-0 w-[700px] h-[700px] ${isDarkMode ? 'bg-blue-900/40' : 'bg-blue-400/30'} rounded-full blur-3xl`}></div>
                        {/* Medium blurred pink blob - center */}
                        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] ${isDarkMode ? 'bg-indigo-900/30' : 'bg-pink-300/20'} rounded-full blur-3xl`}></div>
                    </div>

                    <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                        <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full ${isDarkMode ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' : 'bg-blue-600/15 border-blue-600/30 text-blue-700'} border text-xs font-medium mb-6 animate-fade-in-up`}>
                            <span className="relative flex h-2 w-2">
                                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isDarkMode ? 'bg-blue-400' : 'bg-blue-600'} opacity-75`}></span>
                                <span className={`relative inline-flex rounded-full h-2 w-2 ${isDarkMode ? 'bg-blue-500' : 'bg-blue-600'}`}></span>
                            </span>
                            <span>CRPF AI Procurement — Theme 3</span>
                        </div>

                        <h1 className="text-5xl md:text-6xl lg:text-7xl font-heading font-bold leading-tight animate-slide-up animate-delay-100">
                            Tender Intelligence <br />
                            <span className="gradient-text">PRAHARI</span>
                        </h1>

                        <p className={`text-lg md:text-xl max-w-3xl mx-auto mb-10 ${isDarkMode ? 'text-slate-300' : 'text-slate-600'} animate-slide-up animate-delay-200`}>
                            AI-powered tender eligibility evaluation for CRPF government procurement. <br className="hidden md:block" />
                            From criteria extraction to fraud detection — nine stages, fully auditable.
                        </p>

                        <div className="flex flex-col sm:flex-row items-center justify-center animate-slide-up animate-delay-300">
                            <button
                                onClick={() => setIsAuthModalOpen(true)}
                                className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-lg shadow-lg shadow-blue-500/25 hover:scale-105 hover:shadow-blue-500/40 transition-all duration-300"
                            >
                                Open Evaluation Portal
                            </button>
                        </div>

                        <p className={`mt-8 text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>Gemini AI · FastAPI · React · PostgreSQL · GFR 2017 Compliant</p>
                    </div>
                </section>

                {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
                {/* INTELLIGENT FEATURES SECTION */}
                <section id="features" className="py-24 bg-muted/30 border-y border-border/50">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-16">
                            <h2 className="text-3xl md:text-4xl font-heading font-bold mb-12 text-center">Nine-Stage Evaluation Pipeline</h2>
                            <p className={`text-lg font-semibold max-w-2xl mx-auto ${isDarkMode ? 'text-white' : 'text-black'}`}>Every stage independently auditable. Every decision traceable to a source document and page.</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            <FeatureCard
                                icon={<Search className="text-blue-400" />}
                                title="Criteria Extraction"
                                desc="AI extracts all eligibility criteria from 200-page tenders in one call — typed schema with threshold values, accepted docs, and source quotes."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<ShieldAlert className="text-amber-400" />}
                                title="Tender Self-Audit"
                                desc="Automatically checks the tender itself for contradictions, ambiguous date ranges, and over-restrictive criteria before any bid is evaluated."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<Globe className="text-cyan-400" />}
                                title="Multilingual OCR (13 Scripts)"
                                desc="Natively reads bidder documents in Tamil, Hindi, Marathi, Bengali, and all major Indic scripts. Language logged per document in the audit trail."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<AlertTriangle className="text-red-400" />}
                                title="Document Authenticity"
                                desc="Detects forged GST certificates, manipulated balance sheets, and metadata anomalies. Assigns a tamper-risk score to every uploaded document."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<CheckCircle2 className="text-indigo-400" />}
                                title="Criterion Matching"
                                desc="Deterministic rules for financial thresholds + LLM reasoning for qualitative criteria. Non-disqualification guarantee: low-confidence cases route to Manual Review, never auto-reject."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<Layers className="text-orange-400" />}
                                title="Collusion Detection"
                                desc="Cross-bidder analysis flags shared PDF templates, identical financial figures, metadata overlap, and abnormal pricing clusters."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<BarChart3 className="text-blue-400" />}
                                title="Confidence Heatmap"
                                desc="Bidder × criterion matrix colour-coded by confidence. Officers see in seconds which cases need manual attention."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<MessageSquare className="text-pink-400" />}
                                title="NL Q&A Over Results"
                                desc="Ask plain-English questions: 'Which bidders passed financials but failed on experience?' Powered by Gemini chat."
                                isDarkMode={isDarkMode}
                            />
                            <FeatureCard
                                icon={<Lock className="text-green-400" />}
                                title="Immutable Audit Trail"
                                desc="Every verdict, override, and flag is SHA-256 hashed and timestamped. PostgreSQL trigger blocks any UPDATE or DELETE — legally defensible by design."
                                isDarkMode={isDarkMode}
                            />
                        </div>
                    </div>
                </section>

                {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
            4 & 5. DEMO SECTION (Comparison + Map)
        ━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
                <section id="comparison" className={`py-24 ${isDarkMode ? 'bg-slate-800/50' : 'bg-white'}`}>
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

                            {/* Confidence Heatmap Mini-Demo */}
                            <div className={`p-8 rounded-3xl border ${isDarkMode ? 'bg-slate-900 border-slate-700' : 'bg-slate-50 border-slate-200'} shadow-2xl`}>
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-xl font-bold flex items-center gap-2">
                                        <BarChart3 size={20} className="text-indigo-500" /> Confidence Heatmap
                                    </h3>
                                    <span className="text-xs px-2 py-1 rounded bg-indigo-500/10 text-indigo-500">Preview</span>
                                </div>

                                <div className="space-y-3 text-xs">
                                    {/* Header row */}
                                    <div className="grid grid-cols-5 gap-1 text-center opacity-60 font-medium">
                                        <div></div>
                                        <div>Turnover</div>
                                        <div>ISO Cert</div>
                                        <div>Experience</div>
                                        <div>GST</div>
                                    </div>
                                    {/* Bidder rows */}
                                    {[
                                        { name: 'Bidder A', cells: ['bg-green-500/70', 'bg-green-500/70', 'bg-amber-400/70', 'bg-green-500/70'] },
                                        { name: 'Bidder B', cells: ['bg-green-500/70', 'bg-red-500/70', 'bg-green-500/70', 'bg-green-500/70'] },
                                        { name: 'Bidder C', cells: ['bg-amber-400/70', 'bg-green-500/70', 'bg-red-500/70', 'bg-amber-400/70'] },
                                    ].map(row => (
                                        <div key={row.name} className="grid grid-cols-5 gap-1 items-center">
                                            <div className="font-medium opacity-80 truncate">{row.name}</div>
                                            {row.cells.map((cls, i) => (
                                                <div key={i} className={`h-7 rounded-md ${cls} flex items-center justify-center`}></div>
                                            ))}
                                        </div>
                                    ))}
                                    <div className="flex gap-3 pt-2 opacity-70">
                                        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500/70 inline-block"></span> Eligible</span>
                                        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-400/70 inline-block"></span> Review</span>
                                        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500/70 inline-block"></span> Not Eligible</span>
                                    </div>
                                </div>
                            </div>

                            {/* Audit Trail Card */}
                            <div className={`p-8 rounded-3xl border ${isDarkMode ? 'bg-slate-900 border-slate-700' : 'bg-slate-50 border-slate-200'} shadow-2xl`}>
                                <div className="relative z-10">
                                    <h3 className="text-xl font-bold flex items-center gap-2 mb-2">
                                        <Lock size={20} className="text-blue-500" /> Immutable Audit Trail
                                    </h3>
                                    <p className="text-sm opacity-70 mb-6">Every decision hashed and timestamped. PostgreSQL trigger blocks edits.</p>

                                    <div className="space-y-2 text-xs font-mono">
                                        {[
                                            { type: 'VERDICT_ISSUED', bidder: 'Bidder A', conf: '0.97' },
                                            { type: 'COLLUSION_ALERT', bidder: 'A + C', conf: '0.81' },
                                            { type: 'HUMAN_OVERRIDE', bidder: 'Bidder B', conf: '—' },
                                        ].map((e, i) => (
                                            <div key={i} className={`p-2 rounded-lg ${isDarkMode ? 'bg-slate-800' : 'bg-white border border-slate-200'} flex justify-between`}>
                                                <span className="text-blue-400">{e.type}</span>
                                                <span className="opacity-60">{e.bidder}</span>
                                                <span className="text-green-400">conf:{e.conf}</span>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="flex gap-3 mt-4">
                                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/20 text-green-400 text-xs border border-green-500/30">
                                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> SHA-256 Verified
                                        </div>
                                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/20 text-blue-400 text-xs border border-blue-500/30">
                                            GFR 2017 Compliant
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                </section>

                {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
            6. PLATFORM BENEFITS
        ━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
                <section id="states" className={`py-24 ${isDarkMode ? 'bg-slate-900' : 'bg-slate-50'}`}>
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="text-center mb-12">
                            <h2 className="text-3xl md:text-4xl font-bold mb-3">
                                Why <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-500 to-indigo-600">PRAHARI</span>
                            </h2>
                            <p className="text-lg opacity-60 max-w-2xl mx-auto">
                                The only procurement AI that addresses fraud, collusion, multilingual documents, and legal defensibility in one pipeline
                            </p>
                        </div>

                        <div className="grid md:grid-cols-3 gap-6">
                            {/* Benefit Card 1 */}
                            <div className={`p-8 rounded-2xl border ${isDarkMode ? 'bg-slate-800/50 border-slate-700 hover:bg-slate-800' : 'bg-white border-slate-200 hover:shadow-lg'} transition-all duration-300 hover:-translate-y-1 animate-slide-up`}>
                                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center mb-4 animate-bounce-slow">
                                    <ShieldAlert className="text-white" size={24} />
                                </div>
                                <h3 className="text-xl font-bold mb-2">Non-Disqualification Guarantee</h3>
                                <p className="text-lg opacity-60 leading-relaxed">
                                    The system never silently rejects a bidder. Any verdict below 90% confidence is routed to human review — enforced architecturally, not by policy.
                                </p>
                            </div>

                            {/* Benefit Card 2 */}
                            <div className={`p-8 rounded-2xl border ${isDarkMode ? 'bg-slate-800/50 border-slate-700 hover:bg-slate-800' : 'bg-white border-slate-200 hover:shadow-lg'} transition-all duration-300 hover:-translate-y-1 animate-slide-up animate-delay-100`}>
                                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center mb-4 animate-bounce-slow">
                                    <Clock className="text-white" size={24} />
                                </div>
                                <h3 className="text-xl font-bold mb-2">3–5 Days → Minutes</h3>
                                <p className="text-lg opacity-60 leading-relaxed">
                                    Committees spending 3–5 working days per tender can complete the same evaluation in minutes, with more consistency and a full audit trail.
                                </p>
                            </div>

                            {/* Benefit Card 3 */}
                            <div className={`p-8 rounded-2xl border ${isDarkMode ? 'bg-slate-800/50 border-slate-700 hover:bg-slate-800' : 'bg-white border-slate-200 hover:shadow-lg'} transition-all duration-300 hover:-translate-y-1 animate-slide-up animate-delay-200`}>
                                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center mb-4 animate-bounce-slow">
                                    <FileText className="text-white" size={24} />
                                </div>
                                <h3 className="text-xl font-bold mb-2">Built on Proven Technology</h3>
                                <p className="text-lg opacity-60 leading-relaxed">
                                    Every infrastructure component — Gemini, FastAPI, React, PostgreSQL — is production-tested and GFR 2017 compliant.
                                </p>
                            </div>
                        </div>
                    </div>
                </section>

            </main>

            {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
          9. FOOTER
      ━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
            <footer className={`py-16 border-t ${isDarkMode ? 'bg-slate-950 border-slate-800' : 'bg-slate-100 border-slate-200'}`}>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-12">

                        {/* Column A: PRAHARI Info */}
                        <div className="space-y-4">
                            <div className="mb-4">
                                <span className="font-bold text-lg opacity-90">PRAHARI</span>
                                <p className="text-xs opacity-50 mt-1">AI-Powered Tender Intelligence Platform</p>
                            </div>
                            <p className="text-sm opacity-60 leading-relaxed">
                                CRPF Procurement Evaluation — Theme 3.<br />
                                AI-Powered Procurement Intelligence for CRPF.
                            </p>
                            <div className="text-sm opacity-60 space-y-1">
                                <p>Gemini AI · FastAPI · React · PostgreSQL</p>
                                <p>GFR 2017 Compliant · Differential Privacy</p>
                            </div>
                        </div>

                        {/* Column B: Platform */}
                        <div>
                            <h4 className="font-bold mb-6">Platform</h4>
                            <ul className="space-y-3 text-sm opacity-60">
                                <li><a href="#features" className="hover:text-blue-500 transition-colors">Features</a></li>
                                <li><a href="#comparison" className="hover:text-blue-500 transition-colors">Comparison Tool</a></li>
                                <li><a href="#" className="hover:text-blue-500 transition-colors">Documentation</a></li>
                                <li><a href="#" className="hover:text-blue-500 transition-colors">API Access</a></li>
                                <li><a href="#" className="hover:text-blue-500 transition-colors">Support</a></li>
                            </ul>
                        </div>

                        {/* Column C: Company */}
                        <div>
                            <h4 className="font-bold mb-6">Company</h4>
                            <ul className="space-y-3 text-sm opacity-60">
                                <li><a href="#" className="hover:text-blue-500 transition-colors">About Us</a></li>
                                <li><a href="#" className="hover:text-blue-500 transition-colors">Privacy Policy</a></li>
                                <li><a href="#" className="hover:text-blue-500 transition-colors">Terms of Service</a></li>
                                <li><a href="#" className="hover:text-blue-500 transition-colors">Contact</a></li>
                                <li><a href="#" className="hover:text-blue-500 transition-colors">Careers</a></li>
                            </ul>
                        </div>
                    </div>

                    <div className="mt-16 pt-8 border-t border-slate-500/10 text-center text-xs opacity-40">
                        &copy; {new Date().getFullYear()} PRAHARI — AI-Powered Tender Intelligence for CRPF.
                    </div>
                </div>
            </footer>

            {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━
          7. AI CHAT LAUNCHER
      ━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
            <div className="fixed bottom-6 right-6 z-40">
                <button
                    onClick={toggleChat}
                    className="h-14 w-14 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xl shadow-blue-500/30 flex items-center justify-center hover:scale-110 transition-transform duration-300"
                >
                    {isChatOpen ? <X size={24} /> : <MessageSquare size={24} />}
                </button>
            </div>

            {/* Chat Panel */}
            <div className={`fixed top-0 right-0 h-full w-full sm:w-96 z-30 transform transition-transform duration-300 ease-in-out ${isChatOpen ? 'translate-x-0' : 'translate-x-full'} ${isDarkMode ? 'bg-slate-900 border-l border-slate-800' : 'bg-white border-l border-slate-200'} shadow-2xl`}>
                <div className="flex flex-col h-full">
                    <div className={`p-4 border-b ${isDarkMode ? 'border-slate-800' : 'border-slate-100'} flex justify-between items-center`}>
                        <h3 className="font-bold flex items-center gap-2"><MessageSquare size={18} className="text-blue-500" /> AI Chat</h3>
                        <button
                            onClick={toggleChat}
                            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                            aria-label="Close chat"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {chatHistory.map((msg, i) => (
                            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-slate-200/20 rounded-tl-none'}`}>
                                    {msg.text}
                                </div>
                            </div>
                        ))}
                    </div>

                    <form onSubmit={handleChatSubmit} className={`p-4 border-t ${isDarkMode ? 'border-slate-800' : 'border-slate-100'}`}>
                        <div className="relative">
                            <input
                                type="text"
                                value={chatMessage}
                                onChange={(e) => setChatMessage(e.target.value)}
                                placeholder="Ask about project analysis..."
                                className={`w-full pl-4 pr-10 py-3 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 ${isDarkMode ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-900'}`}
                            />
                            <button type="submit" className="absolute right-2 top-2 p-1.5 rounded-lg bg-blue-500 text-white hover:bg-blue-600 transition-colors">
                                <Send size={16} />
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Auth Modal */}
            <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />

        </div>
    );
};

// Helper Component for Features
const FeatureCard = ({ icon, title, desc, isDarkMode }: { icon: React.ReactNode, title: string, desc: string, isDarkMode: boolean }) => (
    <div className={`p-6 rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${isDarkMode ? 'bg-slate-800/50 border-slate-700 hover:bg-slate-800 hover:shadow-blue-500/10' : 'bg-gradient-to-br from-white to-slate-50 border-blue-100/50 shadow-sm hover:shadow-blue-200/40 hover:border-blue-200'}`}>
        <div className={`h-12 w-12 rounded-xl flex items-center justify-center mb-4 ${isDarkMode ? 'bg-slate-900' : 'bg-slate-50'}`}>
            {icon}
        </div>
        <h3 className="text-lg font-bold mb-2">{title}</h3>
        <p className="text-base opacity-60 leading-relaxed">{desc}</p>
    </div>
);

export default PrahariLanding;