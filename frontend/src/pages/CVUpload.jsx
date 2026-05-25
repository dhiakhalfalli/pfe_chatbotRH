import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import toast from 'react-hot-toast'
import {
    Upload, FileText, X, CheckCircle, AlertCircle, Cpu,
    Star, Briefcase, GraduationCap, Code, Github,
    Plus, Sliders, ChevronDown, Zap, Target
} from 'lucide-react'

// Removed Job Presets and Skill Suggestions

// ─── Score Circle ─────────────────────────────────────────────────────────────
function ScoreCircle({ score }) {
    const pct = Math.round(score)
    const color = pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : pct >= 40 ? '#6366f1' : '#ef4444'
    const label = pct >= 80 ? 'Excellent' : pct >= 60 ? 'Good' : pct >= 40 ? 'Average' : 'Low'
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <div style={{
                width: 88, height: 88, borderRadius: '50%',
                background: `conic-gradient(${color} ${pct * 3.6}deg, var(--color-border) 0deg)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: `0 0 20px ${color}30`,
            }}>
                <div style={{
                    width: 68, height: 68, borderRadius: '50%',
                    background: 'var(--color-bg-card)',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                }}>
                    <span style={{ fontSize: 20, fontWeight: 800, color, lineHeight: 1 }}>{pct}</span>
                    <span style={{ fontSize: 9, color: 'var(--text-muted)', fontWeight: 600 }}>/ 100</span>
                </div>
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color, letterSpacing: '0.05em' }}>{label}</span>
        </div>
    )
}

// Removed TagInput and WeightSlider

// ─── Main Component ───────────────────────────────────────────────────────────
export default function CVUpload() {
    const user = JSON.parse(localStorage.getItem('user')) || { role: 'hr' }
    const isExternal = user.role === 'external'
    
    const [files, setFiles] = useState([])
    const [results, setResults] = useState([])
    const [gdprAccepted, setGdprAccepted] = useState(false)
    const queryClient = useQueryClient()

    const mutation = useMutation({
        mutationFn: ({ file }) => hrApi.uploadCV(file, user.role),
        onSuccess: (data, { file }) => {
            setResults(prev => [{ file: file.name, ...data }, ...prev])
            queryClient.invalidateQueries({ queryKey: ['candidates'] })
            if (data.status === 'failed') {
                toast.error(`❌ ${file.name}: ${data.error || 'Failed to extract text'}`)
            } else {
                toast.success(`✅ ${data.candidate?.full_name || file.name} added to database!`)
            }
        },
        onError: (err) => toast.error(err.message),
    })

    const onDrop = useCallback((accepted) => {
        if (!accepted.length) return
        if (isExternal && files.length >= 1) {
            toast.error("Vous ne pouvez déposer qu'un seul CV.")
            return
        }
        setFiles(prev => isExternal ? [accepted[0]] : [...prev, ...accepted])
    }, [isExternal, files])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'], 'image/*': ['.png', '.jpg', '.jpeg'] },
        maxSize: 10 * 1024 * 1024,
        multiple: !isExternal,
    })

    const processAll = () => {
        if (!files.length) return toast.error('Add at least one CV file')
        if (isExternal && !gdprAccepted) return toast.error('Veuillez accepter les conditions RGPD.')
        files.forEach(file => mutation.mutate({ file }))
        setFiles([])
    }

    return (
        <div>
            <div className="page-header">
                <h1>{isExternal ? 'Déposer mon CV' : 'CV Upload & Analysis'}</h1>
                <p>{isExternal ? 'Postulez en un clic. Votre CV sera analysé par notre IA.' : 'Upload CVs, define job criteria, and get AI-powered scores based on your requirements'}</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                {/* ── Left Panel ── */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

                    {isExternal && results.length >= 1 ? (
                        <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
                            <CheckCircle size={48} color="var(--color-success)" style={{ margin: '0 auto 1rem' }} />
                            <h3>CV Envoyé avec succès !</h3>
                            <p style={{ color: 'var(--text-muted)' }}>Votre candidature a bien été ajoutée à notre base de données RH. Notre équipe reviendra vers vous très vite.</p>
                        </div>
                    ) : (
                        <>
                            {/* Dropzone */}
                            <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}>
                                <input {...getInputProps()} />
                                <div className="upload-icon"><Upload size={28} /></div>
                                <h3 style={{ marginBottom: 8 }}>
                                    {isDragActive ? 'Relâchez le fichier ici !' : (isExternal ? 'Glissez votre CV ici ou cliquez pour l\'importer' : 'Drop CVs or click to upload')}
                                </h3>
                                <p style={{ fontSize: 13 }}>PDF, PNG, JPEG · Max 10MB {isExternal ? '' : 'per file'}</p>
                            </div>

                            {/* File Queue */}
                            {files.length > 0 && (
                                <div className="card">
                                    <h3 style={{ marginBottom: '1rem', fontSize: 14 }}>{isExternal ? 'Fichier sélectionné' : `Queue (${files.length})`}</h3>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 160, overflowY: 'auto' }}>
                                        {files.map((f, i) => (
                                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'var(--color-bg-glass)', borderRadius: 8, border: '1px solid var(--color-border)' }}>
                                                <FileText size={16} color="#6366f1" />
                                                <span style={{ flex: 1, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                                                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(f.size / 1024).toFixed(0)}KB</span>
                                                <button onClick={() => setFiles(prev => prev.filter((_, j) => j !== i))} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                    
                                    {isExternal && (
                                        <div style={{ marginTop: '1rem', padding: '16px', background: 'rgba(99, 102, 241, 0.05)', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: 8, display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                                            <input 
                                                type="checkbox" 
                                                id="gdpr" 
                                                checked={gdprAccepted} 
                                                onChange={e => setGdprAccepted(e.target.checked)} 
                                                style={{ marginTop: 4, transform: 'scale(1.2)', cursor: 'pointer' }}
                                            />
                                            <label htmlFor="gdpr" style={{ cursor: 'pointer', lineHeight: 1.5, color: 'var(--text-primary)', fontSize: 13 }}>
                                                <strong style={{ display: 'block', marginBottom: 4, fontSize: 14 }}>Consentement de Traitement de Données (RGPD)</strong>
                                                En soumettant mon CV, j'accepte expressément que <strong>Segula Technologies</strong> collecte et traite mes données personnelles dans le but d'évaluer ma candidature.
                                                Je comprends que mon profil sera analysé par une <strong>Intelligence Artificielle</strong> garantissant un traitement équitable (sans biais). 
                                                Mes données seront conservées pour une durée maximale de <strong>2 ans</strong>. Je dispose d'un droit d'accès, de rectification et d'effacement de mes données à tout moment via mon espace candidat.
                                            </label>
                                        </div>
                                    )}

                                    <button 
                                        className="btn btn-primary" 
                                        style={{ width: '100%', marginTop: '1rem' }} 
                                        onClick={processAll} 
                                        disabled={mutation.isPending || (isExternal && !gdprAccepted)}
                                    >
                                        {mutation.isPending
                                            ? <><div className="spinner" style={{ width: 16, height: 16 }} /> {isExternal ? 'Envoi en cours…' : 'Analysing…'}</>
                                            : <><Cpu size={16} /> {isExternal ? 'Envoyer mon CV' : `Analyse ${files.length} CV${files.length > 1 ? 's' : ''}`}</>
                                        }
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* ── Right Panel — Results ── */}
                <div>
                    <h3 style={{ marginBottom: '1rem', fontSize: 15, fontWeight: 700 }}>Results</h3>
                    {results.length === 0 ? (
                        <div className="empty-state card">
                            <div className="empty-icon">📊</div>
                            <p>Upload a CV to see the results here</p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '75vh', overflowY: 'auto' }}>
                            {results.map((r, i) => {
                                const c = r.candidate || {}
                                const skills = c.skills || []

                                return (
                                    <div className="card" key={i} style={{ borderLeft: r.status === 'failed' ? '3px solid #ef4444' : '3px solid #10b981' }}>
                                        {/* Header */}
                                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', alignItems: 'flex-start' }}>
                                            <div style={{ flex: 1, minWidth: 0 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                                    <h4 style={{ fontSize: 15 }}>{c.full_name || r.file}</h4>
                                                    {r.status === 'failed' ? (
                                                        <AlertCircle size={14} color="#ef4444" />
                                                    ) : (
                                                        <CheckCircle size={14} color="#10b981" />
                                                    )}
                                                </div>
                                                {r.status === 'failed' ? (
                                                    <p style={{ fontSize: 12, color: '#ef4444', fontWeight: 500, margin: 0 }}>{r.error || 'Failed to extract text'}</p>
                                                ) : (
                                                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{c.email || 'Email not found'}</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* All CV Skills */}
                                        {skills.length > 0 && (
                                            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                                                {skills.slice(0, 15).map((s, j) => (
                                                    <span key={j} className="badge badge-indigo" style={{ fontSize: 11 }}>{s.name || s}</span>
                                                ))}
                                                {skills.length > 15 && <span className="badge badge-gray">+{skills.length - 15}</span>}
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
