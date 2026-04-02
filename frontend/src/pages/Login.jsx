import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, User, ArrowRight } from 'lucide-react'

export default function Login({ onLogin }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const navigate = useNavigate()

    const handleLogin = (e) => {
        e.preventDefault()
        setIsLoading(true)

        // Simulate authentication
        setTimeout(() => {
            setIsLoading(false)
            onLogin(true)
            navigate('/')
        }, 1200)
    }

    return (
        <div className="login-container">
            {/* Background decoration */}
            <div style={{ position: 'absolute', top: -100, right: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)', borderRadius: '50%' }} />
            <div style={{ position: 'absolute', bottom: -100, left: -100, width: 400, height: 400, background: 'radial-gradient(circle, rgba(6,182,212,0.15) 0%, transparent 70%)', borderRadius: '50%' }} />

            <div className="login-card">
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                    <img
                        src="/logo.png"
                        alt="Segula Technologies Logo"
                        style={{ height: 48, marginBottom: '1.5rem' }}
                        onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = '/logo-blue.jpg';
                        }}
                    />
                    <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>Welcome Back</h1>
                    <p style={{ color: 'var(--text-muted)' }}>Sign in to HR Intelligence Platform</p>
                </div>

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    <div className="form-group">
                        <label className="form-label" style={{ color: 'var(--text-secondary)' }}>Email Address</label>
                        <div style={{ position: 'relative' }}>
                            <User size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="email"
                                className="form-input"
                                placeholder="name@segula.fr"
                                style={{ paddingLeft: '2.75rem' }}
                                value={email}
                                onChange={e => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group" style={{ marginBottom: '0.5rem' }}>
                        <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)' }}>
                            Password
                            <a href="#" style={{ fontSize: 12, fontWeight: 500 }}>Forgot Password?</a>
                        </label>
                        <div style={{ position: 'relative' }}>
                            <Lock size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                type="password"
                                className="form-input"
                                placeholder="••••••••"
                                style={{ paddingLeft: '2.75rem' }}
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary"
                        style={{ width: '100%', padding: '0.875rem', fontSize: 15, marginTop: '0.5rem' }}
                        disabled={isLoading}
                    >
                        {isLoading ? <div className="spinner" style={{ width: 20, height: 20 }} /> : (
                            <>Sign In <ArrowRight size={18} /></>
                        )}
                    </button>
                </form>

                <div style={{ textAlign: 'center', marginTop: '2rem', fontSize: 13, color: 'var(--text-muted)' }}>
                    Secure HR Portal by Segula Technologies
                </div>
            </div>
        </div>
    )
}
