import { useState, useEffect } from 'react'
import { Save, RotateCcw, Plus, X, Info, Sliders, BookOpen, Building2, Award, Bell } from 'lucide-react'
import toast from 'react-hot-toast'

const SETTINGS_KEY = 'hr_platform_settings'

const defaultSettings = {
    scoring: {
        skills:         20,
        experience:     25,
        education:      20,
        certifications: 10,
        github:         10,
        contact:        10,
        communication:  5,
    },
    prestigiousSchools: [
        'Polytechnique', 'Mines', 'INSA', 'Supélec', 'Télécom ParisTech',
        'HEC', 'ESSEC', 'EPFL', 'MIT', 'Stanford', 'Harvard', 'Oxford',
        'ESPRIT', 'ENIS', 'ENSI', "Sup'Com", 'EPT', 'INSAT',
    ],
    notableCompanies: [
        'Google', 'Microsoft', 'Amazon', 'Apple', 'Meta', 'IBM', 'SAP',
        'Oracle', 'Accenture', 'Capgemini', 'Sopra Steria', 'Thales',
        'Airbus', 'Orange', 'Atos', 'Deloitte',
    ],
    recognizedCertifications: [
        'AWS', 'Azure', 'GCP', 'Google Cloud', 'Cisco', 'CCNA', 'CCNP',
        'PMP', 'Scrum Master', 'Kubernetes', 'CKA', 'CKAD',
        'Terraform', 'Docker', 'CompTIA', 'Security+', 'OSCP',
    ],
    preferences: {
        language: 'fr',
        emailNotifications: true,
        autoScore: true,
        exportFormat: 'json',
    }
}

function loadSettings() {
    try {
        const s = JSON.parse(localStorage.getItem(SETTINGS_KEY))
        if (!s) return defaultSettings
        return {
            ...defaultSettings,
            ...s,
            scoring: { ...defaultSettings.scoring, ...s.scoring },
            preferences: { ...defaultSettings.preferences, ...s.preferences },
        }
    } catch { return defaultSettings }
}

function saveSettings(s) {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(s))
}

// ── Tag list editor ────────────────────────────────────────────────────────────
function TagEditor({ label, items, onChange, color = '#6366f1' }) {
    const [input, setInput] = useState('')

    const add = () => {
        const v = input.trim()
        if (v && !items.includes(v)) { onChange([...items, v]); setInput('') }
    }

    return (
        <div style={{ marginBottom: '1.5rem' }}>
            <label className="form-label">{label} <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: 12 }}>({items.length})</span></label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
                {items.map((item, i) => (
                    <span key={i} style={{
                        display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px',
                        background: `${color}20`, border: `1px solid ${color}50`,
                        borderRadius: 100, fontSize: 12, fontWeight: 600, color,
                    }}>
                        {item}
                        <button onClick={() => onChange(items.filter((_, j) => j !== i))}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color, padding: 0, lineHeight: 1 }}>
                            <X size={11} />
                        </button>
                    </span>
                ))}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
                <input
                    className="form-input"
                    style={{ flex: 1 }}
                    placeholder={`Add ${label.toLowerCase().split(' ')[0]}…`}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && add()}
                />
                <button className="btn btn-secondary btn-sm" onClick={add} style={{ width: 40 }}>
                    <Plus size={16} />
                </button>
            </div>
        </div>
    )
}

