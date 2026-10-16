import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'motion/react';
import {
  ListOrdered, PlusCircle, Send, Network,
  CheckCircle2, RefreshCw, ShieldAlert, X, Hash,
  FileText, Film, Podcast, Search, Bot,
  RotateCcw, AlertTriangle, Cpu, Sparkles, Paperclip, ChevronDown, CornerDownLeft, SlidersHorizontal
} from 'lucide-react';
import { APIClient, Job, AgentEvent, CreateJobParams, UploadResult, SourceMode } from '../api';
import { ViewState } from '../types';
import { PlanEditor } from './PlanEditor';
import { UploadChip } from './UploadChip';
import { ProgressTracker } from './ProgressTracker';

function getAgentConfig(agentName: string) {
  const name = agentName.toLowerCase();
  if (name.includes('research')) {
    return {
      icon: Search,
      iconColor: 'text-sky-400',
      bgColor: 'bg-sky-500/10 border-sky-500/20',
      textColor: 'text-sky-400',
    };
  }
  if (name.includes('orchestrat') || name.includes('plan')) {
    return {
      icon: ListOrdered,
      iconColor: 'text-purple-400',
      bgColor: 'bg-purple-500/10 border-purple-500/20',
      textColor: 'text-purple-400',
    };
  }
  if (name.includes('writer') || name.includes('edit')) {
    return {
      icon: FileText,
      iconColor: 'text-amber-400',
      bgColor: 'bg-amber-500/10 border-amber-500/20',
      textColor: 'text-amber-400',
    };
  }
  if (name.includes('quality') || name.includes('control') || name.includes('validator') || name.includes('critic')) {
    return {
      icon: ShieldAlert,
      iconColor: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10 border-emerald-500/20',
      textColor: 'text-emerald-400',
    };
  }
  if (name.includes('video')) {
    return {
      icon: Film,
      iconColor: 'text-pink-400',
      bgColor: 'bg-pink-500/10 border-pink-500/20',
      textColor: 'text-pink-400',
    };
  }
  if (name.includes('audio') || name.includes('podcast')) {
    return {
      icon: Podcast,
      iconColor: 'text-indigo-400',
      bgColor: 'bg-indigo-500/10 border-indigo-500/20',
      textColor: 'text-indigo-400',
    };
  }
  return {
    icon: Bot,
    iconColor: 'text-base-400',
    bgColor: 'bg-base-500/10 border-white/6',
    textColor: 'text-base-300',
  };
}


const ACCEPTED_UPLOAD_TYPES = '.pdf,.docx,.txt,.md';

interface ChatViewProps {
  navTo: (v: ViewState) => void;
  currentJob: Job | null;
  events: AgentEvent[];
  topicError?: { reason: string; category?: string; suggested_topic?: string } | null;
  clearTopicError?: () => void;
  handleCreateJob:    (params: CreateJobParams) => void;
  handleApprovePlan:  (jobId: string) => void;
  handleRevisePlan:   (jobId: string, feedback: string) => void;
  handleUpdatePlan:   (jobId: string, plan: any) => void;
  handleResumeJob?:   (jobId: string) => void;
  tone: string;
  setTone: (t: string) => void;
  sections: number;
  setSections: (s: number) => void;
  numImages?: number;
  setNumImages?: (n: number) => void;
  keywordsInput: string;
  setKeywordsInput: (k: string) => void;
  selectedModel: string;
  openSettings?: () => void;
}

