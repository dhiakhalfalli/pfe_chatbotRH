import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import toast from 'react-hot-toast'
import { CalendarDays, Send, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react'

const LEAVE_TYPES = ['annual', 'sick', 'emergency', 'maternity', 'paternity', 'unpaid']

function StatusIcon({ status }) {
    if (status === 'approved') return <CheckCircle size={14} color="#10b981" />
    if (status === 'rejected') return <XCircle size={14} color="#ef4444" />
    return <Clock size={14} color="#f59e0b" />
}

export default function LeavePortal() {
    const [employeeId, setEmployeeId] = useState('emp001')
    const [form, setForm] = useState({
        leave_type: 'annual',
        start_date: '',
        end_date: '',
        reason: '',
    })

    const balanceQuery = useQuery({
        queryKey: ['leave-balance', employeeId],
        queryFn: () => hrApi.getLeaveBalance(employeeId),
        enabled: !!employeeId,
    })

    const submitMutation = useMutation({
        mutationFn: (data) => hrApi.submitLeave(data),
        onSuccess: (data) => {
            toast.success(data.status === 'submitted' ? `Leave submitted!` : data.response || 'Done')
            balanceQuery.refetch()
            setForm({ leave_type: 'annual', start_date: '', end_date: '', reason: '' })
        },
        onError: (err) => toast.error(err.message),
    })

    const handleSubmit = (e) => {
        e.preventDefault()
        if (!form.start_date || !form.end_date) return toast.error('Select start and end dates')
        submitMutation.mutate({ employee_id: employeeId, ...form })
    }

    const balance = balanceQuery.data?.leave_balance || {}

    return (
        <div>
            <div className="page-header">
                <h1>Leave Portal</h1>
                <p>Check your balance and submit leave requests</p>
            </div>

            {/* Employee ID selector */}
            <div style={{ display: 'flex', gap: 12, marginBottom: '2rem', alignItems: 'center' }}>
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Employee ID:</label>
                <input
                    className="form-input"
                    style={{ maxWidth: 160 }}
                    value={employeeId}
                    onChange={e => setEmployeeId(e.target.value)}
                    placeholder="emp001"
                />
                <button className="btn btn-secondary btn-sm" onClick={balanceQuery.refetch}>
                    <RefreshCw size={13} /> Refresh
                </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                {/* Balance Card */}
                <div>
                    <div className="card" style={{ marginBottom: '1.25rem' }}>
                        <h3 style={{ marginBottom: '1.25rem', fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <CalendarDays size={16} color="#6366f1" /> Leave Balance
                        </h3>
                        {balanceQuery.isLoading ? (
                            <div className="spinner" />
                        ) : Object.keys(balance).length === 0 ? (
                            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No balance data found. Check your employee ID.</p>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                {Object.entries(balance).map(([type, days]) => {
                                    const entitlements = { annual: 20, sick: 10, emergency: 3, maternity: 90, paternity: 14, unpaid: 30 }
                                    const total = entitlements[type] || 20
                                    const used = total - days
                                    const pct = (days / total) * 100

                                    return (
                                        <div key={type}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                                                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{type.charAt(0).toUpperCase() + type.slice(1)} Leave</span>
                                                <span style={{ color: 'var(--text-muted)' }}>
                                                    <span style={{ fontWeight: 700, color: 'var(--color-primary-light)' }}>{days}</span>/{total} days
                                                </span>
                                            </div>
                                            <div className="progress-bar">
                                                <div
                                                    className="progress-fill"
                                                    style={{ width: `${pct}%`, background: days <= 3 ? '#ef4444' : 'var(--gradient-primary)' }}
                                                />
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        )}
                    </div>

                    {/* Tips */}
                    <div className="card" style={{ background: 'var(--color-bg-glass)', border: '1px solid var(--color-border)' }}>
                        <h4 style={{ fontSize: 13, marginBottom: 10, color: 'var(--color-primary-light)' }}>💡 Leave Policy</h4>
                        <ul style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 2, paddingLeft: '1rem' }}>
                            <li>Annual leave must be requested 2 weeks in advance</li>
                            <li>Sick leave requires medical certificate after 3 days</li>
                            <li>Unused annual leave is carried forward (max 5 days)</li>
                            <li>Emergency leave approved same-day</li>
                        </ul>
                    </div>
                </div>

                {/* Request Form */}
                <div className="card">
                    <h3 style={{ marginBottom: '1.5rem', fontSize: 15 }}>Submit Leave Request</h3>
                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                        <div className="form-group">
                            <label className="form-label">Leave Type</label>
                            <select
                                className="form-select"
                                value={form.leave_type}
                                onChange={e => setForm(f => ({ ...f, leave_type: e.target.value }))}
                            >
                                {LEAVE_TYPES.map(t => (
                                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                                ))}
                            </select>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            <div className="form-group">
                                <label className="form-label">Start Date</label>
                                <input
                                    className="form-input" type="date"
                                    value={form.start_date}
                                    onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">End Date</label>
                                <input
                                    className="form-input" type="date"
                                    value={form.end_date}
                                    onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
                                    style={{ background: 'var(--color-bg-primary)' }}
                                    required
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label className="form-label">Reason (optional)</label>
                            <textarea
                                className="form-textarea"
                                rows={3}
                                placeholder="Briefly describe your reason…"
                                value={form.reason}
                                onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
                            />
                        </div>

                        <button type="submit" className="btn btn-primary" disabled={submitMutation.isPending}>
                            {submitMutation.isPending
                                ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Submitting…</>
                                : <><Send size={16} /> Submit Request</>
                            }
                        </button>
                    </form>

                    {/* Result */}
                    {submitMutation.isSuccess && (
                        <div style={{
                            marginTop: '1rem',
                            padding: '1rem',
                            background: 'var(--color-surface)',
                            border: '1px solid var(--color-border)',
                            borderRadius: 10,
                        }}>
                            <pre style={{ fontFamily: 'inherit', fontSize: 13, whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
                                {submitMutation.data?.response || 'Request submitted!'}
                            </pre>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
