import React, { useState, useMemo } from 'react';
import {
  Code,
  Eye,
  Columns,
  Copy,
  Check,
  Download,
  Trash2,
  FileCode,
  Sparkles,
  AlertTriangle,
  Info,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { Artifact, ArtifactTab } from '../types/artifact';

interface ArtifactViewerProps {
  artifact: Artifact | null;
  onClearArtifact: () => void;
  onLoadDemoArtifact?: (type: 'html' | 'markdown' | 'essay') => void;
}

import { cleanMarkdownContent } from '../services/markdown';

export { cleanMarkdownContent };

// Configured marked renderer for links and horizontal rules
const customRenderer = new marked.Renderer();

customRenderer.link = function ({ href, title, tokens }: { href: string; title?: string | null; tokens: any[] }) {
  const text = this.parser.parseInline(tokens);
  const titleAttr = title ? ` title="${title}"` : '';
  const isExternal = typeof href === 'string' && (href.startsWith('http://') || href.startsWith('https://'));
  const targetAttr = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';
  return `<a href="${href}"${titleAttr}${targetAttr}>${text}</a>`;
};

customRenderer.hr = function () {
  return '<hr />\n';
};

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifact,
  onClearArtifact,
  onLoadDemoArtifact,
}) => {
  const [activeTab, setActiveTab] = useState<ArtifactTab>('preview');
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Safe sanitized HTML from Markdown
  const sanitizedMarkdownHtml = useMemo(() => {
    if (!artifact || (artifact.type !== 'markdown' && artifact.type !== 'essay')) {
      return '';
    }
    try {
      const cleaned = cleanMarkdownContent(artifact.content, artifact.title);
      const rawHtml = marked.parse(cleaned, {
        async: false,
        gfm: true,
        breaks: false,
        renderer: customRenderer,
      }) as string;
      return DOMPurify.sanitize(rawHtml, {
        USE_PROFILES: { html: true },
        ADD_ATTR: ['target', 'rel', 'class', 'href', 'title'],
      });
    } catch (err) {
      console.error('Markdown parse error:', err);
      return '<p class="text-rose-400">Error rendering Markdown artifact.</p>';
    }
  }, [artifact]);

  // Safe self-contained HTML content for HTML widgets (rendered inside sandboxed iframe)
  const renderedHtmlContent = useMemo(() => {
    if (!artifact || artifact.type !== 'html') {
      return '';
    }
    let content = artifact.content.trim();
    // Strip markdown code fences if wrapped by LLM (```html ... ```)
    if (content.startsWith('```html')) {
      content = content.replace(/^```html\s*/i, '').replace(/\s*```$/, '');
    } else if (content.startsWith('```')) {
      content = content.replace(/^```\s*/, '').replace(/\s*```$/, '');
    }
    return content;
  }, [artifact]);

  const handleCopy = async () => {
    if (!artifact) return;
    try {
      await navigator.clipboard.writeText(artifact.content);
      setCopied(true);
      setCopyError(null);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Clipboard copy failed:', err);
      setCopyError('Failed to copy to clipboard.');
      setTimeout(() => setCopyError(null), 3000);
    }
  };

  const handleDownload = () => {
    if (!artifact) return;
    try {
      const extension =
        artifact.type === 'html'
          ? 'html'
          : artifact.type === 'essay'
          ? 'md'
          : 'md';
      const filename = `${artifact.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '') || 'artifact'}.${extension}`;

      const blob = new Blob([artifact.content], {
        type: artifact.type === 'html' ? 'text/html' : 'text/markdown',
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setDownloadError(null);
    } catch (err) {
      console.error('Download failed:', err);
      setDownloadError('Failed to download artifact file.');
      setTimeout(() => setDownloadError(null), 3000);
    }
  };

  // Empty State
  if (!artifact) {
    return (
      <div className="flex flex-col h-full bg-dark-surface/40 border-l border-dark-border p-6 justify-center items-center text-center">
        <div className="w-14 h-14 rounded-2xl bg-dark-card border border-dark-border flex items-center justify-center text-slate-400 mb-4 shadow-inner">
          <FileCode className="w-7 h-7 text-brand-400/80" />
        </div>

        <h3 className="text-base font-semibold text-slate-200 mb-1">
          Artifact Viewer
        </h3>
        <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-6">
          When the assistant generates interactive HTML tools, strategy roadmaps, or Ship 30 essays, they will render live in this dedicated side-by-side pane.
        </p>

        {onLoadDemoArtifact && (
          <div className="w-full max-w-md p-4 rounded-xl bg-dark-card/70 border border-dark-border text-left">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300">
              <Sparkles className="w-4 h-4 text-brand-400" />
              <span>Explore Sample Artifacts (UI Demonstration)</span>
            </div>
            <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
              Click below to test the sandboxed HTML, Markdown, and Split-view renderers. <em>(Clearly labeled as demonstration data — not transcript content).</em>
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <button
                onClick={() => onLoadDemoArtifact('html')}
                className="p-2 rounded-lg bg-dark-surface hover:bg-dark-hover border border-dark-border hover:border-brand-500/40 text-center transition-all text-xs font-medium text-slate-200 hover:text-white"
              >
                ⚡ HTML Widget
              </button>
              <button
                onClick={() => onLoadDemoArtifact('markdown')}
                className="p-2 rounded-lg bg-dark-surface hover:bg-dark-hover border border-dark-border hover:border-brand-500/40 text-center transition-all text-xs font-medium text-slate-200 hover:text-white"
              >
                📋 Strategy Guide
              </button>
              <button
                onClick={() => onLoadDemoArtifact('essay')}
                className="p-2 rounded-lg bg-dark-surface hover:bg-dark-hover border border-dark-border hover:border-brand-500/40 text-center transition-all text-xs font-medium text-slate-200 hover:text-white"
              >
                ✍️ Ship 30 Essay
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col h-full bg-dark-bg transition-all ${
        isFullscreen ? 'fixed inset-0 z-50 bg-dark-bg p-4' : 'relative'
      }`}
    >
      {/* Top Action & Tab Header */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 border-b border-dark-border bg-dark-surface/90 backdrop-blur-md gap-2 z-10">
        {/* Artifact Title & Type Tag */}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-1.5 rounded-md bg-brand-500/10 text-brand-400 border border-brand-500/20 shrink-0">
            <FileCode className="w-4 h-4" />
          </div>
          <div className="truncate">
            <div className="flex items-center gap-2">
              <h3 className="text-xs md:text-sm font-semibold text-slate-100 truncate">
                {artifact.title}
              </h3>
              {artifact.isDemonstration && (
                <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  Demo
                </span>
              )}
            </div>
            <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">
              Format: {artifact.type}
            </div>
          </div>
        </div>

        {/* Tab Switcher & Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Tabs: Preview / Code / Split */}
          <div
            className="flex items-center p-0.5 rounded-lg bg-dark-card border border-dark-border"
            role="tablist"
            aria-label="Artifact display mode"
          >
            <button
              role="tab"
              aria-selected={activeTab === 'preview'}
              onClick={() => setActiveTab('preview')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'preview'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>

            <button
              role="tab"
              aria-selected={activeTab === 'code'}
              onClick={() => setActiveTab('code')}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'code'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>Code</span>
            </button>

            <button
              role="tab"
              aria-selected={activeTab === 'split'}
              onClick={() => setActiveTab('split')}
              className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'split'
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Split</span>
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg bg-dark-card hover:bg-dark-hover border border-dark-border text-slate-300 hover:text-white transition-colors relative"
              title="Copy artifact source code"
              aria-label="Copy artifact source code"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-growth-emerald" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>

            <button
              onClick={handleDownload}
              className="p-1.5 rounded-lg bg-dark-card hover:bg-dark-hover border border-dark-border text-slate-300 hover:text-white transition-colors"
              title="Download artifact file"
              aria-label="Download artifact file"
            >
              <Download className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-1.5 rounded-lg bg-dark-card hover:bg-dark-hover border border-dark-border text-slate-300 hover:text-white transition-colors"
              title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
              aria-label={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? (
                <Minimize2 className="w-3.5 h-3.5" />
              ) : (
                <Maximize2 className="w-3.5 h-3.5" />
              )}
            </button>

            <button
              onClick={onClearArtifact}
              className="p-1.5 rounded-lg bg-dark-card hover:bg-rose-500/20 border border-dark-border hover:border-rose-500/30 text-slate-400 hover:text-rose-300 transition-colors"
              title="Close artifact"
              aria-label="Close artifact"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Alert / Feedback Banners */}
      {copyError && (
        <div className="px-4 py-2 bg-rose-500/10 border-b border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{copyError}</span>
        </div>
      )}
      {downloadError && (
        <div className="px-4 py-2 bg-rose-500/10 border-b border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{downloadError}</span>
        </div>
      )}

      {/* Demonstration disclaimer notice if active */}
      {artifact.isDemonstration && (
        <div className="px-4 py-1.5 bg-dark-card border-b border-dark-border text-[11px] text-amber-300/90 flex items-center gap-2">
          <Info className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>
            <strong>Demonstration Artifact:</strong> Provided for UI testing. Real artifacts will be compiled from transcripts in Step 07.
          </span>
        </div>
      )}

      {/* Main Viewport Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {/* 1. Preview Mode */}
        {activeTab === 'preview' && (
          <div className="h-full w-full overflow-y-auto p-4 md:p-6 bg-dark-bg flex flex-col">
            {artifact.type === 'html' ? (
              <div className="h-full w-full rounded-xl overflow-hidden border border-dark-border bg-[#0F172A] shadow-lg flex flex-col min-h-[500px]">
                <iframe
                  title={`Sandbox preview of ${artifact.title}`}
                  srcDoc={renderedHtmlContent}
                  sandbox="allow-scripts"
                  className="w-full flex-1 border-none min-h-[500px]"
                />
              </div>
            ) : artifact.type === 'essay' ? (
              <article className="max-w-2xl mx-auto py-6 px-4 bg-dark-surface/50 border border-dark-border rounded-2xl shadow-xl">
                <div className="pb-3 mb-5 border-b border-dark-border flex items-center justify-between text-xs text-slate-400">
                  <span className="text-[11px] font-semibold tracking-wider uppercase text-brand-400">
                    Ship 30 for 30 Atomic Essay
                  </span>
                  {artifact.createdAt && (
                    <span className="text-[10px] text-slate-400 font-mono">
                      {artifact.createdAt}
                    </span>
                  )}
                </div>
                <div
                  className="prose-dark font-serif text-slate-200 text-sm md:text-base leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: sanitizedMarkdownHtml }}
                />
              </article>
            ) : (
              <div className="max-w-3xl mx-auto p-4 bg-dark-surface/30 rounded-xl border border-dark-border">
                <div
                  className="prose-dark text-sm leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: sanitizedMarkdownHtml }}
                />
              </div>
            )}
          </div>
        )}

        {/* 2. Code Mode */}
        {activeTab === 'code' && (
          <div className="h-full w-full overflow-y-auto p-4 bg-[#0A0E17]">
            <pre className="font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap break-all p-4 bg-dark-surface/40 rounded-xl border border-dark-border selection:bg-brand-500/30">
              <code>{artifact.content}</code>
            </pre>
          </div>
        )}

        {/* 3. Split Mode (Side by Side) */}
        {activeTab === 'split' && (
          <div className="h-full w-full grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-dark-border">
            {/* Left: Code */}
            <div className="h-full overflow-y-auto p-4 bg-[#0A0E17]">
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-2 px-1">
                Source Code
              </div>
              <pre className="font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap break-all p-3 bg-dark-surface/40 rounded-xl border border-dark-border">
                <code>{artifact.content}</code>
              </pre>
            </div>

            {/* Right: Live Render */}
            <div className="h-full overflow-y-auto p-4 bg-dark-bg flex flex-col">
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-2 px-1 shrink-0">
                Live Output
              </div>
              {artifact.type === 'html' ? (
                <div className="h-[calc(100%-28px)] rounded-xl overflow-hidden border border-dark-border bg-[#0F172A] shadow-md flex flex-col min-h-[350px]">
                  <iframe
                    title={`Split preview of ${artifact.title}`}
                    srcDoc={renderedHtmlContent}
                    sandbox="allow-scripts"
                    className="w-full flex-1 border-none min-h-[350px]"
                  />
                </div>
              ) : (
                <div
                  className="prose-dark text-xs md:text-sm p-4 bg-dark-surface/40 rounded-xl border border-dark-border leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: sanitizedMarkdownHtml }}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
