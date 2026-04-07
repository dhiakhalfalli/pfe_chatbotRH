import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import { TrendingUp, Star, Briefcase, Code, Award, RefreshCw, X, Mail, Phone, MapPin, User, FileText, BarChart2, MessageSquare, BrainCircuit, Clock } from 'lucide-react'
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

const TABS = ['Profile', 'CV Analysis', 'Interview Notes', 'AI Recommendation']

function CandidateProfile({ candidate: summaryCandidate, onClose }) {
    const [activeTab, setActiveTab] = useState('Profile')
    const [notes, setNotes] = useState('')

    const { data: candidate, isLoading } = useQuery({
        queryKey: ['candidate', summaryCandidate?.candidate_id],
        queryFn: () => hrApi.getCandidate(summaryCandidate.candidate_id),
        enabled: !!summaryCandidate?.candidate_id
    })

    useEffect(() => {
        if (candidate?.notes) {
            setNotes(candidate.notes)
        } else if (candidate) {
            setNotes('')
        }
    }, [candidate])

    const saveNotes = () => {
        if (!candidate?.id) return
        hrApi.updateCandidate(candidate.id, { notes }).then(() => {
            toast.success('Notes saved')
        })
    }

    if (!summaryCandidate) return null

    return (
        <div style={{ position: 'fixed', inset: 0, background: 'var(--color-overlay)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '2rem' }}>
            <div className="card" style={{ width: '100%', maxWidth: 900, maxHeight: '90vh', display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--color-surface)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
                            <User size={32} />
                        </div>
                        <div>
                            <h2 style={{ fontSize: '1.5rem', marginBottom: 4 }}>{(candidate || summaryCandidate).full_name}</h2>
                            <div style={{ display: 'flex', gap: 12, fontSize: 13, color: 'var(--text-muted)' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Mail size={14} /> {(candidate || summaryCandidate).email || 'No email provided'}</span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}><Briefcase size={14} /> {(candidate || summaryCandidate).job_title_applied || 'General Position'}</span>
                            </div>
                        </div>
                    </div>
                    <div>
                        <button onClick={onClose} className="btn btn-ghost" style={{ padding: '8px' }}><X size={20} /></button>
                    </div>
                </div>

                <div style={{ display: 'flex', borderBottom: '1px solid var(--color-border)', padding: '0 1.5rem', background: 'var(--color-bg-card)' }}>
                    {TABS.map(t => (
                        <button
                            key={t}
                            onClick={() => setActiveTab(t)}
                            style={{
                                padding: '1rem', background: 'none', border: 'none', fontSize: 14, fontWeight: 600, cursor: 'pointer',
                                color: activeTab === t ? 'var(--color-primary-light)' : 'var(--text-muted)',
                                borderBottom: `2px solid ${activeTab === t ? 'var(--color-primary-light)' : 'transparent'}`,
                                transition: 'all 0.2s'
                            }}
                        >
                            {t}
                        </button>
                    ))}
                </div>

                <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
                    {isLoading || !candidate ? (
                        <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}><div className="spinner" /></div>
                    ) : (
                        <>
                            {activeTab === 'Profile' && (
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                                    <div>
                                        <h3 style={{ fontSize: 16, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}><FileText size={18} color="var(--color-primary-light)" /> Summary</h3>
                                        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{candidate.summary || `Candidate with ${candidate.years_experience || 0}+ years of experience. Demonstrated solid skills corresponding to a score of ${candidate.score?.total_score || 0}%.`}</p>

                                        <h3 style={{ fontSize: 16, marginTop: '2rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}><Briefcase size={18} color="var(--color-primary-light)" /> Experience</h3>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                            {(candidate.experience || []).slice(0, 3).map((exp, i) => (
                                                <div className="card" key={i} style={{ padding: '1rem' }}>
                                                    <div style={{ fontWeight: 600 }}>{exp.title || exp.role}</div>
                                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{exp.company} • {exp.period}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    <div>
                                        <h3 style={{ fontSize: 16, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}><Award size={18} color="var(--color-primary-light)" /> Key Metrics</h3>
                                        <div className="card" style={{ padding: '1.5rem', marginBottom: '1rem', background: 'var(--color-bg-primary)' }}>
                                            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 8 }}>Overall AI Score</div>
                                            <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 12 }}>
                                                {Math.round(candidate.score?.total_score || 0)}%
                                                <span className={`badge ${candidate.score?.total_score > 80 ? 'badge-green' : 'badge-gray'}`} style={{ fontSize: 12 }}>
                                                    {candidate.score?.total_score > 80 ? 'Excellent Fit' : 'Qualified'}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="card" style={{ padding: '1.5rem' }}>
                                            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: '1rem' }}>Top Skills</div>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                                {(candidate.skills || []).slice(0, 10).map(s => <span key={typeof s === 'string' ? s : s.name} className="badge badge-indigo">{typeof s === 'string' ? s : s.name}</span>)}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            {activeTab === 'CV Analysis' && (
                                <div>
                                    <h3 style={{ fontSize: 16, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: 8 }}><BarChart2 size={18} color="var(--color-cyan)" /> Match Visualization</h3>
                                    <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
                                        {[
                                            { label: 'Skills Match', val: candidate.score?.skills_score },
                                            { label: 'Cloud & DevOps', val: candidate.score?.github_score },
                                            { label: 'Experience Depth', val: candidate.score?.experience_score },
                                            { label: 'Education Alignment', val: candidate.score?.education_score },
                                            { label: 'Communication', val: candidate.score?.communication_score },
                                        ].map((item, i) => (
                                            <div key={i} style={{ marginBottom: 12 }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4, fontWeight: 600 }}>
                                                    <span>{item.label}</span>
                                                    <span style={{ color: 'var(--color-primary-light)' }}>{Math.round(item.val || 0)}%</span>
                                                </div>
                                                <ScoreBar score={item.val || 0} color={item.val > 80 ? 'var(--color-success)' : 'var(--gradient-primary)'} />
                                            </div>
                                        ))}
                                    </div>

                                    <h3 style={{ fontSize: 16, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: 8 }}><Clock size={18} color="var(--color-amber)" /> Experience Timeline</h3>
                                    <div style={{ paddingLeft: 16, borderLeft: '2px solid var(--color-border)', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                        {(candidate.experience || []).map((exp, i) => (
                                            <div key={i} style={{ position: 'relative' }}>
                                                <div style={{ position: 'absolute', left: -21, top: 4, width: 10, height: 10, borderRadius: '50%', background: i === 0 ? 'var(--color-amber)' : 'var(--color-primary)' }} />
                                                <div style={{ fontWeight: 600 }}>{exp.title || exp.role} @ {exp.company}</div>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{exp.period}</div>
                                                <p style={{ fontSize: 13, marginTop: 4, opacity: 0.8 }}>{exp.description?.slice(0, 150)}{exp.description?.length > 150 ? '...' : ''}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {activeTab === 'Interview Notes' && (
                                <div>
                                    <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}><MessageSquare size={16} /> HR Feedback & Notes</h4>
                                    <textarea
                                        className="form-textarea"
                                        placeholder="Add thoughts about the candidate, technical assessment, or cultural fit..."
                                        style={{ width: '100%', minHeight: 200, background: 'var(--color-bg-primary)', color: 'var(--text-primary)' }}
                                        value={notes}
                                        onChange={e => setNotes(e.target.value)}
                                    />
                                    <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                                        <button className="btn btn-primary" onClick={saveNotes}>Save Candidate Notes</button>
                                    </div>
                                </div>
                            )}
                            {activeTab === 'AI Recommendation' && (
                                <div>
                                    <div className="card" style={{ padding: '1.5rem', background: 'var(--color-bg-glass)', borderColor: 'var(--color-border-hover)' }}>
                                        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, color: 'var(--text-primary)' }}>
                                            <BrainCircuit size={24} color="var(--color-primary-light)" /> AI Insights
                                        </h3>
                                        <p style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--text-primary)' }}>
                                            {candidate.full_name} has {candidate.years_experience || 0} years of experience.
                                            The AI analysis suggests a {candidate.score?.total_score}% match for the {candidate.job_title_applied || 'requested'} position.
                                            {candidate.score?.total_score > 85 ? " Strong evidence of leadership and deep technical expertise." : " Good foundational knowledge with relevant experience."}
                                        </p>
                                        <div style={{ marginTop: '1.5rem', display: 'flex', gap: 12 }}>
                                            <button className="btn btn-primary" onClick={() => window.open(`mailto:${candidate.email}`)}>Contact Candidate</button>
                                            <button className="btn btn-secondary" onClick={() => toast('Interview scheduling coming soon')}>Schedule Interview</button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}

export default function CandidateRanking() {
    const location = useLocation()
    const queryParams = new URLSearchParams(location.search)
    const jobFilter = queryParams.get('job')

    const [selectedCandidate, setSelectedCandidate] = useState(null)
    const { data, isLoading, refetch, isFetching } = useQuery({
        queryKey: ['ranking', jobFilter],
        queryFn: () => hrApi.getRanking(50, jobFilter),
        staleTime: 60000,
    })

    const candidates = data?.candidates || []

    return (
        <div>
            <div className="page-header" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div>
                    <h1>Candidate Ranking</h1>
                    <p>
                        {jobFilter ? (
                            <>Showing candidates matched for: <strong style={{ color: 'var(--color-primary-light)' }}>{jobFilter}</strong></>
                        ) : (
                            'AI-scored candidates sorted by total fit score'
                        )}
                    </p>
                </div>
                <button className="btn btn-secondary btn-sm" onClick={refetch} disabled={isFetching}>
                    <RefreshCw size={14} className={isFetching ? 'spinning' : ''} />
                    Refresh
                </button>
            </div>

            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
                    <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
                </div>
            ) : candidates.length === 0 ? (
                <div className="empty-state card">
                    <div className="empty-icon"><TrendingUp size={32} color="#6366f1" /></div>
                    <h3>No Candidates Yet</h3>
                    <p>Upload CVs to start building your candidate pipeline</p>
                </div>
            ) : (
                <>
                    {/* Top 3 podium */}
                    {candidates.length >= 3 && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                            {candidates.slice(0, 3).map((c, i) => (
                                <div className="card" key={c.candidate_id} style={{
                                    borderColor: i === 0 ? 'rgba(245,158,11,0.4)' : 'var(--color-border)',
                                    background: i === 0 ? 'rgba(245,158,11,0.08)' : 'var(--color-bg-card)',
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                        <RankBadge rank={i + 1} />
                                        <StatusBadge status={c.status} />
                                    </div>
                                    <h3 style={{ fontSize: '1rem', marginBottom: 4 }}>{c.full_name}</h3>
                                    <p style={{ fontSize: 12, marginBottom: '1rem' }}>{c.email}</p>
                                    {c.job_title_applied && (
                                        <div style={{ display: 'flex', gap: 4, alignItems: 'center', fontSize: 12, color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                                            <Briefcase size={12} /> {c.job_title_applied}
                                        </div>
                                    )}
                                    <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
                                        <Award size={14} color="#6366f1" /> Total Score
                                    </div>
                                    <ScoreBar score={c.total_score} />
                                    <div style={{ display: 'flex', gap: 6, marginTop: '0.75rem', flexWrap: 'wrap' }}>
                                        {c.top_skills?.slice(0, 3).map(s => (
                                            <span key={s} className="badge badge-indigo" style={{ fontSize: 10 }}>{s}</span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Full table */}
                    <div className="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Candidate</th>
                                    <th>Total Score</th>
                                    <th>Skills</th>
                                    <th>Experience</th>
                                    <th>Experience</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {candidates.map((c) => (
                                    <tr key={c.candidate_id} onClick={() => setSelectedCandidate(c)} style={{ cursor: 'pointer' }}>
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
                                                {c.years_experience ? `${c.years_experience}y` : '–'}
                                            </span>
                                        </td>
                                        <td>
                                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                                {c.skills_score ? `${Math.round(c.skills_score)}/100` : '–'}
                                            </span>
                                        </td>
                                        <td><StatusBadge status={c.status} /></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            <CandidateProfile candidate={selectedCandidate} onClose={() => setSelectedCandidate(null)} />
        </div>
    )
}
