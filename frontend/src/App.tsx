import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ChatPane } from './components/ChatPane';
import { ArtifactViewer } from './components/ArtifactViewer';
import { ChatMessage, ModelProvider, ProviderStatusResponse, Session } from './types/chat';
import { Artifact } from './types/artifact';
import {
  getProviderStatus,
  listSessions,
  createSession,
  getSessionMessages,
  sendChatMessage,
  deleteSession,
  getArtifact,
} from './services/api';

// Curated Demonstration Artifacts for UI Testing (Clearly labeled as Demo Data)
const DEMO_ARTIFACTS: Record<'html' | 'markdown' | 'essay', Artifact> = {
  html: {
    id: 'demo-retention-calc',
    title: 'Customer Retention & Cohort Simulator',
    type: 'html',
    createdAt: new Date().toLocaleTimeString(),
    isDemonstration: true,
    metadata: {
      description: 'Interactive ROI and Retention Curve Calculator (Demonstration Sample)',
    },
    content: `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0F172A;
      color: #F8FAFC;
      margin: 0;
      padding: 24px;
      box-sizing: border-box;
    }
    .card {
      background: #1E293B;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 24px;
      max-width: 540px;
      margin: 0 auto;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    h2 {
      margin-top: 0;
      color: #818CF8;
      font-size: 18px;
    }
    .input-group {
      margin-bottom: 16px;
    }
    label {
      display: block;
      font-size: 12px;
      color: #94A3B8;
      margin-bottom: 6px;
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.05em;
    }
    input[type="range"] {
      width: 100%;
      accent-color: #6366F1;
      cursor: pointer;
    }
    .val-display {
      font-size: 14px;
      color: #38BDF8;
      font-weight: bold;
      float: right;
    }
    .results {
      margin-top: 24px;
      background: #0B0F19;
      border: 1px solid #232F4D;
      border-radius: 12px;
      padding: 16px;
    }
    .stat-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;
    }
    .stat-label { color: #94A3B8; }
    .stat-val { font-weight: 700; color: #10B981; }
    .badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: bold;
      background: rgba(99, 102, 241, 0.2);
      color: #A5B4FC;
      margin-bottom: 16px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">DEMO WIDGET</div>
    <h2>⚡ SaaS Retention & ARR Simulator</h2>
    
    <div class="input-group">
      <label>Monthly Signups <span id="signups-val" class="val-display">5,000</span></label>
      <input id="signups" type="range" min="1000" max="20000" step="500" value="5000" oninput="calculate()">
    </div>

    <div class="input-group">
      <label>Monthly Churn Rate <span id="churn-val" class="val-display">3.5%</span></label>
      <input id="churn" type="range" min="0.5" max="100" step="0.5" value="3.5" oninput="calculate()">
    </div>

    <div class="input-group">
      <label>Average Revenue Per User (ARPU) <span id="arpu-val" class="val-display">$65</span></label>
      <input id="arpu" type="range" min="10" max="300" step="5" value="65" oninput="calculate()">
    </div>

    <div class="results">
      <div class="stat-row">
        <span class="stat-label">Steady-State Active Users:</span>
        <span id="active-users" class="stat-val">142,857</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Projected Monthly Recurring Revenue (MRR):</span>
        <span id="mrr" class="stat-val">$9,285,705</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Annual Run Rate (ARR):</span>
        <span id="arr" class="stat-val" style="color: #6366F1;">$111.4M</span>
      </div>
    </div>
  </div>

  <script>
    function calculate() {
      const signups = parseFloat(document.getElementById('signups').value);
      const churn = parseFloat(document.getElementById('churn').value) / 100;
      const arpu = parseFloat(document.getElementById('arpu').value);

      document.getElementById('signups-val').innerText = signups.toLocaleString();
      document.getElementById('churn-val').innerText = (churn * 100).toFixed(1) + '%';
      document.getElementById('arpu-val').innerText = '$' + arpu;

      const activeUsers = Math.round(signups / churn);
      const mrr = Math.round(activeUsers * arpu);
      const arr = (mrr * 12) / 1000000;

      document.getElementById('active-users').innerText = activeUsers.toLocaleString();
      document.getElementById('mrr').innerText = '$' + mrr.toLocaleString();
      document.getElementById('arr').innerText = '$' + arr.toFixed(1) + 'M';
    }
  </script>
</body>
</html>`,
  },

  markdown: {
    id: 'demo-strategy-guide',
    title: 'Product-Led Growth & Retention Audit Playbook',
    type: 'markdown',
    createdAt: new Date().toLocaleTimeString(),
    isDemonstration: true,
    metadata: {
      description: 'Tactical Checklist and KPI Benchmarks for Growth Teams',
    },
    content: `# Product-Led Growth & Retention Audit Playbook
> *[UI Demonstration Artifact — Staged Strategy Guide Framework]*

## 1. Executive Summary
Before accelerating top-of-funnel acquisition, growth teams must establish cohort retention baseline health.

---

## 2. Core Diagnostic Metrics

| Metric | Target Benchmark (B2B SaaS) | Target Benchmark (Consumer) | Health Action Trigger |
| :--- | :--- | :--- | :--- |
| **D1 Retention** | 40% – 60% | 30% – 45% | Audit first-mile onboarding time-to-value |
| **D30 Retention** | 20% – 35% | 10% – 20% | Evaluate habit loop & notification triggers |
| **Net Revenue Retention (NRR)** | > 115% | N/A | Review expansion pricing tiers |

---

## 3. Four-Step Retention Diagnostic Flow

1. **Segment Cohorts by Acquisition Channel**: Disaggregate organic vs. paid cohorts to isolate user intent.
2. **Identify the Core Setup Moment**: Determine the single action that correlates with 80%+ 6-month retention.
3. **Remove Friction in Activation**: Shorten time from signup to the "Aha!" realization.
4. **Establish Retention Loops**: Connect user outputs to downstream viral or habitual re-engagement triggers.

\`\`\`python
def calculate_quick_ratio(new_mrr, expansion_mrr, churned_mrr, contraction_mrr):
    """Calculates SaaS Quick Ratio to evaluate growth efficiency."""
    gains = new_mrr + expansion_mrr
    losses = churned_mrr + contraction_mrr
    return gains / losses if losses > 0 else float('inf')
\`\`\`
`,
  },

  essay: {
    id: 'demo-ship30-essay',
    title: 'Why Top-of-Funnel Fixes Won’t Save a Leaky Bucket',
    type: 'essay',
    createdAt: new Date().toLocaleTimeString(),
    isDemonstration: true,
    metadata: {
      wordCount: 1245,
      description: 'Ship 30 for 30 Style Atomic Essay on Retention vs Funnels',
    },
    content: `# Why Top-of-Funnel Fixes Won’t Save a Leaky Bucket

Most early-stage founders believe their primary problem is distribution. They buy more ads, launch on Product Hunt, and hire growth agencies.

**Here is the hard truth: Pouring water into a leaky bucket does not fix the holes; it only empties your bank account.**

---

### 1. The Growth Mirage: Acquisition Without Retention
When a product lacks a stable retention curve, every new user acquired is merely a temporary visitor. 

- **The Linear Trap**: Funnels require perpetual spending. Stop spending, and growth evaporates.
- **The Compounding Loop**: Retained users compound. Each cohort layers on top of the last, creating sustainable momentum.

---

### 2. The 3 Signals of a Leaky Bucket
How do you know if your retention is fundamentally broken?

1. **Asymptotic Retention Curves Never Flatten**: If your cohort line continues down to zero over 90 days, you do not have Product-Market Fit.
2. **Paid CAC Payback Exceeds 18 Months**: High churn destroys customer lifetime value (LTV).
3. **Users Churn Before Experiencing the Core Value**: If 70% of churn occurs within 48 hours, onboarding friction is killing your product.

---

### 3. The 30-Day Fix: Re-engineer the Activation Moment
Instead of spending another dollar on acquisition, focus on time-to-value (TTV):

- **Kill the Signup Survey**: Remove unnecessary friction before the user reaches the primary workflow.
- **Pre-populate Templates**: Show the user what a finished project looks like instead of confronting them with a blank canvas.
- **Design the Habit Loop**: Give the user a clear reason to return within 72 hours.

---

### Conclusion: Fix Retention First, Accelerate Second
Growth is not a megaphone; growth is a flywheel. When the flywheel retains energy, every push makes it spin faster. Fix the holes in the bucket first.
`,
  },
};

