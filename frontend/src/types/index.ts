export type UserRole = 'admin' | 'manager' | 'analyst';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id?: string;
  is_active: boolean;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'reported' | 'investigating' | 'pending_approval' | 'approved' | 'rejected' | 'resolved';
  latitude: number;
  longitude: number;
  district: string;
  language: string;
  source: string;
  is_synthetic: boolean;
  created_at: string;
  updated_at: string;
}

export interface StationObservation {
  id: string;
  station_id: string;
  station_name: string;
  district: string;
  level: number;
  unit: string;
  danger_level: number;
  recorded_at: string;
  source: string;
  is_synthetic: boolean;
}

export interface RiskFactor {
  water_level?: number;
  forecast_trend?: number;
  asset_exposure?: number;
  historical_frequency?: number;
  incident_severity?: number;
  [key: string]: number | undefined;
}

export interface RiskAssessment {
  id: string;
  incident_id: string;
  score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  model_version: string;
  factors: RiskFactor;
  missing_factors: string[];
  limitations: string[];
  created_at: string;
}

export interface Task {
  id: string;
  incident_id: string;
  parent_task_id?: string | null;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
  assigned_agent_id?: string | null;
  assigned_team_id?: string | null;
  dependencies: string[];
  created_at: string;
}

export interface Team {
  id: string;
  name: string;
  district: string;
  zone: string;
  status: 'available' | 'deployed' | 'off_duty';
  skills?: Array<{ skill: string; proficiency: number }>;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: 'idle' | 'busy' | 'offline';
  capabilities: string[];
}

export interface Approval {
  id: string;
  incident_id: string;
  task_id?: string | null;
  recommendation: {
    approval_id?: string;
    incident_id?: string;
    summary?: string;
    priority?: string;
    recommended_actions?: string[];
    evidence_summary?: string[];
    risk_factors?: Record<string, number>;
    assigned_teams?: string[];
    caveats?: string[];
    status?: string;
    [key: string]: any;
  };
  reviewer_id?: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'needs_revision';
  comment?: string | null;
  version: number;
  created_at: string;
  reviewed_at?: string | null;
}

export interface AuditEvent {
  id: string;
  actor: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  previous_hash: string;
  event_hash: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface AgentRun {
  id: string;
  incident_id: string;
  agent_id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: string | null;
  completed_at?: string | null;
  step_count: number;
  retry_count: number;
  error_message?: string | null;
}

export interface SecurityEvent {
  id: string;
  threat_type: string;
  decision: 'allow' | 'block' | 'flag';
  confidence: number;
  input_snippet: string;
  reasons: string[];
  created_at: string;
}
