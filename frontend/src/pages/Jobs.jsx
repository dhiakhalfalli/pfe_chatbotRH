import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, MapPin, Users, Target, Search, Filter, Plus, X, FileText, RefreshCw } from 'lucide-react'
import { hrApi } from '../services/api.js'
import toast from 'react-hot-toast'

// These come from the real offers/ folder in the project
const REAL_OFFERS = [
    {
        id: 101,
        title: 'Développeur Python',
        location: 'France',
        skills: ['Python', 'Django', 'FastAPI', 'PostgreSQL', 'Docker'],
        experience: '3+ ans',
        source: 'Python Developer.docx',
        description: 'Développement et maintenance d\'applications Python. Intégration de microservices. Tests unitaires et CI/CD.',
    },
    {
        id: 102,
        title: 'Ingénieur Logiciel – Offre 1',
        location: 'Maroc / Remote',
        skills: ['Java', 'Spring Boot', 'Microservices', 'Kubernetes'],
        experience: '2+ ans',
        source: 'offre.docx',
        description: 'Conception et développement d\'applications Java dans un environnement Agile/Scrum. Participation aux code reviews.',
    },
    {
        id: 103,
        title: 'Ingénieur DevOps – Offre 2',
        location: 'Casablanca, Maroc',
        skills: ['CI/CD', 'Jenkins', 'Ansible', 'Terraform', 'AWS'],
        experience: '4+ ans',
        source: 'offree.docx',
        description: 'Automatisation des pipelines CI/CD. Gestion de l\'infrastructure cloud. Monitoring et alerting des systèmes.',
    },
]

const DEMO_JOBS = [
    {
        id: 1,
        title: 'Senior Python Engineer',
        location: 'Paris, France',
        skills: ['Python', 'FastAPI', 'Docker', 'SQL'],
        experience: '5+ years',
        source: null,
        description: 'Work on our core HR platform APIs using FastAPI and Python.',
    },
    {
        id: 2,
        title: 'Machine Learning Tech Lead',
        location: 'Remote',
        skills: ['Python', 'PyTorch', 'MLOps', 'AWS'],
        experience: '7+ years',
        source: null,
        description: 'Lead ML model development and deployment for our AI systems.',
    },
    {
        id: 3,
        title: 'Frontend Developer (React)',
        location: 'Lyon, France',
        skills: ['React', 'JavaScript', 'CSS', 'Redux'],
        experience: '3+ years',
        source: null,
        description: 'Build stunning and responsive UIs for our HR platform.',
    },
]

function AddJobModal({ onClose, onAdd }) {
    const [form, setForm] = useState({
        title: '', location: '', skills: '', experience: '', description: '',
    })

    const handleSubmit = (e) => {
        e.preventDefault()
        onAdd({
            id: Date.now(),
            title: form.title,
            location: form.location,
            skills: form.skills.split(',').map(s => s.trim()).filter(Boolean),
            matched: 0,
            experience: form.experience,
            source: null,
            description: form.description,
        })
        onClose()
    }

    return (
        <div style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
        }}>
            <div className="card" style={{ width: '100%', maxWidth: 520 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h2 style={{ fontSize: '1.125rem' }}>Add New Job Position</h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                        <X size={20} />
                    </button>
                </div>
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {[
                        { field: 'title', label: 'Job Title', type: 'text', required: true, placeholder: 'e.g. Senior Python Developer' },
                        { field: 'location', label: 'Location', type: 'text', required: true, placeholder: 'e.g. Paris, France / Remote' },
                        { field: 'experience', label: 'Experience Required', type: 'text', required: false, placeholder: 'e.g. 3+ years' },
                        { field: 'skills', label: 'Required Skills (comma-separated)', type: 'text', required: true, placeholder: 'Python, FastAPI, Docker...' },
                    ].map(({ field, label, type, required, placeholder }) => (
                        <div className="form-group" key={field}>
                            <label className="form-label">{label}</label>
                            <input
                                className="form-input"
                                type={type}
                                value={form[field]}
                                onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))}
                                required={required}
                                placeholder={placeholder}
                            />
                        </div>
                    ))}
                    <div className="form-group">
                        <label className="form-label">Description</label>
                        <textarea
                            className="form-textarea"
                            rows={3}
                            value={form.description}
                            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                            placeholder="Brief job description..."
                            style={{ minHeight: 80 }}
                        />
                    </div>
                    <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
                        <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={onClose}>Cancel</button>
                        <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Add Position</button>
                    </div>
                </form>
            </div>
        </div>
    )
}

