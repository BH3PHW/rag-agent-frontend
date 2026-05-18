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
