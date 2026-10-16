import React from 'react';
import { motion } from 'motion/react';
import { LayoutTemplate } from 'lucide-react';

export function EmptyState({
  icon,
  title,
  description,
  onGenerate,
  error,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  onGenerate: () => void;
  error?: string | null;
}) {
  return (
    <div className="card-bento p-10 md:p-14 flex flex-col items-center justify-center text-center min-h-[380px] max-w-2xl mx-auto">
      <div className="w-16 h-16 bg-accent-500/10 rounded-2xl flex items-center justify-center mb-5 border border-accent-500/20 text-accent-400 shadow-sm">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-base-50 mb-2">{title}</h3>
      <p className="text-base-400 mb-6 max-w-md text-xs md:text-sm leading-relaxed">{description}</p>

      {error && (
        <div className="mb-6 p-3 rounded-xl bg-signal-error-dim/20 border border-signal-error/25 text-signal-error text-xs max-w-md flex items-center gap-2.5">
          <div className="w-1.5 h-1.5 rounded-full bg-signal-error animate-pulse shrink-0"></div>
          <span className="text-left font-medium">{error}</span>
        </div>
      )}

      <button
        onClick={onGenerate}
        className="btn-primary px-6 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer shadow-md"
      >
        <LayoutTemplate className="w-4 h-4" />
        <span>Generate Now</span>
      </button>
    </div>
  );
}
