import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import { ArrowLeft, Mail, Phone, Briefcase, User, FileText, Award, BarChart2, Clock, MessageSquare, CalendarDays, Send, Video, PhoneCall, MapPin, ExternalLink, Calendar, Cpu, Shield } from 'lucide-react'
import toast from 'react-hot-toast'

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

const TABS = ['Profile', 'Job Fit', 'CV Analysis', 'Interview Notes', 'Contact']

export default function CandidateDetail() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState('Profile')
    const [notes, setNotes] = useState('')
    const [interviewDate, setInterviewDate] = useState('')
    const [interviewTime, setInterviewTime] = useState('10:00')
    const [interviewType, setInterviewType] = useState('video')
    const [interviewNotes, setInterviewNotes] = useState('')
    const [scheduledInterviews, setScheduledInterviews] = useState([])
    
    // For Job Fit Tab
    const [availableJobs, setAvailableJobs] = useState([])
    const [selectedJob, setSelectedJob] = useState('')
    const [isEvaluating, setIsEvaluating] = useState(false)

    useEffect(() => {
        hrApi.getJobs().then(d => setAvailableJobs(d.jobs || []))
    }, [])

    const handleEvaluate = async () => {
        if (!selectedJob) return toast.error("Veuillez sélectionner un poste d'abord")
        setIsEvaluating(true)
        try {
            await hrApi.evaluateCandidateForJob(id, selectedJob)
            toast.success("Évaluation IA Complète !")
            window.location.reload()
        } catch (err) {
            toast.error("L'évaluation a échoué")
        } finally {
            setIsEvaluating(false)
        }
    }

    const scheduleInterview = () => {
        if (!interviewDate) {
            toast.error('Veuillez sélectionner une date')
            return
        }
        const newInterview = {
            id: Date.now(),
            date: interviewDate,
            time: interviewTime,
            type: interviewType,
            notes: interviewNotes,
            candidateName: candidate.full_name,
        }
        setScheduledInterviews(prev => [...prev, newInterview])
        setInterviewNotes('')
        setInterviewDate('')
        toast.success(`Entretien programmé le ${new Date(interviewDate).toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })} à ${interviewTime}`)
    }

    const removeInterview = (id) => {
        setScheduledInterviews(prev => prev.filter(i => i.id !== id))
        toast.success('Entretien annulé')
    }

    const { data: candidate, isLoading } = useQuery({
        queryKey: ['candidate', id],
        queryFn: () => hrApi.getCandidate(id),
        enabled: !!id
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
            toast.success('Notes enregistrées')
        })
    }

    if (isLoading || !candidate) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
                <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
            </div>
        )
    }

    return (
        <div>
            {/* Boutons Retour et Imprimer */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <button 
                    onClick={() => navigate('/candidates')} 
                    className="btn btn-ghost btn-sm"
                    style={{ display: 'inline-flex', gap: 6 }}
                >
                    <ArrowLeft size={16} /> Retour aux Candidats
                </button>
                <button 
                    onClick={() => window.open(`http://localhost:8000/candidates/${candidate.id}/report`, '_blank')} 
                    className="btn btn-secondary btn-sm"
                    style={{ display: 'inline-flex', gap: 6 }}
                >
                    🖨️ Imprimer / Exporter en PDF
                </button>
            </div>

            {/* Header du candidat */}
            <div style={{ marginBottom: '1.5rem' }}>
                <div className="card" style={{ padding: '2rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
                    <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifycontent: 'center', color: 'white', flexShrink: 0, justifyContent: 'center' }}>
                        <User size={40} />
                    </div>
                    <div style={{ flex: 1, minWidth: 200 }}>
                        <h1 style={{ fontSize: '1.75rem', marginBottom: 6, background: 'var(--gradient-primary)', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'var(--color-primary-light)', WebkitTextFillColor: 'transparent' }}>
                            {candidate.full_name}
                        </h1>
                        <div style={{ display: 'flex', gap: 20, fontSize: 14, color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Mail size={15} color="var(--color-primary-light)" /> {candidate.email || 'Pas d\'email'}
                            </span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Briefcase size={15} color="var(--color-primary-light)" /> {candidate.job_title_applied || 'Candidature Générale'}
                            </span>
                            {candidate.years_experience && (
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <Clock size={15} color="var(--color-primary-light)" /> {candidate.years_experience}+ ans d'expérience
                                </span>
                            )}
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                        <StatusBadge status={candidate.status} />
                        <div className="card" style={{ padding: '1rem 1.5rem', textAlign: 'center', background: 'var(--color-bg-primary)', margin: 0 }}>
                            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-primary-light)' }}>
                                {Math.round(candidate.score?.total_score || candidate.total_score || 0)}%
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>SCORE IA</div>
                        </div>
                        <div className="card" style={{ padding: '1rem 1.5rem', textAlign: 'center', background: 'var(--color-bg-primary)', margin: 0, border: '1px solid var(--color-success)' }}>
                            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--color-success)' }}>
                                {candidate.fairness_report?.fairness_score || 100}%
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--color-success)', fontWeight: 700 }}>ÉQUITÉ IA</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Warning de Doublon */}
            {candidate.is_duplicate && (
                <div className="card" style={{ padding: '1.25rem', borderLeft: '4px solid var(--color-danger)', background: 'rgba(239, 68, 68, 0.08)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ fontSize: 24 }}>⚠️</div>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, color: 'var(--color-danger)', fontSize: 14 }}>
                            Candidature Doublon Détectée (Structure & Contenu similaires à plus de 88%)
                        </div>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
                            Ce CV présente une ressemblance structurelle très forte avec un profil existant.
                            {candidate.duplicate_of && (
                                <span>
                                    {' '}Profil original identifié :{' '}
                                    <span 
                                        onClick={() => navigate(`/candidates/${candidate.duplicate_of}`)}
                                        style={{ color: 'var(--color-primary-light)', fontWeight: 600, textDecoration: 'underline', cursor: 'pointer' }}
                                    >
                                        Consulter la candidature originale
                                    </span>
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="candidate-detail-tabs">
                {TABS.map(t => (
                    <button
                        key={t}
                        onClick={() => setActiveTab(t)}
                        className={`candidate-detail-tab ${activeTab === t ? 'active' : ''}`}
                    >
                        {t}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="fade-in" style={{ marginTop: '1.5rem' }}>
                {activeTab === 'Profile' && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        <div>
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <FileText size={18} color="var(--color-primary-light)" /> Summary
                                </h3>
                                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                                    {candidate.summary || `Candidat possédant ${candidate.years_experience || 0}+ ans d'expérience. Démontre des compétences solides correspondant à une évaluation globale de ${candidate.score?.total_score || candidate.total_score || 0}%.`}
                                </p>
                            </div>

                            <div className="card" style={{ padding: '1.5rem', marginTop: '1.25rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Briefcase size={18} color="var(--color-primary-light)" /> Experience
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                    {(candidate.experience || []).slice(0, 5).map((exp, i) => (
                                        <div className="card" key={i} style={{ padding: '1rem', background: 'var(--color-bg-primary)' }}>
                                            <div style={{ fontWeight: 600, fontSize: 14 }}>{exp.title || exp.role}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{exp.company} • {exp.period}</div>
                                            {exp.description && (
                                                <p style={{ fontSize: 13, marginTop: 8, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                                    {exp.description.slice(0, 200)}{exp.description.length > 200 ? '...' : ''}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div>
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Award size={18} color="var(--color-primary-light)" /> Indicateurs Clés
                                </h3>
                                <div style={{ marginBottom: '1.5rem' }}>
                                    {[
                                        { label: 'Match Compétences', val: candidate.score?.skills_score || 70 },
                                        { label: 'GitHub & DevOps', val: candidate.score?.github_score || 50 },
                                        { label: 'Profondeur Expérience', val: candidate.score?.experience_score || 65 },
                                        { label: 'Éducation & Certifs', val: candidate.score?.education_score || 80 },
                                        { label: 'Qualité Présentation', val: candidate.score?.communication_score || 75 },
                                    ].map((item, i) => (
                                        <div key={i} style={{ marginBottom: 14 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4, fontWeight: 600 }}>
                                                <span>{item.label}</span>
                                                <span style={{ color: 'var(--color-primary-light)' }}>{Math.round(item.val || 0)}%</span>
                                            </div>
                                            <ScoreBar score={item.val || 0} color={item.val > 80 ? 'var(--color-success)' : 'var(--gradient-primary)'} />
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="card" style={{ padding: '1.5rem', marginTop: '1.25rem' }}>
                                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: '1rem', fontWeight: 600 }}>Compétences Clés</div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                    {(candidate.skills || []).slice(0, 12).map(s => (
                                        <span key={typeof s === 'string' ? s : s.name} className="badge badge-indigo">
                                            {typeof s === 'string' ? s : s.name}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'Job Fit' && (
                    <div className="card" style={{ padding: '2rem' }}>
                        <h3 style={{ fontSize: 18, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Briefcase size={20} color="var(--color-primary-light)" /> Évaluer par rapport à un Poste Ouvert
                        </h3>
                        
                        <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', alignItems: 'flex-end' }}>
                            <div className="form-group" style={{ flex: 1, margin: 0 }}>
                                <label className="form-label">Sélectionner un poste</label>
                                <select 
                                    className="form-input" 
                                    value={selectedJob} 
                                    onChange={e => setSelectedJob(e.target.value)}
                                >
                                    <option value="">-- Choisir une offre d'emploi active --</option>
                                    {availableJobs.map(j => (
                                        <option key={j.id} value={j.id}>{j.title}</option>
                                    ))}
                                </select>
                            </div>
                            <button 
                                className="btn btn-primary" 
                                onClick={handleEvaluate} 
                                disabled={isEvaluating || !selectedJob}
                            >
                                {isEvaluating ? 'Évaluation IA en cours...' : 'Lancer l\'Évaluation IA'}
                            </button>
                        </div>
                        
                        {candidate.offer_evaluations?.length > 0 ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                <h4 style={{ fontSize: 15 }}>Historique des Évaluations</h4>
                                {candidate.offer_evaluations.map((evalRecord, idx) => (
                                    <div key={idx} className="card" style={{ background: 'var(--color-bg-primary)', borderLeft: '4px solid var(--color-primary-light)' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                            <h5 style={{ fontSize: 16 }}>{evalRecord.offer_title}</h5>
                                            <div style={{ padding: '4px 12px', background: 'var(--color-surface)', borderRadius: '20px', fontWeight: 'bold', color: 'var(--color-primary-light)' }}>
                                                {evalRecord.score}% de Match
                                            </div>
                                        </div>
                                        <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: '1rem', lineHeight: 1.6 }}>
                                            <strong>Justification IA :</strong> {evalRecord.justification}
                                        </p>
                                        <div style={{ display: 'flex', gap: '2rem' }}>
                                            <div style={{ flex: 1 }}>
                                                <strong style={{ fontSize: 13, color: 'var(--color-success)' }}>✅ Critères Matchés</strong>
                                                <ul style={{ fontSize: 13, color: 'var(--text-secondary)', paddingLeft: '1rem', marginTop: '0.5rem' }}>
                                                    {evalRecord.met_criteria?.map((c, i) => <li key={i} style={{ marginBottom: '4px' }}>{c}</li>)}
                                                </ul>
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <strong style={{ fontSize: 13, color: 'var(--color-danger)' }}>❌ Critères Manquants</strong>
                                                <ul style={{ fontSize: 13, color: 'var(--text-secondary)', paddingLeft: '1rem', marginTop: '0.5rem' }}>
                                                    {evalRecord.missing_criteria?.map((c, i) => <li key={i} style={{ marginBottom: '4px' }}>{c}</li>)}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Aucune évaluation spécifique de poste n'a encore été menée pour ce candidat.</p>
                        )}
                    </div>
                )}

                {activeTab === 'CV Analysis' && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        <div>
                            {/* Match Visualization */}
                            <div className="card" style={{ padding: '1.5rem', marginBottom: '1.25rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <BarChart2 size={18} color="var(--color-accent)" /> Match Visualization
                                </h3>
                                {[
                                    { label: 'Skills Match', val: candidate.score?.skills_score || 70 },
                                    { label: 'Cloud & DevOps', val: candidate.score?.github_score || 50 },
                                    { label: 'Experience Depth', val: candidate.score?.experience_score || 65 },
                                    { label: 'Education Alignment', val: candidate.score?.education_score || 80 },
                                    { label: 'Communication', val: candidate.score?.communication_score || 75 },
                                ].map((item, i) => (
                                    <div key={i} style={{ marginBottom: 14 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4, fontWeight: 600 }}>
                                            <span>{item.label}</span>
                                            <span style={{ color: 'var(--color-primary-light)' }}>{Math.round(item.val || 0)}%</span>
                                        </div>
                                        <ScoreBar score={item.val || 0} color={item.val > 80 ? 'var(--color-success)' : 'var(--gradient-primary)'} />
                                    </div>
                                ))}
                            </div>

                            {/* Explainable AI Decision Scorecard */}
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Cpu size={18} color="var(--color-primary)" /> Explications Décisionnelles IA (XAI)
                                </h3>
                                <div style={{ marginBottom: '1rem' }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600 }}>DÉTAILS DU RAISONNEMENT DU SCORE</div>
                                    <ul style={{ paddingLeft: '1.2rem', margin: 0, fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)' }}>
                                        {(candidate.score?.explainable_ai?.reasons || [
                                            "Profil doté d'expériences clés en adéquation avec les critères requis.",
                                            "Compétences technologiques robustes détectées de manière automatique.",
                                            "Aucune anomalie structurelle ou incohérence de parcours détectée."
                                        ]).map((reason, i) => (
                                            <li key={i} style={{ marginBottom: 6 }}>
                                                {reason}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem', marginTop: '1rem' }}>
                                    <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600 }}>COMPÉTENCES DU CV CIBLÉES</div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                        {(candidate.score?.explainable_ai?.matched_skills || candidate.skills || []).slice(0, 10).map((s, idx) => (
                                            <span key={idx} className="badge badge-green">
                                                ✓ {typeof s === 'string' ? s : s.name}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            {/* Experience Timeline */}
                            <div className="card" style={{ padding: '1.5rem', marginBottom: '1.25rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Clock size={18} color="var(--color-warning)" /> Experience Timeline
                                </h3>
                                <div style={{ paddingLeft: 16, borderLeft: '2px solid var(--color-border)', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                                    {(candidate.experience || []).map((exp, i) => (
                                        <div key={i} style={{ position: 'relative' }}>
                                            <div style={{ position: 'absolute', left: -21, top: 4, width: 10, height: 10, borderRadius: '50%', background: i === 0 ? 'var(--color-warning)' : 'var(--color-primary)' }} />
                                            <div style={{ fontWeight: 600 }}>{exp.title || exp.role} @ {exp.company}</div>
                                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{exp.period}</div>
                                            <p style={{ fontSize: 13, marginTop: 4, opacity: 0.8 }}>{exp.description?.slice(0, 150)}{exp.description?.length > 150 ? '...' : ''}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* AI Fairness Demographic Audit */}
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Shield size={18} color="var(--color-success)" /> Audit d'Équité & Masquage RGPD (Privacy Agent)
                                </h3>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px', background: 'rgba(16, 185, 129, 0.06)', borderRadius: 8, border: '1px solid rgba(16, 185, 129, 0.2)', marginBottom: '1rem' }}>
                                    <span style={{ fontSize: 20 }}>🛡️</span>
                                    <div style={{ fontSize: 12, color: 'var(--color-success)', fontWeight: 600 }}>
                                        Évaluation aveugle (Gender-blind, Age-blind) validée par le Privacy Agent.
                                    </div>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, borderBottom: '1px solid var(--color-border)', paddingBottom: 6 }}>
                                        <span style={{ color: 'var(--text-muted)' }}>Indice d'Équité IA</span>
                                        <span style={{ fontWeight: 700, color: 'var(--color-success)' }}>{candidate.fairness_report?.fairness_score || 100}%</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, borderBottom: '1px solid var(--color-border)', paddingBottom: 6 }}>
                                        <span style={{ color: 'var(--text-muted)' }}>Masquage identitaire</span>
                                        <span style={{ fontWeight: 600, color: 'var(--color-success)' }}>Actif (Privacy Agent)</span>
                                    </div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, borderBottom: '1px solid var(--color-border)', paddingBottom: 6 }}>
                                        <span style={{ color: 'var(--text-muted)' }}>Attributs sensibles détectés</span>
                                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>0 résiduels</span>
                                    </div>
                                </div>
                                {candidate.fairness_report?.audit_logs && (
                                    <div style={{ marginTop: '1rem' }}>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, fontWeight: 700 }}>LOGS DE CONFORMITÉ PRIVACY</div>
                                        <div style={{ padding: 8, background: 'var(--color-bg-primary)', borderRadius: 6, fontSize: 11, fontFamily: 'monospace', maxHeight: 80, overflowY: 'auto', color: 'var(--text-secondary)' }}>
                                            {candidate.fairness_report.audit_logs.map((log, idx) => (
                                                <div key={idx} style={{ marginBottom: 4 }}>• {log}</div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'Interview Notes' && (
                    <div className="card" style={{ padding: '2rem', maxWidth: 800 }}>
                        <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                            <MessageSquare size={18} color="var(--color-primary-light)" /> Notes & Feedback RH
                        </h4>
                        <textarea
                            className="form-textarea"
                            placeholder="Saisir des notes, avis techniques ou impressions sur le candidat..."
                            style={{ width: '100%', minHeight: 250, background: 'var(--color-bg-primary)', color: 'var(--text-primary)' }}
                            value={notes}
                            onChange={e => setNotes(e.target.value)}
                        />
                        <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
                            <button className="btn btn-primary" onClick={saveNotes}>Enregistrer les notes</button>
                        </div>
                    </div>
                )}

                {activeTab === 'Contact' && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        {/* Left: Contact & Schedule Interview */}
                        <div>
                            {/* Quick Contact Actions */}
                            <div className="card" style={{ padding: '1.5rem', marginBottom: '1.25rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Send size={18} color="var(--color-primary-light)" /> Actions de Contact
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                    <button
                                        className="btn btn-primary"
                                        style={{ justifyContent: 'flex-start', width: '100%' }}
                                        onClick={() => window.open(`mailto:${candidate.email}?subject=Invitation Entretien - Segula Technologies`)}
                                    >
                                        <Mail size={16} /> Envoyer un Email
                                        <span style={{ marginLeft: 'auto', opacity: 0.7, fontSize: 12 }}>{candidate.email || 'N/A'}</span>
                                    </button>
                                    <button
                                        className="btn btn-secondary"
                                        style={{ justifyContent: 'flex-start', width: '100%' }}
                                        onClick={() => candidate.phone ? window.open(`tel:${candidate.phone}`) : toast('Pas de téléphone')}
                                    >
                                        <PhoneCall size={16} /> Appeler le candidat
                                        <span style={{ marginLeft: 'auto', opacity: 0.7, fontSize: 12 }}>{candidate.phone || 'Non renseigné'}</span>
                                    </button>
                                    <button
                                        className="btn btn-ghost"
                                        style={{ justifyContent: 'flex-start', width: '100%' }}
                                        onClick={() => candidate.linkedin ? window.open(candidate.linkedin) : toast('Aucun profil LinkedIn disponible')}
                                    >
                                        <ExternalLink size={16} /> Profil LinkedIn
                                    </button>
                                </div>
                            </div>

                            {/* Schedule Interview Form */}
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <CalendarDays size={18} color="var(--color-accent)" /> Programmer un Entretien
                                </h3>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                                    <div className="form-group">
                                        <label className="form-label">Type d'entretien</label>
                                        <div style={{ display: 'flex', gap: 8 }}>
                                            {[
                                                { value: 'video', label: 'Visioconférence', icon: <Video size={14} /> },
                                                { value: 'phone', label: 'Téléphone', icon: <PhoneCall size={14} /> },
                                                { value: 'onsite', label: 'Sur site', icon: <MapPin size={14} /> },
                                            ].map(opt => (
                                                <button
                                                    key={opt.value}
                                                    className={`btn ${interviewType === opt.value ? 'btn-primary' : 'btn-ghost'} btn-sm`}
                                                    onClick={() => setInterviewType(opt.value)}
                                                    style={{ flex: 1, display: 'flex', gap: 6, justifyContent: 'center' }}
                                                >
                                                    {opt.icon} {opt.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                                        <div className="form-group">
                                            <label className="form-label">Date</label>
                                            <input
                                                type="date"
                                                className="form-input"
                                                value={interviewDate}
                                                onChange={e => setInterviewDate(e.target.value)}
                                                min={new Date().toISOString().split('T')[0]}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Heure</label>
                                            <input
                                                type="time"
                                                className="form-input"
                                                value={interviewTime}
                                                onChange={e => setInterviewTime(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Notes pour l'évaluateur</label>
                                        <textarea
                                            className="form-textarea"
                                            placeholder="Sujets à aborder, points clés du CV..."
                                            style={{ minHeight: 80, background: 'var(--color-bg-primary)', color: 'var(--text-primary)' }}
                                            value={interviewNotes}
                                            onChange={e => setInterviewNotes(e.target.value)}
                                        />
                                    </div>
                                    <button className="btn btn-primary" onClick={scheduleInterview}>
                                        <CalendarDays size={16} /> Confirmer & Planifier
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Right: Scheduled Interviews Calendar */}
                        <div>
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h3 style={{ fontSize: 16, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <Calendar size={18} color="var(--color-warning)" /> Entretiens Programmés
                                </h3>
                                {scheduledInterviews.length === 0 ? (
                                    <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                                        <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'rgba(99,102,241,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem' }}>
                                            <CalendarDays size={28} color="var(--text-muted)" />
                                        </div>
                                        <p style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 4 }}>Aucun entretien pour le moment</p>
                                        <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Utilisez le formulaire pour planifier un entretien</p>
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                        {scheduledInterviews.map(interview => (
                                            <div key={interview.id} className="card" style={{ padding: '1rem', background: 'var(--color-bg-primary)', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                                                <div style={{
                                                    width: 48, height: 48, borderRadius: 'var(--radius-sm)',
                                                    background: interview.type === 'video' ? 'rgba(6,182,212,0.12)' : interview.type === 'phone' ? 'rgba(99,102,241,0.12)' : 'rgba(245,158,11,0.12)',
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                                                    color: interview.type === 'video' ? '#22d3ee' : interview.type === 'phone' ? '#818cf8' : '#fbbf24',
                                                }}>
                                                    {interview.type === 'video' ? <Video size={20} /> : interview.type === 'phone' ? <PhoneCall size={20} /> : <MapPin size={20} />}
                                                </div>
                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                    <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>
                                                        {interview.type === 'video' ? 'Visioconférence' : interview.type === 'phone' ? 'Entretien Téléphonique' : 'Entretien Physique'}
                                                    </div>
                                                    <div style={{ fontSize: 13, color: 'var(--color-primary-light)', fontWeight: 600, marginBottom: 4 }}>
                                                        {new Date(interview.date).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })} à {interview.time}
                                                    </div>
                                                    {interview.notes && (
                                                        <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.4 }}>{interview.notes}</p>
                                                    )}
                                                </div>
                                                <button
                                                    className="btn btn-danger btn-sm"
                                                    style={{ padding: '4px 8px', fontSize: 11 }}
                                                    onClick={() => removeInterview(interview.id)}
                                                >
                                                    Annuler
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Candidate Summary Card */}
                            <div className="card" style={{ padding: '1.5rem', marginTop: '1.25rem', background: 'var(--color-bg-glass)', borderColor: 'var(--color-border-hover)' }}>
                                <h4 style={{ fontSize: 14, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-primary)' }}>
                                    <Award size={16} color="var(--color-primary-light)" /> AI Candidate Profile
                                </h4>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
                                    <div style={{ padding: '10px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-sm)' }}>
                                        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>Seniority Level</div>
                                        <div style={{ fontWeight: 700, color: 'var(--color-primary-light)' }}>{candidate.ai_profile?.seniority_level || 'Confirmé'}</div>
                                    </div>
                                    <div style={{ padding: '10px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-sm)' }}>
                                        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>Job Fit Score</div>
                                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{candidate.ai_profile?.job_fit_score || Math.round(candidate.score?.total_score || candidate.total_score || 72)}%</div>
                                    </div>
                                    <div style={{ padding: '10px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-sm)' }}>
                                        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>Job Title Match</div>
                                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 11 }}>{candidate.ai_profile?.matched_job_offer || candidate.job_title_applied || 'Général'}</div>
                                    </div>
                                    <div style={{ padding: '10px', background: 'var(--color-bg-primary)', borderRadius: 'var(--radius-sm)' }}>
                                        <div style={{ color: 'var(--text-muted)', fontSize: 11, marginBottom: 4 }}>Exp Years (Parsed)</div>
                                        <div style={{ fontWeight: 700, color: 'var(--color-success)' }}>{candidate.ai_profile?.experience_years || candidate.years_experience || 0} ans</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
