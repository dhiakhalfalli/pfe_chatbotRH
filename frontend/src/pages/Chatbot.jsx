import { useState, useRef, useEffect, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import {
    Bot, User, Copy, Check, Download, ArrowUp, Zap,
    Plus, MessageSquare, Trash2, ChevronLeft, ChevronRight,
    Search, Clock, Edit3, BookOpen, Sparkles, UserCircle, X, Mail
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'

// ─── LocalStorage helpers ────────────────────────────────────────────────────
function getStorageKey() {
    try {
        const user = JSON.parse(localStorage.getItem('user'))
        const id = user?.email || user?.id || 'default'
        return `hr_chat_sessions_${id.replace(/[^a-z0-9]/gi, '_')}`
    } catch { return 'hr_chat_sessions_default' }
}

function loadSessions() {
    try {
        return JSON.parse(localStorage.getItem(getStorageKey())) || []
    } catch { return [] }
}

function saveSessions(sessions) {
    localStorage.setItem(getStorageKey(), JSON.stringify(sessions))
}

function createSession(title = 'Conversation Récente') {
    const user = JSON.parse(localStorage.getItem('user')) || { role: 'hr' }
    return {
        id: `session_${Date.now()}`,
        title,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        messages: [],
        employeeId: user.role === 'external' ? null : 'emp001',
        candidateId: '',
    }
}

function formatDate(isoString) {
    const d = new Date(isoString)
    const now = new Date()
    const diff = now - d
    if (diff < 60000) return 'À l\'instant'
    if (diff < 3600000) return `Il y a ${Math.floor(diff / 60000)}m`
    if (diff < 86400000) return `Il y a ${Math.floor(diff / 3600000)}h`
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}

// ─── Message Bubble ──────────────────────────────────────────────────────────
function MessageBubble({ msg }) {
    const isUser = msg.role === 'user'
    const [copied, setCopied] = useState(false)

    const handleCopy = () => {
        navigator.clipboard.writeText(msg.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className={`cmsg ${isUser ? 'cmsg-user' : 'cmsg-ai'}`}>
            {!isUser && (
                <div className="cmsg-avatar">
                    <Bot size={16} />
                </div>
            )}
            <div className="cmsg-body">
                {!isUser && (
                    <div className="cmsg-meta">
                        <span className="cmsg-agent">
                            {msg.agent
                                ? msg.agent.replace('_agent', '').replace('_', ' ').toUpperCase() + ' AGENT'
                                : 'HR ASSISTANT'}
                        </span>
                        {msg.intent && msg.intent !== 'welcome' && (
                            <span className="cmsg-intent">
                                <Zap size={9} /> {msg.intent.replace(/_/g, ' ')}
                            </span>
                        )}
                    </div>
                )}
                <div className={`cmsg-bubble ${isUser ? 'cmsg-bubble-user' : 'cmsg-bubble-ai'}`}>
                    <ReactMarkdown
                        components={{
                            p: ({ node, ...props }) => <p style={{ margin: '0 0 8px 0', lineHeight: 1.7 }} {...props} />,
                            ul: ({ node, ...props }) => <ul style={{ margin: '0 0 8px 0', paddingLeft: 18 }} {...props} />,
                            ol: ({ node, ...props }) => <ol style={{ margin: '0 0 8px 0', paddingLeft: 18 }} {...props} />,
                            li: ({ node, ...props }) => <li style={{ marginBottom: 3 }} {...props} />,
                            code: ({ node, inline, ...props }) => inline
                                ? <code style={{ background: 'rgba(99,102,241,0.15)', padding: '1px 5px', borderRadius: 4, fontSize: '0.88em', fontFamily: 'monospace' }} {...props} />
                                : <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '0.75rem', borderRadius: 8, overflow: 'auto', fontSize: 13, fontFamily: 'monospace', margin: '8px 0' }}><code {...props} /></pre>,
                            strong: ({ node, ...props }) => <strong style={{ color: isUser ? 'rgba(255,255,255,0.95)' : 'var(--color-primary-light)', fontWeight: 700 }} {...props} />,
                        }}
                    >
                        {msg.content}
                    </ReactMarkdown>
                    {!isUser && (
                        <button className="cmsg-copy" onClick={handleCopy} title="Copier">
                            {copied ? <Check size={12} color="var(--color-success)" /> : <Copy size={12} />}
                        </button>
                    )}
                </div>
                <div className="cmsg-time">
                    {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                </div>
            </div>
            {isUser && (
                <div className="cmsg-avatar cmsg-avatar-user">
                    <User size={16} />
                </div>
            )}
        </div>
    )
}

// ─── Typing indicator ────────────────────────────────────────────────────────
function TypingIndicator() {
    return (
        <div className="cmsg cmsg-ai">
            <div className="cmsg-avatar"><Bot size={16} /></div>
            <div className="cmsg-body">
                <div className="cmsg-meta"><span className="cmsg-agent">HR ASSISTANT</span></div>
                <div className="cmsg-bubble cmsg-bubble-ai" style={{ width: 'fit-content', paddingRight: '1.125rem' }}>
                    <div className="ctyping">
                        <span /><span /><span />
                    </div>
                </div>
            </div>
        </div>
    )
}

// ─── Main Chatbot Component ──────────────────────────────────────────────────
export default function Chatbot() {
    const user = JSON.parse(localStorage.getItem('user')) || { role: 'hr' }

    // Load candidates for selector
    const { data: candidatesData } = useQuery({
        queryKey: ['candidates'],
        queryFn: () => hrApi.getCandidates(100),
        enabled: user.role === 'hr',
    })
    const candidates = candidatesData?.candidates || []

    // Load jobs for copilot selector
    const { data: jobsData } = useQuery({
        queryKey: ['jobs'],
        queryFn: () => hrApi.getJobs(100),
        enabled: user.role === 'hr',
    })
    const jobs = jobsData?.jobs || []

    // Sessions state
    const [sessions, setSessions] = useState(() => {
        const s = loadSessions()
        if (s.length === 0) {
            const initial = createSession('Conversation Récente')
            saveSessions([initial])
            return [initial]
        }
        return s
    })
    const [activeId, setActiveId] = useState(() => {
        const s = loadSessions()
        return s.length > 0 ? s[0].id : null
    })
    const [sidebarOpen, setSidebarOpen] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [editingId, setEditingId] = useState(null)
    const [editTitle, setEditTitle] = useState('')
    const [input, setInput] = useState('')

    // Copilot Dialog States
    const [activeCopilotAction, setActiveCopilotAction] = useState(null) // 'compare' | 'shortlist' | 'reject' | null
    const [compareC1, setCompareC1] = useState('')
    const [compareC2, setCompareC2] = useState('')
    const [shortlistJob, setShortlistJob] = useState('')
    const [rejectCandidate, setRejectCandidate] = useState('')
    const [rejectJobTitle, setRejectJobTitle] = useState('')
    const [isCopilotPending, setIsCopilotPending] = useState(false)

    const messagesEndRef = useRef(null)
    const textareaRef = useRef(null)
    const editInputRef = useRef(null)

    const activeSession = sessions.find(s => s.id === activeId) || sessions[0]
    const messages = activeSession?.messages || []

    // Scroll to bottom on new message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 140) + 'px'
        }
    }, [input])

    // Focus edit input
    useEffect(() => {
        if (editingId) editInputRef.current?.focus()
    }, [editingId])

    // Persist sessions
    const persistSessions = useCallback((updated) => {
        setSessions(updated)
        saveSessions(updated)
    }, [])

    // Update session helper
    const updateSession = useCallback((id, patch) => {
        setSessions(prev => {
            const updated = prev.map(s => s.id === id ? { ...s, ...patch, updatedAt: new Date().toISOString() } : s)
            saveSessions(updated)
            return updated
        })
    }, [])

    // ─── Chat mutation ───────────────────────────────────────────────────────
    const mutation = useMutation({
        mutationFn: ({ query, session }) =>
            hrApi.queryHR(
                query,
                session.employeeId || null,
                session.candidateId || null,
                session.id,           // thread_id = session ID → backend memory
                { role: user.role, email: user.email, name: user.name }
            ),
        onSuccess: (data, variables) => {
            const aiMsg = {
                id: `ai_${Date.now()}`,
                role: 'assistant',
                content: data.response || JSON.stringify(data.data, null, 2),
                agent: data.agent,
                intent: data.intent,
                timestamp: new Date().toISOString(),
            }
            setSessions(prev => {
                const updated = prev.map(s =>
                    s.id === variables.session.id
                        ? { ...s, messages: [...s.messages, aiMsg], updatedAt: new Date().toISOString() }
                        : s
                )
                saveSessions(updated)
                return updated
            })
        },
        onError: (err, variables) => {
            const errMsg = {
                id: `err_${Date.now()}`,
                role: 'assistant',
                content: `⚠️ **Error:** ${err.message}\n\nAssurez-vous que le serveur backend est lancé sur http://localhost:8000`,
                agent: 'system',
                timestamp: new Date().toISOString(),
            }
            setSessions(prev => {
                const updated = prev.map(s =>
                    s.id === variables.session.id
                        ? { ...s, messages: [...s.messages, errMsg], updatedAt: new Date().toISOString() }
                        : s
                )
                saveSessions(updated)
                return updated
            })
        },
    })

    // ─── Send message ────────────────────────────────────────────────────────
    const sendMessage = useCallback(() => {
        const q = input.trim()
        if (!q || mutation.isPending || !activeSession) return

        const userMsg = {
            id: `user_${Date.now()}`,
            role: 'user',
            content: q,
            timestamp: new Date().toISOString(),
        }

        // Auto-title from first message
        const isFirst = activeSession.messages.length === 0
        const newTitle = isFirst ? q.slice(0, 45) + (q.length > 45 ? '…' : '') : activeSession.title

        setSessions(prev => {
            const updated = prev.map(s =>
                s.id === activeSession.id
                    ? { ...s, messages: [...s.messages, userMsg], title: newTitle, updatedAt: new Date().toISOString() }
                    : s
            )
            saveSessions(updated)
            return updated
        })

        setInput('')
        if (textareaRef.current) textareaRef.current.style.height = 'auto'

        mutation.mutate({ query: q, session: { ...activeSession, title: newTitle } })
    }, [input, mutation, activeSession])

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    // ─── Copilot Action ──────────────────────────────────────────────────────
    const triggerCopilotAction = async () => {
        if (!activeSession) return
        setIsCopilotPending(true)
        try {
            let msgContent = ""
            if (activeCopilotAction === 'compare') {
                if (!compareC1 || !compareC2) {
                    toast.error("Veuillez sélectionner deux candidats")
                    setIsCopilotPending(false)
                    return
                }
                const c1Obj = candidates.find(c => c.id === compareC1)
                const c2Obj = candidates.find(c => c.id === compareC2)
                const comparison = await hrApi.copilotCompare(compareC1, compareC2)
                msgContent = `### 🧠 Comparaison de Candidats : **${c1Obj?.full_name}** vs **${c2Obj?.full_name}**\n\n` + (comparison.response || '')
            } else if (activeCopilotAction === 'shortlist') {
                if (!shortlistJob) {
                    toast.error("Veuillez sélectionner un poste")
                    setIsCopilotPending(false)
                    return
                }
                const jobObj = jobs.find(j => j.id === shortlistJob)
                const shortlist = await hrApi.copilotShortlist(shortlistJob)
                msgContent = `### 📋 Shortlist IA Proposée : **${jobObj?.title}**\n\n` + (shortlist.response || '')
            } else if (activeCopilotAction === 'reject') {
                if (!rejectCandidate || !rejectJobTitle) {
                    toast.error("Veuillez renseigner le candidat et le poste")
                    setIsCopilotPending(false)
                    return
                }
                const candObj = candidates.find(c => c.id === rejectCandidate)
                const rejection = await hrApi.copilotExplainRejection(rejectCandidate, rejectJobTitle)
                msgContent = `### ✉️ Modèle de Refus Constructif : **${candObj?.full_name}** (${rejectJobTitle})\n\n` + (rejection.response || '')
            }

            const copilotMsg = {
                id: `copilot_${Date.now()}`,
                role: 'assistant',
                content: msgContent,
                agent: 'rh_copilot',
                intent: activeCopilotAction,
                timestamp: new Date().toISOString(),
            }

            setSessions(prev => {
                const updated = prev.map(s =>
                    s.id === activeSession.id
                        ? { ...s, messages: [...s.messages, copilotMsg], updatedAt: new Date().toISOString() }
                        : s
                )
                saveSessions(updated)
                return updated
            })

            setActiveCopilotAction(null)
            setCompareC1('')
            setCompareC2('')
            setShortlistJob('')
            setRejectCandidate('')
            setRejectJobTitle('')
            toast.success("Copilot IA exécuté avec succès !")
        } catch (err) {
            toast.error("L'action Copilot a échoué.")
        } finally {
            setIsCopilotPending(false)
        }
    }

    // ─── Session actions ─────────────────────────────────────────────────────
    const newSession = () => {
        const s = createSession('Conversation Récente')
        const updated = [s, ...sessions]
        persistSessions(updated)
        setActiveId(s.id)
        setInput('')
    }

    const deleteSession = (id, e) => {
        e.stopPropagation()
        const updated = sessions.filter(s => s.id !== id)
        if (updated.length === 0) {
            const s = createSession('Conversation Récente')
            persistSessions([s])
            setActiveId(s.id)
        } else {
            persistSessions(updated)
            if (activeId === id) setActiveId(updated[0].id)
        }
    }

    const startEdit = (s, e) => {
        e.stopPropagation()
        setEditingId(s.id)
        setEditTitle(s.title)
    }

    const confirmEdit = (id) => {
        if (editTitle.trim()) updateSession(id, { title: editTitle.trim() })
        setEditingId(null)
    }

    const downloadSession = () => {
        if (!activeSession) return
        const text = activeSession.messages
            .map(m => `[${new Date(m.timestamp).toLocaleTimeString()}] ${m.role.toUpperCase()}: ${m.content}`)
            .join('\n\n')
        const blob = new Blob([text], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `chat-${activeSession.title.slice(0, 20)}-${Date.now()}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    const filteredSessions = sessions.filter(s =>
        s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.messages.some(m => m.content.toLowerCase().includes(searchQuery.toLowerCase()))
    )

    // Group sessions by date
    const today = new Date().toDateString()
    const yesterday = new Date(Date.now() - 86400000).toDateString()

    const groupedSessions = filteredSessions.reduce((acc, s) => {
        const d = new Date(s.updatedAt).toDateString()
        const label = d === today ? 'Aujourd\'hui' : d === yesterday ? 'Hier' : 'Anciennes'
        acc[label] = acc[label] || []
        acc[label].push(s)
        return acc
    }, {})

    return (
        <div className="chatv2">
            {/* ── Sidebar ──────────────────────────────────────────────── */}
            <aside className={`chatv2-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
                <div className="chatv2-sidebar-head">
                    <button className="chatv2-new-btn" onClick={newSession}>
                        <Plus size={16} /> Nouvelle Conversation
                    </button>
                    <button className="chatv2-collapse-btn" onClick={() => setSidebarOpen(false)} title="Close sidebar">
                        <ChevronLeft size={18} />
                    </button>
                </div>

                <div className="chatv2-search-wrapper">
                    <Search size={14} className="chatv2-search-icon" />
                    <input
                        className="chatv2-search"
                        placeholder="Rechercher..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="chatv2-session-list">
                    {Object.entries(groupedSessions).map(([label, list]) => (
                        <div key={label}>
                            <div className="chatv2-group-label">{label}</div>
                            {list.map(s => (
                                <div
                                    key={s.id}
                                    className={`chatv2-session-item ${s.id === activeId ? 'active' : ''}`}
                                    onClick={() => setActiveId(s.id)}
                                >
                                    <MessageSquare size={14} style={{ flexShrink: 0, opacity: 0.6 }} />
                                    <div className="chatv2-session-info">
                                        {editingId === s.id ? (
                                            <input
                                                ref={editInputRef}
                                                className="chatv2-edit-input"
                                                value={editTitle}
                                                onChange={e => setEditTitle(e.target.value)}
                                                onBlur={() => confirmEdit(s.id)}
                                                onKeyDown={e => e.key === 'Enter' && confirmEdit(s.id)}
                                                onClick={e => e.stopPropagation()}
                                            />
                                        ) : (
                                            <span className="chatv2-session-title">{s.title}</span>
                                        )}
                                        <span className="chatv2-session-time">
                                            {s.messages.length} msg · {formatDate(s.updatedAt)}
                                        </span>
                                    </div>
                                    <div className="chatv2-session-actions">
                                        <button onClick={e => startEdit(s, e)} title="Renommer"><Edit3 size={13} /></button>
                                        <button onClick={e => deleteSession(s.id, e)} title="Supprimer"><Trash2 size={13} /></button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ))}
                    {filteredSessions.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)', fontSize: 13 }}>
                            Aucune conversation trouvée
                        </div>
                    )}
                </div>
            </aside>

            {/* ── Main Chat ─────────────────────────────────────────────── */}
            <div className="chatv2-main">
                {/* Top bar */}
                <div className="chatv2-topbar">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        {!sidebarOpen && (
                            <button className="chatv2-icon-btn" onClick={() => setSidebarOpen(true)} title="Open history">
                                <ChevronRight size={18} />
                            </button>
                        )}
                        <div className="chatv2-topbar-icon">
                            <Sparkles size={18} />
                        </div>
                        <div>
                            <div className="chatv2-topbar-title">
                                {activeSession?.title || 'Assistant de Recrutement IA'}
                            </div>
                            <div className="chatv2-topbar-sub">
                                <span className="chatv2-dot" /> Multi-Agents · LangGraph · {messages.length} messages
                            </div>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        {/* Employee context — HR only */}
                        {user.role !== 'external' && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                                <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Employee:</span>
                                <input
                                    className="chatv2-ctx-input"
                                    value={activeSession?.employeeId || ''}
                                    onChange={e => updateSession(activeId, { employeeId: e.target.value })}
                                    placeholder="emp001"
                                />
                            </div>
                        )}
                        {/* Candidate focus selector (HR only) */}
                        {user.role === 'hr' && candidates.length > 0 && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                                <UserCircle size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                                <span style={{ color: 'var(--text-muted)', fontWeight: 600, whiteSpace: 'nowrap' }}>Focus Candidat:</span>
                                <select
                                    className="chatv2-ctx-input"
                                    style={{ maxWidth: 160 }}
                                    value={activeSession?.candidateId || ''}
                                    onChange={e => updateSession(activeId, { candidateId: e.target.value })}
                                >
                                    <option value="">— Aucun —</option>
                                    {candidates.map(c => (
                                        <option key={c.id} value={c.id}>{c.full_name}</option>
                                    ))}
                                </select>
                                {activeSession?.candidateId && (
                                    <button
                                        className="chatv2-icon-btn"
                                        style={{ width: 22, height: 22, padding: 0, border: 'none', opacity: 0.6 }}
                                        onClick={() => updateSession(activeId, { candidateId: '' })}
                                        title="Clear candidate focus"
                                    >
                                        <X size={12} />
                                    </button>
                                )}
                            </div>
                        )}
                        <button className="chatv2-icon-btn" onClick={downloadSession} title="Export chat">
                            <Download size={16} />
                        </button>
                    </div>
                </div>

                {/* Candidate focus banner */}
                {activeSession?.candidateId && (() => {
                    const c = candidates.find(x => x.id === activeSession.candidateId)
                    return c ? (
                        <div style={{ margin: '0 1.25rem 0', padding: '8px 14px', background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                            <UserCircle size={16} color="var(--color-primary-light)" style={{ flexShrink: 0 }} />
                            <span style={{ color: 'var(--text-muted)' }}>Focus sur :</span>
                            <strong style={{ color: 'var(--color-primary-light)' }}>{c.full_name}</strong>
                            {c.score?.total_score && (
                                <span style={{ marginLeft: 4, padding: '2px 8px', background: 'rgba(99,102,241,0.15)', borderRadius: 100, fontSize: 11, fontWeight: 700, color: 'var(--color-primary-light)' }}>
                                    {Math.round(c.score.total_score)}% match
                                </span>
                            )}
                            <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>
                                Tous les messages incluront le profil de ce candidat
                            </span>
                        </div>
                    ) : null
                })()}

                {/* Messages */}
                <div className="chatv2-messages">
                    {messages.length === 0 && (
                        <div className="chatv2-empty">
                            <div className="chatv2-empty-icon">
                                <BookOpen size={32} />
                            </div>
                            <h3>Bienvenue dans votre Assistant IA Recrutement</h3>
                            <p>Posez-moi vos questions sur les candidats, leur score, l'équité IA ou l'analyse des compétences.</p>
                            <div className="chatv2-empty-agents">
                                {['📄 Agent CV', '🛡️ Agent RGPD', '🤝 Agent Matching', '🧠 Copilot IA', '🎤 Agent Entretien'].map(a => (
                                    <span key={a} className="chatv2-agent-tag">{a}</span>
                                ))}
                            </div>
                        </div>
                    )}
                    {messages.map((msg, i) => (
                        <MessageBubble key={msg.id || i} msg={msg} />
                    ))}
                    {mutation.isPending && <TypingIndicator />}
                    <div ref={messagesEndRef} />
                </div>

                {/* Context memory indicator */}
                {messages.length > 0 && (
                    <div className="chatv2-memory-bar">
                        <Clock size={12} />
                        <span>Mémoire : {messages.length} message{messages.length > 1 ? 's' : ''} · Thread ID : {activeSession?.id?.slice(-8)}</span>
                    </div>
                )}

                {/* Copilot Action Pills */}
                {user.role === 'hr' && (
                    <div style={{ display: 'flex', gap: 10, margin: '0 1.25rem 8px', flexWrap: 'wrap' }}>
                        <button 
                            className="btn btn-ghost btn-xs" 
                            style={{ background: 'rgba(99, 102, 241, 0.08)', borderColor: 'rgba(99, 102, 241, 0.25)', fontSize: 12, color: 'var(--color-primary-light)', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
                            onClick={() => setActiveCopilotAction('compare')}
                        >
                            <Sparkles size={13} /> Comparer des candidats
                        </button>
                        <button 
                            className="btn btn-ghost btn-xs" 
                            style={{ background: 'rgba(6, 182, 212, 0.08)', borderColor: 'rgba(6, 182, 212, 0.25)', fontSize: 12, color: '#06b6d4', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
                            onClick={() => setActiveCopilotAction('shortlist')}
                        >
                            <BookOpen size={13} /> Suggérer Shortlist
                        </button>
                        <button 
                            className="btn btn-ghost btn-xs" 
                            style={{ background: 'rgba(245, 158, 11, 0.08)', borderColor: 'rgba(245, 158, 11, 0.25)', fontSize: 12, color: '#f59e0b', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
                            onClick={() => setActiveCopilotAction('reject')}
                        >
                            <Mail size={13} /> Rédiger Refus Éthique
                        </button>
                    </div>
                )}

                {/* Input */}
                <div className="chatv2-input-wrap">
                    <div className="chatv2-input-box">
                        <textarea
                            ref={textareaRef}
                            className="chatv2-textarea"
                            placeholder="Écrivez un message ou lancez un Copilot IA ci-dessus..."
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            rows={1}
                        />
                        <button
                            className={`chatv2-send ${input.trim() ? 'ready' : ''}`}
                            onClick={sendMessage}
                            disabled={!input.trim() || mutation.isPending}
                        >
                            {mutation.isPending
                                ? <div className="spinner" style={{ width: 16, height: 16, borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} />
                                : <ArrowUp size={18} strokeWidth={2.5} />
                            }
                        </button>
                    </div>
                    <div className="chatv2-hint">Entrée pour envoyer · Maj+Entrée pour saut de ligne</div>
                </div>
            </div>

            {/* Sleek Copilot Dialog Modal */}
            {activeCopilotAction && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0, 0, 0, 0.6)', backdropFilter: 'blur(4px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 9999, transition: 'all 0.3s ease'
                }}>
                    <div className="card fade-in" style={{ width: 440, padding: '2rem', background: 'var(--color-bg-glass)', border: '1px solid var(--color-border-hover)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <h3 style={{ fontSize: 18, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-primary)' }}>
                                <Sparkles size={20} color="var(--color-primary-light)" /> 
                                {activeCopilotAction === 'compare' && "Comparer deux Candidats"}
                                {activeCopilotAction === 'shortlist' && "Suggérer Shortlist"}
                                {activeCopilotAction === 'reject' && "Rédiger Refus Éthique"}
                            </h3>
                            <button className="chatv2-icon-btn" onClick={() => setActiveCopilotAction(null)} style={{ border: 'none', background: 'none' }}>
                                <X size={18} />
                            </button>
                        </div>

                        {activeCopilotAction === 'compare' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                                <div className="form-group">
                                    <label className="form-label">Premier candidat</label>
                                    <select className="form-input" value={compareC1} onChange={e => setCompareC1(e.target.value)}>
                                        <option value="">-- Choisir premier candidat --</option>
                                        {candidates.map(c => <option key={c.id} value={c.id}>{c.full_name}</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Second candidat</label>
                                    <select className="form-input" value={compareC2} onChange={e => setCompareC2(e.target.value)}>
                                        <option value="">-- Choisir second candidat --</option>
                                        {candidates.filter(c => c.id !== compareC1).map(c => <option key={c.id} value={c.id}>{c.full_name}</option>)}
                                    </select>
                                </div>
                            </div>
                        )}

                        {activeCopilotAction === 'shortlist' && (
                            <div className="form-group">
                                <label className="form-label">Sélectionner le Poste</label>
                                <select className="form-input" value={shortlistJob} onChange={e => setShortlistJob(e.target.value)}>
                                    <option value="">-- Choisir un poste ouvert --</option>
                                    {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
                                </select>
                            </div>
                        )}

                        {activeCopilotAction === 'reject' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                                <div className="form-group">
                                    <label className="form-label">Candidat concerné</label>
                                    <select className="form-input" value={rejectCandidate} onChange={e => setRejectCandidate(e.target.value)}>
                                        <option value="">-- Choisir le candidat --</option>
                                        {candidates.map(c => <option key={c.id} value={c.id}>{c.full_name}</option>)}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Titre du Poste</label>
                                    <input 
                                        type="text" 
                                        className="form-input" 
                                        placeholder="Ex: Développeur Python"
                                        value={rejectJobTitle} 
                                        onChange={e => setRejectJobTitle(e.target.value)} 
                                    />
                                </div>
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: '2rem' }}>
                            <button className="btn btn-ghost" onClick={() => setActiveCopilotAction(null)}>
                                Annuler
                            </button>
                            <button 
                                className="btn btn-primary" 
                                onClick={triggerCopilotAction}
                                disabled={isCopilotPending}
                            >
                                {isCopilotPending ? "Analyse en cours..." : "Lancer le Copilot IA"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