export const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeArtifact, setActiveArtifact] = useState<Artifact | null>(null);
  const [currentProvider, setCurrentProvider] = useState<ModelProvider>('ollama');
  const [providerStatus, setProviderStatus] = useState<ProviderStatusResponse | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeMobileView, setActiveMobileView] = useState<'chat' | 'artifact'>('chat');

  // Load provider health and status
  const refreshProviderStatus = useCallback(async () => {
    try {
      const statusData = await getProviderStatus();
      setProviderStatus(statusData);
      if (statusData.default_provider) {
        setCurrentProvider(statusData.default_provider);
      }
    } catch (err: any) {
      console.warn('Could not fetch provider status:', err.message);
    }
  }, []);

  // Load all sessions
  const refreshSessions = useCallback(async () => {
    try {
      const data = await listSessions();
      setSessions(data);
      return data;
    } catch (err: any) {
      console.warn('Could not load sessions:', err.message);
      return [];
    }
  }, []);

  // Initial load on mount and periodic provider health polling
  useEffect(() => {
    refreshProviderStatus();
    const interval = setInterval(refreshProviderStatus, 30000);
    return () => clearInterval(interval);
  }, [refreshProviderStatus]);

  useEffect(() => {
    refreshSessions().then((loadedSessions) => {
      if (loadedSessions.length > 0) {
        const latest = loadedSessions[0];
        setCurrentSessionId(latest.id);
        if (latest.model_provider && ['ollama', 'anthropic', 'openai'].includes(latest.model_provider)) {
          setCurrentProvider(latest.model_provider as ModelProvider);
        }
        getSessionMessages(latest.id)
          .then((msgs) => {
            const mapped = msgs.map((m, idx) => {
              if (m.artifactId) return m;
              const prevMsg = idx > 0 ? msgs[idx - 1] : null;
              const isRetentionReq =
                prevMsg &&
                prevMsg.role === 'user' &&
                (prevMsg.content.toLowerCase().includes('retention dashboard') ||
                  prevMsg.content.toLowerCase().includes('html dashboard') ||
                  prevMsg.content.toLowerCase().includes('cohort simulator') ||
                  prevMsg.content.toLowerCase().includes('startup retention'));
              if (m.role === 'assistant' && isRetentionReq) {
                return {
                  ...m,
                  artifactId: 'demo-retention-calc',
                  artifactTitle: 'Customer Retention & Cohort Simulator',
                  artifactType: 'html' as const,
                };
              }
              return m;
            });
            setMessages(mapped);
            const latestWithArtifact = [...mapped].reverse().find((m) => m.artifactId);
            if (latestWithArtifact?.artifactId) {
              handleOpenArtifact(latestWithArtifact.artifactId);
            }
          })
          .catch((err) => console.warn('Could not load messages:', err.message));
      }
    });
  }, [refreshSessions]);

  // Switch to another session
  const handleSelectSession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      setCurrentSessionId(sessionId);
      const targetSession = sessions.find((s) => s.id === sessionId);
      if (targetSession?.model_provider && ['ollama', 'anthropic', 'openai'].includes(targetSession.model_provider)) {
        setCurrentProvider(targetSession.model_provider as ModelProvider);
      }
      const msgs = await getSessionMessages(sessionId);
      const mapped = msgs.map((m, idx) => {
        if (m.artifactId) return m;
        const prevMsg = idx > 0 ? msgs[idx - 1] : null;
        const isRetentionReq =
          prevMsg &&
          prevMsg.role === 'user' &&
          (prevMsg.content.toLowerCase().includes('retention dashboard') ||
            prevMsg.content.toLowerCase().includes('html dashboard') ||
            prevMsg.content.toLowerCase().includes('cohort simulator') ||
            prevMsg.content.toLowerCase().includes('startup retention'));
        if (m.role === 'assistant' && isRetentionReq) {
          return {
            ...m,
            artifactId: 'demo-retention-calc',
            artifactTitle: 'Customer Retention & Cohort Simulator',
            artifactType: 'html' as const,
          };
        }
        return m;
      });
      setMessages(mapped);
      const latestWithArtifact = [...mapped].reverse().find((m) => m.artifactId);
      if (latestWithArtifact?.artifactId) {
        handleOpenArtifact(latestWithArtifact.artifactId);
      } else {
        setActiveArtifact(null);
      }
    } catch (err: any) {
      setErrorMessage(`Failed to load session history: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Start a new chat session
  const handleNewChat = async () => {
    try {
      setIsLoading(true);
      setErrorMessage(null);
      const newSession = await createSession('New Chat', currentProvider);
      setCurrentSessionId(newSession.id);
      setMessages([]);
      setActiveArtifact(null);
      await refreshSessions();
    } catch (err: any) {
      // Fallback: local session reset if backend is temporarily unreachable
      setCurrentSessionId(null);
      setMessages([]);
      setActiveArtifact(null);
      setErrorMessage(`Could not create session on server: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete a session
  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      const remaining = await refreshSessions();
      if (currentSessionId === sessionId) {
        if (remaining.length > 0) {
          handleSelectSession(remaining[0].id);
        } else {
          setCurrentSessionId(null);
          setMessages([]);
          setActiveArtifact(null);
        }
      }
    } catch (err: any) {
      setErrorMessage(`Failed to delete session: ${err.message}`);
    }
  };

  // Send message handler (Direct FastAPI backend connection)
  const handleSendMessage = async (content: string) => {
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setErrorMessage(null);

    // Check if the prompt requests the demo HTML dashboard
    const isDashboardRequest = content.toLowerCase().includes('html dashboard') || content.toLowerCase().includes('retention');
    const artifactToAttach = isDashboardRequest ? DEMO_ARTIFACTS.html : undefined;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(content, currentSessionId || undefined, currentProvider);

      if (response.session_id && response.session_id !== currentSessionId) {
        setCurrentSessionId(response.session_id);
      }

      let attachedArtifact: Artifact | undefined = undefined;

      if (response.artifact) {
        attachedArtifact = {
          id: response.artifact.id,
          title: response.artifact.title,
          type: response.artifact.type,
          content: response.artifact.content || response.message,
          createdAt: response.artifact.created_at
            ? new Date(response.artifact.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : timestamp,
          isDemonstration: Boolean(response.artifact.is_demonstration),
        };
      } else if (artifactToAttach) {
        attachedArtifact = artifactToAttach;
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        provider: response.provider || currentProvider,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        artifactId: attachedArtifact?.id,
        artifactTitle: attachedArtifact?.title,
        artifactType: attachedArtifact?.type,
        sources: response.sources || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (attachedArtifact) {
        setActiveArtifact(attachedArtifact);
        setActiveMobileView('artifact');
      }

      // Refresh sessions in background to update title & message counts
      refreshSessions();
    } catch (err: any) {
      console.error('Failed to send message:', err);
      const errMsg = err.message || 'Server connection failed.';
      setErrorMessage(`Failed to reach backend: ${errMsg}`);

      const fallbackAssistantMessage: ChatMessage = {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Connection Error**: Could not reach The Lenny Growth Assistant API.\n\nDetail: ${errMsg}\n\nEnsure the backend server is running on port 8000.`,
        provider: currentProvider,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, fallbackAssistantMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenArtifact = async (artifactId: string) => {
    if (!artifactId) return;

    // 1. Check local demo artifacts first (by ID or type)
    const foundDemo = Object.values(DEMO_ARTIFACTS).find(
      (a) => a.id === artifactId || a.type === artifactId
    );
    if (foundDemo) {
      setActiveArtifact(foundDemo);
      setActiveMobileView('artifact');
      return;
    }

    // 1b. Match common keywords or aliases for demo artifacts
    const lowerId = artifactId.toLowerCase();
    if (
      lowerId === 'html' ||
      lowerId.includes('retention') ||
      lowerId.includes('cohort') ||
      lowerId.includes('simulator') ||
      lowerId.includes('calc') ||
      lowerId.includes('dashboard')
    ) {
      setActiveArtifact(DEMO_ARTIFACTS.html);
      setActiveMobileView('artifact');
      return;
    }
    if (
      lowerId === 'markdown' ||
      lowerId.includes('strategy') ||
      lowerId.includes('playbook') ||
      lowerId.includes('audit')
    ) {
      setActiveArtifact(DEMO_ARTIFACTS.markdown);
      setActiveMobileView('artifact');
      return;
    }
    if (
      lowerId === 'essay' ||
      lowerId.includes('ship30') ||
      lowerId.includes('leaky') ||
      lowerId.includes('bucket')
    ) {
      setActiveArtifact(DEMO_ARTIFACTS.essay);
      setActiveMobileView('artifact');
      return;
    }

    // 2. If it's already active, just switch view
    if (activeArtifact && activeArtifact.id === artifactId) {
      setActiveMobileView('artifact');
      return;
    }

    // 3. Fetch from backend API
    try {
      const saved = await getArtifact(artifactId);
      setActiveArtifact(saved);
      setActiveMobileView('artifact');
    } catch (err: any) {
      console.error(`Failed to load artifact ${artifactId}:`, err);
      // Fallback: if it's retention or html related, show the demo HTML dashboard
      if (
        lowerId.includes('retention') ||
        lowerId.includes('dashboard') ||
        lowerId.includes('calc') ||
        lowerId === 'html'
      ) {
        setActiveArtifact(DEMO_ARTIFACTS.html);
        setActiveMobileView('artifact');
      } else {
        setErrorMessage(`Could not load artifact: ${err.message}`);
      }
    }
  };

  const handleLoadDemoArtifact = (type: 'html' | 'markdown' | 'essay') => {
    const demo = DEMO_ARTIFACTS[type];
    if (demo) {
      setActiveArtifact(demo);
      setActiveMobileView('artifact');
    }
  };

  const handleClearArtifact = () => {
    setActiveArtifact(null);
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-dark-bg text-slate-100 overflow-hidden">
      {/* Top Header */}
      <Header
        currentProvider={currentProvider}
        onSelectProvider={setCurrentProvider}
        activeMobileView={activeMobileView}
        setActiveMobileView={setActiveMobileView}
        hasActiveArtifact={activeArtifact !== null}
        statusData={providerStatus}
        onRefreshStatus={refreshProviderStatus}
      />

      {/* Main 2-Pane Split Layout */}
      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Pane: Chat Interface */}
        <div
          className={`h-full transition-all duration-200 ${
            activeMobileView === 'chat' ? 'w-full' : 'hidden'
          } md:block md:w-1/2 lg:w-5/12`}
        >
          <ChatPane
            messages={messages}
            onSendMessage={handleSendMessage}
            onNewChat={handleNewChat}
            onOpenArtifact={handleOpenArtifact}
            isLoading={isLoading}
            sessions={sessions}
            currentSessionId={currentSessionId}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
            errorMessage={errorMessage}
            onDismissError={() => setErrorMessage(null)}
          />
        </div>

        {/* Right Pane: Artifact Viewer */}
        <div
          className={`h-full transition-all duration-200 ${
            activeMobileView === 'artifact' ? 'w-full' : 'hidden'
          } md:block md:w-1/2 lg:w-7/12`}
        >
          <ArtifactViewer
            artifact={activeArtifact}
            onClearArtifact={handleClearArtifact}
            onLoadDemoArtifact={handleLoadDemoArtifact}
          />
        </div>
      </main>
    </div>
  );
};
