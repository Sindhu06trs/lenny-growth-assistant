import React, { useState } from 'react';
import { Radio, AlertCircle, ChevronDown, Check, Server, Cloud, Cpu, RefreshCw } from 'lucide-react';
import { ModelProvider, ProviderStatusResponse } from '../types/chat';

interface ProviderStatusProps {
  currentProvider: ModelProvider;
  onSelectProvider: (provider: ModelProvider) => void;
  statusData?: ProviderStatusResponse | null;
  onRefreshStatus?: () => void;
}

export const ProviderStatus: React.FC<ProviderStatusProps> = ({
  currentProvider,
  onSelectProvider,
  statusData,
  onRefreshStatus,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const providerMeta: Record<ModelProvider, { name: string; icon: React.ReactNode }> = {
    ollama: {
      name: 'Ollama (Local LLM)',
      icon: <Cpu className="w-3.5 h-3.5" />,
    },
    anthropic: {
      name: 'Anthropic Claude',
      icon: <Cloud className="w-3.5 h-3.5" />,
    },
    openai: {
      name: 'OpenAI GPT-4o',
      icon: <Server className="w-3.5 h-3.5" />,
    },
  };

  const currentInfo = statusData?.providers?.[currentProvider];
  const currentStatus = currentInfo?.status || 'unavailable';

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return (
          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Connected
          </span>
        );
      case 'configured':
        return (
          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-sky-500/15 text-sky-400 border border-sky-500/30 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
            Configured
          </span>
        );
      case 'model_not_found':
        return (
          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Model Missing
          </span>
        );
      case 'authentication_failed':
        return (
          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
            Auth Error
          </span>
        );
      default:
        return (
          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-slate-500/15 text-slate-400 border border-slate-500/30 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
            Offline
          </span>
        );
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-dark-surface hover:bg-dark-hover border border-dark-border text-xs text-slate-300 transition-all shadow-sm"
        aria-label="AI Provider status and model selection"
        aria-expanded={isOpen}
      >
        <span className="text-slate-400">
          {providerMeta[currentProvider]?.icon}
        </span>

        <span className="font-medium text-slate-200">
          {currentInfo?.model || providerMeta[currentProvider]?.name}
        </span>

        {getStatusBadge(currentStatus)}

        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-84 rounded-xl bg-dark-surface border border-dark-border shadow-2xl p-3 z-50 animate-in fade-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-dark-border text-slate-300">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-brand-400" />
                <span className="text-xs font-semibold text-slate-200">
                  Select AI Provider
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-slate-500">Live Status</span>
                {onRefreshStatus && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onRefreshStatus();
                    }}
                    className="p-1 rounded hover:bg-dark-card text-slate-400 hover:text-slate-200 transition-colors"
                    title="Refresh AI Provider Status"
                    aria-label="Refresh AI Provider Status"
                  >
                    <RefreshCw className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-1.5 mb-3">
              {(Object.keys(providerMeta) as ModelProvider[]).map((pKey) => {
                const isSelected = currentProvider === pKey;
                const pInfo = statusData?.providers?.[pKey];
                const pStatus = pInfo?.status || 'unavailable';

                return (
                  <button
                    key={pKey}
                    onClick={() => {
                      onSelectProvider(pKey);
                      setIsOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-lg flex items-start justify-between transition-colors ${
                      isSelected
                        ? 'bg-brand-500/15 border border-brand-500/40 text-slate-100'
                        : 'hover:bg-dark-card border border-dark-border/40 text-slate-300'
                    }`}
                  >
                    <div className="space-y-0.5 max-w-[200px]">
                      <div className="text-xs font-medium text-slate-200 flex items-center gap-1.5">
                        {providerMeta[pKey].icon}
                        <span>{providerMeta[pKey].name}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {pInfo?.model || 'default'}
                      </div>
                      {pInfo?.detail && (
                        <div className="text-[10px] text-slate-500 leading-tight truncate">
                          {pInfo.detail}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {getStatusBadge(pStatus)}
                      {isSelected && (
                        <Check className="w-3.5 h-3.5 text-brand-400 mt-1" />
                      )}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Ollama Installed Models Pill if Ollama connected */}
            {statusData?.providers?.ollama?.available_models?.length ? (
              <div className="p-2 mb-2 rounded-lg bg-dark-card border border-dark-border text-[11px] text-slate-300">
                <span className="text-[10px] font-semibold text-slate-400 block mb-1">
                  Installed Ollama Models:
                </span>
                <div className="flex flex-wrap gap-1">
                  {statusData.providers.ollama.available_models.map((m) => (
                    <span
                      key={m}
                      className="px-1.5 py-0.5 rounded bg-dark-surface border border-dark-border text-[10px] font-mono text-slate-300"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="flex items-start gap-2 p-2 rounded-lg bg-dark-card border border-dark-border text-[11px] text-slate-400 leading-relaxed">
              <AlertCircle className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
              <div>
                <strong>Notice:</strong> Step 06 connects live chat inference. Lenny's transcript RAG grounding is planned for <strong>Step 07</strong>.
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
