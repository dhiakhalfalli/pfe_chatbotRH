import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import { DollarSign, TrendingUp, Calendar, RefreshCw, Banknote, ArrowDownCircle, ArrowUpCircle, User } from 'lucide-react'

const DEMO_EMPLOYEES = ['emp001', 'emp002', 'emp003']

export default function Payroll() {
    const [employeeId, setEmployeeId] = useState('emp001')
    const [inputVal, setInputVal] = useState('emp001')

    const { data, isLoading, refetch } = useQuery({
        queryKey: ['payroll', employeeId],
        queryFn: () => hrApi.getPayroll(employeeId),
        enabled: !!employeeId,
    })

    const records = data?.records || []

    const totalPaid = records.reduce((s, r) => s + (r.net_pay || 0), 0)
    const lastRecord = records[records.length - 1]

    return (
        <div>
            <div className="page-header">
                <h1>Payroll</h1>
                <p>View salary records and compensation history for employees</p>
            </div>

            {/* Employee selector */}
            <div style={{ display: 'flex', gap: 12, marginBottom: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <User size={16} color="var(--text-muted)" />
                <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Employee ID:</label>
                <input
                    className="form-input"
                    style={{ maxWidth: 180 }}
                    value={inputVal}
                    onChange={e => setInputVal(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && setEmployeeId(inputVal)}
                    placeholder="emp001"
                />
                <button className="btn btn-secondary btn-sm" onClick={() => setEmployeeId(inputVal)}>
                    <RefreshCw size={13} /> Load
                </button>
                <div style={{ display: 'flex', gap: 6 }}>
                    {DEMO_EMPLOYEES.map(id => (
                        <button
                            key={id}
                            className={`btn btn-sm ${employeeId === id ? 'btn-primary' : 'btn-ghost'}`}
                            onClick={() => { setEmployeeId(id); setInputVal(id) }}
                        >{id}</button>
                    ))}
                </div>
            </div>

            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
                    <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
                </div>
            ) : records.length === 0 ? (
                <div className="empty-state card">
                    <div className="empty-icon"><Banknote size={32} color="#6366f1" /></div>
                    <h3>No Payroll Records</h3>
                    <p>No payroll data found for employee <strong>{employeeId}</strong>. Create an employee first via the Employees page.</p>
                </div>
            ) : (
                <>
                    {/* Summary Cards */}
                    <div className="stat-grid" style={{ marginBottom: '2rem' }}>
                        <div className="stat-card">
                            <div className="stat-icon indigo"><DollarSign size={22} /></div>
                            <div>
                                <div className="stat-value">${totalPaid.toLocaleString()}</div>
                                <div className="stat-label">Total Paid (YTD)</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon emerald"><TrendingUp size={22} /></div>
                            <div>
                                <div className="stat-value">${lastRecord?.base_salary?.toLocaleString() || '—'}</div>
                                <div className="stat-label">Base Salary</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon cyan"><Calendar size={22} /></div>
                            <div>
                                <div className="stat-value">{records.length}</div>
                                <div className="stat-label">Pay Records</div>
                            </div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-icon amber"><ArrowDownCircle size={22} /></div>
                            <div>
                                <div className="stat-value">${lastRecord?.deductions?.toLocaleString() || '0'}</div>
                                <div className="stat-label">Last Deductions</div>
                            </div>
                        </div>
                    </div>

                    {/* Payroll Table */}
                    <div className="card" style={{ padding: 0 }}>
                        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', gap: 10 }}>
                            <Banknote size={16} color="#6366f1" />
                            <span style={{ fontWeight: 700, fontSize: 15 }}>Payment History – {employeeId}</span>
                        </div>
                        <div className="table-wrapper" style={{ borderRadius: 0, border: 'none' }}>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Period</th>
                                        <th>Base Salary</th>
                                        <th>Bonus</th>
                                        <th>Deductions</th>
                                        <th>Net Pay</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {records.map((rec, i) => (
                                        <tr key={i}>
                                            <td style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{rec.pay_period || rec.period || `Period ${i + 1}`}</td>
                                            <td style={{ fontWeight: 600 }}>${(rec.base_salary || 0).toLocaleString()}</td>
                                            <td style={{ color: 'var(--color-success)' }}>+${(rec.bonus || 0).toLocaleString()}</td>
                                            <td style={{ color: 'var(--color-danger)' }}>-${(rec.deductions || 0).toLocaleString()}</td>
                                            <td style={{ fontWeight: 800, fontSize: 15, color: 'var(--color-primary-light)' }}>${(rec.net_pay || 0).toLocaleString()}</td>
                                            <td>
                                                <span className={`badge ${rec.status === 'paid' ? 'badge-green' : 'badge-yellow'}`}>
                                                    {rec.status || 'paid'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
