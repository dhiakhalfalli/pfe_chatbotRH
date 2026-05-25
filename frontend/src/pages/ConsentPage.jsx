import { useState, useEffect } from 'react'
import { Shield, CheckCircle, XCircle, AlertTriangle, Lock, Trash2, Eye, Clock } from 'lucide-react'

const API_BASE = 'http://localhost:8000'

export default function ConsentPage() {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    const candidateId = user?.candidate_id || user?.id || null

    const [consentDetails, setConsentDetails] = useState(null)
    const [consentStatus, setConsentStatus] = useState(null) // 'accepted' | 'refused' | null
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState(null)
    const [hasConsented, setHasConsented] = useState(
        localStorage.getItem('gdpr_consent') === 'true'
    )

    useEffect(() => {
        fetchConsentDetails()
    }, [])

    const fetchConsentDetails = async () => {
        try {
            const res = await fetch(`${API_BASE}/consent/request${candidateId ? `?candidate_id=${candidateId}` : ''}`)
            if (res.ok) {
                const data = await res.json()
                setConsentDetails(data)
            }
        } catch {
            // Fallback statique si le backend est indisponible
            setConsentDetails({
                message: "Avant d'analyser votre candidature, nous avons besoin de votre consentement pour l'utilisation temporaire de vos données personnelles.",
                details: {
                    purpose: "Analyse intelligente du profil et classement des candidatures",
                    data_used: ["Compétences", "Expériences", "Formations", "Certifications"],
                    data_masked_from_ai: ["Nom complet", "Email", "Téléphone", "Photo"],
                    retention_period: "72 heures après traitement",
                    your_rights: ["Accès", "Rectification", "Effacement (Art. 17 RGPD)", "Retrait du consentement"],
                    legal_basis: "Consentement explicite – Article 6(1)(a) RGPD",
                }
            })
        }
    }

    const handleConsent = async (accepted) => {
        setLoading(true)
        try {
            if (candidateId) {
                await fetch(`${API_BASE}/consent`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        candidate_id: candidateId,
                        consented: accepted,
                    })
                })
            }
            localStorage.setItem('gdpr_consent', accepted ? 'true' : 'false')
            setHasConsented(accepted)
            setConsentStatus(accepted ? 'accepted' : 'refused')
            setMessage(accepted
                ? "✅ Consentement enregistré. Vos données seront supprimées automatiquement après 72h."
                : "❌ Consentement refusé. Aucune donnée personnelle ne sera traitée par nos systèmes IA."
            )
        } catch {
            setMessage("⚠️ Erreur lors de l'enregistrement. Veuillez réessayer.")
        } finally {
            setLoading(false)
        }
    }

    const handleDeleteData = async () => {
        if (!candidateId) {
            setMessage("⚠️ Aucun profil candidat associé à ce compte.")
            return
        }
        setLoading(true)
        try {
            const res = await fetch(`${API_BASE}/candidates/${candidateId}/anonymize`, { method: 'POST' })
            if (res.ok) {
                localStorage.removeItem('gdpr_consent')
                setHasConsented(false)
                setConsentStatus('refused')
                setMessage("🗑️ Vos données personnelles ont été anonymisées conformément au RGPD (Art. 17).")
            }
        } catch {
            setMessage("⚠️ Erreur lors de la suppression. Contactez notre DPO.")
        } finally {
            setLoading(false)
        }
    }

    const d = consentDetails?.details

    return (
        <div style={{ maxWidth: 760, margin: '0 auto', padding: '2rem 1rem' }}>

            {/* Header */}
            <div style={{
                background: 'linear-gradient(135deg, var(--color-primary), #7c3aed)',
                borderRadius: 16,
                padding: '2rem',
                marginBottom: '1.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                color: '#fff',
            }}>
                <div style={{
                    background: 'rgba(255,255,255,0.15)',
                    borderRadius: 12,
                    padding: 14,
                    flexShrink: 0,
                }}>
                    <Shield size={32} />
                </div>
                <div>
                    <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>
                        Protection des Données Personnelles
                    </h1>
                    <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
                        Conformité RGPD – Règlement Général sur la Protection des Données
                    </p>
                </div>
            </div>

            {/* Message de feedback */}
            {message && (
                <div style={{
                    background: consentStatus === 'accepted'
                        ? 'rgba(16,185,129,0.12)'
                        : consentStatus === 'refused'
                        ? 'rgba(239,68,68,0.12)'
                        : 'rgba(245,158,11,0.12)',
                    border: `1px solid ${consentStatus === 'accepted' ? 'rgba(16,185,129,0.4)' : consentStatus === 'refused' ? 'rgba(239,68,68,0.4)' : 'rgba(245,158,11,0.4)'}`,
                    borderRadius: 10,
                    padding: '1rem 1.25rem',
                    marginBottom: '1.5rem',
                    fontSize: '0.9rem',
                    color: 'var(--text-primary)',
                }}>
                    {message}
                </div>
            )}

            {/* Message principal */}
            <div className="card" style={{ marginBottom: '1rem', padding: '1.5rem' }}>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                    <AlertTriangle size={20} style={{ color: 'var(--color-warning)', flexShrink: 0, marginTop: 2 }} />
                    <p style={{ margin: 0, lineHeight: 1.7, color: 'var(--text-primary)' }}>
                        {consentDetails?.message || "Chargement..."}
                    </p>
                </div>
            </div>

            {d && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>

                    {/* Données utilisées */}
                    <div className="card" style={{ padding: '1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.75rem' }}>
                            <Eye size={16} style={{ color: 'var(--color-primary)' }} />
                            <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Données analysées</h3>
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                            {d.data_used?.map(item => (
                                <li key={item} style={{ marginBottom: 4 }}>
                                    <span style={{ color: 'var(--color-success)' }}>✓ </span>{item}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Données masquées */}
                    <div className="card" style={{ padding: '1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.75rem' }}>
                            <Lock size={16} style={{ color: 'var(--color-success)' }} />
                            <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Données masquées avant IA</h3>
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                            {d.data_masked_from_ai?.map(item => (
                                <li key={item} style={{ marginBottom: 4 }}>
                                    <span style={{ color: 'var(--color-primary)' }}>🔒 </span>{item}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Durée de conservation */}
                    <div className="card" style={{ padding: '1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.75rem' }}>
                            <Clock size={16} style={{ color: 'var(--color-warning)' }} />
                            <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Conservation</h3>
                        </div>
                        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                            Vos données seront supprimées automatiquement <strong>{d.retention_period}</strong>.
                        </p>
                        <p style={{ margin: '0.5rem 0 0', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                            Base légale : {d.legal_basis}
                        </p>
                    </div>

                    {/* Vos droits */}
                    <div className="card" style={{ padding: '1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.75rem' }}>
                            <Shield size={16} style={{ color: 'var(--color-primary)' }} />
                            <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Vos droits</h3>
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                            {d.your_rights?.map(right => (
                                <li key={right} style={{ marginBottom: 4 }}>{right}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}

            {/* Statut actuel */}
            {hasConsented && !consentStatus && (
                <div className="card" style={{
                    padding: '1rem 1.25rem',
                    marginBottom: '1rem',
                    background: 'rgba(16,185,129,0.08)',
                    border: '1px solid rgba(16,185,129,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                }}>
                    <CheckCircle size={18} style={{ color: 'var(--color-success)' }} />
                    <span style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                        Vous avez déjà donné votre consentement. Vos données seront supprimées automatiquement après 72h.
                    </span>
                </div>
            )}

            {/* Boutons d'action */}
            {!consentStatus && (
                <div className="card" style={{ padding: '1.5rem' }}>
                    <p style={{ margin: '0 0 1rem', fontWeight: 600, fontSize: '0.95rem' }}>
                        Votre décision :
                    </p>
                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <button
                            onClick={() => handleConsent(true)}
                            disabled={loading}
                            style={{
                                flex: 1,
                                minWidth: 160,
                                padding: '0.85rem 1.5rem',
                                borderRadius: 10,
                                border: 'none',
                                background: 'linear-gradient(135deg, var(--color-success), #059669)',
                                color: '#fff',
                                fontWeight: 600,
                                fontSize: '0.95rem',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 8,
                                transition: 'opacity 0.2s',
                                opacity: loading ? 0.7 : 1,
                            }}
                        >
                            <CheckCircle size={18} />
                            J'accepte
                        </button>
                        <button
                            onClick={() => handleConsent(false)}
                            disabled={loading}
                            style={{
                                flex: 1,
                                minWidth: 160,
                                padding: '0.85rem 1.5rem',
                                borderRadius: 10,
                                border: '1px solid var(--border-color)',
                                background: 'transparent',
                                color: 'var(--text-secondary)',
                                fontWeight: 600,
                                fontSize: '0.95rem',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 8,
                                opacity: loading ? 0.7 : 1,
                            }}
                        >
                            <XCircle size={18} />
                            Je refuse
                        </button>
                    </div>
                    <p style={{ margin: '0.75rem 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        En acceptant, vous autorisez l'analyse temporaire de votre profil par nos agents IA.
                        Vous pouvez retirer votre consentement à tout moment.
                    </p>
                </div>
            )}

            {/* Supprimer mes données */}
            {(hasConsented || consentStatus === 'accepted') && candidateId && (
                <div className="card" style={{
                    padding: '1.25rem',
                    marginTop: '1rem',
                    border: '1px solid rgba(239,68,68,0.3)',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: '0.5rem' }}>
                        <Trash2 size={16} style={{ color: '#ef4444' }} />
                        <strong style={{ fontSize: '0.9rem', color: '#ef4444' }}>Droit à l'effacement (Art. 17 RGPD)</strong>
                    </div>
                    <p style={{ margin: '0 0 0.75rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        Supprimer immédiatement vos données personnelles (nom, email, téléphone, photo).
                        Vos compétences et score seront conservés de façon anonyme.
                    </p>
                    <button
                        onClick={handleDeleteData}
                        disabled={loading}
                        style={{
                            padding: '0.6rem 1.2rem',
                            borderRadius: 8,
                            border: '1px solid rgba(239,68,68,0.5)',
                            background: 'rgba(239,68,68,0.08)',
                            color: '#ef4444',
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                        }}
                    >
                        <Trash2 size={14} />
                        Supprimer mes données personnelles
                    </button>
                </div>
            )}
        </div>
    )
}
