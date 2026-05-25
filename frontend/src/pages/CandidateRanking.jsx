import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import { DEFAULT_JOBS } from '../data/defaultJobs.js'
import {
    TrendingUp, Briefcase, Award, RefreshCw, Github,
    Linkedin, Phone, Mail, AlertTriangle, ShieldCheck, Star
} from 'lucide-react'
import toast from 'react-hot-toast'

function RankBadge({ rank }) {
    if (rank === 1) return <span style={{ fontSize: 20 }}>🥇</span>
    if (rank === 2) return <span style={{ fontSize: 20 }}>🥈</span>
    if (rank === 3) return <span style={{ fontSize: 20 }}>🥉</span>
    return <span style={{ fontWeight: 800, color: 'var(--text-muted)', fontSize: 14 }}>#{rank}</span>
}

function ScoreBar({ score, color = 'var(--gradient-primary)' }) {
    return (
        <div className="score-bar-wrapper">
            <div className="score-bar" style={{ flex: 1 }}>
                <div className="score-bar-fill" style={{ width: `${score}%`, background: color }} />
            </div>
            <span className="score-text">{Math.round(score)}%</span>
        </div>
    )
}

function StatusBadge({ status }) {
    const map = {
        pending: 'badge-gray',
        reviewed: 'badge-cyan',
        shortlisted: 'badge-green',
        interview_scheduled: 'badge-yellow',
        hired: 'badge-indigo',
        rejected: 'badge-red',
    }
    return <span className={`badge ${map[status] || 'badge-gray'}`}>{status?.replace('_', ' ')}</span>
}

