import { Sun, Moon, Menu, Layers, Terminal } from 'lucide-react';
import { ViewState } from '../types';
import { useTheme } from '../hooks/useTheme';

interface TopNavProps {
  view: ViewState;
  onToggleMobileSidebar?: () => void;
  openSettings?: () => void;
  selectedModel?: string;
}

export function TopNav({ view, onToggleMobileSidebar, openSettings, selectedModel = 'Gemini 3.1 Flash Lite' }: TopNavProps) {
  const { theme, toggleTheme } = useTheme();

  const viewLabels: Record<ViewState, { title: string; category: string }> = {
    chat: { title: 'Content Studio', category: 'Creation Hub' },
    graph: { title: 'Agent Graph', category: 'LangGraph Topology' },
    content: { title: 'Studio & Assets', category: 'Output Center' },
  };

  const current = viewLabels[view] || { title: 'Workspace', category: 'AI Content Factory' };

  return (
    <nav className="sticky top-0 w-full z-40 bg-base-950/85 backdrop-blur-xl flex justify-between items-center px-4 md:px-8 py-2.5 border-b border-white/6 h-14 shrink-0 shadow-sm transition-colors">
      {/* Left: Brand / View Breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobileSidebar}
          className="md:hidden p-2 rounded-xl text-base-400 hover:text-base-100 hover:bg-white/5 transition-colors cursor-pointer"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent-500/10 border border-accent-500/20 flex items-center justify-center text-accent-400 shadow-sm shrink-0">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-base-400 hidden sm:inline">{current.category}</span>
              <span className="text-xs text-base-600 hidden sm:inline">/</span>
              <h2 className="text-sm font-bold text-base-100 tracking-tight">{current.title}</h2>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Status Pill & Controls */}
      <div className="flex items-center gap-2.5">
        {/* Engine status indicator */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-base-900 border border-white/8 text-xs text-base-300">
          <span className="w-2 h-2 rounded-full bg-signal-success animate-pulse shrink-0" />
          <span className="text-[11px] font-medium text-base-400">Model:</span>
          <span className="text-[11px] font-mono font-semibold text-base-200 truncate max-w-[140px]">{selectedModel}</span>
        </div>

        {/* Settings button if provided */}
        {openSettings && (
          <button
            onClick={openSettings}
            className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-base-300 hover:text-base-100 hover:bg-white/5 border border-transparent hover:border-white/8 transition-all cursor-pointer"
            title="Configure AI Models & Quotas"
          >
            <Terminal className="w-3.5 h-3.5 text-accent-400" />
            <span>Config</span>
          </button>
        )}

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-xl text-base-400 hover:text-accent-400 hover:bg-white/5 border border-transparent hover:border-white/8 transition-all cursor-pointer"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        {/* Workspace Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-base-900 border border-white/8 text-[11px] font-semibold text-base-300">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-400" />
          <span>Local Engine</span>
        </div>
      </div>
    </nav>
  );
}
