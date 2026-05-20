export interface User {
  id: string;
  username: string;
  email: string;
  role: 'consumer' | 'enterprise_admin' | 'system_admin';
  enterpriseId?: string;
  createdAt?: string;
  lastLoginAt?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken?: string;
  expiresIn?: number;
}

export interface LoginResponse {
  user: User;
  token: string;
  refreshToken?: string;
}

export interface Enterprise {
  id: string;
  name: string;
  plan?: string;
  status?: 'active' | 'suspended';
  userCount?: number;
  documentCount?: number;
  sessionCount?: number;
  createdAt?: string;
  updatedAt?: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  documentCount?: number;
  enterpriseId?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface Document {
  id: string;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  fileSize?: number;
  knowledgeBaseId?: string;
  enterpriseId?: string;
  createdAt?: string;
}

export interface ChatSession {
  id: string;
  userId: string;
  enterpriseId?: string;
  title?: string;
  messageCount?: number;
  createdAt: string;
  updatedAt?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: unknown[];
  createdAt: string;
}

export interface Alert {
  id: string;
  type: 'security' | 'system' | 'usage';
  level: 'info' | 'warning' | 'critical';
  message: string;
  status: 'active' | 'acknowledged' | 'resolved';
  enterpriseId?: string;
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
}

export interface AnalyticsStats {
  totalSessions: number;
  totalMessages: number;
  totalUsers: number;
  totalDocuments: number;
  activeTenants?: number;
  dailyActivity?: Array<{
    date: string;
    sessions: number;
    messages: number;
  }>;
  topEnterprises?: Array<{
    name: string;
    sessions: number;
    users: number;
  }>;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: string;
  version: string;
  lastUpdate?: string;
}

export interface Source {
  id: string;
  title: string;
  content: string;
  score: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface AppSettings {
  apiKey: string;
  apiEndpoint: string;
  model: string;
  temperature: number;
  topP: number;
  topK: number;
  chunkSize: number;
  chunkOverlap: number;
}

export interface CleaningRule {
  id: string;
  name: string;
  type: 'remove_whitespace' | 'remove_newlines' | 'remove_special_chars' | 'custom';
  enabled: boolean;
  pattern?: string;
  replacement?: string;
}

export interface CleaningJob {
  id: string;
  documentId: string;
  documentName: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  rules: CleaningRule[];
  startTime?: Date;
  endTime?: Date;
  result?: string;
  userId: string;
}

export interface Channel {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive';
  config: Record<string, unknown>;
}

export interface HumanAgent {
  id: string;
  name: string;
  email: string;
  status: 'online' | 'offline' | 'busy';
  currentChats: number;
  maxChats: number;
}

export interface SemanticRule {
  id?: string;
  category: string;
  description: string;
  keywords: string[];
  enabled: boolean;
  requires_human: boolean;
}

export interface SensitiveSettings {
  enable_semantic_detection: boolean;
  enable_keyword_detection: boolean;
  human_required_categories: string[];
  semantic_rules: SemanticRule[];
  sensitivity_threshold: number;
  auto_escalation_enabled: boolean;
  sensitive_words: string[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}