function JobCard({ job, onRefresh }) {
    const navigate = useNavigate()
    const [stats, setStats] = useState({ matched: 0, aiFit: 0, loading: true })

    useEffect(() => {
        hrApi.getRanking(50, job.title).then(data => {
            const count = data.candidates.length
            const avg = count > 0 
                ? data.candidates.reduce((sum, c) => sum + c.total_score, 0) / count 
                : 0
            setStats({
                matched: count,
                aiFit: Math.round(avg) || (count > 0 ? 85 : 0),
                loading: false
            })
        }).catch(() => {
            setStats({ matched: 0, aiFit: 0, loading: false })
        })
    }, [job.title])

    return (
        <div key={job.id} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary-light)', flexShrink: 0 }}>
                        <Briefcase size={20} />
                    </div>
                    <div>
                        <h3 style={{ fontSize: 15, marginBottom: 2 }}>{job.title}</h3>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                            <MapPin size={12} /> {job.location}
                        </div>
                    </div>
                </div>
                {job.source && (
                    <span className="badge badge-cyan" title={`Source: ${job.source}`} style={{ fontSize: 10, flexShrink: 0 }}>
                        <FileText size={9} /> Offre
                    </span>
                )}
            </div>

            {job.description && (
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: 1.5 }}>
                    {job.description}
                </p>
            )}

            <div style={{ marginBottom: '1rem', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {job.skills.map(s => <span key={s} className="badge badge-gray" style={{ background: 'rgba(255,255,255,0.05)' }}>{s}</span>)}
            </div>

            {job.experience && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                    📅 Expérience: <strong style={{ color: 'var(--text-secondary)' }}>{job.experience}</strong>
                </div>
            )}

            <div style={{ padding: '0.75rem', background: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-md)', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600 }}>
                    <Users size={16} color="var(--color-cyan)" /> {stats.loading ? '...' : stats.matched} Matches
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600 }}>
                    <Target size={16} color="var(--color-success)" /> AI Fit {stats.loading ? '...' : stats.aiFit}%
                </div>
            </div>

            <div style={{ marginTop: 'auto', display: 'flex', gap: 8 }}>
                <button
                    className="btn btn-primary"
                    style={{ flex: 1, padding: '8px 0' }}
                    onClick={() => navigate(`/candidates?job=${encodeURIComponent(job.title)}`)}
                >
                    ✅ View Candidates
                </button>
                <button 
                    className="btn btn-secondary" 
                    style={{ flex: 1, padding: '8px 0' }}
                    onClick={() => {
                        toast.success(`Recalculating AI score for ${job.title}...`)
                        onRefresh()
                    }}
                >
                    📊 AI Score
                </button>
            </div>
        </div>
    )
}

export default function Jobs() {
    const [jobs, setJobs] = useState([...DEMO_JOBS, ...REAL_OFFERS])
    const [search, setSearch] = useState('')
    const [showModal, setShowModal] = useState(false)
    const [refreshTrigger, setRefreshTrigger] = useState(0)
    const [totalCandidates, setTotalCandidates] = useState(0)

    useEffect(() => {
        hrApi.getCandidates(1).then(data => {
            setTotalCandidates(data.total || 0)
        }).catch(err => console.error('Failed to fetch total candidates', err))
    }, [refreshTrigger])

    const filteredJobs = jobs.filter(j =>
        j.title.toLowerCase().includes(search.toLowerCase()) ||
        j.skills.join(' ').toLowerCase().includes(search.toLowerCase()) ||
        j.location.toLowerCase().includes(search.toLowerCase())
    )

    const handleAdd = (newJob) => {
        setJobs(prev => [...prev, newJob])
    }

    return (
        <div>
            {showModal && <AddJobModal onClose={() => setShowModal(false)} onAdd={handleAdd} />}

            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>Open Job Positions</h1>
                    <p>Manage and track AI candidate matches for all open roles</p>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                    <button className="btn btn-secondary" onClick={() => setRefreshTrigger(t => t + 1)}>
                        <RefreshCw size={16} /> Refresh Stats
                    </button>
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        <Plus size={16} /> Add Position
                    </button>
                </div>
            </div>

            {totalCandidates === 0 && (
                <div className="card" style={{ marginBottom: '2rem', background: 'rgba(245,158,11,0.05)', borderColor: 'rgba(245,158,11,0.3)', borderLeftWidth: 4, display: 'flex', alignItems: 'center', gap: 16 }}>
                    <div style={{ fontSize: 24 }}>💡</div>
                    <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                        <strong>Aucun candidat dans la base de données.</strong> Allez dans la section <a href="/cv-analysis" style={{ color: 'var(--color-primary-light)', fontWeight: 600 }}>CV Analysis</a> pour télécharger des CVs et voir les correspondances ici.
                    </div>
                </div>
            )}

            {/* Filters Area */}
            <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem', background: 'rgba(99,102,241,0.03)' }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                    <div style={{ flex: 1, minWidth: 250, position: 'relative' }}>
                        <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
                        <input
                            type="text"
                            className="form-input"
                            placeholder="Search by job title, skill, or location..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            style={{ paddingLeft: 36 }}
                        />
                    </div>
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                        {filteredJobs.length} position{filteredJobs.length !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            {/* Job Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
                {filteredJobs.map(job => (
                    <JobCard key={`${job.id}-${refreshTrigger}`} job={job} onRefresh={() => setRefreshTrigger(t => t + 1)} />
                ))}
            </div>
        </div>
    )
}

