import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { hrApi } from '../services/api.js'
import {
    Users, FileText, TrendingUp, CheckCircle, Clock,
    Cpu, Activity, Zap, Award, Briefcase, Brain, Target,
    CalendarDays, MessageSquare, Upload, ArrowRight,
    UserCheck, BarChart3, BookOpen, Bell, Star
} from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend, AreaChart, Area
} from 'recharts'

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']

const agentStatuses = [
    { name: 'CV Agent', icon: '📄', tasks: 12, color: '#6366f1' },
    { name: 'Interview Agent', icon: '🎤', tasks: 4, color: '#06b6d4' },
    { name: 'Onboarding Agent', icon: '🚀', tasks: 2, color: '#10b981' },
    { name: 'Training Agent', icon: '📚', tasks: 7, color: '#f59e0b' },
    { name: 'Payroll Agent', icon: '💰', tasks: 15, color: '#8b5cf6' },
    { name: 'Leave Agent', icon: '🏖️', tasks: 9, color: '#ec4899' },
]

const mockScoreData = [
    { range: '90-100', count: 3 },
    { range: '80-90', count: 8 },
    { range: '70-80', count: 15 },
    { range: '60-70', count: 22 },
    { range: '50-60', count: 18 },
    { range: '<50', count: 9 },
]

const mockStatusData = [
    { name: 'Pending', value: 45 },
    { name: 'Shortlisted', value: 20 },
    { name: 'Interview', value: 12 },
    { name: 'Hired', value: 8 },
    { name: 'Rejected', value: 15 },
]

const mockActivityData = [
    { day: 'Mon', cvs: 8, interviews: 2 },
    { day: 'Tue', cvs: 14, interviews: 5 },
    { day: 'Wed', cvs: 11, interviews: 3 },
    { day: 'Thu', cvs: 19, interviews: 7 },
    { day: 'Fri', cvs: 16, interviews: 4 },
    { day: 'Sat', cvs: 5, interviews: 1 },
    { day: 'Sun', cvs: 3, interviews: 0 },
]

const recentActivity = [
    { type: 'cv', text: 'New CV uploaded — Mohamed Yassine Chrigui', time: '5m ago', score: 60 },
    { type: 'interview', text: 'Interview scheduled — Sarah El Amin', time: '1h ago', score: null },
    { type: 'hire', text: 'Candidate hired — Omar Ben Ali', time: '3h ago', score: null },
    { type: 'cv', text: 'New CV uploaded — Laura Martin', time: '5h ago', score: 84 },
]

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
        <div style={{
            background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 10,
            padding: '10px 14px',
            fontSize: 13,
            boxShadow: 'var(--shadow-md)'
        }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
            {payload.map((p, i) => (
                <p key={i} style={{ color: p.color, fontWeight: 700 }}>{p.name}: {p.value}</p>
            ))}
        </div>
    )
}

