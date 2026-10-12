import type { ChatMessage, ProviderStatusResponse, Session } from '../types/chat.ts';
import type { Artifact } from '../types/artifact.ts';

const getBaseUrl = (): string => {
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    return 'http://127.0.0.1:8000';
  }
  return 'http://127.0.0.1:8000';
};

const API_BASE_URL = getBaseUrl().replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  detail?: any;

  constructor(message: string, status: number, detail?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail: any = null;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.error || errorJson;
    } catch {
      errorDetail = response.statusText;
    }
    const message = typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail);
    throw new ApiError(message, response.status, errorDetail);
  }
  if (response.status === 204) {
    return {} as T;
  }
  return response.json();
}

/**
 * Health check: GET /health
 */
export async function getHealth(): Promise<{ status: string; service: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return handleResponse(response);
}

/**
 * Database connectivity: GET /health/db
 */
export async function getDatabaseHealth(): Promise<{ status: string; database: string; detail?: string }> {
  const response = await fetch(`${API_BASE_URL}/health/db`);
  return handleResponse(response);
}

/**
 * Provider status: GET /api/providers/status
 */
export async function getProviderStatus(): Promise<ProviderStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/api/providers/status`);
  return handleResponse(response);
}

/**
 * List conversation sessions: GET /api/sessions
 */
export async function listSessions(limit: number = 50, offset: number = 0): Promise<Session[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions?limit=${limit}&offset=${offset}`);
  return handleResponse(response);
}

/**
 * Create a new conversation session: POST /api/sessions
 */
export async function createSession(title?: string, provider?: string): Promise<Session> {
  const response = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, provider }),
  });
  return handleResponse(response);
}

/**
 * Get messages for a session: GET /api/sessions/{session_id}/messages
 */
export async function getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}/messages`);
  const data = await handleResponse<any[]>(response);
  return data.map((item) => ({
    id: item.id,
    role: item.role,
    content: item.content,
    provider: item.provider,
    timestamp: item.created_at ? new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
    artifactId: item.artifact_id,
    artifactTitle: item.artifact_title,
    artifactType: item.artifact_type,
    sources: item.sources || [],
  }));
}

/**
 * Get artifact by ID: GET /api/artifacts/{artifact_id}
 */
export async function getArtifact(artifactId: string): Promise<Artifact> {
  const response = await fetch(`${API_BASE_URL}/api/artifacts/${encodeURIComponent(artifactId)}`);
  const data = await handleResponse<any>(response);
  return {
    id: data.id,
    title: data.title,
    type: data.type,
    content: data.content,
    createdAt: data.created_at ? new Date(data.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
    isDemonstration: Boolean(data.is_demonstration),
  };
}

/**
 * Send a chat message: POST /api/chat
 */
export async function sendChatMessage(
  message: string,
  sessionId?: string,
  provider?: string
): Promise<{
  status: string;
  session_id: string;
  message: string;
  sources: any[];
  provider: string;
  timestamp: string;
  artifact?: {
    id: string;
    title: string;
    type: 'markdown' | 'html' | 'essay';
    content: string;
    session_id?: string;
    message_id?: string;
    version?: number;
    is_demonstration?: boolean;
    created_at?: string;
  } | null;
  artifact_id?: string | null;
}> {
  const payload: any = { message };
  if (sessionId) payload.session_id = sessionId;
  if (provider) payload.provider = provider;

  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

/**
 * Delete a session: DELETE /api/sessions/{session_id}
 */
export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  });
  return handleResponse(response);
}
