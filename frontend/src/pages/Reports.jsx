import { useState, useEffect } from 'react'
import { hrApi } from '../services/api.js'
import {
    BarChart2, Users, TrendingUp, Award, Download, RefreshCw,
    GitBranch, Star, Briefcase, GraduationCap, Phone, CheckCircle,
    AlertTriangle, FileText, Code
} from 'lucide-react'

// ── Helpers ───────────────────────────────────────────────────────────────────
function kpiColor(value, thresholds = [60, 80]) {
    if (value >= thresholds[1]) return '#10b981'
    if (value >= thresholds[0]) return '#f59e0b'
    return '#ef4444'
}

// ── KPI Card ──────────────────────────────────────────────────────────────────
function KPICard({ icon: Icon, label, value, sub, color = '#6366f1' }) {
    return (
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
                width: 52, height: 52, borderRadius: 'var(--radius-md)',
                background: `${color}20`, display: 'flex', alignItems: 'center',
                justifyContent: 'center', color, flexShrink: 0
            }}>
                <Icon size={22} />
            </div>
            <div>
                <div style={{ fontSize: 24, fontWeight: 800, color }}>{value}</div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
                {sub && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{sub}</div>}
            </div>
        </div>
    )
}

// ── Horizontal Bar ────────────────────────────────────────────────────────────
function HBar({ label, value, max, color = '#6366f1', suffix = '' }) {
    const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <div style={{ width: 130, fontSize: 12, color: 'var(--text-secondary)', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</div>
            <div style={{ flex: 1, height: 10, background: 'var(--color-surface)', borderRadius: 99, overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 99, transition: 'width 0.7s ease' }} />
            </div>
            <div style={{ width: 36, fontSize: 12, fontWeight: 700, color }}>{value}{suffix}</div>
        </div>
    )
}

// ── Score distribution histogram ──────────────────────────────────────────────
function ScoreHistogram({ candidates }) {
    const buckets = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
    const counts = buckets.map(b => candidates.filter(c => {
        const s = c.total_score ?? c.score?.total_score ?? 0
        return s >= b && s < b + 10
    }).length)
    const maxCount = Math.max(...counts, 1)

    const bucketColors = [
        '#ef4444','#ef4444','#f97316','#f97316','#f59e0b',
        '#eab308','#84cc16','#22c55e','#10b981','#10b981'
    ]

    return (
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 120, padding: '0 4px' }}>
            {buckets.map((b, i) => (
                <div key={b} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: bucketColors[i] }}>{counts[i] || ''}</div>
                    <div style={{
                        width: '100%', borderRadius: '4px 4px 0 0',
                        background: bucketColors[i],
                        height: `${(counts[i] / maxCount) * 90}px`,
                        minHeight: counts[i] > 0 ? 4 : 0,
                        transition: 'height 0.7s ease',
                        opacity: 0.85
                    }} />
                    <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{b}-{b + 10}</div>
                </div>
            ))}
        </div>
    )
}