// ─── HR Dashboard ────────────────────────────────────────────────────────────
function HRDashboard({ stats, isLoading, navigate }) {
    const rec = stats?.recruitment || {}
    const priv = stats?.privacy || {}
    const jobs = stats?.jobs || {}

    // Transformer la distribution de score
    const scoreData = rec.score_distribution 
        ? Object.entries(rec.score_distribution).map(([range, count]) => ({ range, count })) 
        : mockScoreData

    // Pipeline data
    const pipelineData = [
        { name: 'En attente', value: rec.pending ?? 0 },
        { name: 'Shortlistés', value: rec.shortlisted ?? 0 },
        { name: 'Recrutés', value: rec.hired ?? 0 },
    ]

    // Formater la heatmap des compétences
    const skillsData = rec.skills_heatmap || [
        { skill: 'Python', count: 12 },
        { skill: 'React', count: 8 },
        { skill: 'Docker', count: 5 }
    ]

    // Formater les jobs
    const topCandsPerJob = rec.top_candidates_per_job || {}

    return (
        <>
            {/* KPI Cards */}
            <div className="stat-grid" style={{ marginBottom: '1.75rem' }}>
                {[
                    { label: 'Candidats Totaux', value: isLoading ? '…' : rec.total_candidates ?? 0, icon: Users, color: 'indigo', change: 'Enregistrés en base', dir: 'up', link: '/candidates' },
                    { label: 'Score IA Moyen', value: isLoading ? '…' : `${Math.round(rec.average_score ?? 0)}%`, icon: Brain, color: 'emerald', change: 'Compétences & Exp', dir: 'up', link: '/candidates' },
                    { label: 'Candidats Shortlistés', value: isLoading ? '…' : rec.shortlisted ?? 0, icon: UserCheck, color: 'cyan', change: 'Sélection prioritaires', dir: 'up', link: '/candidates' },
                    { label: 'Postes Ouverts', value: isLoading ? '…' : jobs.total_active ?? 0, icon: Briefcase, color: 'amber', change: 'Offres actives', dir: 'up', link: '/jobs' },
                    { label: 'Temps d\'analyse moyen', value: isLoading ? '…' : `${rec.average_processing_time_sec ?? 1.4}s`, icon: Clock, color: 'emerald', change: 'Optimisation asynchrone', dir: 'up', link: '/cv-analysis' },
                ].map(({ label, value, icon: Icon, color, change, dir, link }) => (
                    <div className="stat-card" key={label} onClick={() => navigate(link)} style={{ cursor: 'pointer' }}>
                        <div className={`stat-icon ${color}`}><Icon size={22} /></div>
                        <div>
                            <div className="stat-value">{value}</div>
                            <div className="stat-label">{label}</div>
                            <div className="stat-change up" style={{ color: 'var(--text-muted)' }}><Activity size={11} /> {change}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                {/* Weekly Activity */}
                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <TrendingUp size={16} color="#6366f1" /> Activité Hebdomadaire (Dépôts de CV)
                    </h3>
                    <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={rec.activity_chart || mockActivityData}>
                            <defs>
                                <linearGradient id="cvGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="intGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.07)" />
                            <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Area type="monotone" dataKey="cvs" stroke="#6366f1" strokeWidth={2} fill="url(#cvGrad)" name="CVs Déposés" />
                            <Area type="monotone" dataKey="interviews" stroke="#06b6d4" strokeWidth={2} fill="url(#intGrad)" name="Entretiens" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Pipeline Pie */}
                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <BarChart3 size={16} color="#06b6d4" /> Pipeline des Candidats
                    </h3>
                    <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                            <Pie data={pipelineData} cx="50%" cy="50%" innerRadius={50} outerRadius={78}
                                paddingAngle={3} dataKey="value">
                                {pipelineData.map((_, i) => (
                                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip content={<CustomTooltip />} />
                            <Legend iconType="circle" iconSize={9}
                                formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{v}</span>} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Bottom Row: Score Distribution + Skills Heatmap + Top Candidates per Job */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr 1fr', gap: '1.5rem' }}>
                {/* Score Distribution */}
                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>Distribution des Scores CV</h3>
                    <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={scoreData} barSize={22}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                            <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 10 }} />
                            <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                            <Tooltip content={<CustomTooltip />} />
                            <Bar dataKey="count" fill="url(#barGradient)" radius={[4, 4, 0, 0]} name="Candidats" />
                            <defs>
                                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#6366f1" />
                                    <stop offset="100%" stopColor="#06b6d4" />
                                </linearGradient>
                            </defs>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Skills Heatmap */}
                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Target size={16} color="#fbbf24" /> Heatmap des Compétences CV
                    </h3>
                    <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={skillsData} layout="vertical" barSize={12}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                            <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} />
                            <YAxis dataKey="skill" type="category" tick={{ fill: '#64748b', fontSize: 10 }} width={80} />
                            <Tooltip />
                            <Bar dataKey="count" fill="#fbbf24" radius={[0, 4, 4, 0]} name="Occurrences" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Top Candidates Per Job */}
                <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
                    <h3 style={{ marginBottom: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Award size={16} color="#10b981" /> Top Profils par Poste
                    </h3>
                    <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 180 }}>
                        {Object.entries(topCandsPerJob).length === 0 ? (
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', padding: '20px 0' }}>
                                En attente d'évaluations de postes...
                            </div>
                        ) : (
                            Object.entries(topCandsPerJob).map(([title, list]) => (
                                <div key={title} style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, border: '1px solid var(--color-border)' }}>
                                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-primary-light)' }}>{title}</div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>
                                        {list.map((cand, idx) => (
                                            <div key={cand.candidate_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }} onClick={() => navigate(`/candidates/${cand.candidate_id}`)}>
                                                <span style={{ cursor: 'pointer', color: 'var(--text-primary)' }}>{idx+1}. {cand.name}</span>
                                                <span style={{ fontWeight: 700, color: 'var(--color-success)' }}>{cand.score}%</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </>
    )
}

// ─── Employee Dashboard ──────────────────────────────────────────────────────
function EmployeeDashboard({ user, navigate }) {
    const name = user?.name || user?.email?.split('@')[0] || 'Employee'

    const upcomingEvents = [
        { date: 'Apr 12', label: 'Team Meeting', type: 'meeting' },
        { date: 'Apr 15', label: 'Annual Review', type: 'review' },
        { date: 'Apr 18', label: 'Training: Cloud Basics', type: 'training' },
    ]

    const myProgress = [
        { label: 'Cloud Fundamentals', pct: 78, color: '#6366f1' },
        { label: 'Leadership Skills', pct: 45, color: '#06b6d4' },
        { label: 'Agile Methods', pct: 92, color: '#10b981' },
    ]

    return (
        <>
            {/* Welcome Banner */}
            <div className="card" style={{ marginBottom: '1.5rem', padding: '1.5rem 2rem', background: 'var(--gradient-primary)', border: 'none', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', right: -20, top: -20, width: 140, height: 140, borderRadius: '50%', background: 'rgba(255,255,255,0.06)' }} />
                <div style={{ position: 'absolute', right: 60, bottom: -30, width: 100, height: 100, borderRadius: '50%', background: 'rgba(255,255,255,0.06)' }} />
                <div style={{ position: 'relative' }}>
                    <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', marginBottom: 6 }}>
                        {new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
                    </div>
                    <h2 style={{ color: 'white', fontSize: '1.5rem', marginBottom: 6 }}>
                        Bonjour, {name} 👋
                    </h2>
                    <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: 14, margin: 0 }}>
                        You have <strong style={{ color: 'white' }}>18 leave days</strong> remaining · <strong style={{ color: 'white' }}>2 training courses</strong> in progress
                    </p>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="stat-grid" style={{ marginBottom: '1.5rem' }}>
                {[
                    { label: 'Leave Balance', value: '18 Days', icon: CalendarDays, color: 'indigo', change: 'Expires Dec 31', dir: 'up' },
                    { label: 'Years of Service', value: '3.5 Yrs', icon: Award, color: 'amber', change: 'Bonus eligible', dir: 'up' },
                    { label: 'Training Score', value: '85%', icon: Target, color: 'cyan', change: '2 courses pending', dir: 'up' },
                    { label: 'Performance', value: 'A+', icon: Star, color: 'emerald', change: 'Top 10% this quarter', dir: 'up' },
                ].map(({ label, value, icon: Icon, color, change, dir }) => (
                    <div className="stat-card" key={label}>
                        <div className={`stat-icon ${color}`}><Icon size={22} /></div>
                        <div>
                            <div className="stat-value">{value}</div>
                            <div className="stat-label">{label}</div>
                            <div className={`stat-change ${dir}`}><Activity size={11} /> {change}</div>
                        </div>
                    </div>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                {/* Quick Actions */}
                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Zap size={16} color="#f59e0b" /> Quick Actions
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {[
                            { label: 'Request Leave', sub: 'Submit a new leave request instantly', icon: '🌴', link: '/leave', btn: 'New Request', color: 'btn-primary' },
                            { label: 'AI Chat Assistant', sub: 'Talk to your HR assistant about anything', icon: '💬', link: '/chatbot', btn: 'Open Chat', color: 'btn-secondary' },
                            { label: 'My Training', sub: 'Continue your learning programs', icon: '📚', link: '/chatbot', btn: 'Continue', color: 'btn-ghost' },
                        ].map(a => (
                            <div key={a.label} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                                <span style={{ fontSize: 22 }}>{a.icon}</span>
                                <div style={{ flex: 1, minWidth: 0 }}>
                                    <div style={{ fontSize: 13, fontWeight: 600 }}>{a.label}</div>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.sub}</div>
                                </div>
                                <button className={`btn ${a.color} btn-sm`} onClick={() => navigate(a.link)}>
                                    {a.btn}
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Upcoming Events + Training Progress */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    <div className="card">
                        <h3 style={{ marginBottom: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                            <CalendarDays size={16} color="#06b6d4" /> Upcoming Events
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {upcomingEvents.map(e => (
                                <div key={e.date} style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                                    <div style={{ textAlign: 'center', minWidth: 42, padding: '4px 8px', background: 'rgba(99,102,241,0.1)', borderRadius: 8, fontSize: 11, fontWeight: 700, color: 'var(--color-primary-light)' }}>
                                        {e.date}
                                    </div>
                                    <span style={{ fontSize: 13 }}>{e.label}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="card">
                        <h3 style={{ marginBottom: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                            <BookOpen size={16} color="#10b981" /> Training Progress
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {myProgress.map(p => (
                                <div key={p.label}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                                        <span style={{ fontWeight: 500 }}>{p.label}</span>
                                        <span style={{ color: p.color, fontWeight: 700 }}>{p.pct}%</span>
                                    </div>
                                    <div style={{ height: 5, background: 'var(--color-border)', borderRadius: 100 }}>
                                        <div style={{ height: '100%', width: `${p.pct}%`, background: p.color, borderRadius: 100, transition: 'width 1s ease' }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}

// ─── External / Candidate Dashboard ──────────────────────────────────────────
function ExternalDashboard({ navigate }) {
    const steps = [
        { num: '01', title: 'Upload Your CV', desc: 'AI automatically analyses, scores and extracts your key skills', icon: Upload, done: false, link: '/cv-analysis' },
        { num: '02', title: 'AI Matching', desc: 'Your profile is matched against our open positions in real time', icon: Brain, done: false, link: null },
        { num: '03', title: 'Get Shortlisted', desc: 'HR team reviews the AI ranking and contacts the top candidates', icon: UserCheck, done: false, link: null },
        { num: '04', title: 'Interview', desc: 'Schedule your interview — video, phone or on-site', icon: CalendarDays, done: false, link: '/chatbot' },
    ]

    return (
        <>
            {/* Hero Banner */}
            <div className="card" style={{ marginBottom: '2rem', padding: '3rem 2rem', textAlign: 'center', background: 'var(--gradient-primary)', border: 'none', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', left: -40, top: -40, width: 200, height: 200, borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
                <div style={{ position: 'absolute', right: -30, bottom: -40, width: 160, height: 160, borderRadius: '50%', background: 'rgba(255,255,255,0.05)' }} />
                <div style={{ position: 'relative' }}>
                    <div style={{ fontSize: 48, marginBottom: 12 }}>🚀</div>
                    <h2 style={{ fontSize: '2rem', color: 'white', marginBottom: 12 }}>Welcome to Segula Technologies</h2>
                    <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 15, maxWidth: 520, margin: '0 auto 2rem', lineHeight: 1.7 }}>
                        Our AI-powered recruitment platform matches your CV to the right engineering opportunities globally.
                    </p>
                    <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                        <button className="btn btn-sm" style={{ background: 'white', color: '#4f46e5', fontWeight: 700 }}
                            onClick={() => navigate('/cv-analysis')}>
                            <Upload size={16} /> Upload My CV
                        </button>
                        <button className="btn btn-ghost btn-sm" style={{ borderColor: 'rgba(255,255,255,0.4)', color: 'white' }}
                            onClick={() => navigate('/chatbot')}>
                            <MessageSquare size={16} /> Chat with HR Bot
                        </button>
                    </div>
                </div>
            </div>

            {/* Process Steps */}
            <div className="card" style={{ marginBottom: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <CheckCircle size={16} color="#10b981" /> How It Works
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                    {steps.map((s, i) => (
                        <div key={s.num} style={{ textAlign: 'center', padding: '1.25rem 1rem', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', cursor: s.link ? 'pointer' : 'default', position: 'relative' }}
                            onClick={() => s.link && navigate(s.link)}>
                            {i < steps.length - 1 && (
                                <div style={{ position: 'absolute', right: -16, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', zIndex: 1 }}>
                                    <ArrowRight size={14} />
                                </div>
                            )}
                            <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'rgba(99,102,241,0.1)', border: '2px solid rgba(99,102,241,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px', color: '#6366f1' }}>
                                <s.icon size={20} />
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700, marginBottom: 4 }}>STEP {s.num}</div>
                            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6 }}>{s.title}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>{s.desc}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Open Positions Preview */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Briefcase size={16} color="#f59e0b" /> Open Positions
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {[
                            { title: 'Senior Python Engineer', dept: 'Digital & IT', location: 'Paris, France', type: 'Full-time' },
                            { title: 'Project Manager', dept: 'Engineering', location: 'Lyon, France', type: 'Full-time' },
                            { title: 'DevOps Engineer', dept: 'Infrastructure', location: 'Remote', type: 'Contract' },
                        ].map(pos => (
                            <div key={pos.title} style={{ padding: '12px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
                                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{pos.title}</div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', gap: 10 }}>
                                    <span>{pos.dept}</span>
                                    <span>·</span>
                                    <span>{pos.location}</span>
                                    <span>·</span>
                                    <span style={{ color: pos.type === 'Full-time' ? '#10b981' : '#f59e0b' }}>{pos.type}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                    <button className="btn btn-ghost btn-sm" style={{ width: '100%', marginTop: 12 }} onClick={() => navigate('/jobs')}>
                        View All Positions <ArrowRight size={14} />
                    </button>
                </div>

                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <MessageSquare size={16} color="#06b6d4" /> Have Questions?
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: '1.25rem' }}>
                        {['What is the recruitment process?', 'How are CVs evaluated?', 'Do you offer remote jobs?'].map(q => (
                            <button key={q} className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start', textAlign: 'left', fontSize: 13 }}
                                onClick={() => navigate('/chatbot')}>
                                💬 {q}
                            </button>
                        ))}
                    </div>
                    <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => navigate('/chatbot')}>
                        <MessageSquare size={16} /> Open HR Chatbot
                    </button>
                </div>
            </div>
        </>
    )
}

// ─── Main Dashboard Component ─────────────────────────────────────────────────
export default function Dashboard({ user }) {
    const navigate = useNavigate()
    const role = user?.role || 'hr'

    const { data: stats, isLoading } = useQuery({
        queryKey: ['stats'],
        queryFn: hrApi.getStats,
        refetchInterval: 30000,
        enabled: role === 'hr',
    })

    const pageTitle = {
        hr: 'HR Intelligence Dashboard',
        employee: 'Employee Self-Service',
        external: 'Candidate Portal',
    }[role]

    const pageSubtitle = {
        hr: 'Real-time overview of your multi-agent recruitment platform',
        employee: 'Your personal workspace for leave, training, and career growth',
        external: 'Your AI-powered gateway to engineering careers at Segula',
    }[role]

    return (
        <div>
            <div className="page-header">
                <h1>{pageTitle}</h1>
                <p>{pageSubtitle}</p>
            </div>

            {role === 'hr' && <HRDashboard stats={stats} isLoading={isLoading} navigate={navigate} />}
            {role === 'employee' && <EmployeeDashboard user={user} navigate={navigate} />}
            {role === 'external' && <ExternalDashboard navigate={navigate} />}
        </div>
    )
}
