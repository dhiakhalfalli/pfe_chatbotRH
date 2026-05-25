import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useLocation } from 'react-router-dom'
import { hrApi } from '../services/api.js'
import { MessageSquare, X, Send, Cpu, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import '../index.css'

export default function ChatbotPopup() {
    const location = useLocation()
    const user = JSON.parse(localStorage.getItem('user')) || { role: 'hr' }
    // Don't show popup when already on the chatbot page
    if (location.pathname === '/chatbot') return null
    const [isOpen, setIsOpen] = useState(false)
    const [messages, setMessages] = useState([
        {
            id: 'welcome',
            role: 'assistant',
            content: "👋 Hello! I am the **Segula HR Assistant**.\n\nI can answer questions about **Segula Technologies**, HR policies, employee benefits, leave rules, and how to apply for jobs.\n\nAsk me anything!",
            timestamp: new Date()
        }
    ])
    const [input, setInput] = useState('')
    const messagesEndRef = useRef(null)

    useEffect(() => {
        if (isOpen) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages, isOpen])

    const mutation = useMutation({
        // Passing a forced intent implicitly by adding 'Segula question:'
        // But orchestrator handles 'segula' keyword automatically.
        mutationFn: ({ query }) => hrApi.queryHR(`Segula question: ${query}`, null, null, 'chat', { role: user.role, email: user.email }),
        onSuccess: (data) => {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                content: data.response || (data.result && data.result.response) || JSON.stringify(data.result, null, 2),
                agent: data.agent,
                timestamp: new Date(),
            }])
        },
        onError: (err) => {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                role: 'assistant',
                content: `⚠️ Error: ${err.message}`,
                timestamp: new Date(),
            }])
        },
    })

    const sendMessage = () => {
        const q = input.trim()
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

    if (!isOpen) {
        return (
            <div className="chatbot-bubble" onClick={() => setIsOpen(true)} title="Ask Segula HR">
                <MessageSquare size={24} />
                <div className="badge">1</div>
            </div>
        )
    }

    return (
        <div style={{
            position: 'fixed',
            bottom: 40,
            right: 40,
            width: 380,
            height: 550,
            backgroundColor: 'var(--color-bg-card)',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid var(--color-border)',
            boxShadow: '0 15px 40px rgba(0,0,0,0.4)',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 1000,
            overflow: 'hidden'
        }}>
            <div style={{
                background: 'linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%)',
                padding: '1rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                color: 'white'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Cpu size={16} />
                    </div>
                    <div>
                        <div style={{ fontWeight: 700, fontSize: 14 }}>Segula HR Assistant</div>
                        <div style={{ fontSize: 11, opacity: 0.8 }}>AI Knowledge Base · Always Online</div>
                    </div>
                </div>
                <button
                    onClick={() => setIsOpen(false)}
                    style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', opacity: 0.8 }}
                >
                    <X size={20} />
                </button>
            </div>
            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
                backgroundColor: 'var(--color-bg-primary)'
            }}>
                {messages.map((msg, i) => (
                    <div key={msg.id || i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
                        {msg.role === 'assistant' && (
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, display: 'flex', gap: 4, alignItems: 'center' }}>
                                <Zap size={10} color="#06b6d4" />
                                {msg.agent ? msg.agent.replace('_agent', '').toUpperCase() : 'AI'}
                            </div>
                        )}
                        <div style={{
                            padding: '10px 14px',
                            borderRadius: 14,
                            backgroundColor: msg.role === 'user' ? 'var(--color-primary)' : 'var(--color-bg-secondary)',
                            borderBottomRightRadius: msg.role === 'user' ? 4 : 14,
                            borderBottomLeftRadius: msg.role === 'assistant' ? 4 : 14,
                            color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                            fontSize: 13,
                            lineHeight: 1.5
                        }}>
                            <ReactMarkdown
                                components={{
                                    p: ({ node, ...props }) => <p style={{ margin: '0 0 8px 0' }} {...props} />,
                                    ul: ({ node, ...props }) => <ul style={{ margin: '0 0 8px 0', paddingLeft: 16 }} {...props} />,
                                    ol: ({ node, ...props }) => <ol style={{ margin: '0 0 8px 0', paddingLeft: 16 }} {...props} />,
                                    li: ({ node, ...props }) => <li style={{ marginBottom: 2 }} {...props} />
                                }}
                            >
                                {msg.content}
                            </ReactMarkdown>
                        </div>
                    </div>
                ))}

                {mutation.isPending && (
                    <div style={{ alignSelf: 'flex-start' }}>
                        <div style={{
                            padding: '10px 14px',
                            borderRadius: '14px 14px 14px 4px',
                            backgroundColor: 'var(--color-bg-secondary)',
                            display: 'flex',
                            gap: 4
                        }}>
                            <div className="typing-dot" />
                            <div className="typing-dot" />
                            <div className="typing-dot" />
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div style={{ borderTop: '1px solid var(--color-border)', padding: '0.75rem', display: 'flex', gap: 8, backgroundColor: 'var(--color-bg-card)' }}>
                <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about Segula rules..."
                    style={{
                        flex: 1,
                        background: 'var(--color-bg-secondary)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 100,
                        padding: '8px 16px',
                        color: 'var(--text-primary)',
                        outline: 'none',
                        fontSize: 13
                    }}
                />
                <button
                    onClick={sendMessage}
                    disabled={!input.trim() || mutation.isPending}
                    style={{
                        width: 36, height: 36,
                        borderRadius: '50%',
                        background: 'var(--gradient-primary)',
                        border: 'none',
                        color: 'white',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        cursor: input.trim() ? 'pointer' : 'not-allowed',
                        opacity: input.trim() ? 1 : 0.5
                    }}
                >
                    <Send size={16} />
                </button>
            </div>
        </div>
    )
}
