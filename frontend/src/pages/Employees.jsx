import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hrApi } from '../services/api.js'
import toast from 'react-hot-toast'
import { Users, Plus, Building2, Briefcase, X } from 'lucide-react'

function CreateEmployeeModal({ onClose }) {
    const qc = useQueryClient()
    const [form, setForm] = useState({
        full_name: '', email: '', department: '', job_title: '',
        start_date: new Date().toISOString().split('T')[0],
        base_salary: '', skills: '',
    })

    const mutation = useMutation({
        mutationFn: (data) => hrApi.createEmployee(data),
        onSuccess: () => {
            toast.success('Employee created!')
            qc.invalidateQueries(['employees'])
            onClose()
        },
        onError: (err) => toast.error(err.message),
    })

    const submit = (e) => {
        e.preventDefault()
        mutation.mutate({
            ...form,
            base_salary: parseFloat(form.base_salary) || 0,
            skills: form.skills.split(',').map(s => s.trim()).filter(Boolean),
        })
    }

    return (
        <div style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            z: 100, zIndex: 100,
        }}>
            <div className="card" style={{ width: '100%', maxWidth: 500 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h2 style={{ fontSize: '1.125rem' }}>Add New Employee</h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
                        <X size={20} />
                    </button>
                </div>
                <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {[
                        { field: 'full_name', label: 'Full Name', type: 'text', required: true },
                        { field: 'email', label: 'Email', type: 'email', required: true },
                        { field: 'department', label: 'Department', type: 'text', required: true },
                        { field: 'job_title', label: 'Job Title', type: 'text', required: true },
                        { field: 'start_date', label: 'Start Date', type: 'date', required: true },
                        { field: 'base_salary', label: 'Monthly Base Salary ($)', type: 'number', required: true },
                        { field: 'skills', label: 'Skills (comma-separated)', type: 'text' },
                    ].map(({ field, label, type, required }) => (
                        <div className="form-group" key={field}>
                            <label className="form-label">{label}</label>
                            <input
                                className="form-input"
                                type={type}
                                value={form[field]}
                                onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))}
                                required={required}
                            />
                        </div>
                    ))}
                    <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                        <button type="button" className="btn btn-ghost" style={{ flex: 1 }} onClick={onClose}>Cancel</button>
                        <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={mutation.isPending}>
                            {mutation.isPending ? 'Creating…' : 'Create Employee'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default function Employees() {
    const [showModal, setShowModal] = useState(false)
    const [dept, setDept] = useState('')

    const { data, isLoading } = useQuery({
        queryKey: ['employees', dept],
        queryFn: () => hrApi.getEmployees(dept || undefined),
    })

    const employees = data?.employees || []

    return (
        <div>
            {showModal && <CreateEmployeeModal onClose={() => setShowModal(false)} />}

            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>Employees</h1>
                    <p>Manage your workforce and employee profiles</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                    <Plus size={16} /> Add Employee
                </button>
            </div>

            {/* Filter */}
            <div style={{ display: 'flex', gap: 12, marginBottom: '1.5rem', alignItems: 'center' }}>
                <Building2 size={16} color="var(--text-muted)" />
                <input
                    className="form-input"
                    style={{ maxWidth: 250 }}
                    placeholder="Filter by department…"
                    value={dept}
                    onChange={e => setDept(e.target.value)}
                />
            </div>

            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
                    <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
                </div>
            ) : employees.length === 0 ? (
                <div className="empty-state card">
                    <div className="empty-icon"><Users size={32} color="#6366f1" /></div>
                    <h3>No Employees Found</h3>
                    <p>Add your first employee to get started</p>
                    <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => setShowModal(true)}>
                        <Plus size={16} /> Add Employee
                    </button>
                </div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.25rem' }}>
                    {employees.map((emp) => (
                        <div className="card" key={emp.id}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                                <div className="avatar" style={{ width: 44, height: 44, fontSize: 18 }}>
                                    {emp.full_name?.charAt(0) || '?'}
                                </div>
                                <div>
                                    <h3 style={{ fontSize: 15 }}>{emp.full_name}</h3>
                                    <p style={{ fontSize: 12, marginTop: 2 }}>{emp.email}</p>
                                </div>
                                <span className={`badge ${emp.is_active ? 'badge-green' : 'badge-gray'}`} style={{ marginLeft: 'auto', fontSize: 11 }}>
                                    {emp.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13 }}>
                                <div style={{ display: 'flex', gap: 8, color: 'var(--text-secondary)' }}>
                                    <Briefcase size={14} color="var(--text-muted)" />
                                    <span>{emp.job_title}</span>
                                </div>
                                <div style={{ display: 'flex', gap: 8, color: 'var(--text-secondary)' }}>
                                    <Building2 size={14} color="var(--text-muted)" />
                                    <span>{emp.department}</span>
                                </div>
                            </div>

                            {/* Leave Balance */}
                            {emp.leave_balance && (
                                <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(99,102,241,0.05)', borderRadius: 10, border: '1px solid rgba(99,102,241,0.1)' }}>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 8 }}>LEAVE BALANCE</div>
                                    <div style={{ display: 'flex', gap: '1rem' }}>
                                        {Object.entries(emp.leave_balance).map(([type, days]) => (
                                            <div key={type} style={{ textAlign: 'center' }}>
                                                <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--color-primary-light)' }}>{days}</div>
                                                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{type}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Skills */}
                            {emp.skills?.length > 0 && (
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: '0.75rem' }}>
                                    {emp.skills.slice(0, 5).map(s => (
                                        <span key={s} className="badge badge-indigo" style={{ fontSize: 10 }}>{s}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
