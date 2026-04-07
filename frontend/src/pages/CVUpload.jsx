import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import toast from 'react-hot-toast'
import {
    Upload, FileText, X, CheckCircle, AlertCircle, Cpu,
    Star, Briefcase, GraduationCap, Code, Github
} from 'lucide-react'

function ScoreCircle({ score }) {
    const pct = Math.round(score)
    const color = pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444'
    return (
        <div style={{
            width: 90, height: 90,
            borderRadius: '50%',
            background: `conic-gradient(${color} ${pct * 3.6}deg, var(--color-border) 0deg)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                width: 70, height: 70,
                borderRadius: '50%',
                background: 'var(--color-bg-card)',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            }}>
                <span style={{ fontSize: 20, fontWeight: 800, color }}>{pct}</span>
                <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>score</span>
            </div>
        </div>
    )
}

export default function CVUpload() {
    const [files, setFiles] = useState([])
    const [jobTitle, setJobTitle] = useState('')
    const [requiredSkills, setRequiredSkills] = useState('')
    const [results, setResults] = useState([])
    const queryClient = useQueryClient()

    const mutation = useMutation({
        mutationFn: ({ file, jobTitle, requiredSkills }) =>
            hrApi.uploadCV(file, jobTitle, requiredSkills),
        onSuccess: (data, { file }) => {
            setResults(prev => [{ file: file.name, ...data }, ...prev])
            queryClient.invalidateQueries({ queryKey: ['ranking'] })
            toast.success(`CV processed: ${data.candidate?.full_name || file.name}`)
        },
        onError: (err) => toast.error(err.message),
    })

    const onDrop = useCallback((accepted) => {
        setFiles(prev => [...prev, ...accepted])
    }, [])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'], 'image/*': ['.png', '.jpg', '.jpeg'] },
        maxSize: 10 * 1024 * 1024,
        multiple: true,
    })

    const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx))

    const processAll = () => {
        if (!files.length) return toast.error('Add at least one CV file')
        files.forEach(file => {
            mutation.mutate({ file, jobTitle, requiredSkills })
        })
        setFiles([])
    }

    return (
        <div>
            <div className="page-header">
                <h1>CV Upload & Analysis</h1>
                <p>Upload candidate CVs for AI-powered parsing, scoring, and profiling</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                {/* Upload Panel */}
                <div>
                    <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}>
                        <input {...getInputProps()} />
                        <div className="upload-icon">
                            <Upload size={28} />
                        </div>
                        <h3 style={{ marginBottom: 8 }}>
                            {isDragActive ? 'Drop CVs here!' : 'Drop CVs or click to upload'}
                        </h3>
                        <p style={{ fontSize: 13 }}>Supports PDF, PNG, JPEG • Max 10MB per file</p>
                    </div>

                    {/* Options */}
                    <div className="card" style={{ marginTop: '1.25rem' }}>
                        <h3 style={{ marginBottom: '0.25rem', fontSize: 15 }}>Processing Options</h3>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: '1rem', lineHeight: 1.5 }}>
                            <strong>Note:</strong> All uploaded CVs are automatically parsed and securely saved into the central Candidate Database.
                            These optional fields allow the AI to actively match and score the CV against a specific role.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div className="form-group">
                                <label className="form-label">Job Position (optional)</label>
                                <input
                                    className="form-input"
                                    placeholder="e.g. Senior Python Engineer"
                                    value={jobTitle}
                                    onChange={e => setJobTitle(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Required Skills (comma-separated)</label>
                                <input
                                    className="form-input"
                                    placeholder="e.g. python, react, docker, aws"
                                    value={requiredSkills}
                                    onChange={e => setRequiredSkills(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>

                    {/* File Queue */}
                    {files.length > 0 && (
                        <div className="card" style={{ marginTop: '1.25rem' }}>
                            <h3 style={{ marginBottom: '1rem', fontSize: 15 }}>
                                Queue ({files.length} files)
                            </h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 200, overflowY: 'auto' }}>
                                {files.map((f, i) => (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'center', gap: 10,
                                        padding: '8px 12px',
                                        background: 'var(--color-bg-glass)',
                                        borderRadius: 8,
                                        border: '1px solid var(--color-border)',
                                    }}>
                                        <FileText size={16} color="#6366f1" />
                                        <span style={{ flex: 1, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(f.size / 1024).toFixed(0)}KB</span>
                                        <button onClick={() => removeFile(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                                            <X size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                            <button
                                className="btn btn-primary"
                                style={{ width: '100%', marginTop: '1rem' }}
                                onClick={processAll}
                                disabled={mutation.isPending}
                            >
                                {mutation.isPending
                                    ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Processing…</>
                                    : <><Cpu size={16} /> Analyse {files.length} CV{files.length > 1 ? 's' : ''}</>
                                }
                            </button>
                        </div>
                    )}
                </div>

                {/* Results Panel */}
                <div>
                    <h3 style={{ marginBottom: '1rem', fontSize: 15, fontWeight: 700 }}>
                        Processing Results
                    </h3>
                    {results.length === 0 ? (
                        <div className="empty-state card">
                            <div className="empty-icon">📄</div>
                            <p>Results will appear here after processing</p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '70vh', overflowY: 'auto' }}>
                            {results.map((r, i) => {
                                const candidate = r.candidate || {}
                                const score = r.score || candidate.score || {}
                                const skills = candidate.skills || []
                                return (
                                    <div className="card" key={i}>
                                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', marginBottom: '1rem' }}>
                                            <ScoreCircle score={score.total_score || 0} />
                                            <div style={{ flex: 1 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                    <h4 style={{ fontSize: 15 }}>{candidate.full_name || r.file}</h4>
                                                    {r.status === 'completed' && <CheckCircle size={14} color="#10b981" />}
                                                </div>
                                                <p style={{ fontSize: 13, marginTop: 2 }}>{candidate.email || 'Email not found'}</p>
                                                {candidate.job_title_applied && (
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                                                        <Briefcase size={12} /> {candidate.job_title_applied}
                                                    </div>
                                                )}
                                                {candidate.github_url && (
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#6366f1', marginTop: 2 }}>
                                                        <Github size={12} /> {candidate.github_url}
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Sub-scores */}
                                        {score.total_score && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: '1rem' }}>
                                                {[
                                                    { label: 'Skills', val: score.skills_score, icon: Code },
                                                    { label: 'Experience', val: score.experience_score, icon: Briefcase },
                                                    { label: 'Education', val: score.education_score, icon: GraduationCap },
                                                    { label: 'GitHub', val: score.github_score, icon: Github },
                                                ].map(({ label, val, icon: Icon }) => (
                                                    <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                                                        <Icon size={12} color="var(--text-muted)" style={{ width: 16 }} />
                                                        <span style={{ width: 70, color: 'var(--text-muted)' }}>{label}</span>
                                                        <div className="score-bar" style={{ flex: 1 }}>
                                                            <div className="score-bar-fill" style={{ width: `${val || 0}%` }} />
                                                        </div>
                                                        <span style={{ width: 32, textAlign: 'right', fontWeight: 700, color: 'var(--color-primary-light)', fontSize: 12 }}>{Math.round(val || 0)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}

                                        {/* Skills */}
                                        {skills.length > 0 && (
                                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                                {skills.slice(0, 6).map((s, j) => (
                                                    <span key={j} className="badge badge-indigo" style={{ fontSize: 11 }}>
                                                        {s.name || s}
                                                    </span>
                                                ))}
                                                {skills.length > 6 && <span className="badge badge-gray">+{skills.length - 6}</span>}
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
