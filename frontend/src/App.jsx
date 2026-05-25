import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import {
    LayoutDashboard, Users, MessageSquare, Upload,
    BookOpen, Settings as SettingsIcon, Cpu, TrendingUp,
    Menu, ChevronLeft, ChevronRight, Search, Shield,
    Sun, Moon, LogOut, UserCheck, Bell, X
} from 'lucide-react'
import toast from 'react-hot-toast'
import Dashboard from './pages/Dashboard.jsx'
import CVUpload from './pages/CVUpload.jsx'
import CandidateRanking from './pages/CandidateRanking.jsx'
import Chatbot from './pages/Chatbot.jsx'
import Login from './pages/Login.jsx'
import Jobs from './pages/Jobs.jsx'
import CandidateDetail from './pages/CandidateDetail.jsx'
import Reports from './pages/Reports.jsx'
import Settings from './pages/Settings.jsx'
import ConsentPage from './pages/ConsentPage.jsx'
import ChatbotPopup from './components/ChatbotPopup.jsx'

const navItems = [
    {
        group: 'Recrutement', items: [
            { to: '/', label: 'Tableau de bord', icon: LayoutDashboard, roles: ['hr', 'external'] },
            { to: '/reports', label: 'Rapports', icon: TrendingUp, roles: ['hr'] },
            { to: '/candidates', label: 'Candidats', icon: Users, roles: ['hr'] },
            { to: '/jobs', label: 'Offres d\'emploi', icon: BookOpen, roles: ['hr'] },
            { to: '/cv-analysis', label: 'Analyser un CV', icon: Upload, roles: ['hr'] },
        ]
    },
    {
        group: 'Espace Candidat', items: [
            { to: '/cv-analysis', label: 'Déposer mon CV', icon: Upload, roles: ['external'] },
            { to: '/chatbot', label: 'Mon Assistant IA', icon: MessageSquare, roles: ['external'] },
        ]
    },
    {
        group: 'Outils IA', items: [
            { to: '/chatbot', label: 'Assistant RH IA', icon: MessageSquare, roles: ['hr'] },
            { to: '/consent', label: 'Consentement RGPD', icon: Shield, roles: ['hr', 'external'] },
            { to: '/settings', label: 'Paramètres', icon: SettingsIcon, roles: ['hr'] },
        ]
    },
]

function Sidebar({ isCollapsed, setIsCollapsed, theme, toggleTheme, userRole, onLogout }) {
    const [searchQuery, setSearchQuery] = useState('')

    const filteredNavItems = navItems.map(group => ({
        ...group,
        items: group.items.filter(item => 
            item.label.toLowerCase().includes(searchQuery.toLowerCase()) &&
            item.roles.includes(userRole)
        )
    })).filter(group => group.items.length > 0)

    return (
        <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-logo" style={{ flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: 8 }}>
                <img
                    src="/logo.png"
                    alt="Segula Technologies"
                    style={{ height: '36px', filter: 'drop-shadow(0 2px 8px rgba(99,102,241,0.2))' }}
                    onError={(e) => { e.target.src = '/logo-blue.jpg' }}
                />
                <div className="sidebar-logo-text" style={{ textAlign: 'center' }}>
                    <div className="title">HR Intelligence</div>
                    <div className="subtitle" style={{ color: 'var(--color-primary-light)' }}>Global Engineering Group</div>
                </div>
            </div>

            <div className={`sidebar-search ${isCollapsed ? 'collapsed' : ''}`}>
                <div className="search-input-wrapper">
                    <Search className="search-icon" size={16} />
                    {!isCollapsed && (
                        <input
                            type="text"
                            placeholder="Rechercher..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="sidebar-search-input"
                        />
                    )}
                </div>
            </div>

            <nav className="sidebar-nav">
                {filteredNavItems.map(({ group, items }) => (
                    <div key={group}>
                        <div className="nav-section-label">{group}</div>
                        {items.map(({ to, label, icon: Icon }) => (
                            <NavLink
                                key={to}
                                to={to}
                                end={to === '/'}
                                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                                title={isCollapsed ? label : ""}
                            >
                                <Icon className="nav-icon" size={20} />
                                <span className="nav-label">{label}</span>
                            </NavLink>
                        ))}
                    </div>
                ))}
            </nav>
            <div className="sidebar-toggle-container" style={{ gap: '8px' }}>
                <button
                    className="sidebar-toggle"
                    onClick={toggleTheme}
                    title={theme === 'dark' ? "Mode Clair" : "Mode Sombre"}
                    aria-label="Toggle theme"
                >
                    {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                </button>
                <button
                    className="sidebar-toggle"
                    onClick={onLogout}
                    title="Déconnexion"
                    aria-label="Logout"
                >
                    <LogOut size={18} />
                </button>
                <button
                    className="sidebar-toggle"
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
            </div>

            <div className="sidebar-footer">
                <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
                    <span style={{ color: 'var(--color-success)' }}>● </span> 6 Agents IA Actifs
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 4 }}>
                    🔒 Conforme RGPD
                </div>
            </div>
        </aside>
    )
}

