import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { OverviewPage } from './pages/OverviewPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { IncidentDetailPage } from './pages/IncidentDetailPage';
import { SecureAIPage } from './pages/SecureAIPage';
import { KnowledgeGridPage } from './pages/KnowledgeGridPage';
import { WorkforceOSPage } from './pages/WorkforceOSPage';
import { AgentOpsPage } from './pages/AgentOpsPage';
import { HumanAIPage } from './pages/HumanAIPage';
import { AuditPage } from './pages/AuditPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<OverviewPage />} />
            <Route path="incidents" element={<IncidentsPage />} />
            <Route path="incidents/:id" element={<IncidentDetailPage />} />
            <Route path="secureai" element={<SecureAIPage />} />
            <Route path="knowledge" element={<KnowledgeGridPage />} />
            <Route path="workforce" element={<WorkforceOSPage />} />
            <Route path="agentops" element={<AgentOpsPage />} />
            <Route path="approvals" element={<HumanAIPage />} />
            <Route path="audit" element={<AuditPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
