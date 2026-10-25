import React, { useState, useMemo } from 'react';
import {
  LayoutDashboard, FileEdit, Plus, RefreshCw, Trash2, RotateCcw,
  Activity, Search, Clock, CheckCircle2, AlertCircle, ArrowUpRight, Sparkles
} from 'lucide-react';
import { motion } from 'motion/react';
import { Job } from '../api';
import { ViewState } from '../types';

interface SidebarProps {
  view: ViewState;
  navTo: (v: ViewState) => void;
  jobs: Job[];
  currentJob: Job | null;
  loadJob: (id: string) => void;
  startNewJob: () => void;
  onDeleteJob?: (id: string) => void;
  onResumeJob?: (id: string) => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export function Sidebar({
  view, navTo, jobs, currentJob, loadJob, startNewJob, onDeleteJob, onResumeJob,
  isMobileOpen, onCloseMobile
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'active'>('all');

  const navItems: { key: ViewState; icon: React.ReactNode; label: string; badge?: string }[] = [
    { key: 'chat',    icon: <LayoutDashboard className="w-4 h-4" />, label: 'AI Content Factory' },
    { key: 'graph',   icon: <Activity        className="w-4 h-4" />, label: 'Agent Graph', badge: '14 Agents' },
    { key: 'content', icon: <FileEdit       className="w-4 h-4" />, label: 'Asset Studio' },
  ];

  const filteredJobs = useMemo(() => {
    return jobs.filter(job => {
      const matchesSearch = job.topic.toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchesSearch) return false;
      if (statusFilter === 'completed') return job.status === 'completed';
      if (statusFilter === 'active') return job.status === 'running' || job.status === 'awaiting_approval';
      return true;
    });
  }, [jobs, searchQuery, statusFilter]);

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
        />
      )}

      <aside className={`w-[260px] h-full fixed left-0 top-0 bg-base-950 flex flex-col z-50 overflow-hidden border-r border-white/6 shadow-xl transition-transform duration-300 md:translate-x-0 ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}>
        
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-5 pt-5 pb-4 border-b border-white/6">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-400 to-accent-600 flex items-center justify-center text-base-950 shadow-md shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <h1 className="font-display text-lg text-base-50 leading-none truncate">
              AI Content Factory
            </h1>
            <p className="text-[10px] text-base-400 font-medium tracking-wide mt-1">Multi-Agent Engine</p>
          </div>
        </div>

        {/* New Generation CTA */}
        <div className="p-3">
          <button
            onClick={startNewJob}
            className="btn-primary w-full py-2.5 px-3.5 rounded-xl flex items-center justify-center gap-2 text-xs font-semibold shadow-sm cursor-pointer"
          >
            <Plus className="w-4 h-4" strokeWidth={2.5} />
            <span>New Generation</span>
          </button>
        </div>

        {/* Primary Views Navigation */}
        <nav className="flex flex-col gap-0.5 px-3 mb-3">
          <div className="text-[10px] font-bold text-base-500 uppercase tracking-wider px-2 py-1.5">
            Workspaces
          </div>
          {navItems.map(item => {
            const isActive = view === item.key;
            return (
              <button
                key={item.key}
                onClick={() => navTo(item.key)}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  isActive
                    ? 'bg-accent-500/12 text-accent-300 font-semibold border border-accent-500/25'
                    : 'text-base-400 hover:text-base-100 hover:bg-white/4 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <span className={isActive ? 'text-accent-400' : 'text-base-400'}>{item.icon}</span>
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/6 text-base-400">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Recent Jobs History Section */}
        <div className="flex-1 flex flex-col min-h-0 border-t border-white/6 pt-3 px-3">
          <div className="flex items-center justify-between px-2 mb-2">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3 h-3 text-base-500" />
              <span className="text-[10px] font-bold text-base-500 uppercase tracking-wider">Recent Jobs</span>
            </div>
            <span className="text-[10px] font-mono text-base-500">{jobs.length}</span>
          </div>

          {/* Quick Search */}
          {jobs.length > 3 && (
            <div className="relative mb-2">
              <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-base-500" />
              <input
                type="text"
                placeholder="Filter jobs..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-base-900 border border-white/6 rounded-lg pl-7 pr-2.5 py-1 text-[11px] text-base-200 placeholder:text-base-600 focus:outline-none focus:border-accent-500/30"
              />
            </div>
          )}

          {/* Job Items List */}
          <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {filteredJobs.slice(0, 15).map(job => {
              const isSelected = currentJob?.id === job.id;
              return (
                <div key={job.id} className="relative group w-full">
                  <button
                    onClick={() => loadJob(job.id)}
                    className={`w-full text-left rounded-lg px-2.5 py-2 text-xs flex items-center justify-between transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-accent-500/15 border border-accent-500/30 text-base-100 font-semibold'
                        : 'text-base-300 hover:text-base-100 hover:bg-white/4 border border-transparent'
                    }`}
                  >
                    <span className="truncate pr-2 text-[11.5px] leading-tight font-medium">
                      {job.topic}
                    </span>

                    {/* Status Pill */}
                    <div className="shrink-0 flex items-center group-hover:opacity-0 transition-opacity">
                      {job.status === 'completed' && (
                        <span className="text-[9px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
                          Done
                        </span>
                      )}
                      {job.status === 'awaiting_approval' && (
                        <span className="text-[9px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded animate-pulse">
                          Review
                        </span>
                      )}
                      {job.status === 'running' && (
                        <span className="text-[9px] font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.5 rounded animate-pulse">
                          Active
                        </span>
                      )}
                      {job.status === 'failed' && (
                        <span className="text-[9px] font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-1.5 py-0.5 rounded">
                          Error
                        </span>
                      )}
                    </div>
                  </button>

                  {/* Actions on hover */}
                  <div className="absolute right-1 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-1 bg-base-900/90 backdrop-blur-sm px-1 py-0.5 rounded">
                    {onResumeJob && job.status === 'failed' && (
                      <button
                        onClick={(e) => { e.stopPropagation(); onResumeJob(job.id); }}
                        className="p-1 rounded text-amber-400 hover:bg-amber-500/15 transition-colors cursor-pointer"
                        title="Resume from last checkpoint"
                      >
                        <RotateCcw className="w-3 h-3" />
                      </button>
                    )}
                    {onDeleteJob && (
                      <button
                        onClick={(e) => { e.stopPropagation(); onDeleteJob(job.id); }}
                        className="p-1 rounded text-base-500 hover:text-rose-400 hover:bg-rose-500/15 transition-colors cursor-pointer"
                        title="Delete job"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}

            {filteredJobs.length === 0 && (
              <div className="text-[11px] text-base-500 px-2 py-4 text-center">
                {searchQuery ? 'No matching jobs' : 'No jobs generated yet'}
              </div>
            )}
          </div>
        </div>

        {/* Footer info */}
        <div className="p-3 border-t border-white/6 text-[10px] text-base-500 flex items-center justify-between">
          <span>LangGraph v0.2</span>
          <span className="font-mono text-signal-success">● Ready</span>
        </div>
      </aside>
    </>
  );
}
