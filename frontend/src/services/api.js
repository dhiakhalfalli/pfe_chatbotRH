import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
    baseURL: BASE_URL,
    timeout: 60000,
    headers: { 'Content-Type': 'application/json' },
})

// Response interceptor for error handling
api.interceptors.response.use(
    (res) => res,
    (err) => {
        const message = err.response?.data?.detail || err.message || 'Unknown error'
        console.error('[API Error]', message)
        return Promise.reject(new Error(message))
    }
)

export const hrApi = {
    // ── Stats ─────────────────────────────────────────────────────────────
    getStats: () => api.get('/stats').then(r => r.data),

    // ── Job Offers ────────────────────────────────────────────────────────
    getJobs: (limit = 50, skip = 0) => api.get('/jobs', { params: { limit, skip } }).then(r => r.data),
    getJob: (id) => api.get(`/jobs/${id}`).then(r => r.data),
    createJob: (data) => api.post('/jobs', data).then(r => r.data),
    evaluateCandidateForJob: (candidateId, jobId) => api.post(`/candidates/${candidateId}/evaluate/${jobId}`).then(r => r.data),

    // ── Candidates ────────────────────────────────────────────────────────
    getCandidates: (limit = 50, skip = 0) =>
        api.get('/candidates', { params: { limit, skip } }).then(r => r.data),
    getCandidate: (id) => api.get(`/candidates/${id}`).then(r => r.data),
    updateCandidate: (id, data) => api.patch(`/candidates/${id}`, data).then(r => r.data),
    getRanking: (limit = 20, jobId = null) =>
        api.get('/candidate_ranking', { params: { limit, job_id: jobId } }).then(r => r.data),
    rankAllForJob: (jobId) =>
        api.post(`/jobs/${jobId}/rank-all`).then(r => r.data),
    qualityRanking: (limit = 100) =>
        api.get('/candidates/quality-ranking', { params: { limit } }).then(r => r.data),
    refreshScores: () =>
        api.post('/refresh_all_candidate_scores').then(r => r.data),

    // ── CV Upload ─────────────────────────────────────────────────────────
    uploadCV: (file, uploaderRole = null) => {
        const form = new FormData()
        form.append('file', file)
        if (uploaderRole) {
            form.append('uploader_role', uploaderRole)
        }
        return api.post('/upload_cv', form, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }).then(r => r.data)
    },

    // ── Chatbot ───────────────────────────────────────────────────────────
    queryHR: (query, employeeId = null, candidateId = null, threadId = 'default', metadata = null) =>
        api.post('/query_hr', {
            query, 
            employee_id: employeeId, 
            candidate_id: candidateId, 
            thread_id: threadId, 
            metadata
        }).then(r => r.data),

    // ── Leave ─────────────────────────────────────────────────────────────
    submitLeave: (data) => api.post('/leave_request', data).then(r => r.data),
    getLeaveBalance: (employeeId) =>
        api.get(`/leave_balance/${employeeId}`).then(r => r.data),

    // ── Employees ─────────────────────────────────────────────────────────
    getEmployees: (department) =>
        api.get('/employees', { params: department ? { department } : {} }).then(r => r.data),
    getEmployee: (id) => api.get(`/employee_profile/${id}`).then(r => r.data),
    createEmployee: (data) => api.post('/employee', data).then(r => r.data),

    // ── HR Processes ──────────────────────────────────────────────────────
    createOnboarding: (data) => api.post('/onboarding', data).then(r => r.data),
    getTrainingRecommendations: (data) =>
        api.post('/training_recommendations', data).then(r => r.data),
    generateInterviewQuestions: (data) =>
        api.post('/interview_questions', data).then(r => r.data),

    // ── Payroll ───────────────────────────────────────────────────────────
    getPayroll: (employeeId) =>
        api.get(`/payroll/${employeeId}`).then(r => r.data),

    // ── Health ────────────────────────────────────────────────────────────
    health: () => api.get('/health').then(r => r.data),

    // ── Copilot ───────────────────────────────────────────────────────────
    copilotCompare: (c1, c2) => api.post('/copilot/compare', { candidate1_id: c1, candidate2_id: c2 }).then(r => r.data),
    copilotShortlist: (jobId) => api.post('/copilot/shortlist', { job_id: jobId }).then(r => r.data),
    copilotExplainRejection: (candidateId, jobTitle) => api.post('/copilot/explain-rejection', { candidate_id: candidateId, job_title: jobTitle }).then(r => r.data),
}

export default api