export default function Reports() {
    const [candidates, setCandidates] = useState([])
    const [qualityData, setQualityData] = useState(null)
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)

    const loadData = () => {
        setLoading(true)
        Promise.all([
            hrApi.getStats(),
            hrApi.qualityRanking(500),
            hrApi.getCandidates(500),
        ]).then(([s, q, c]) => {
            setStats(s)
            setQualityData(q)
            setCandidates(q?.candidates || c?.candidates || [])
        }).catch(console.error)
          .finally(() => setLoading(false))
    }

    useEffect(() => { loadData() }, [])

    // ── Derived stats ──────────────────────────────────────────────────────────
    const total         = candidates.length
    const avgScore      = total > 0 ? candidates.reduce((s, c) => s + (c.total_score ?? 0), 0) / total : 0
    const withGitHub    = candidates.filter(c => c.has_github).length
    const withLinkedIn  = candidates.filter(c => c.has_linkedin).length
    const withPhone     = candidates.filter(c => c.phone).length
    const withCerts     = candidates.filter(c => (c.certifications_count ?? 0) > 0).length
    const alertCount    = candidates.reduce((n, c) => n + (c.alerts?.length ?? 0), 0)

    // Top skills frequency
    const skillFreq = {}
    candidates.forEach(c => (c.top_skills || []).forEach(s => {
        skillFreq[s] = (skillFreq[s] || 0) + 1
    }))
    const topSkills = Object.entries(skillFreq)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15)

    // Score breakdown averages
    const avgBreakdown = {}
    const dims = ['skills', 'experience', 'education', 'github', 'certifications', 'contact', 'communication']
    dims.forEach(d => {
        const vals = candidates.map(c => c.score_breakdown?.[d] ?? 0)
        avgBreakdown[d] = vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : 0
    })

    // Top candidates
    const top5 = [...candidates].sort((a, b) => b.total_score - a.total_score).slice(0, 5)

    // Status distribution
    const statusMap = {}
    candidates.forEach(c => {
        const s = c.status || 'pending'
        statusMap[s] = (statusMap[s] || 0) + 1
    })

    // ── Export ─────────────────────────────────────────────────────────────────
    const exportJSON = () => {
        const data = JSON.stringify({ generated_at: new Date().toISOString(), total, candidates }, null, 2)
        const blob = new Blob([data], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a'); a.href = url
        a.download = `candidates_report_${Date.now()}.json`
        a.click(); URL.revokeObjectURL(url)
    }

    const exportCSV = () => {
        const headers = ['Rank','Name','Email','Phone','Score','Skills','Experience_yrs','Status','GitHub','LinkedIn','Certs','Alerts']
        const rows = candidates.map(c => [
            c.rank, c.full_name, c.email || '', c.phone || '',
            c.total_score, (c.top_skills||[]).join('; '),
            c.years_experience || 0, c.status || '',
            c.has_github ? 'Yes':'No', c.has_linkedin ? 'Yes':'No',
            c.certifications_count || 0, (c.alerts||[]).map(a=>a.msg).join('; ')
        ])
        const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(',')).join('\n')
        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a'); a.href = url
        a.download = `candidates_report_${Date.now()}.csv`
        a.click(); URL.revokeObjectURL(url)
    }

    if (loading) return (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '6rem' }}>
            <div className="spinner" style={{ width: 48, height: 48, borderWidth: 4 }} />
        </div>
    )

    return (
        <div>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>Analytics & Reports</h1>
                    <p>Candidate pipeline insights, quality distribution and export tools</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-secondary btn-sm" onClick={loadData}>
                        <RefreshCw size={14} /> Refresh
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={exportCSV}>
                        <Download size={14} /> CSV
                    </button>
                    <button className="btn btn-primary btn-sm" onClick={exportJSON}>
                        <Download size={14} /> JSON
                    </button>
                </div>
            </div>

            {/* ── KPI Row ──────────────────────────────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                <KPICard icon={Users}     label="Total Candidates"    value={total}               color="#6366f1" />
                <KPICard icon={Award}     label="Avg Quality Score"   value={`${Math.round(avgScore)}%`} sub="Global CV rating" color={kpiColor(avgScore)} />
                <KPICard icon={GitBranch} label="With GitHub"         value={withGitHub}           sub={`${total > 0 ? Math.round(withGitHub/total*100) : 0}% of candidates`} color="#ec4899" />
                <KPICard icon={Phone}     label="Phone on File"       value={withPhone}            sub={`${total > 0 ? Math.round(withPhone/total*100) : 0}% of candidates`} color="#10b981" />
                <KPICard icon={Star}      label="With Certifications" value={withCerts}            sub={`${total > 0 ? Math.round(withCerts/total*100) : 0}% of candidates`} color="#f59e0b" />
                <KPICard icon={AlertTriangle} label="Total Alerts"    value={alertCount}           sub="Anomalies detected" color={alertCount > 0 ? '#ef4444' : '#10b981'} />
            </div>

            {/* ── Row 2: Histogram + Breakdown ─────────────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                {/* Score distribution */}
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <BarChart2 size={16} color="#6366f1" /> Score Distribution
                    </h3>
                    {total > 0
                        ? <ScoreHistogram candidates={candidates} />
                        : <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No data yet</p>}
                    <div style={{ display: 'flex', gap: 12, marginTop: '1rem', fontSize: 11, color: 'var(--text-muted)', justifyContent: 'center' }}>
                        <span style={{ color: '#ef4444' }}>■</span> Low ({'<'}40)
                        <span style={{ color: '#f59e0b' }}>■</span> Medium (40-70)
                        <span style={{ color: '#10b981' }}>■</span> High ({'>'}70)
                    </div>
                </div>

                {/* Avg breakdown by dimension */}
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <TrendingUp size={16} color="#6366f1" /> Average Score by Dimension
                    </h3>
                    <HBar label="Skills Breadth"    value={Math.round(avgBreakdown.skills)}        max={100} color="#6366f1" suffix="%" />
                    <HBar label="Experience"        value={Math.round(avgBreakdown.experience)}    max={100} color="#f59e0b" suffix="%" />
                    <HBar label="Education"         value={Math.round(avgBreakdown.education)}     max={100} color="#10b981" suffix="%" />
                    <HBar label="Certifications"    value={Math.round(avgBreakdown.certifications)}max={100} color="#06b6d4" suffix="%" />
                    <HBar label="GitHub"            value={Math.round(avgBreakdown.github)}        max={100} color="#ec4899" suffix="%" />
                    <HBar label="Contact Complete"  value={Math.round(avgBreakdown.contact)}       max={100} color="#8b5cf6" suffix="%" />
                    <HBar label="Communication"     value={Math.round(avgBreakdown.communication)} max={100} color="#f97316" suffix="%" />
                </div>
            </div>

            {/* ── Row 3: Top skills + Status + Top 5 ───────────────────────── */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 180px 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                {/* Top skills */}
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Code size={16} color="#6366f1" /> Top Skills Across All CVs
                    </h3>
                    {topSkills.length === 0
                        ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No data yet</p>
                        : topSkills.map(([skill, count]) => (
                            <HBar key={skill} label={skill} value={count} max={topSkills[0][1]} color="#6366f1" />
                        ))}
                </div>

                {/* Pipeline status */}
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: '1.25rem' }}>Pipeline</h3>
                    {Object.entries(statusMap).length === 0
                        ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No data</p>
                        : Object.entries(statusMap).map(([status, count]) => {
                            const colors = {
                                pending: '#6b7280', reviewed: '#06b6d4', shortlisted: '#10b981',
                                interview_scheduled: '#f59e0b', hired: '#6366f1', rejected: '#ef4444'
                            }
                            const color = colors[status] || '#6b7280'
                            return (
                                <div key={status} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                                    <span style={{ fontSize: 12, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                                        {status.replace('_', ' ')}
                                    </span>
                                    <span style={{ fontWeight: 700, fontSize: 14, color }}>{count}</span>
                                </div>
                            )
                        })}
                </div>

                {/* Top 5 candidates */}
                <div className="card">
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Award size={16} color="#f59e0b" /> Top 5 Candidates
                    </h3>
                    {top5.length === 0
                        ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No data yet</p>
                        : top5.map((c, i) => {
                            const color = kpiColor(c.total_score)
                            return (
                                <div key={c.candidate_id} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                                    <span style={{ fontSize: 16 }}>{['🥇','🥈','🥉','4️⃣','5️⃣'][i]}</span>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontWeight: 600, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.full_name}</div>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(c.top_skills||[]).slice(0,3).join(', ')}</div>
                                    </div>
                                    <span style={{ fontWeight: 800, color, fontSize: 14, minWidth: 36, textAlign: 'right' }}>{Math.round(c.total_score)}%</span>
                                </div>
                            )
                        })}
                </div>
            </div>

            {/* ── Alert summary ─────────────────────────────────────────────── */}
            {alertCount > 0 && (
                <div className="card" style={{ borderLeft: '4px solid #f59e0b', background: 'rgba(245,158,11,0.04)' }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: '1rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <AlertTriangle size={16} /> Detected Anomalies
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 8 }}>
                        {candidates.filter(c => c.alerts?.length > 0).map(c => (
                            <div key={c.candidate_id} style={{ padding: '8px 12px', background: 'var(--color-surface)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.2)' }}>
                                <div style={{ fontWeight: 600, fontSize: 13 }}>{c.full_name}</div>
                                {c.alerts.map((a, i) => (
                                    <div key={i} style={{ fontSize: 11, color: '#f59e0b', marginTop: 2 }}>⚠ {a.msg}</div>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
