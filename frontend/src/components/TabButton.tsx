import React from 'react';
import { motion } from 'motion/react';

export function TabButton<T extends string>({
  id,
  icon,
  label,
  activeTab,
  setActiveTab,
}: {
  id: T;
  icon: React.ReactNode;
  label: string;
  activeTab: T;
  setActiveTab: (t: T) => void;
}) {
  const active = activeTab === id;
  return (
    <button
      onClick={() => setActiveTab(id)}
      className={`px-3.5 py-2 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 whitespace-nowrap relative cursor-pointer
      ${
        active
          ? 'bg-accent-500/12 text-accent-300 border border-accent-500/25 shadow-xs'
          : 'text-base-400 hover:text-base-100 hover:bg-white/4 border border-transparent'
      }`}
    >
      {icon} <span>{label}</span>
      {active && (
        <motion.div
          layoutId="tab-active-underline"
          className="absolute -bottom-[9px] left-2 right-2 h-[2px] bg-accent-500 rounded-full"
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
        />
      )}
    </button>
  );
}
