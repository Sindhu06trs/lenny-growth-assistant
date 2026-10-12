import React from 'react';
import { Sparkles, MessageSquare, FileCode } from 'lucide-react';
import { ModelProvider, ProviderStatusResponse } from '../types/chat';
import { ProviderStatus } from './ProviderStatus';

interface HeaderProps {
  currentProvider: ModelProvider;
  onSelectProvider: (provider: ModelProvider) => void;
  activeMobileView: 'chat' | 'artifact';
  setActiveMobileView: (view: 'chat' | 'artifact') => void;
  hasActiveArtifact: boolean;
  statusData?: ProviderStatusResponse | null;
  onRefreshStatus?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentProvider,
  onSelectProvider,
  activeMobileView,
  setActiveMobileView,
  hasActiveArtifact,
  statusData,
  onRefreshStatus,
}) => {
  return (
    <header className="flex items-center justify-between px-4 py-3 bg-dark-surface border-b border-dark-border select-none z-20">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm md:text-base font-bold text-slate-100 tracking-tight">
              The Lenny Growth Assistant
            </h1>
            <span className="hidden sm:inline-block text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
              FDE Assessment
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            Podcast Transcript Intelligence & Strategy Engine
          </p>
        </div>
      </div>

      {/* Center Mobile View Switcher (Visible only on small screens) */}
      <div className="flex md:hidden items-center p-0.5 rounded-lg bg-dark-card border border-dark-border">
        <button
          onClick={() => setActiveMobileView('chat')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
            activeMobileView === 'chat'
              ? 'bg-brand-600 text-white'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          aria-label="Show chat view"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          <span>Chat</span>
        </button>

        <button
          onClick={() => setActiveMobileView('artifact')}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors relative ${
            activeMobileView === 'artifact'
              ? 'bg-brand-600 text-white'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          aria-label="Show artifact viewer"
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>Artifact</span>
          {hasActiveArtifact && activeMobileView !== 'artifact' && (
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
          )}
        </button>
      </div>

      {/* Right: Model Provider Status Pill */}
      <div className="flex items-center gap-3">
        <ProviderStatus
          currentProvider={currentProvider}
          onSelectProvider={onSelectProvider}
          statusData={statusData}
          onRefreshStatus={onRefreshStatus}
        />
      </div>
    </header>
  );
};