// ── Mini score pill ────────────────────────────────────────────────────────────
function ScorePill({ label, value, color }) {
    return (
        <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            gap: 2, minWidth: 52,
        }}>
            <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: `conic-gradient(${color} ${value * 3.6}deg, var(--color-border) 0deg)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                position: 'relative',
            }}>
                <div style={{
                    width: 26, height: 26, borderRadius: '50%',
                    background: 'var(--color-bg-card)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 9, fontWeight: 700, color,
                }}>
                    {Math.round(value)}
                </div>
            </div>
            <span style={{ fontSize: 9, color: 'var(--text-muted)', fontWeight: 600, textAlign: 'center', lineHeight: 1.2 }}>{label}</span>
        </div>
    )
}

// ── Global quality table row ──────────────────────────────────────────────────
function GlobalRow({ c, navigate }) {
    const score = c.total_score
    const color = score >= 75 ? '#10b981' : score >= 50 ? '#f59e0b' : score >= 30 ? '#6366f1' : '#ef4444'
    const bd = c.score_breakdown || {}

    return (
        <tr onClick={() => navigate(`/candidates/${c.candidate_id}`)} style={{ cursor: 'pointer' }}>
            <td><RankBadge rank={c.rank} /></td>
            <td>
                <div style={{ fontWeight: 600 }}>{c.full_name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', gap: 6, marginTop: 2, flexWrap: 'wrap' }}>
                    {c.email && <span style={{ display: 'flex', alignItems: 'center', gap: 2 }}><Mail size={10} />{c.email}</span>}
                    {c.phone && <span style={{ display: 'flex', alignItems: 'center', gap: 2 }}><Phone size={10} />{c.phone}</span>}
                    {c.has_github && <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: 2 }}><Github size={10} />GitHub</span>}
                    {c.has_linkedin && <span style={{ color: '#0077b5', display: 'flex', alignItems: 'center', gap: 2 }}><Linkedin size={10} />LinkedIn</span>}
                </div>
            </td>
            <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="score-bar" style={{ width: 80 }}>
                        <div className="score-bar-fill" style={{ width: `${score}%`, background: color }} />
                    </div>
                    <span style={{ fontWeight: 700, color, minWidth: 32 }}>{Math.round(score)}%</span>
                </div>
            </td>
            <td>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {(c.top_skills || []).slice(0, 4).map(s => (
                        <span key={s} className="badge badge-indigo" style={{ fontSize: 10 }}>{s}</span>
                    ))}
                </div>
            </td>
            <td>
                {/* Mini breakdown circles */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {bd.skills      != null && <ScorePill label="Skills"   value={bd.skills}      color="#6366f1" />}
                    {bd.experience  != null && <ScorePill label="Exp"      value={bd.experience}  color="#f59e0b" />}
                    {bd.education   != null && <ScorePill label="Edu"      value={bd.education}   color="#10b981" />}
                    {bd.github      != null && <ScorePill label="GitHub"   value={bd.github}      color="#ec4899" />}
                    {bd.certifications != null && <ScorePill label="Certs" value={bd.certifications} color="#06b6d4" />}
                </div>
            </td>
            <td>
                {c.alerts && c.alerts.length > 0 ? (
                    <div title={c.alerts.map(a => a.msg).join('\n')}
                        style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#f59e0b', fontSize: 11, fontWeight: 600 }}>
                        <AlertTriangle size={13} />
                        {c.alerts.length} alert{c.alerts.length > 1 ? 's' : ''}
                    </div>
                ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#10b981', fontSize: 11 }}>
                        <ShieldCheck size={13} /> OK
                    </div>
                )}
            </td>
            <td><StatusBadge status={c.status} /></td>
        </tr>
    )
}

export default function CandidateRanking() {
    const location = useLocation()
    const navigate = useNavigate()
    const queryParams = new URLSearchParams(location.search)
    const [selectedJobId, setSelectedJobId] = useState(queryParams.get('job') || '')
    const [rankingData, setRankingData] = useState(null)
    const [globalData, setGlobalData] = useState(null)
    const [isRanking, setIsRanking] = useState(false)
    const [isLoadingGlobal, setIsLoadingGlobal] = useState(false)

    // Fetch jobs to populate the dropdown, fall back to DEFAULT_JOBS
    const { data: jobsData } = useQuery({
        queryKey: ['jobs'],
        queryFn: () => hrApi.getJobs(),
    })
    const dbJobs = jobsData?.jobs || []
    const dbTitles = new Set(dbJobs.map(j => j.title.toLowerCase()))
    const extraJobs = DEFAULT_JOBS.filter(j => !dbTitles.has(j.title.toLowerCase()))
    const jobs = dbJobs.length > 0 ? [...dbJobs, ...extraJobs] : DEFAULT_JOBS

    // Load global quality ranking when no job is selected
    useEffect(() => {
        if (selectedJobId) return
        setIsLoadingGlobal(true)
        hrApi.qualityRanking(200)
            .then(data => setGlobalData(data))
            .catch(() => setGlobalData({ candidates: [] }))
            .finally(() => setIsLoadingGlobal(false))
    }, [selectedJobId])

    // Auto-rank all candidates when job is selected
    useEffect(() => {
        if (!selectedJobId) { setRankingData(null); return }
        setIsRanking(true)
        hrApi.rankAllForJob(selectedJobId)
            .then(data => setRankingData(data))
            .catch(() => { toast.error('Ranking failed — check backend'); setRankingData({ candidates: [] }) })
            .finally(() => setIsRanking(false))
    }, [selectedJobId])

    const handleRefresh = () => {
        if (selectedJobId) {
            setIsRanking(true)
            hrApi.rankAllForJob(selectedJobId)
                .then(data => setRankingData(data))
                .catch(() => toast.error('Refresh failed'))
                .finally(() => setIsRanking(false))
        } else {
            setIsLoadingGlobal(true)
            hrApi.qualityRanking(200)
                .then(data => setGlobalData(data))
                .catch(() => {})
                .finally(() => setIsLoadingGlobal(false))
        }
    }

    const loading      = selectedJobId ? isRanking : isLoadingGlobal
    const candidates   = selectedJobId ? (rankingData?.candidates || []) : (globalData?.candidates || [])
    const isGlobalMode = !selectedJobId

    return (
        <div>
            <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div>
                    <h1>Candidate Ranking</h1>
                    <p>
                        {isGlobalMode
                            ? 'Global CV quality score based on contact, skills, experience, education, GitHub and certifications.'
                            : 'Ranking all candidates by skill-match score for the selected job offer.'}
                    </p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={handleRefresh} disabled={loading}>
                    <RefreshCw size={14} className={loading ? 'spinning' : ''} />
                    Refresh
                </button>
            </div>

            {/* ── Job offer selector ─────────────────────────────────────────── */}
            <div className="card" style={{ marginBottom: '2rem' }}>
                <label className="form-label" style={{ fontWeight: 600, marginBottom: '0.5rem', display: 'block' }}>
                    🎯 Evaluate against a Job Offer <span style={{ fontWeight: 400, color: 'var(--text-muted)', fontSize: 12 }}>(optional — leave blank for global ranking)</span>
                </label>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <select
                        className="form-input"
                        style={{ flex: 1 }}
                        value={selectedJobId}
                        onChange={(e) => setSelectedJobId(e.target.value)}
                    >
                        <option value="">— Global CV Quality Ranking (all criteria) —</option>
                        {jobs.map(job => (
                            <option key={job.id || job._id} value={job.id || job._id}>
                                {job.title}
                            </option>
                        ))}
                    </select>
                    {selectedJobId && (
                        <button className="btn btn-ghost" style={{ fontSize: 12 }} onClick={() => setSelectedJobId('')}>
                            ✕ Clear filter
                        </button>
                    )}
                </div>
                {isGlobalMode && (
                    <div style={{ marginTop: '0.75rem', display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-muted)', flexWrap: 'wrap' }}>
                        <span>📊 <b>20%</b> Skills breadth</span>
                        <span>📈 <b>25%</b> Experience quality</span>
                        <span>🎓 <b>20%</b> Education</span>
                        <span>🏅 <b>10%</b> Certifications</span>
                        <span>⚙️ <b>10%</b> GitHub / Portfolio</span>
                        <span>📞 <b>10%</b> Contact completeness</span>
                        <span>💬 <b>5%</b> Communication</span>
                    </div>
                )}
            </div>

            {/* ── Loading ────────────────────────────────────────────────────── */}
            {loading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4rem', gap: 16 }}>
                    <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
                    <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
                        {isGlobalMode ? 'Computing global quality scores…' : 'Ranking all candidates for this offer…'}
                    </p>
                </div>

            ) : candidates.length === 0 ? (
                <div className="empty-state card">
                    <div className="empty-icon"><TrendingUp size={32} color="#6366f1" /></div>
                    <h3>No candidates yet</h3>
                    <p>Upload CVs via the <a href="/cv-analysis" style={{ color: 'var(--color-primary-light)' }}>CV Analysis</a> page to see rankings here.</p>
                </div>

            ) : (
                <>
                    {/* ── Top 3 podium ──────────────────────────────────────── */}
                    {candidates.length >= 3 && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                            {candidates.slice(0, 3).map((c, i) => {
                                const bd = c.score_breakdown || {}
                                return (
                                    <div className="card" key={c.candidate_id} style={{
                                        borderColor: i === 0 ? 'rgba(245,158,11,0.4)' : 'var(--color-border)',
                                        background:  i === 0 ? 'rgba(245,158,11,0.08)' : 'var(--color-bg-card)',
                                        cursor: 'pointer',
                                    }} onClick={() => navigate(`/candidates/${c.candidate_id}`)}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                                            <RankBadge rank={i + 1} />
                                            <StatusBadge status={c.status} />
                                        </div>
                                        <h3 style={{ fontSize: '1rem', marginBottom: 2 }}>{c.full_name}</h3>
                                        <p style={{ fontSize: 11, marginBottom: '0.75rem', color: 'var(--text-muted)' }}>{c.email}</p>
                                        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                                            <Award size={14} color="#6366f1" />
                                            {isGlobalMode ? 'Quality Score' : 'Match Score'}
                                        </div>
                                        <ScoreBar score={c.total_score} />
                                        {isGlobalMode && (
                                            <div style={{ display: 'flex', gap: 6, marginTop: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                                                {bd.skills     != null && <ScorePill label="Skills"  value={bd.skills}     color="#6366f1" />}
                                                {bd.experience != null && <ScorePill label="Exp"     value={bd.experience} color="#f59e0b" />}
                                                {bd.education  != null && <ScorePill label="Edu"     value={bd.education}  color="#10b981" />}
                                                {bd.github     != null && <ScorePill label="GitHub"  value={bd.github}     color="#ec4899" />}
                                            </div>
                                        )}
                                        <div style={{ display: 'flex', gap: 5, marginTop: '0.5rem', flexWrap: 'wrap' }}>
                                            {c.top_skills?.slice(0, 3).map(s => (
                                                <span key={s} className="badge badge-indigo" style={{ fontSize: 10 }}>{s}</span>
                                            ))}
                                        </div>
                                        {c.alerts?.length > 0 && (
                                            <div style={{ marginTop: '0.5rem', fontSize: 11, color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 4 }}>
                                                <AlertTriangle size={12} /> {c.alerts.length} alert{c.alerts.length > 1 ? 's' : ''}
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    )}

                    {/* ── Full table ────────────────────────────────────────── */}
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Candidate</th>
                                    <th>{isGlobalMode ? 'Quality Score' : 'Match Score'}</th>
                                    <th>Skills</th>
                                    {isGlobalMode
                                        ? <th>Score Breakdown</th>
                                        : <th>Skills Match</th>}
                                    {isGlobalMode && <th>Alerts</th>}
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {isGlobalMode
                                    ? candidates.map(c => <GlobalRow key={c.candidate_id} c={c} navigate={navigate} />)
                                    : candidates.map(c => (
                                        <tr key={c.candidate_id} onClick={() => navigate(`/candidates/${c.candidate_id}`)} style={{ cursor: 'pointer' }}>
                                            <td><RankBadge rank={c.rank} /></td>
                                            <td>
                                                <div style={{ fontWeight: 600 }}>{c.full_name}</div>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{c.email}</div>
                                            </td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                    <div className="score-bar" style={{ width: 80 }}>
                                                        <div className="score-bar-fill" style={{ width: `${c.total_score}%`, background: 'var(--gradient-primary)' }} />
                                                    </div>
                                                    <span style={{ fontWeight: 700, color: 'var(--color-primary-light)' }}>
                                                        {Math.round(c.total_score)}%
                                                    </span>
                                                </div>
                                            </td>
                                            <td>
                                                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', maxWidth: 200 }}>
                                                    {c.top_skills?.slice(0, 4).map(s => (
                                                        <span key={s} className="badge badge-indigo" style={{ fontSize: 10 }}>{s}</span>
                                                    ))}
                                                </div>
                                            </td>
                                            <td>
                                                <span style={{ fontWeight: 600 }}>
                                                    {c.skills_score ? `${Math.round(c.skills_score)}%` : '–'}
                                                </span>
                                            </td>
                                            <td><StatusBadge status={c.status} /></td>
                                        </tr>
                                    ))
                                }
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    )
}
