import React from 'react';
import {
  LayoutGrid,
  FileText,
  CheckCircle2,
  GitCompare,
  Clock,
  AlertTriangle,
  Plus,
  Trash2
} from 'lucide-react';
import type { DashboardStats } from '../types';

export type NavTab = 'overview' | 'documents' | 'facts' | 'relationships' | 'timeline' | 'review';

interface AppLayoutProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  onOpenUpload: () => void;
  onClearAll?: () => void;
  stats?: DashboardStats | null;
  children: React.ReactNode;
}

interface NavItemConfig {
  id: NavTab;
  label: string;
  icon: React.FC<{ className?: string }>;
  getCount?: (stats?: DashboardStats | null) => number | undefined;
  isWarningBadge?: boolean;
}

const NAV_ITEMS: NavItemConfig[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: LayoutGrid,
  },
  {
    id: 'documents',
    label: 'Documents',
    icon: FileText,
    getCount: (stats) => stats?.total_documents,
  },
  {
    id: 'facts',
    label: 'Facts',
    icon: CheckCircle2,
    getCount: (stats) => stats?.total_facts,
  },
  {
    id: 'relationships',
    label: 'Relationships',
    icon: GitCompare,
    getCount: (stats) => stats?.total_relationships,
  },
  {
    id: 'timeline',
    label: 'Timeline',
    icon: Clock,
  },
  {
    id: 'review',
    label: 'Review',
    icon: AlertTriangle,
    getCount: (stats) => stats?.needs_review_count,
    isWarningBadge: true,
  },
];

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentTab,
  onTabChange,
  onOpenUpload,
  onClearAll,
  stats,
  children,
}) => {
  return (
    <div className="flex flex-col h-screen w-screen bg-stone-50/50 text-stone-900 overflow-hidden font-sans antialiased">
      {/* Top Header across entire full width */}
      <header className="h-14 border-b border-stone-200/80 bg-white px-6 flex items-center justify-between shrink-0 z-10">
        {/* Left: Dot + Title + Divider + Subtitle */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xl leading-none text-black">●</span>
            <span className="font-bold text-stone-900 text-sm tracking-tight">KnowledgeMesh</span>
          </div>
          <span className="text-stone-300 font-light text-sm">|</span>
          <span className="text-xs text-stone-400 font-normal">Evidence-backed document intelligence</span>
        </div>

        {/* Right: Trash / Reset + Upload PDF */}
        <div className="flex items-center gap-3">
          {onClearAll && (
            <button
              type="button"
              onClick={onClearAll}
              title="Reset Knowledge Base"
              className="p-1.5 text-stone-400 hover:text-rose-600 hover:bg-stone-100 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}

          <button
            type="button"
            onClick={onOpenUpload}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black text-white hover:bg-stone-800 text-xs font-medium transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload PDF</span>
          </button>
        </div>
      </header>

      {/* Main App Body: Sidebar + Content */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-56 border-r border-stone-200/80 bg-white flex flex-col justify-between shrink-0 select-none">
          <div className="p-3">
            <div className="text-[10px] font-bold text-stone-400 uppercase tracking-wider px-3 pt-3 pb-2">
              KNOWLEDGE BASE
            </div>

            <nav className="space-y-1">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                const count = item.getCount ? item.getCount(stats) : undefined;

                return (
                  <button
                    key={item.id}
                    onClick={() => onTabChange(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'bg-stone-100 text-stone-900 font-semibold'
                        : 'text-stone-600 hover:bg-stone-50 hover:text-stone-900'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`h-4 w-4 ${isActive ? 'text-stone-900' : 'text-stone-400'}`} />
                      <span>{item.label}</span>
                    </div>

                    {count !== undefined && count > 0 && (
                      <span
                        className={`text-[10px] font-mono font-medium px-1.5 py-0.5 rounded-full ${
                          item.isWarningBadge
                            ? 'bg-amber-100 text-amber-800 font-semibold'
                            : 'text-stone-400'
                        }`}
                      >
                        {count}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-stone-100">
            <div className="text-xs font-semibold text-stone-900">KnowledgeMesh Core</div>
            <div className="text-[11px] text-stone-400 mt-0.5">Groq · llama-3.3-70b</div>
          </div>
        </aside>

        {/* Scrollable Page Viewport */}
        <main className="flex-1 overflow-y-auto p-8 bg-stone-50/50">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
