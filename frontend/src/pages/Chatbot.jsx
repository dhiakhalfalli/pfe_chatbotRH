import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import { Send, Cpu, Zap, MessageSquare, Bot, User, Copy, Download, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const QUICK_PROMPTS = [
    'What are Segula benefits?',
    'How to apply for a job?',
    'Leave policy',
    'Generate Python interview questions',
]

const WELCOME_MSG = {
    id: 'welcome',
    role: 'assistant',
    content: `👋 Welcome to the **HR Intelligence Assistant**!

I'm powered by 6 specialized AI agents:

• 📄 **CV Agent** – Analyse and score candidate CVs
• 🎤 **Interview Agent** – Generate interview questions  
• 🚀 **Onboarding Agent** – Create employee onboarding plans
• 📚 **Training Agent** – Recommend learning programs
• 💰 **Payroll Agent** – Answer salary & compensation questions
• 🏖️ **Leave Agent** – Manage vacation and time off

How can I help you today?
      
**Pro Tip:** You can select a candidate from the dropdown above to focus our discussion on their specific profile and skills!`,
    agent: 'system',
    intent: 'welcome',
    timestamp: new Date(),
}

function MessageBubble({ msg }) {
    const isUser = msg.role === 'user'
    const [copied, setCopied] = useState(false)

    const handleCopy = () => {
        navigator.clipboard.writeText(msg.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className={`message ${isUser ? 'user' : 'assistant'}`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
                {!isUser ? (
                    <>
                        <div className="avatar" style={{ width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--gradient-primary)', borderRadius: '50%', color: 'white' }}>
                            <Bot size={16} />
                        </div>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>
                            {msg.agent ? `${msg.agent.replace('_agent', '').replace('_', ' ').toUpperCase()} AGENT` : 'AI ASSISTANT'}
                        </span>
                        {msg.intent && msg.intent !== 'welcome' && (
                            <span className="badge badge-indigo" style={{ fontSize: 10 }}>
                                <Zap size={8} /> {msg.intent.replace('_', ' ')}
                            </span>
                        )}
                    </>
                ) : (
                    <>
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>YOU</span>
                        <div className="avatar" style={{ width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(99, 102, 241, 0.2)', borderRadius: '50%', color: 'var(--text-primary)' }}>
                            <User size={16} />
                        </div>
                    </>
                )}
            </div>
            <div className="message-bubble" style={{ position: 'relative', paddingRight: !isUser ? '2rem' : '1rem' }}>
                <ReactMarkdown
                    components={{
                        p: ({ node, ...props }) => <p style={{ margin: '0 0 10px 0', lineHeight: 1.6 }} {...props} />,
                        ul: ({ node, ...props }) => <ul style={{ margin: '0 0 10px 0', paddingLeft: 20 }} {...props} />,
                        ol: ({ node, ...props }) => <ol style={{ margin: '0 0 10px 0', paddingLeft: 20 }} {...props} />,
                        li: ({ node, ...props }) => <li style={{ marginBottom: 4 }} {...props} />,
                        pre: ({ node, ...props }) => <pre style={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', margin: 0, lineHeight: 1.6 }} {...props} />
                    }}
                >
                    {msg.content}
                </ReactMarkdown>

                {!isUser && (
                    <button
                        onClick={handleCopy}
                        style={{ position: 'absolute', top: '8px', right: '8px', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                        title="Copy message"
                    >
                        {copied ? <Check size={14} color="var(--color-success)" /> : <Copy size={14} />}
                    </button>
                )}
            </div>
            <div className={`message-meta`} style={{ textAlign: isUser ? 'right' : 'left', fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
                {msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
        </div>
    )
}

export default function Chatbot() {
    const [messages, setMessages] = useState([WELCOME_MSG])
    const [input, setInput] = useState('')
    const [employeeId, setEmployeeId] = useState('emp001')
    const [candidateId, setCandidateId] = useState('')
    const [candidates, setCandidates] = useState([])
    const messagesEndRef = useRef(null)

    useEffect(() => {
        hrApi.getCandidates(100).then(data => {
            setCandidates(data.candidates || [])
        }).catch(err => console.error(err))
    }, [])

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const mutation = useMutation({
        mutationFn: ({ query }) => {
            console.log('Querying HR:', { query, employeeId, candidateId })
            return hrApi.queryHR(query, employeeId || null, candidateId || null, 'chat')
        },
        onSuccess: (data) => {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                content: data.response || JSON.stringify(data.data, null, 2),
                agent: data.agent,
                intent: data.intent,
                timestamp: new Date(),
            }])
        },
        onError: (err) => {
            const errorMsg = typeof err === 'object' && err !== null 
                ? (err.message || JSON.stringify(err)) 
                : String(err)
            
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                content: `⚠️ Error: ${errorMsg}\n\nMake sure the backend is running on http://localhost:8000`,
                agent: 'system',
                timestamp: new Date(),
            }])
        },
    })

    const sendMessage = (text = input) => {
        const q = text.trim()
        if (!q || mutation.isPending) return
        setMessages(prev => [...prev, {
            id: Date.now(),
            role: 'user',
            content: q,
            timestamp: new Date(),
        }])
        setInput('')
        mutation.mutate({ query: q })
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    const downloadConversation = () => {
        const text = messages.map(m => `[${m.timestamp?.toLocaleTimeString()}] ${m.role.toUpperCase()}: ${m.content}`).join('\n\n')
        const blob = new Blob([text], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `hr-chat-history-${new Date().toISOString().split('T')[0]}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    return (
        <div>
            <div className="page-header">
                <h1>HR Assistant</h1>
                <p>Multi-agent AI chatbot powered by LangGraph orchestration</p>
            </div>

            {/* Context Selectors */}
            <div style={{ display: 'flex', gap: 12, marginBottom: '1.25rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13 }}>
                    <label style={{ color: 'var(--text-muted)', fontWeight: 600, whiteSpace: 'nowrap' }}>Employee Context:</label>
                    <input
                        className="form-input"
                        style={{ width: 120 }}
                        value={employeeId}
                        onChange={e => setEmployeeId(e.target.value)}
                        placeholder="emp001"
                    />
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 13 }}>
                    <label style={{ color: 'var(--text-muted)', fontWeight: 600, whiteSpace: 'nowrap' }}>Candidate Focus:</label>
                    <select
                        className="form-input"
                        style={{ width: 180, padding: '4px 8px' }}
                        value={candidateId}
                        onChange={e => setCandidateId(e.target.value)}
                    >
                        <option value="">None Selected</option>
                        {candidates.map(c => (
                            <option key={c.id} value={c.id}>{c.full_name}</option>
                        ))}
                    </select>
                </div>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 12, color: 'var(--color-success)', marginLeft: 'auto' }}>
                    <div className="chat-agent-dot" style={{ width: 8, height: 8 }} />
                    6 Agents Orchestrated
                </div>
            </div>

            {/* Chat Window */}
            <div className="chat-container">
                <div className="chat-header">
                    <div className="chat-agent-dot" />
                    <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 700 }}>HR Intelligence Assistant</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                            {candidateId 
                                ? `Focusing on: ${candidates.find(c => c.id === candidateId)?.full_name}` 
                                : 'Multi-Agent Orchestrator · LangGraph'}
                        </div>
                    </div>
                    <button
                        onClick={downloadConversation}
                        className="btn btn-ghost btn-sm"
                        style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}
                        title="Download Chat History"
                    >
                        <Download size={14} /> Download
                    </button>
                    <span className="badge badge-green" style={{ marginLeft: 8, fontSize: 11 }}>
                        <MessageSquare size={10} /> Online
                    </span>
                </div>

                <div className="chat-messages">
                    {messages.map((msg, i) => (
                        <MessageBubble key={msg.id || i} msg={msg} />
                    ))}
                    {mutation.isPending && (
                        <div className="message assistant">
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                                <div className="avatar" style={{ width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--gradient-primary)', borderRadius: '50%', color: 'white' }}>
                                    <Bot size={16} />
                                </div>
                                <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>AI IS THINKING...</span>
                            </div>
                            <div className="message-bubble" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--color-border)', width: 'fit-content' }}>
                                <div className="typing-indicator" style={{ display: 'flex', gap: 4, padding: '4px' }}>
                                    <div className="typing-dot" style={{ width: 6, height: 6, background: 'var(--text-muted)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '-0.32s' }} />
                                    <div className="typing-dot" style={{ width: 6, height: 6, background: 'var(--text-muted)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '-0.16s' }} />
                                    <div className="typing-dot" style={{ width: 6, height: 6, background: 'var(--text-muted)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both' }} />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Quick prompts */}
                <div style={{ padding: '0.5rem 1.5rem', borderTop: '1px solid var(--color-border)' }}>
                    <div className="quick-actions">
                        {QUICK_PROMPTS.map(p => (
                            <button key={p} className="quick-action-chip" onClick={() => sendMessage(p)}>
                                {p}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="chat-input-area">
                    <div className="chat-input-row">
                        <textarea
                            className="chat-textarea"
                            placeholder="Ask me about payroll, leave, CVs, interviews, or onboarding…"
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            rows={1}
                        />
                        <button
                            className="chat-send-btn"
                            onClick={() => sendMessage()}
                            disabled={!input.trim() || mutation.isPending}
                            title="Send (Enter)"
                        >
                            {mutation.isPending ? <div className="spinner" style={{ width: 16, height: 16 }} /> : <Send size={18} />}
                        </button>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, textAlign: 'center' }}>
                        Press Enter to send · Shift+Enter for new line
                    </div>
                </div>
            </div>
        </div>
    )
}
