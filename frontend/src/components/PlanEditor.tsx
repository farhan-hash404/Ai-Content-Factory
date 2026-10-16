import { useState, useRef, useEffect } from 'react';
import {
  Bot, Trash2, GripVertical, Pencil, PlusSquare
} from 'lucide-react';

interface EditableTask {
  id: number;
  title: string;
  goal: string;
  bullets: string[];
  target_words: number;
  tags: string[];
}

interface PlanEditorProps {
  plan: any;
  jobId: string;
  onApprove: () => void;
  onRevise: (feedback: string) => void;
  onUpdatePlan: (plan: any) => void;
}

export function PlanEditor({ plan, onApprove, onRevise, onUpdatePlan }: PlanEditorProps) {
  const [editedTitle, setEditedTitle]       = useState(plan.blog_title || '');
  const [editedTone, setEditedTone]         = useState(plan.tone       || 'professional');
  const [editedAudience, setEditedAudience] = useState(plan.audience   || 'general');
  const [tasks, setTasks] = useState<EditableTask[]>(() =>
    (plan.tasks || []).map((t: any, i: number) => ({
      id: i,
      title:        t.title        || '',
      goal:         t.goal         || '',
      bullets:      t.bullets      || [],
      target_words: t.target_words || 350,
      tags:         t.tags         || [],
    }))
  );
  const [feedback, setFeedback]               = useState('');
  const [isEdited, setIsEdited]               = useState(false);
  const [expandedSection, setExpandedSection] = useState<number | null>(null);
  const [pendingFocusIdx, setPendingFocusIdx] = useState<number | null>(null);
  const titleRefs = useRef<Record<number, HTMLInputElement | null>>({});

  // Focus + scroll the newly added section's title input after it mounts.
  useEffect(() => {
    if (pendingFocusIdx === null) return;
    const el = titleRefs.current[pendingFocusIdx];
    if (el) {
      el.focus();
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    setPendingFocusIdx(null);
  }, [pendingFocusIdx, tasks.length]);

  const markEdited = () => setIsEdited(true);

  const updateTask = (idx: number, field: keyof EditableTask, value: any) => {
    setTasks(prev => prev.map((t, i) => i === idx ? { ...t, [field]: value } : t));
    markEdited();
  };

  const removeTask = (idx: number) => {
    if (tasks.length <= 1) return; // keep at least 1 section
    setTasks(prev => prev.filter((_, i) => i !== idx).map((t, i) => ({ ...t, id: i })));
    markEdited();
  };

  const addTask = () => {
    setTasks(prev => {
      const newIdx = prev.length;
      setExpandedSection(newIdx);
      setPendingFocusIdx(newIdx);
      return [...prev, {
        id: newIdx,
        title:        '',
        goal:         '',
        bullets:      [],
        target_words: 350,
        tags:         [],
      }];
    });
    markEdited();
  };

  const handleSaveAndApprove = () => {
    onUpdatePlan({
      blog_title: editedTitle,
      tone:       editedTone,
      audience:   editedAudience,
      tasks: tasks.map((t) => ({
        title:        t.title,
        goal:         t.goal,
        bullets:      t.bullets,
        target_words: t.target_words,
        tags:         t.tags,
      })),
    });
  };

  return (
    <div className="w-full mt-2">
      <div className="card-bento p-5 md:p-6 border-amber-500/30 bg-base-900/90 shadow-xl">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center text-amber-400 shrink-0">
              <Bot className="w-4 h-4 text-amber-400" />
            </div>
            <div>
              <h3 className="text-sm md:text-base font-bold text-base-100">Plan Ready for Human Approval</h3>
              <p className="text-xs text-base-400">Review or customize the outline below before parallel writers execute.</p>
            </div>
          </div>
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0">
            {tasks.length} Sections
          </span>
        </div>

        {/* Blog Title */}
        <div className="p-3.5 rounded-xl bg-base-950/60 border border-white/8 mb-4 focus-within:border-accent-500/35 transition-colors">
          <label className="text-[10px] font-bold text-base-400 uppercase tracking-wider mb-1.5 block">
            Blog Post Title
          </label>
          <input
            type="text"
            className="w-full bg-base-900 border border-white/8 rounded-lg px-3 py-2 text-sm text-base-100 font-semibold focus:outline-none focus:border-accent-500/40"
            value={editedTitle}
            onChange={e => { setEditedTitle(e.target.value); markEdited(); }}
          />
        </div>

        {/* Sections */}
        <div className="space-y-2.5 mb-5">
          <div className="flex items-center justify-between mb-1 px-1">
            <span className="text-[10px] font-bold text-base-400 uppercase tracking-wider">
              Outline Sections
            </span>
            <span className="text-[10px] text-base-500">
              Total Target: ~{tasks.reduce((sum, t) => sum + (t.target_words || 350), 0)} words
            </span>
          </div>

          {tasks.map((task, idx) => (
            <div
              key={idx}
              className="bg-base-950/40 rounded-xl border border-white/6 overflow-hidden transition-all hover:border-white/12 hover:bg-base-950/60"
            >
              {/* Section Header */}
              <div className="flex items-center gap-3 px-3.5 py-2.5">
                <GripVertical className="w-3.5 h-3.5 text-base-600 shrink-0" />
                <span className="flex items-center justify-center w-5 h-5 rounded-md bg-accent-500/10 text-accent-400 text-[11px] font-bold shrink-0">
                  {idx + 1}
                </span>
                <input
                  ref={el => { titleRefs.current[idx] = el; }}
                  type="text"
                  className="flex-1 bg-transparent border-none text-xs md:text-sm text-base-100 font-semibold focus:ring-0 focus:outline-none placeholder:text-base-600"
                  placeholder="Section title..."
                  value={task.title}
                  onChange={e => updateTask(idx, 'title', e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setExpandedSection(expandedSection === idx ? null : idx)}
                  className="p-1.5 rounded-lg text-base-400 hover:text-accent-400 hover:bg-white/5 transition-colors cursor-pointer"
                  title="Edit details (goal, key points, words)"
                >
                  <Pencil className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => removeTask(idx)}
                  disabled={tasks.length <= 1}
                  className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
                    tasks.length <= 1 ? 'text-base-700 cursor-not-allowed' : 'text-base-400 hover:text-rose-400 hover:bg-rose-500/10'
                  }`}
                  title="Remove section"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Expanded Details */}
              {expandedSection === idx && (
                <div className="px-4 pb-4.5 pt-1.5 border-t border-white/4 space-y-4">
                  <div>
                    <label className="text-[10px] font-bold text-base-400 uppercase tracking-widest mb-1.5 block">Goal</label>
                    <input
                      type="text"
                      className="w-full bg-base-900/60 border border-white/6 rounded-lg px-3.5 py-2.5 text-sm text-base-200 focus:outline-none focus:border-accent-500/40 transition-colors"
                      placeholder="What should the reader learn from this section?"
                      value={task.goal}
                      onChange={e => updateTask(idx, 'goal', e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-base-400 uppercase tracking-widest mb-1.5 block">Key Points (one per line)</label>
                    <textarea
                      className="w-full bg-base-900/60 border border-white/6 rounded-lg px-3.5 py-2.5 text-sm text-base-200 focus:outline-none focus:border-accent-500/40 transition-colors resize-none h-24"
                      placeholder="Enter key points, one per line..."
                      value={task.bullets.join('\n')}
                      onChange={e => updateTask(idx, 'bullets', e.target.value.split('\n').filter((b: string) => b.trim()))}
                    />
                  </div>
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <label className="text-[10px] font-bold text-base-400 uppercase tracking-widest mb-1.5 block">Target Words</label>
                      <input
                        type="number"
                        className="w-full bg-base-900/60 border border-white/6 rounded-lg px-3.5 py-2.5 text-sm text-base-200 focus:outline-none focus:border-accent-500/40 transition-colors"
                        value={task.target_words}
                        min={100}
                        max={1000}
                        onChange={e => {
                          const raw = e.target.value;
                          const parsed = raw === '' ? 0 : parseInt(raw, 10);
                          updateTask(idx, 'target_words', isNaN(parsed) ? 0 : parsed);
                        }}
                        onBlur={e => {
                          const parsed = parseInt(e.target.value, 10);
                          const safe = isNaN(parsed) ? 350 : Math.min(1000, Math.max(100, parsed));
                          updateTask(idx, 'target_words', safe);
                        }}
                      />
                    </div>
                    <div className="flex-1">
                      <label className="text-[10px] font-bold text-base-400 uppercase tracking-widest mb-1.5 block">SEO Tags (comma-sep)</label>
                      <input
                        type="text"
                        className="w-full bg-base-900/60 border border-white/6 rounded-lg px-3.5 py-2.5 text-sm text-base-200 focus:outline-none focus:border-accent-500/40 transition-colors"
                        placeholder="tag1, tag2"
                        value={task.tags.join(', ')}
                        onChange={e => updateTask(idx, 'tags', e.target.value.split(',').map((s: string) => s.trim()).filter(Boolean))}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Add Section Button */}
          <button
            type="button"
            onClick={addTask}
            className="w-full py-2.5 rounded-xl border border-dashed border-white/12 text-base-400 hover:text-accent-400 hover:border-accent-500/40 hover:bg-accent-500/5 transition-all flex items-center justify-center gap-2 text-xs font-semibold cursor-pointer"
          >
            <PlusSquare className="w-4 h-4" />
            Add Section to Outline
          </button>
        </div>

        {/* AI Revision Feedback */}
        <div className="mb-4">
          <label className="text-[10px] font-bold text-base-400 uppercase tracking-wider mb-1.5 block">
            Natural Language Feedback (Optional)
          </label>
          <textarea
            className="w-full bg-base-950/60 border border-white/8 rounded-xl p-3 text-xs md:text-sm text-base-100 focus:outline-none focus:border-accent-500/40 transition-colors resize-none h-18 placeholder:text-base-600"
            placeholder="e.g., 'Add a section comparing local RAG with cloud vector databases' or 'Make tone more academic'..."
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2.5 justify-end flex-wrap items-center pt-2 border-t border-white/6">
          {feedback.trim().length > 0 && (
            <button
              type="button"
              onClick={() => { onRevise(feedback); setFeedback(''); }}
              className="px-4 py-2 bg-base-800 hover:bg-base-750 text-base-200 rounded-xl text-xs font-semibold transition-colors border border-white/8 hover:border-white/16 cursor-pointer"
            >
              Request AI Revision
            </button>
          )}
          {isEdited && (
            <button
              type="button"
              onClick={handleSaveAndApprove}
              className="px-4 py-2 bg-accent-500/12 hover:bg-accent-500/20 text-accent-300 border border-accent-500/25 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <Pencil className="w-3.5 h-3.5" />
              Save Edits & Launch Writers
            </button>
          )}
          <button
            type="button"
            onClick={onApprove}
            className="btn-primary px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md cursor-pointer"
          >
            <span>{isEdited ? 'Approve Original' : 'Approve Outline & Write Content'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
