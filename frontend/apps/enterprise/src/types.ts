export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface Source {
  id: string;
  title: string;
  content: string;
  score: number;
}

export interface Document {
  id: string;
  name: string;
  size: number;
  uploadDate: Date;
  status: 'processing' | 'ready' | 'error';
  userId: string;
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

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'user' | 'agent';
  createdAt?: Date;
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

export interface ChatSession {
  id: string;
  userId: string;
  enterpriseId: string;
  status: string;
  createdAt: Date;
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
