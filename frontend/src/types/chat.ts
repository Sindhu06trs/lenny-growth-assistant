export type MessageRole = 'user' | 'assistant' | 'system';

export interface SourceCitation {
  id?: string;
  excerpt: string;
  title: string;
  guest: string;
  youtube_url?: string;
  timestamp?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  provider?: string;
  isNotice?: boolean;
  artifactId?: string;
  artifactTitle?: string;
  artifactType?: 'markdown' | 'html' | 'essay';
  sources?: SourceCitation[];
}

export type ModelProvider = 'anthropic' | 'ollama' | 'openai';

export interface ProviderInfo {
  name: string;
  configured: boolean;
  status: 'connected' | 'configured' | 'unavailable' | 'authentication_failed' | 'model_not_found';
  model: string;
  available_models: string[];
  detail?: string | null;
}

export interface ProviderStatusResponse {
  default_provider: ModelProvider;
  providers: Record<ModelProvider, ProviderInfo>;
}

export interface Session {
  id: string;
  title: string;
  model_provider: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}