// ── Weight slider ──────────────────────────────────────────────────────────────
function WeightSlider({ label, value, onChange, color = '#6366f1' }) {
    return (
        <div style={{ marginBottom: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <label style={{ fontSize: 13, fontWeight: 600 }}>{label}</label>
                <span style={{ fontSize: 13, fontWeight: 800, color }}>{value}%</span>
            </div>
            <input
                type="range"
                min={0} max={50} step={1}
                value={value}
                onChange={e => onChange(Number(e.target.value))}
                style={{ width: '100%', accentColor: color }}
            />
        </div>
    )
}

// ── Section wrapper ────────────────────────────────────────────────────────────
function Section({ icon: Icon, title, color = '#6366f1', children }) {
    return (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: 15, fontWeight: 700, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 32, height: 32, borderRadius: 'var(--radius-sm)', background: `${color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', color }}>
                    <Icon size={16} />
                </div>
                {title}
            </h2>
            {children}
        </div>
    )
}

export default function Settings() {
    const [settings, setSettings] = useState(loadSettings)
    const [dirty, setDirty] = useState(false)

    const update = (path, value) => {
        setSettings(prev => {
            const next = { ...prev }
            const keys = path.split('.')
            let cur = next
            for (let i = 0; i < keys.length - 1; i++) { cur[keys[i]] = { ...cur[keys[i]] }; cur = cur[keys[i]] }
            cur[keys[keys.length - 1]] = value
            return next
        })
        setDirty(true)
    }

    const totalWeight = Object.values(settings.scoring).reduce((a, b) => a + b, 0)
    const weightColor = Math.abs(totalWeight - 100) <= 1 ? '#10b981' : totalWeight > 100 ? '#ef4444' : '#f59e0b'

    const handleSave = () => {
        saveSettings(settings)
        setDirty(false)
        toast.success('Settings saved successfully!')
    }

    const handleReset = () => {
        setSettings(defaultSettings)
        saveSettings(defaultSettings)
        setDirty(false)
        toast.success('Settings reset to defaults')
    }

    return (
        <div>
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>Platform Settings</h1>
                    <p>Configure scoring weights, reference data and platform preferences</p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-ghost btn-sm" onClick={handleReset}>
                        <RotateCcw size={14} /> Reset Defaults
                    </button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={!dirty} style={{ opacity: dirty ? 1 : 0.5 }}>
                        <Save size={16} /> Save Settings
                    </button>
                </div>
            </div>

            {/* ── Scoring Weights ─────────────────────────────────────────────── */}
            <Section icon={Sliders} title="CV Quality Scoring Weights (RF-20)" color="#6366f1">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: '1.5rem', padding: '12px 16px', borderRadius: 'var(--radius-md)', background: totalWeight === 100 ? 'rgba(16,185,129,0.08)' : 'rgba(245,158,11,0.08)', border: `1px solid ${weightColor}40` }}>
                    <Info size={16} color={weightColor} />
                    <span style={{ fontSize: 13, color: weightColor, fontWeight: 600 }}>
                        Total weight: <strong>{totalWeight}%</strong>
                        {totalWeight !== 100 && ` — ${totalWeight > 100 ? 'reduce' : 'increase'} by ${Math.abs(totalWeight - 100)}% to reach 100%`}
                    </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 2rem' }}>
                    <WeightSlider label="📊 Skills Breadth (RF-07)"         value={settings.scoring.skills}          onChange={v => update('scoring.skills', v)}          color="#6366f1" />
                    <WeightSlider label="📈 Experience Quality (RF-05, RF-09)" value={settings.scoring.experience}  onChange={v => update('scoring.experience', v)}      color="#f59e0b" />
                    <WeightSlider label="🎓 Education (RF-06, RF-10)"        value={settings.scoring.education}       onChange={v => update('scoring.education', v)}       color="#10b981" />
                    <WeightSlider label="🏅 Certifications (RF-11)"          value={settings.scoring.certifications}  onChange={v => update('scoring.certifications', v)}  color="#06b6d4" />
                    <WeightSlider label="⚙️ GitHub / Portfolio (RF-08, RF-13)" value={settings.scoring.github}       onChange={v => update('scoring.github', v)}          color="#ec4899" />
                    <WeightSlider label="📞 Contact Completeness (RF-04)"    value={settings.scoring.contact}         onChange={v => update('scoring.contact', v)}         color="#8b5cf6" />
                    <WeightSlider label="💬 Communication (RF-17)"           value={settings.scoring.communication}   onChange={v => update('scoring.communication', v)}   color="#f97316" />
                </div>
            </Section>

            {/* ── Reference Lists ─────────────────────────────────────────────── */}
            <Section icon={BookOpen} title="Prestigious Schools (RF-10)" color="#10b981">
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Candidates from these institutions receive a +15 point education bonus.
                </p>
                <TagEditor
                    label="Schools & Universities"
                    items={settings.prestigiousSchools}
                    onChange={v => update('prestigiousSchools', v)}
                    color="#10b981"
                />
            </Section>

            <Section icon={Building2} title="Notable Companies (RF-09)" color="#f59e0b">
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Experience at these companies earns a +10 point experience bonus (max +20).
                </p>
                <TagEditor
                    label="Companies"
                    items={settings.notableCompanies}
                    onChange={v => update('notableCompanies', v)}
                    color="#f59e0b"
                />
            </Section>

            <Section icon={Award} title="Recognized Certifications (RF-11)" color="#06b6d4">
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Each recognized certification adds +25 points to the certification score (max 100).
                </p>
                <TagEditor
                    label="Certifications"
                    items={settings.recognizedCertifications}
                    onChange={v => update('recognizedCertifications', v)}
                    color="#06b6d4"
                />
            </Section>

            {/* ── Platform Preferences ─────────────────────────────────────────── */}
            <Section icon={Bell} title="Platform Preferences" color="#8b5cf6">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>

                    <div className="form-group">
                        <label className="form-label">Interface Language</label>
                        <select className="form-input" value={settings.preferences.language}
                            onChange={e => update('preferences.language', e.target.value)}>
                            <option value="fr">🇫🇷 Français</option>
                            <option value="en">🇬🇧 English</option>
                            <option value="ar">🇹🇳 العربية</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Default Export Format</label>
                        <select className="form-input" value={settings.preferences.exportFormat}
                            onChange={e => update('preferences.exportFormat', e.target.value)}>
                            <option value="json">JSON</option>
                            <option value="csv">CSV / Excel</option>
                            <option value="pdf">PDF Report</option>
                        </select>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: 'var(--color-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                        <input type="checkbox" id="autoScore" checked={settings.preferences.autoScore}
                            onChange={e => update('preferences.autoScore', e.target.checked)}
                            style={{ width: 16, height: 16, accentColor: '#6366f1' }} />
                        <div>
                            <label htmlFor="autoScore" style={{ cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>Auto-score on CV upload</label>
                            <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: 0 }}>Automatically compute quality score when CVs are uploaded</p>
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', background: 'var(--color-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                        <input type="checkbox" id="emailNotif" checked={settings.preferences.emailNotifications}
                            onChange={e => update('preferences.emailNotifications', e.target.checked)}
                            style={{ width: 16, height: 16, accentColor: '#6366f1' }} />
                        <div>
                            <label htmlFor="emailNotif" style={{ cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>Email Notifications</label>
                            <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: 0 }}>Receive alerts for new candidates and anomalies detected</p>
                        </div>
                    </div>
                </div>
            </Section>

            {dirty && (
                <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 999 }}>
                    <button className="btn btn-primary" onClick={handleSave} style={{ boxShadow: '0 8px 32px rgba(99,102,241,0.4)' }}>
                        <Save size={16} /> Save Changes
                    </button>
                </div>
            )}
        </div>
    )
}
