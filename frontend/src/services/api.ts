import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('infrasphere_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem('infrasphere_token');
      localStorage.removeItem('infrasphere_user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export const authApi = {
  login: async (email: string, password: string) => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },
};

export const incidentsApi = {
  list: async (params?: { category?: string; severity?: string; district?: string }) => {
    const res = await api.get('/incidents', { params });
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get(`/incidents/${id}`);
    return res.data;
  },
  create: async (data: any) => {
    const res = await api.post('/incidents', data);
    return res.data;
  },
  analyze: async (id: string) => {
    const res = await api.post(`/incidents/${id}/analyze`);
    return res.data;
  },
};

export const secureAiApi = {
  inspectPrompt: async (text: string) => {
    const res = await api.post('/secureai/inspect', { text });
    return res.data;
  },
  listEvents: async () => {
    const res = await api.get('/secureai/events');
    return res.data;
  },
  listPolicies: async () => {
    const res = await api.get('/secureai/policies');
    return res.data;
  },
};

export const knowledgeApi = {
  query: async (query: string, top_k: number = 4) => {
    const res = await api.post('/knowledge/query', { query, top_k });
    return res.data;
  },
  listDocuments: async () => {
    const res = await api.get('/knowledge/documents');
    return res.data;
  },
  getGraph: async () => {
    const res = await api.get('/knowledge/graph');
    return res.data;
  },
  getContradictions: async () => {
    const res = await api.get('/knowledge/contradictions');
    return res.data;
  },
};

export const workforceApi = {
  listTeams: async () => {
    const res = await api.get('/workforce/teams');
    return res.data;
  },
  listAgents: async () => {
    const res = await api.get('/workforce/agents');
    return res.data;
  },
  listTasks: async (incident_id?: string) => {
    const res = await api.get('/workforce/tasks', { params: { incident_id } });
    return res.data;
  },
  simulateMatch: async (skills: string[], district: string) => {
    const res = await api.post('/workforce/simulate-match', { skills, district });
    return res.data;
  },
};

export const agentOpsApi = {
  listRuns: async (params?: { incident_id?: string; agent_id?: string }) => {
    const res = await api.get('/agentops/runs', { params });
    return res.data;
  },
  listSpans: async (run_id?: string) => {
    const res = await api.get('/agentops/spans', { params: { run_id } });
    return res.data;
  },
  listCircuitBreakers: async () => {
    const res = await api.get('/agentops/circuit-breakers');
    return res.data;
  },
  tripCircuitBreaker: async (agent_id: string, reason?: string) => {
    const res = await api.post(`/agentops/circuit-breakers/${agent_id}/trip`, { reason });
    return res.data;
  },
  resetCircuitBreaker: async (agent_id: string) => {
    const res = await api.post(`/agentops/circuit-breakers/${agent_id}/reset`);
    return res.data;
  },
};

export const approvalsApi = {
  list: async (status?: string) => {
    const res = await api.get('/approvals', { params: { status } });
    return res.data;
  },
  get: async (id: string) => {
    const res = await api.get(`/approvals/${id}`);
    return res.data;
  },
  submitDecision: async (id: string, decision: 'approved' | 'rejected' | 'needs_revision', comment?: string) => {
    const res = await api.post(`/approvals/${id}/decision`, { decision, comment });
    return res.data;
  },
  submitFeedback: async (id: string, rating: 'helpful' | 'unhelpful', notes?: string) => {
    const res = await api.post(`/approvals/${id}/feedback`, { rating, notes });
    return res.data;
  },
};

export const auditApi = {
  listEvents: async (limit: number = 50) => {
    const res = await api.get('/audit/events', { params: { limit } });
    return res.data;
  },
  verifyChain: async () => {
    const res = await api.get('/audit/verify');
    return res.data;
  },
};

export const dataSourcesApi = {
  listStations: async () => {
    const res = await api.get('/data-sources/stations');
    return res.data;
  },
};

export const metricsApi = {
  getOverview: async () => {
    const res = await api.get('/metrics/overview');
    return res.data;
  },
};

export default api;
