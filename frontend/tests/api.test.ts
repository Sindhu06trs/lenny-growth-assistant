import { describe, it, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  getHealth,
  getDatabaseHealth,
  getProviderStatus,
  createSession,
  listSessions,
  getSessionMessages,
  sendChatMessage,
  deleteSession,
  getArtifact,
} from '../src/services/api.ts';

// Backup global fetch
const originalFetch = globalThis.fetch;

describe('Frontend API Service Suite', () => {
  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('handles getHealth successfully', async () => {
    globalThis.fetch = async (url: any) => {
      assert.match(String(url), /\/health$/);
      return new Response(JSON.stringify({ status: 'ok', service: 'lenny-growth-assistant' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const health = await getHealth();
    assert.equal(health.status, 'ok');
  });

  it('handles API request error gracefully when server returns 500', async () => {
    globalThis.fetch = async () => {
      return new Response(JSON.stringify({ detail: 'Internal Database Failure' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    await assert.rejects(
      async () => {
        await getDatabaseHealth();
      },
      (err: any) => {
        assert.match(err.message, /Internal Database Failure/);
        return true;
      }
    );
  });

  it('fetches provider status correctly', async () => {
    const mockStatus = {
      default_provider: 'ollama',
      providers: {
        ollama: {
          configured: true,
          status: 'connected',
          model: 'llama3.2:3b',
          base_url: 'http://localhost:11434',
          installed_models: ['llama3.2:3b'],
          error: null,
        },
        anthropic: {
          configured: false,
          status: 'unavailable',
          model: 'claude-3-5-sonnet-20241022',
          base_url: null,
          installed_models: [],
          error: 'API key not configured',
        },
      },
    };

    globalThis.fetch = async (url: any) => {
      assert.match(String(url), /\/api\/providers\/status$/);
      return new Response(JSON.stringify(mockStatus), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const result = await getProviderStatus();
    assert.equal(result.default_provider, 'ollama');
    assert.equal(result.providers.ollama.status, 'connected');
    assert.equal(result.providers.anthropic.status, 'unavailable');
  });

  it('sends a chat message and returns response', async () => {
    const mockResponse = {
      session_id: 'test-session-123',
      message: 'Hello, this is Lenny AI.',
      provider: 'ollama',
      sources: [],
      status: 'success',
      timestamp: '2026-10-11T00:00:00Z',
    };

    globalThis.fetch = async (url: any, init?: any) => {
      assert.match(String(url), /\/api\/chat$/);
      assert.equal(init?.method, 'POST');
      const body = JSON.parse(init.body);
      assert.equal(body.message, 'What is product market fit?');
      assert.equal(body.provider, 'ollama');

      return new Response(JSON.stringify(mockResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const reply = await sendChatMessage('What is product market fit?', undefined, 'ollama');

    assert.equal(reply.session_id, 'test-session-123');
    assert.equal(reply.provider, 'ollama');
    assert.equal(reply.message, 'Hello, this is Lenny AI.');
  });

  it('supports session switching and lifecycle (create, list, get, delete)', async () => {
    // 1. Create
    globalThis.fetch = async (url: any, init?: any) => {
      if (init?.method === 'POST') {
        return new Response(
          JSON.stringify({
            id: 'sess-new',
            title: 'Growth Strategy',
            created_at: '2026-10-11T00:00:00Z',
            updated_at: '2026-10-11T00:00:00Z',
          }),
          { status: 201 }
        );
      }
      return new Response(JSON.stringify([]), { status: 200 });
    };

    const session = await createSession('Growth Strategy');
    assert.equal(session.id, 'sess-new');
    assert.equal(session.title, 'Growth Strategy');

    // 2. List
    globalThis.fetch = async () => {
      return new Response(
        JSON.stringify([
          { id: 'sess-new', title: 'Growth Strategy', created_at: '2026-10-11T00:00:00Z', updated_at: '2026-10-11T00:00:00Z' },
          { id: 'sess-old', title: 'Retention', created_at: '2026-10-10T00:00:00Z', updated_at: '2026-10-10T00:00:00Z' },
        ]),
        { status: 200 }
      );
    };

    const sessions = await listSessions();
    assert.equal(sessions.length, 2);
    assert.equal(sessions[0].id, 'sess-new');

    // 3. Messages for session
    globalThis.fetch = async (url: any) => {
      assert.match(String(url), /\/api\/sessions\/sess-new\/messages$/);
      return new Response(
        JSON.stringify([
          { id: 'm1', role: 'user', content: 'Hi', session_id: 'sess-new', created_at: '2026-10-11T00:00:00Z' },
        ]),
        { status: 200 }
      );
    };

    const messages = await getSessionMessages('sess-new');
    assert.equal(messages.length, 1);
    assert.equal(messages[0].content, 'Hi');

    // 4. Delete
    globalThis.fetch = async (url: any, init?: any) => {
      assert.match(String(url), /\/api\/sessions\/sess-new$/);
      assert.equal(init?.method, 'DELETE');
      return new Response(JSON.stringify({ status: 'deleted' }), { status: 200 });
    };

    await deleteSession('sess-new');
  });

  it('fetches an artifact by ID via getArtifact', async () => {
    const mockArtifact = {
      id: 'art-essay-101',
      title: 'Customer Retention Playbook',
      type: 'essay',
      content: '# Customer Retention Playbook\nRetention is the foundation of growth.',
      version: 1,
      is_demonstration: false,
      created_at: '2026-10-12T12:00:00Z',
    };

    globalThis.fetch = async (url: any) => {
      assert.match(String(url), /\/api\/artifacts\/art-essay-101$/);
      return new Response(JSON.stringify(mockArtifact), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const artifact = await getArtifact('art-essay-101');
    assert.equal(artifact.id, 'art-essay-101');
    assert.equal(artifact.title, 'Customer Retention Playbook');
    assert.equal(artifact.type, 'essay');
    assert.equal(artifact.isDemonstration, false);
    assert.match(artifact.content, /Retention is the foundation/);
  });

  it('fetches demo HTML artifact via getArtifact', async () => {
    const mockDemoArtifact = {
      id: 'demo-retention-calc',
      title: 'Customer Retention & Cohort Simulator',
      type: 'html',
      content: '<!DOCTYPE html><html><body><h1>⚡ SaaS Retention & ARR Simulator</h1></body></html>',
      version: 1,
      is_demonstration: true,
      created_at: '2026-10-12T00:00:00Z',
    };

    globalThis.fetch = async (url: any) => {
      assert.match(String(url), /\/api\/artifacts\/demo-retention-calc$/);
      return new Response(JSON.stringify(mockDemoArtifact), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const artifact = await getArtifact('demo-retention-calc');
    assert.equal(artifact.id, 'demo-retention-calc');
    assert.equal(artifact.title, 'Customer Retention & Cohort Simulator');
    assert.equal(artifact.type, 'html');
    assert.equal(artifact.isDemonstration, true);
    assert.match(artifact.content, /SaaS Retention & ARR Simulator/);
  });

  it('parses message with linked artifact in getSessionMessages', async () => {
    globalThis.fetch = async (url: any) => {
      assert.match(String(url), /\/api\/sessions\/sess-with-art\/messages$/);
      return new Response(
        JSON.stringify([
          {
            id: 'msg-assistant-1',
            role: 'assistant',
            content: 'Here is your essay.',
            session_id: 'sess-with-art',
            created_at: '2026-10-12T12:00:00Z',
            artifact_id: 'art-essay-101',
            artifact_title: 'Customer Retention Playbook',
            artifact_type: 'essay',
            sources: [],
          },
        ]),
        { status: 200 }
      );
    };

    const messages = await getSessionMessages('sess-with-art');
    assert.equal(messages.length, 1);
    assert.equal(messages[0].artifactId, 'art-essay-101');
    assert.equal(messages[0].artifactTitle, 'Customer Retention Playbook');
    assert.equal(messages[0].artifactType, 'essay');
  });

  it('receives artifact metadata in sendChatMessage response', async () => {
    const mockChatResponse = {
      status: 'success',
      session_id: 'sess-essay',
      message: '# Why Retention Matters\nRetention compounds.',
      provider: 'ollama',
      sources: [],
      timestamp: '2026-10-12T12:00:00Z',
      artifact_id: 'art-created-1',
      artifact: {
        id: 'art-created-1',
        title: 'Why Retention Matters',
        type: 'essay',
        content: '# Why Retention Matters\nRetention compounds.',
        session_id: 'sess-essay',
        message_id: 'msg-1',
        version: 1,
        is_demonstration: false,
        created_at: '2026-10-12T12:00:00Z',
      },
    };

    globalThis.fetch = async (url: any) => {
      assert.match(String(url), /\/api\/chat$/);
      return new Response(JSON.stringify(mockChatResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    };

    const response = await sendChatMessage('Write an essay about retention', 'sess-essay', 'ollama');
    assert.equal(response.status, 'success');
    assert.equal(response.artifact_id, 'art-created-1');
    assert.ok(response.artifact);
    assert.equal(response.artifact?.title, 'Why Retention Matters');
    assert.equal(response.artifact?.type, 'essay');
  });
});