/* ---------- Hero Feature Templates ---------- */
const HERO_TEMPLATES = [
  {
    icon: FileText,
    title: 'Research & Deep Dive',
    desc: 'Multi-query web scraping, semantic chunking, and grounded section writing.',
    sampleTopic: 'How LangGraph enables persistent multi-agent execution loops',
    sampleTone: 'technical',
    sampleSections: 4,
    badge: 'Standard Workflow'
  },
  {
    icon: Film,
    title: 'Video Storyboard & Voice',
    desc: 'Scripting, Edge TTS voiceover, Whisper timestamps, and Pexels stock B-roll.',
    sampleTopic: 'Autonomous AI agents: From reasoning loops to production systems',
    sampleTone: 'conversational',
    sampleSections: 3,
    badge: 'Video Ready'
  },
  {
    icon: Podcast,
    title: 'Conversational Podcast',
    desc: 'Two-host script synthesis with neural voice generation and studio mastering.',
    sampleTopic: 'The future of generative voice synthesis and neural dialogue',
    sampleTone: 'educational',
    sampleSections: 3,
    badge: 'Audio Episode'
  },
  {
    icon: ShieldAlert,
    title: 'Academic Audit & Eval',
    desc: 'In-house G-Eval scorecard and DeepEval LLM-as-a-judge academic rubrics.',
    sampleTopic: 'Empirical comparison of LLM-as-judge alignment and scoring rubrics',
    sampleTone: 'academic',
    sampleSections: 4,
    badge: 'Evaluation Focus'
  },
] as const;