export default function App() {
    const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null)
    const [isCollapsed, setIsCollapsed] = useState(false)
    const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark')
    const [notifications, setNotifications] = useState([])
    const [isNotifOpen, setIsNotifOpen] = useState(false)

    const toggleTheme = () => {
        const newTheme = theme === 'dark' ? 'light' : 'dark'
        setTheme(newTheme)
        localStorage.setItem('theme', newTheme)
    }

    const handleLogout = () => {
        setUser(null)
        localStorage.removeItem('user')
    }

    const handleLogin = (userData) => {
        setUser(userData)
        localStorage.setItem('user', JSON.stringify(userData))
    }

    // Charger les notifications initiales
    useEffect(() => {
        if (!user) return
        const recipient = user.role === 'hr' ? 'hr' : user.id || 'candidate'
        fetch(`http://localhost:8000/notifications/${recipient}`)
            .then(res => res.json())
            .then(data => {
                if (data.notifications) {
                    setNotifications(data.notifications)
                }
            })
            .catch(err => console.error("Erreur de chargement des notifications:", err))
    }, [user])

    // Écouter les notifications SSE en temps réel
    useEffect(() => {
        if (!user) return
        const recipient = user.role === 'hr' ? 'hr' : user.id || 'candidate'
        const es = new EventSource(`http://localhost:8000/notifications/stream/${recipient}`)

        es.onmessage = (event) => {
            try {
                const notif = JSON.parse(event.data)
                setNotifications(prev => [notif, ...prev])

                toast.custom((t) => (
                    <div className="toast-card" style={{ 
                        borderLeft: `4px solid ${notif.type === 'duplicate_warning' ? 'var(--color-danger)' : 'var(--color-success)'}`,
                        opacity: t.visible ? 1 : 0,
                        transition: 'opacity 0.3s ease-in-out'
                    }}>
                        <Bell size={18} style={{ color: notif.type === 'duplicate_warning' ? 'var(--color-danger)' : 'var(--color-success)' }} />
                        <div>
                            <div style={{ fontWeight: 700, fontSize: 13 }}>{notif.title}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{notif.message}</div>
                        </div>
                    </div>
                ), { duration: 5000 })
            } catch (err) {
                console.error("SSE parsing error:", err)
            }
        }

        return () => {
            es.close()
        }
    }, [user])

    const handleMarkAsRead = async (notifId) => {
        try {
            await fetch(`http://localhost:8000/notifications/${notifId}/read`, { method: 'POST' })
            setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, is_read: true } : n))
        } catch (err) {
            console.error("Error marking read:", err)
        }
    }

    const handleMarkAllRead = async () => {
        if (!user) return
        const recipient = user.role === 'hr' ? 'hr' : user.id || 'candidate'
        try {
            await fetch(`http://localhost:8000/notifications/read-all/${recipient}`, { method: 'POST' })
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
        } catch (err) {
            console.error("Error marking all read:", err)
        }
    }

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme)
    }, [theme])

    if (!user) {
        return (
            <BrowserRouter>
                <Login onLogin={handleLogin} />
            </BrowserRouter>
        )
    }

    const unreadCount = notifications.filter(n => !n.is_read).length

    return (
        <BrowserRouter>
            <div className={`app-layout ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
                <Sidebar 
                    isCollapsed={isCollapsed} 
                    setIsCollapsed={setIsCollapsed} 
                    theme={theme} 
                    toggleTheme={toggleTheme} 
                    userRole={user.role}
                    onLogout={handleLogout}
                />
                
                {/* Bell Button Absolue */}
                <div className="notif-bell-container">
                    <button className="notif-bell-btn" onClick={() => setIsNotifOpen(!isNotifOpen)} title="Notifications">
                        <Bell size={20} />
                        {unreadCount > 0 && <span className="notif-badge">{unreadCount}</span>}
                    </button>
                </div>

                {/* Sliding notifications drawer */}
                <div className={`notif-drawer ${isNotifOpen ? 'open' : ''}`}>
                    <div className="notif-drawer-header">
                        <h3>Notifications Temps Réel</h3>
                        <button className="notif-close-btn" onClick={() => setIsNotifOpen(false)}>
                            <X size={20} />
                        </button>
                    </div>
                    <div className="notif-list">
                        {notifications.length === 0 ? (
                            <div className="notif-empty">
                                <Bell size={32} />
                                <span>Aucune notification pour le moment.</span>
                            </div>
                        ) : (
                            notifications.map(n => (
                                <div 
                                    key={n.id} 
                                    className={`notif-item ${!n.is_read ? 'unread' : ''}`}
                                    onClick={() => handleMarkAsRead(n.id)}
                                    style={{ borderLeftColor: n.type === 'duplicate_warning' ? 'var(--color-danger)' : n.type === 'cv_upload' ? 'var(--color-success)' : 'var(--color-primary)' }}
                                >
                                    <div className="notif-item-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        {n.type === 'duplicate_warning' ? '⚠️' : n.type === 'cv_upload' ? '📥' : '🔔'}
                                        {n.title}
                                    </div>
                                    <div className="notif-item-desc">{n.message}</div>
                                    <div className="notif-item-time">{new Date(n.timestamp).toLocaleTimeString()}</div>
                                </div>
                            ))
                        )}
                    </div>
                    {notifications.length > 0 && (
                        <div className="notif-actions">
                            <button className="btn btn-secondary btn-sm" onClick={handleMarkAllRead}>Tout marquer comme lu</button>
                        </div>
                    )}
                </div>

                <main className="main-content">
                    <div className="page-content fade-in">
                        <Routes>
                            <Route path="/" element={<Dashboard user={user} />} />
                            <Route path="/cv-analysis" element={<CVUpload />} />
                            <Route path="/candidates" element={<CandidateRanking />} />
                            <Route path="/candidates/:id" element={<CandidateDetail />} />
                            <Route path="/chatbot" element={<Chatbot />} />
                            <Route path="/jobs" element={<Jobs />} />
                            <Route path="/reports" element={<Reports />} />
                            <Route path="/settings" element={<Settings />} />
                            <Route path="/consent" element={<ConsentPage />} />
                            <Route path="/upload-cv" element={<CVUpload />} />
                        </Routes>
                    </div>
                </main>
                <ChatbotPopup />
            </div>
        </BrowserRouter>
    )
}
