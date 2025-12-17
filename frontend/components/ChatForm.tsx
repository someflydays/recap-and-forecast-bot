"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

type Mode = "recap" | "forecast" | "general";
type Timeframe = "today" | "this week" | "this month" | "this year";
type Model = "gpt-4o" | "gpt-5.2";

const EXAMPLE_TOPICS = [
  "Tesla stock performance",
  "AI developments",
  "Climate change policy",
  "Federal Reserve interest rates",
  "SpaceX launches",
  "Bitcoin trends",
];

const STORAGE_KEY = "recap-forecast-preferences";

export default function ChatForm() {
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<Mode>("recap");
  const [timeframe, setTimeframe] = useState<Timeframe>("today");
  const [model, setModel] = useState<Model>("gpt-4o");

  const [response, setResponse] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const controllerRef = useRef<AbortController | null>(null);

  // Load preferences from localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const prefs = JSON.parse(saved);
        if (prefs.mode) setMode(prefs.mode);
        if (prefs.timeframe) setTimeframe(prefs.timeframe);
        if (prefs.model) setModel(prefs.model);
      } catch {
        // Ignore invalid JSON
      }
    }
  }, []);

  // Save preferences to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ mode, timeframe, model }));
  }, [mode, timeframe, model]);

  const startStreaming = async () => {
    if (!message.trim()) return;

    controllerRef.current?.abort();
    const ctrl = new AbortController();
    controllerRef.current = ctrl;

    setIsStreaming(true);
    setStatus("Analyzing topic");
    setResponse("");
    setError("");

    const payload = {
      message,
      mode,
      timeframe,
      model: model === "gpt-5.2" ? "gpt-5.2-2025-12-11" : "gpt-4o",
    };

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: ctrl.signal,
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || `Server error: ${res.status}`);
      }

      if (!res.body) {
        throw new Error("No response stream.");
      }

      setStatus("Searching the web");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      setStatus("Preparing report");
      let done = false;
      let first = true;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          if (first) {
            setStatus("Generating report");
            first = false;
          }
          const chunk = decoder.decode(value);
          setResponse((prev) => prev + chunk);
        }
      }
      setStatus("Complete");
    } catch (err: any) {
      if (err.name === "AbortError") {
        setStatus("Cancelled");
      } else {
        setStatus("Error");
        setError(err.message || "An unexpected error occurred");
        console.error(err);
      }
    } finally {
      setIsStreaming(false);
      controllerRef.current = null;
    }
  };

  const handleButtonClick = () => {
    if (isStreaming) {
      controllerRef.current?.abort();
      setIsStreaming(false);
      setStatus("Cancelled");
      controllerRef.current = null;
    } else {
      startStreaming();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isStreaming && message.trim()) {
      e.preventDefault();
      startStreaming();
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = response;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClear = () => {
    setMessage("");
    setResponse("");
    setError("");
    setStatus("");
  };

  const handleExampleClick = (topic: string) => {
    setMessage(topic);
  };

  return (
    <div className="space-y-6">
      {/* Main Card */}
      <div className="glass rounded-2xl p-6 sm:p-8">
        <form onKeyDown={handleKeyDown} className="space-y-5">
          {/* Topic Input */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
                Topic
              </label>
              {(message || response) && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                >
                  Clear all
                </button>
              )}
            </div>
            <textarea
              className="glass-input w-full p-4 rounded-xl text-[var(--text-primary)] placeholder-[var(--text-muted)] resize-none text-base"
              rows={3}
              placeholder="Enter any topic to explore..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={isStreaming}
            />
          </div>

          {/* Example Topics */}
          {!message && !response && (
            <div className="flex flex-wrap gap-2">
              <span className="text-xs text-[var(--text-muted)]">Try:</span>
              {EXAMPLE_TOPICS.map((topic) => (
                <button
                  key={topic}
                  type="button"
                  onClick={() => handleExampleClick(topic)}
                  className="text-xs px-2.5 py-1 rounded-full bg-[var(--surface)] border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] transition-all"
                >
                  {topic}
                </button>
              ))}
            </div>
          )}

          {/* Controls Grid */}
          <div className="grid grid-cols-3 gap-3">
            {/* Mode Selector */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
                Mode
              </label>
              <select
                className="glass-input w-full p-3 rounded-xl text-[var(--text-primary)] text-sm cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2024%2024%22%20stroke%3D%22%2394a3b8%22%3E%3Cpath%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%222%22%20d%3D%22M19%209l-7%207-7-7%22%2F%3E%3C%2Fsvg%3E')] bg-[length:1.25rem] bg-[right_0.75rem_center] bg-no-repeat pr-10"
                value={mode}
                onChange={(e) => setMode(e.target.value as Mode)}
                disabled={isStreaming}
              >
                <option value="recap">Recap</option>
                <option value="forecast">Forecast</option>
                <option value="general">General</option>
              </select>
            </div>

            {/* Timeframe Selector */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
                Timeframe
              </label>
              <select
                className="glass-input w-full p-3 rounded-xl text-[var(--text-primary)] text-sm cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2024%2024%22%20stroke%3D%22%2394a3b8%22%3E%3Cpath%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%222%22%20d%3D%22M19%209l-7%207-7-7%22%2F%3E%3C%2Fsvg%3E')] bg-[length:1.25rem] bg-[right_0.75rem_center] bg-no-repeat pr-10 disabled:opacity-40 disabled:cursor-not-allowed"
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value as Timeframe)}
                disabled={isStreaming || mode === "general"}
              >
                <option value="today">Today</option>
                <option value="this week">This Week</option>
                <option value="this month">This Month</option>
                <option value="this year">This Year</option>
              </select>
            </div>

            {/* Model Selector */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
                Model
              </label>
              <select
                className="glass-input w-full p-3 rounded-xl text-[var(--text-primary)] text-sm cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2024%2024%22%20stroke%3D%22%2394a3b8%22%3E%3Cpath%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%222%22%20d%3D%22M19%209l-7%207-7-7%22%2F%3E%3C%2Fsvg%3E')] bg-[length:1.25rem] bg-[right_0.75rem_center] bg-no-repeat pr-10"
                value={model}
                onChange={(e) => setModel(e.target.value as Model)}
                disabled={isStreaming}
              >
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-5.2">gpt-5.2</option>
              </select>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="button"
            onClick={handleButtonClick}
            disabled={!message.trim() && !isStreaming}
            className={`w-full py-3.5 px-6 rounded-xl font-medium text-white transition-all duration-200 ${
              isStreaming
                ? "btn-secondary text-[var(--text-secondary)]"
                : "btn-primary disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
            }`}
          >
            {isStreaming ? "Cancel" : "Generate Report"}
          </button>
        </form>

        {/* Status Indicator */}
        {isStreaming && (
          <div className="mt-6 flex items-center gap-3">
            <div className="relative">
              <div className="w-2 h-2 bg-sky-500 rounded-full animate-pulse" />
              <div className="absolute inset-0 w-2 h-2 bg-sky-500 rounded-full animate-ping opacity-75" />
            </div>
            <span className="text-sm text-[var(--text-secondary)]">{status}</span>
            <div className="flex-1 h-1 rounded-full overflow-hidden bg-[var(--surface)]">
              <div className="h-full loading-shimmer rounded-full" />
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && !isStreaming && (
          <div className="mt-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-red-400">Error</p>
                <p className="text-sm text-red-300/80 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Response Card */}
      {response && (
        <div className="glass rounded-2xl p-6 sm:p-8 response-card">
          <div className="flex items-center justify-between mb-4 pb-4 border-b border-[var(--border)]">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-sky-400" />
              <span className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">
                {mode === "recap" ? "Recap Report" : mode === "forecast" ? "Forecast Report" : "General Report"}
              </span>
            </div>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors px-2 py-1 rounded-md hover:bg-[var(--surface)]"
            >
              {copied ? (
                <>
                  <svg className="w-4 h-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-green-400">Copied!</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <div className="prose prose-invert max-w-none">
            <ReactMarkdown>{response}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
