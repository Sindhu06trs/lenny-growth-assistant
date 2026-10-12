import React, { useState } from 'react';
import { User, Sparkles, AlertCircle, FileCode, ArrowRight, BookOpen, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import type { ChatMessage } from '../types/chat.ts';

interface MessageBubbleProps {
  message: ChatMessage;
  onOpenArtifact?: (artifactId: string) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onOpenArtifact,
}) => {
  const [showCitations, setShowCitations] = useState(true);
  const isUser = message.role === 'user';
  const isNotice = message.isNotice || message.role === 'system';

  if (isNotice) {
    return (
      <div className="flex justify-center my-4">
        <div className="flex items-start gap-3 max-w-xl p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-xs leading-relaxed shadow-sm">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-amber-300">Backend Notice</div>
            <div className="text-amber-200/90">{message.content}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex items-start gap-3 my-4 group ${
        isUser ? 'flex-row-reverse justify-start' : 'justify-start'
      }`}
    >
      {/* Avatar Badge */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-md ${
          isUser
            ? 'bg-brand-600 text-white ring-2 ring-brand-500/30'
            : 'bg-dark-card border border-dark-border text-brand-400'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4 text-brand-400" />}
      </div>

      {/* Message Content Container */}
      <div
        className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-4 transition-all shadow-sm ${
          isUser
            ? 'bg-brand-600/20 border border-brand-500/40 text-slate-100 rounded-tr-sm'
            : 'bg-dark-surface border border-dark-border text-slate-200 rounded-tl-sm'
        }`}
      >
        {/* Header: Role & Timestamp */}
        <div className="flex items-center gap-2 mb-1.5 text-[11px] text-slate-400">
          <span className="font-medium text-slate-300">
            {isUser ? 'You' : 'The Lenny Growth Assistant'}
          </span>
          {message.provider && (
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-dark-card border border-dark-border text-brand-300">
              {message.provider}
            </span>
          )}
          <span>•</span>
          <span>{message.timestamp}</span>
        </div>

        {/* Text Body */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
        </div>

        {/* Verified Transcript Sources & Citations (Step 07) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-dark-border/60">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-brand-300">
                <BookOpen className="w-3.5 h-3.5 text-brand-400" />
                <span>Verified Sources & Citations ({message.sources.length})</span>
              </div>
              <button
                type="button"
                onClick={() => setShowCitations(!showCitations)}
                className="text-[11px] text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1 cursor-pointer"
                aria-label={showCitations ? "Hide citations" : "Show citations"}
              >
                <span>{showCitations ? 'Hide' : 'View'}</span>
                {showCitations ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            </div>

            {showCitations && (
              <div className="space-y-2 mt-2">
                {message.sources.map((source, idx) => (
                  <div
                    key={source.id || idx}
                    className="p-2.5 rounded-lg bg-dark-card/80 border border-dark-border/70 text-xs text-slate-300 space-y-1.5 shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="font-medium text-slate-200 leading-snug">
                        {source.title}
                        {source.guest && (
                          <span className="text-slate-400 font-normal text-[11px]"> • Guest: {source.guest}</span>
                        )}
                      </div>
                      {source.timestamp && (
                        <span className="shrink-0 text-[10px] font-mono px-1.5 py-0.5 rounded bg-brand-500/10 text-brand-400 border border-brand-500/20">
                          {source.timestamp}
                        </span>
                      )}
                    </div>

                    {source.excerpt && (
                      <p className="text-[11px] text-slate-300/90 leading-relaxed italic border-l-2 border-brand-500/40 pl-2 py-0.5">
                        "{source.excerpt}"
                      </p>
                    )}

                    {source.youtube_url && (
                      <div className="pt-1">
                        <a
                          href={source.youtube_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-brand-400 hover:text-brand-300 transition-colors hover:underline"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>Watch on YouTube{source.timestamp ? ` (${source.timestamp})` : ''}</span>
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Embedded Artifact Reference Card if present */}
        {(message.artifactId || (message.artifactTitle && message.artifactTitle.length > 0)) && (
          <div className="mt-3 pt-3 border-t border-dark-border/60">
            <button
              onClick={() => {
                const targetId = message.artifactId || (message.artifactType === 'html' ? 'demo-retention-calc' : 'demo-retention-calc');
                if (onOpenArtifact) onOpenArtifact(targetId);
              }}
              className="w-full flex items-center justify-between p-2.5 rounded-lg bg-dark-card hover:bg-dark-hover border border-dark-border group/btn transition-colors text-left cursor-pointer"
              aria-label={`Open artifact ${message.artifactTitle || 'Generated Artifact'}`}
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-md bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  <FileCode className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold text-slate-200 group-hover/btn:text-brand-300 transition-colors">
                    {message.artifactTitle || 'Interactive Artifact'}
                  </div>
                  <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
                    {message.artifactType || 'Artifact'} • Click to view
                  </div>
                </div>
              </div>
              <div className="flex items-center text-xs text-brand-400 gap-1 font-medium group-hover/btn:translate-x-0.5 transition-transform">
                <span>Open in Viewer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