export function ChatView({
  navTo, currentJob, events, topicError, clearTopicError,
  handleCreateJob, handleApprovePlan, handleRevisePlan, handleUpdatePlan, handleResumeJob,
  tone, setTone, sections, setSections, numImages = 0, setNumImages, keywordsInput, setKeywordsInput, selectedModel,
  openSettings
}: ChatViewProps) {
  const [topicInput, setTopicInput] = useState('');
  const [isResuming, setIsResuming] = useState(false);
  const [isGenerationSettingsOpen, setIsGenerationSettingsOpen] = useState(false);

  // Document upload state
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'ready' | 'error'>('idle');
  const [uploadName, setUploadName] = useState<string>('');
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploadError, setUploadError] = useState<string>('');
  const [sourceMode, setSourceMode] = useState<SourceMode>('hybrid');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const clearUpload = () => {
    setUploadStatus('idle');
    setUploadName('');
    setUploadResult(null);
    setUploadError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleFileSelected = async (file: File | undefined) => {
    if (!file) return;
    setUploadStatus('uploading');
    setUploadName(file.name);
    setUploadResult(null);
    setUploadError('');
    try {
      const result = await APIClient.uploadDocument(file);
      setUploadResult(result);
      setUploadStatus('ready');
      if (!topicInput.trim() && result.derived_topic) {
        setTopicInput(result.derived_topic);
      }
    } catch (e: any) {
      setUploadError(e?.message || 'Upload failed.');
      setUploadStatus('error');
    }
  };

  const submitJob = (overrideTopic?: string) => {
    let topic = (overrideTopic ?? topicInput).trim();
    if (!topic && sourceMode === 'auto_topic' && uploadResult?.derived_topic) {
      topic = uploadResult.derived_topic;
    }
    if (!topic) return;
    const upload_id = uploadStatus === 'ready' ? uploadResult?.upload_id : undefined;
    const keywords = keywordsInput
      .split(',')
      .map(k => k.trim())
      .filter(k => k.length > 0);
    handleCreateJob({
      topic, tone, sections, keywords,
      generate_podcast: false, generate_video: false, generate_campaign: false,
      generate_images: numImages > 0,
      num_images: numImages,
      upload_id,
      source_mode: upload_id ? sourceMode : undefined,
    });
    setTopicInput('');
    setKeywordsInput('');
    clearUpload();
  };

  const isAwaitingApproval = currentJob?.status === 'awaiting_approval';
  const showHero = !currentJob && events.length === 0;

  return (
    <main className="flex-1 flex flex-col p-4 md:p-6 lg:p-8 relative overflow-y-auto">
      <div className="flex-1 flex flex-col gap-6 max-w-5xl w-full mx-auto pb-6">
        
        {/* Top Header / Context */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-base-50">
              {!currentJob
                ? 'AI Content Factory'
                : currentJob.status === 'completed'
                  ? 'Generation Complete'
                  : currentJob.status === 'failed'
                    ? 'Pipeline Paused'
                    : currentJob.status === 'awaiting_approval'
                      ? 'Review Outline Plan'
                      : 'Running Multi-Agent Graph…'}
            </h2>
            <p className="text-xs md:text-sm text-base-400 mt-1 flex items-center gap-2">
              <span className="font-mono text-base-500">LangGraph Core</span>
              <span>•</span>
              <span>14 Specialized Nodes</span>
              <span>•</span>
              <span className="text-accent-400 font-medium">HITL Enabled</span>
            </p>
          </div>

          {currentJob && (
            <div className="flex items-center gap-2.5">
              <span className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 border ${
                currentJob.status === 'completed'
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : currentJob.status === 'awaiting_approval'
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    : currentJob.status === 'failed'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      : 'bg-accent-500/10 text-accent-400 border-accent-500/20'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  currentJob.status === 'completed' ? 'bg-emerald-400' :
                  currentJob.status === 'awaiting_approval' ? 'bg-amber-400 animate-ping' :
                  currentJob.status === 'failed' ? 'bg-rose-400' :
                  'bg-accent-400 animate-pulse'
                }`} />
                {currentJob.status.replace('_', ' ')}
              </span>

              {currentJob.status === 'completed' && (
                <button
                  onClick={() => navTo('content')}
                  className="btn-primary px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Open in Studio</span>
                </button>
              )}
            </div>
          )}
        </header>

        {/* -------- Welcome Hero & Quick Templates -------- */}
        {showHero && (
          <div className="space-y-6 animate-fadeIn">
            
            {/* Mission banner */}
            <div className="card-bento p-6 md:p-8 relative overflow-hidden">
              <div className="max-w-2xl">
                <span className="text-[11px] font-bold uppercase tracking-wider text-accent-400 px-2.5 py-1 rounded-full bg-accent-500/10 border border-accent-500/20 inline-block mb-3">
                  Production-Grade Agent Pipeline
                </span>
                <h3 className="text-xl md:text-2xl font-bold text-base-50 tracking-tight leading-snug mb-2">
                  Autonomous Research, Synthesis & Evaluation
                </h3>
                <p className="text-xs md:text-sm text-base-400 leading-relaxed">
                  Provide a topic or upload source documentation. The engine coordinates web research, drafts structured outlines, writes sections concurrently, verifies citations, and benchmarks content quality.
                </p>
              </div>
            </div>

            {/* Template Presets Grid */}
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-base-400 mb-3 px-1">
                Quick-Start Presets
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {HERO_TEMPLATES.map((tmpl) => {
                  const Icon = tmpl.icon;
                  return (
                    <div
                      key={tmpl.title}
                      onClick={() => {
                        setTopicInput(tmpl.sampleTopic);
                        setTone(tmpl.sampleTone);
                        setSections(tmpl.sampleSections);
                      }}
                      className="card-bento p-4 cursor-pointer hover:border-accent-500/40 hover:-translate-y-0.5 transition-all flex flex-col justify-between group"
                    >
                      <div>
                        <div className="flex items-center justify-between mb-2.5">
                          <div className="w-8 h-8 rounded-lg bg-accent-500/10 border border-accent-500/20 flex items-center justify-center text-accent-400">
                            <Icon className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] font-mono font-semibold px-2 py-0.5 rounded bg-white/4 text-base-400">
                            {tmpl.badge}
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-base-100 mb-1 group-hover:text-accent-300 transition-colors">
                          {tmpl.title}
                        </h4>
                        <p className="text-[11px] text-base-400 leading-relaxed">
                          {tmpl.desc}
                        </p>
                      </div>

                      <div className="mt-3 pt-2.5 border-t border-white/6 flex items-center justify-between text-[10px] text-accent-400 font-medium">
                        <span>Use preset</span>
                        <CornerDownLeft className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>
        )}

        {/* -------- Active Pipeline Tracker -------- */}
        {currentJob && (
          <div className="space-y-4">
            <ProgressTracker events={events} jobStatus={currentJob.status} />

            {/* Prompt preview chip */}
            <div className="card-bento p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-base-500 block mb-0.5">Topic Objective</span>
                <p className="text-sm font-semibold text-base-100">{currentJob.topic}</p>
              </div>
              <div className="flex items-center gap-2 text-xs text-base-400 shrink-0">
                <span className="px-2 py-0.5 rounded bg-white/5 border border-white/8 font-mono">Tone: {currentJob.tone}</span>
                {currentJob.keywords && currentJob.keywords.length > 0 && (
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/8 font-mono">
                    {currentJob.keywords.length} keywords
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* -------- HITL Plan Approval Gate -------- */}
        {isAwaitingApproval && currentJob?.plan && (
          <div className="card-bento border-amber-500/30 bg-amber-500/5 p-5 md:p-6 space-y-4 animate-fadeIn">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/25 flex items-center justify-center text-amber-400 shrink-0">
                <ListOrdered className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-500/20 text-amber-300">
                    Human-in-the-Loop Review
                  </span>
                  <span className="text-xs text-base-400">Step 2 of 4</span>
                </div>
                <h3 className="text-base font-bold text-base-100 mt-1">Review & Customize Generation Outline</h3>
                <p className="text-xs text-base-300 mt-1 leading-relaxed">
                  The Orchestrator planned the section hierarchy below. You can modify titles, adjust targets, or ask the AI to re-plan before parallel workers write content.
                </p>
              </div>
            </div>

            <PlanEditor
              plan={currentJob.plan}
              jobId={currentJob.id}
              onApprove={() => handleApprovePlan(currentJob.id)}
              onRevise={(fb) => handleRevisePlan(currentJob.id, fb)}
              onUpdatePlan={(plan) => handleUpdatePlan(currentJob.id, plan)}
            />
          </div>
        )}

        {/* -------- User Objective Card (when job is active) -------- */}
        {currentJob && (
          <div className="card-bento p-4 md:p-5 flex flex-col md:flex-row md:items-center justify-between gap-3 border-accent-500/25 bg-accent-500/5">
            <div>
              <div className="text-[10px] font-bold text-accent-400 uppercase tracking-wider mb-1">
                Active Topic Request
              </div>
              <p className="text-sm md:text-base font-semibold text-base-100">
                {currentJob.topic}
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-base-300 shrink-0">
              <span className="px-2.5 py-1 rounded-lg bg-base-900 border border-white/8 font-mono">
                Tone: <span className="text-base-100 font-semibold">{currentJob.tone}</span>
              </span>
              {currentJob.keywords && currentJob.keywords.length > 0 && (
                <span className="px-2.5 py-1 rounded-lg bg-base-900 border border-white/8 font-mono">
                  {currentJob.keywords.length} keywords
                </span>
              )}
            </div>
          </div>
        )}

        {/* -------- Real-Time Agent Stream Timeline -------- */}
        {events.length > 0 && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between px-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-base-500">
                Agent Activity Stream ({events.length})
              </span>
              {currentJob?.status === 'running' && (
                <span className="text-[11px] text-accent-400 font-medium flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-400 animate-pulse" />
                  Live Orchestration
                </span>
              )}
            </div>

            <div className="space-y-2 max-h-[50vh] overflow-y-auto pr-1 custom-scrollbar">
              {events.map((event, i) => {
                const config = getAgentConfig(event.agent_name);
                const AgentIcon = config.icon;
                const isLatest = i === events.length - 1;
                const isWorking = (event.status === 'working' || event.status === 'started') && isLatest && currentJob?.status === 'running';

                return (
                  <motion.div
                    key={i}
                    className="card-bento p-3.5 flex items-start gap-3 transition-all"
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${config.bgColor}`}>
                      <AgentIcon className={`w-4 h-4 ${config.iconColor}`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${config.bgColor} ${config.textColor}`}>
                          {event.agent_name.replace('_', ' ')}
                        </span>
                        <span className="text-[10px] text-base-500 font-mono">
                          {new Date(event.timestamp * 1000).toLocaleTimeString()}
                        </span>
                      </div>

                      <div className="text-xs md:text-sm text-base-200 leading-relaxed flex items-center gap-2 mt-1">
                        {event.status === 'error' ? (
                          <span className="text-signal-error font-bold text-xs shrink-0 px-1.5 py-0.5 rounded bg-signal-error/10 border border-signal-error/20">
                            Failed
                          </span>
                        ) : isWorking ? (
                          <RefreshCw className="w-3.5 h-3.5 text-accent-400 animate-spin shrink-0" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5 text-signal-success shrink-0" />
                        )}
                        <span className="flex-1 break-words">{event.message}</span>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        )}

        {/* -------- Pipeline Interrupted / Resumption Banner -------- */}
        {currentJob?.status === 'failed' && (
          <div className="card-bento border-rose-500/30 bg-rose-500/5 p-5 md:p-6 space-y-4 animate-fadeIn">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-rose-500/15 border border-rose-500/25 flex items-center justify-center text-rose-400 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-500/20 text-rose-300">
                    Execution Halted
                  </span>
                </div>
                <h3 className="text-base font-bold text-base-100 mt-1">Pipeline Interrupted</h3>
                <p className="text-xs text-base-300 mt-1 leading-relaxed">
                  Execution stopped. Thanks to SQLite state checkpoints, you can resume execution without repeating previous research or LLM calls.
                </p>
                {currentJob.error_message && (
                  <div className="mt-2.5 p-3 rounded-lg bg-base-950/80 border border-white/8 text-xs font-mono text-rose-300 break-all">
                    {currentJob.error_message}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={async () => {
                  if (!handleResumeJob || isResuming) return;
                  setIsResuming(true);
                  try {
                    await handleResumeJob(currentJob.id);
                  } finally {
                    setTimeout(() => setIsResuming(false), 2000);
                  }
                }}
                disabled={isResuming || !handleResumeJob}
                className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer"
              >
                {isResuming ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Resuming from Checkpoint…</span>
                  </>
                ) : (
                  <>
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Resume from Last Step</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

      </div>

      {/* -------- Generation Input Composer Deck -------- */}
      {(!currentJob || currentJob.status === 'completed' || currentJob.status === 'failed') && (
        <div className="w-full max-w-4xl mx-auto mt-4 shrink-0 z-30">
          
          {/* Topic validation error */}
          {topicError && (
            <div className="mb-3 p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-300 text-xs flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
              <div className="flex-1">
                <span className="font-bold">Topic validation rejected:</span> {topicError.reason}
                {topicError.suggested_topic && (
                  <button
                    onClick={() => {
                      setTopicInput(topicError.suggested_topic!);
                      clearTopicError?.();
                    }}
                    className="block mt-1.5 text-accent-300 hover:underline font-semibold"
                  >
                    Use suggested topic: "{topicError.suggested_topic}"
                  </button>
                )}
              </div>
              <button onClick={() => clearTopicError?.()} className="p-1 hover:text-white cursor-pointer">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Main Composer Bento Card */}
          <div className="card-bento p-4 shadow-xl border-white/10 hover:border-accent-500/30 focus-within:border-accent-500/50 transition-all flex flex-col gap-3">
            
            {/* Document attachment chip */}
            {uploadStatus !== 'idle' && (
              <UploadChip
                status={uploadStatus}
                filename={uploadName}
                result={uploadResult}
                errorMessage={uploadError}
                sourceMode={sourceMode}
                onSourceModeChange={setSourceMode}
                onClear={clearUpload}
              />
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_UPLOAD_TYPES}
              className="hidden"
              onChange={e => handleFileSelected(e.target.files?.[0])}
            />

            {/* Prompt input field */}
            <div className="w-full">
              <textarea
                className="w-full bg-transparent border-none text-base-100 placeholder:text-base-500 text-sm md:text-base font-medium min-h-[58px] max-h-[180px] resize-none focus:outline-none focus:ring-0 leading-relaxed font-sans"
                placeholder={
                  uploadStatus === 'ready' && sourceMode === 'auto_topic'
                    ? (uploadResult?.derived_topic
                        ? `Auto-topic derived: "${uploadResult.derived_topic}". Press Generate or customize below.`
                        : 'Auto-topic mode: document ready. Enter custom focus or press Generate.')
                    : 'Enter topic, question, or research focus (e.g., "State persistence and checkpointing in LangGraph")...'
                }
                value={topicInput}
                onChange={e => setTopicInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    submitJob();
                  }
                }}
              />
            </div>

            {/* Advanced Settings Drawer */}
            <div className="border-t border-white/6 pt-2">
              <button
                type="button"
                onClick={() => setIsGenerationSettingsOpen(prev => !prev)}
                className="flex items-center gap-2 py-1 text-xs font-semibold text-base-400 hover:text-base-200 transition-colors cursor-pointer"
              >
                <SlidersHorizontal className="w-3.5 h-3.5 text-accent-400" />
                <span>Pipeline Parameters</span>
                <span className="text-[10px] font-normal text-base-500">
                  ({tone} · {sections} sections · {numImages} figures)
                </span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isGenerationSettingsOpen ? 'rotate-180' : ''}`} />
              </button>

              {isGenerationSettingsOpen && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-3 rounded-xl bg-base-950/50 border border-white/6">
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-base-400 block mb-1">
                      Writing Tone
                    </label>
                    <select
                      value={tone}
                      onChange={e => setTone(e.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-base-900 px-2.5 py-1.5 text-xs text-base-200 focus:outline-none focus:border-accent-500/50"
                    >
                      <option value="professional">Professional</option>
                      <option value="academic">Academic & Grounded</option>
                      <option value="technical">Technical Deep-Dive</option>
                      <option value="conversational">Conversational</option>
                      <option value="persuasive">Persuasive / Opinion</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-base-400 block mb-1">
                      Body Sections ({sections})
                    </label>
                    <input
                      type="range"
                      min={2}
                      max={6}
                      value={sections}
                      onChange={e => setSections(Number(e.target.value))}
                      className="w-full mt-2 cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-base-400 block mb-1">
                      AI Figures ({numImages})
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={4}
                      value={numImages}
                      onChange={e => setNumImages?.(Number(e.target.value))}
                      className="w-full mt-2 cursor-pointer accent-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-base-400 block mb-1">
                      Target Keywords
                    </label>
                    <input
                      value={keywordsInput}
                      onChange={e => setKeywordsInput(e.target.value)}
                      placeholder="e.g. LangGraph, RAG, agents"
                      className="w-full rounded-lg border border-white/10 bg-base-900 px-2.5 py-1.5 text-xs text-base-200 placeholder:text-base-600 focus:outline-none focus:border-accent-500/50"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Toolbar */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadStatus === 'uploading'}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                    uploadStatus === 'ready'
                      ? 'text-accent-400 bg-accent-500/15 border-accent-500/30'
                      : 'text-base-300 hover:text-base-100 bg-white/4 hover:bg-white/8 border-white/8'
                  }`}
                >
                  <Paperclip className="w-3.5 h-3.5" />
                  <span>{uploadStatus === 'ready' ? 'Replace Doc' : 'Attach PDF/Docx'}</span>
                </button>

                {openSettings && (
                  <button
                    type="button"
                    onClick={openSettings}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/4 hover:bg-white/8 border border-white/8 text-xs text-base-300 hover:text-base-100 transition-colors cursor-pointer"
                  >
                    <Cpu className="w-3.5 h-3.5 text-accent-400" />
                    <span className="font-mono text-[11px] truncate max-w-[120px]">{selectedModel}</span>
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3">
                <span className="hidden sm:inline text-[11px] text-base-500 font-mono">
                  Press <kbd className="px-1.5 py-0.5 rounded bg-white/6 border border-white/10 text-base-400 font-sans text-[10px]">Enter ↵</kbd>
                </span>

                <button
                  type="button"
                  onClick={() => submitJob()}
                  disabled={
                    uploadStatus === 'uploading'
                    || (!topicInput.trim()
                        && !(sourceMode === 'auto_topic' && uploadStatus === 'ready' && !!uploadResult?.derived_topic))
                  }
                  className="btn-primary px-5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <span>Launch Engine</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

          </div>
        </div>
      )}
    </main>
  );
}
