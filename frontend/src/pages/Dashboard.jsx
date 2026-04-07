import { useQuery } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import {
    Users, FileText, TrendingUp, CheckCircle, Clock,
    Cpu, Activity, Zap, Award, Briefcase, Brain, Target,
    CalendarDays, Banknote, MessageSquare
} from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts'

const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']

const agentStatuses = [
    { name: 'CV Agent', status: 'online', tasks: 12, color: '#6366f1' },
    { name: 'Interview Agent', status: 'online', tasks: 4, color: '#06b6d4' },
    { name: 'Onboarding Agent', status: 'online', tasks: 2, color: '#10b981' },
    { name: 'Training Agent', status: 'online', tasks: 7, color: '#f59e0b' },
    { name: 'Payroll Agent', status: 'online', tasks: 15, color: '#8b5cf6' },
    { name: 'Leave Agent', status: 'online', tasks: 9, color: '#ec4899' },
]

const mockScoreData = [
    { range: '90-100', count: 3 }, { range: '80-90', count: 8 },
    { range: '70-80', count: 15 }, { range: '60-70', count: 22 },
    { range: '50-60', count: 18 }, { range: '<50', count: 9 },
]

const mockStatusData = [
    { name: 'Pending', value: 45 }, { name: 'Shortlisted', value: 20 },
    { name: 'Interview', value: 12 }, { name: 'Hired', value: 8 }, { name: 'Rejected', value: 15 },
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

export default function Dashboard({ user }) {
    const { data: stats, isLoading } = useQuery({
        queryKey: ['stats'],
        queryFn: hrApi.getStats,
        refetchInterval: 30000,
        enabled: user?.role === 'hr',
    })

    const role = user?.role || 'hr'

    const renderHRDashboard = () => {
        const s = stats?.candidates || {}
        return (
            <>
                {/* Stat Cards */}
                <div className="stat-grid" style={{ marginBottom: '2rem' }}>
                    {[
                        { label: 'Total Candidates', value: isLoading ? '…' : s.total ?? 142, icon: Users, color: 'indigo', change: '+12 this week', dir: 'up' },
                        { label: 'CVs Processed', value: isLoading ? '…' : s.total ?? 135, icon: FileText, color: 'cyan', change: '+3 today', dir: 'up' },
                        { label: 'Open Positions', value: isLoading ? '…' : '12', icon: Briefcase, color: 'amber', change: '2 new', dir: 'up' },
                        { label: 'AI Analyses Completed', value: isLoading ? '…' : '158', icon: Brain, color: 'emerald', change: '+10 today', dir: 'up' },
                        { label: 'Hiring Success Rate', value: '88%', icon: Target, color: 'indigo', change: '+2% from last month', dir: 'up' },
                    ].map(({ label, value, icon: Icon, color, change, dir }) => (
                        <div className="stat-card" key={label}>
                            <div className={`stat-icon ${color}`}>
                                <Icon size={22} />
                            </div>
                            <div>
                                <div className="stat-value">{value}</div>
                                <div className="stat-label">{label}</div>
                                <div className={`stat-change ${dir}`}>
                                    <Activity size={11} /> {change}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Charts Row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                    {/* Score Distribution */}
                    <div className="card">
                        <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>CV Score Distribution</h3>
                        <ResponsiveContainer width="100%" height={220}>
                            <BarChart data={mockScoreData} barSize={28}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(99,102,241,0.08)" />
                                <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 11 }} />
                                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Bar dataKey="count" fill="url(#barGradient)" radius={[4, 4, 0, 0]} name="Candidates" />
                                <defs>
                                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="#6366f1" />
                                        <stop offset="100%" stopColor="#06b6d4" />
                                    </linearGradient>
                                </defs>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Status Breakdown */}
                    <div className="card">
                        <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem' }}>Candidate Pipeline</h3>
                        <ResponsiveContainer width="100%" height={220}>
                            <PieChart>
                                <Pie data={mockStatusData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                                    paddingAngle={3} dataKey="value">
                                    {mockStatusData.map((_, i) => (
                                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip content={<CustomTooltip />} />
                                <Legend iconType="circle" iconSize={10}
                                    formatter={(v) => <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{v}</span>} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Agent Status */}
                <div className="card">
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Cpu size={18} color="#6366f1" /> Agent Status Monitor
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                        {agentStatuses.map((agent) => (
                            <div key={agent.name} style={{
                                background: 'rgba(255,255,255,0.02)',
                                border: '1px solid rgba(99,102,241,0.1)',
                                borderRadius: 12,
                                padding: '1rem',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                            }}>
                                <div style={{
                                    width: 10, height: 10, borderRadius: '50%',
                                    background: '#10b981',
                                    boxShadow: '0 0 8px #10b981',
                                    flexShrink: 0,
                                }} />
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{agent.name}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{agent.tasks} tasks completed</div>
                                </div>
                                <div style={{
                                    marginLeft: 'auto',
                                    padding: '2px 8px',
                                    background: `${agent.color}20`,
                                    color: agent.color,
                                    borderRadius: 100,
                                    fontSize: 11,
                                    fontWeight: 700,
                                }}>
                                    ONLINE
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* AI Suggestions Panel */}
                <div className="card" style={{ marginTop: '2rem', background: 'var(--color-bg-glass)', borderColor: 'var(--color-border-hover)' }}>
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-primary)' }}>
                        <Brain size={18} color="var(--color-primary-light)" /> AI Suggestions
                    </h3>
                    <div style={{ background: 'var(--color-bg-primary)', padding: '1.5rem', borderRadius: 'var(--radius-md)', borderLeft: '4px solid var(--color-primary)', borderTop: '1px solid var(--color-border)', borderRight: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                            <div>
                                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Recommended candidate:</div>
                                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>John Smith</div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Match score:</div>
                                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--color-success)' }}>92%</div>
                            </div>
                        </div>
                        <div>
                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-primary-light)', marginBottom: 4 }}>Reason:</div>
                            <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                Strong Python + Docker experience. Candidate has 5 years Python experience, worked extensively on cloud systems, and matches 92% of the Senior Python Engineer job requirements. The CV shows strong evidence of system architecture and API design skills.
                            </p>
                        </div>
                        <div style={{ marginTop: '1.25rem', display: 'flex', gap: 12 }}>
                            <button className="btn btn-primary btn-sm">Review Profile</button>
                            <button className="btn btn-secondary btn-sm">Schedule Interview</button>
                        </div>
                    </div>
                </div>
            </>
        )
    }

    const renderEmployeeDashboard = () => {
        return (
            <>
                <div className="stat-grid" style={{ marginBottom: '2rem' }}>
                    {[
                        { label: 'Leave Balance', value: '18 Days', icon: CalendarDays, color: 'indigo', change: 'Expires in 3 months', dir: 'up' },
                        { label: 'Last Salary', value: '4,250 €', icon: Banknote, color: 'emerald', change: 'Paid on March 30', dir: 'up' },
                        { label: 'Years of Service', value: '3.5 Years', icon: Award, color: 'amber', change: 'Bonus eligible', dir: 'up' },
                        { label: 'Training Progress', value: '85%', icon: Target, color: 'cyan', change: '2 courses pending', dir: 'up' },
                    ].map(({ label, value, icon: Icon, color, change, dir }) => (
                        <div className="stat-card" key={label}>
                            <div className={`stat-icon ${color}`}>
                                <Icon size={22} />
                            </div>
                            <div>
                                <div className="stat-value">{value}</div>
                                <div className="stat-label">{label}</div>
                                <div className={`stat-change ${dir}`}>
                                    <Activity size={11} /> {change}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="card" style={{ background: 'var(--color-bg-glass)', borderColor: 'var(--color-border-hover)' }}>
                    <h3 style={{ marginBottom: '1.25rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-primary)' }}>
                        <Zap size={18} color="var(--color-accent-2)" /> Employee Quick AI Actions
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
                        <div style={{ background: 'var(--color-bg-primary)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                            <h4>Request Time Off</h4>
                            <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '8px 0 16px' }}>Let AI handle the paperwork and check your balance instantly.</p>
                            <button className="btn btn-primary btn-sm">New Request</button>
                        </div>
                        <div style={{ background: 'var(--color-bg-primary)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                            <h4>Career Feedback</h4>
                            <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '8px 0 16px' }}>Analyze your performance and get AI-driven career path suggestions.</p>
                            <button className="btn btn-secondary btn-sm">Get Feedback</button>
                        </div>
                    </div>
                </div>
            </>
        )
    }

    const renderExternalDashboard = () => {
        return (
            <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 2rem' }}>
                    <Users size={40} color="var(--color-primary)" />
                </div>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Welcome to Segula Technologies</h1>
                <p style={{ fontSize: '1.25rem', color: 'var(--text-muted)', maxWidth: 600, margin: '0 auto 3rem' }}>
                    Your portal to find the best career opportunities in global engineering.
                    Start by uploading your resume or chatting with our AI assistant.
                </p>
                <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
                    <button className="btn btn-primary btn-lg" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <FileText size={20} /> Upload My Resume
                    </button>
                    <button className="btn btn-secondary btn-lg" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <MessageSquare size={20} /> Chat with HR Bot
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div>
            <div className="page-header">
                <h1>{role === 'hr' ? 'HR Intelligence Home Page' : role === 'employee' ? 'Employee Self-Service' : 'Candidate Portal'}</h1>
                <p>
                    {role === 'hr' ? 'Real-time overview of your multi-agent HR platform' : 
                     role === 'employee' ? 'Manage your leave, payroll and career development' : 
                     'Build your career with our AI recruitment tools'}
                </p>
            </div>

            {role === 'hr' && renderHRDashboard()}
            {role === 'employee' && renderEmployeeDashboard()}
            {role === 'external' && renderExternalDashboard()}
        </div>
    )
}
