import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import {
    LayoutDashboard, Users, MessageSquare, Upload, Calendar,
    BookOpen, DollarSign, CalendarDays, Settings, Cpu, TrendingUp,
    Menu, ChevronLeft, ChevronRight, Search, UserCog, Banknote
} from 'lucide-react'
import Dashboard from './pages/Dashboard.jsx'
import CVUpload from './pages/CVUpload.jsx'
import CandidateRanking from './pages/CandidateRanking.jsx'
import Chatbot from './pages/Chatbot.jsx'
import Employees from './pages/Employees.jsx'
import LeavePortal from './pages/LeavePortal.jsx'
import Login from './pages/Login.jsx'
import Jobs from './pages/Jobs.jsx'
import Payroll from './pages/Payroll.jsx'
import ChatbotPopup from './components/ChatbotPopup.jsx'

const navItems = [
    {
        group: 'Overview', items: [
            { to: '/', label: 'Dashboard', icon: LayoutDashboard },
            { to: '/reports', label: 'Reports', icon: TrendingUp },
        ]
    },
    {
        group: 'Recruitment', items: [
            { to: '/candidates', label: 'Candidates', icon: Users },
            { to: '/jobs', label: 'Job Positions', icon: BookOpen },
            { to: '/cv-analysis', label: 'CV Analysis', icon: Upload },
        ]
    },
    {
        group: 'HR Operations', items: [
            { to: '/employees', label: 'Employees', icon: UserCog },
            { to: '/leave', label: 'Leave Portal', icon: CalendarDays },
            { to: '/payroll', label: 'Payroll', icon: Banknote },
            { to: '/chatbot', label: 'AI Chat Assistant', icon: MessageSquare },
            { to: '/settings', label: 'Settings', icon: Settings },
        ]
    },
]

function Sidebar({ isCollapsed, setIsCollapsed }) {
    const [searchQuery, setSearchQuery] = useState('')

    const filteredNavItems = navItems.map(group => ({
        ...group,
        items: group.items.filter(item => item.label.toLowerCase().includes(searchQuery.toLowerCase()))
    })).filter(group => group.items.length > 0)

    return (
        <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
            <div className="sidebar-logo">
                <div style={{ padding: '0 8px', display: 'flex', alignItems: 'center' }}>
                    <img
                        src="/logo.png"
                        alt="Segula Technologies"
                        style={{ height: '32px', filter: 'drop-shadow(0 2px 8px rgba(99,102,241,0.2))' }}
                        onError={(e) => { e.target.src = '/logo-blue.jpg' }}
                    />
                </div>
                <div className="sidebar-logo-text">
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
                            placeholder="Search..."
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
            <div className="sidebar-toggle-container">
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
                    <span style={{ color: 'var(--color-success)' }}>● </span> 6 Agents Online
                </div>
            </div>
        </aside>
    )
}

// Removed inline ChatbotBubble function in favor of imported ChatbotPopup

export default function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [isCollapsed, setIsCollapsed] = useState(false)

    if (!isAuthenticated) {
        return (
            <BrowserRouter>
                <Login onLogin={setIsAuthenticated} />
            </BrowserRouter>
        )
    }

    return (
        <BrowserRouter>
            <div className={`app-layout ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
                <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
                <main className="main-content">
                    <div className="page-content fade-in">
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/cv-analysis" element={<CVUpload />} />
                            <Route path="/candidates" element={<CandidateRanking />} />
                            <Route path="/chatbot" element={<Chatbot />} />
                            <Route path="/jobs" element={<Jobs />} />
                            <Route path="/reports" element={<div className="page-header"><h1>Reports</h1><p>Coming soon...</p></div>} />
                            <Route path="/settings" element={<div className="page-header"><h1>Settings</h1><p>Coming soon...</p></div>} />
                            {/* Legacy routes mapping just in case */}
                            <Route path="/upload-cv" element={<CVUpload />} />
                            <Route path="/employees" element={<Employees />} />
                            <Route path="/leave" element={<LeavePortal />} />
                            <Route path="/payroll" element={<Payroll />} />
                        </Routes>
                    </div>
                    {/* The Global Footer */}
                    <footer className="global-footer">
                        <img
                            src="/logo.png"
                            alt="Segula Technologies"
                            onError={(e) => { e.target.src = '/logo-blue.jpg' }}
                        />
                        <p>© {new Date().getFullYear()} Segula Technologies - Global Engineering Group. All rights reserved.</p>
                        <p style={{ fontSize: 11, marginTop: 4, opacity: 0.6 }}>Internal HR Intelligence Platform v1.0</p>
                    </footer>
                </main>
                <ChatbotPopup />
            </div>
        </BrowserRouter>
    )
}
