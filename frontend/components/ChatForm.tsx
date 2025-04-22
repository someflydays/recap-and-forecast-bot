"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

const ChatForm = () => {
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<"recap" | "foresight" | "general">("recap");
  const [timeframe, setTimeframe] = useState<
  "today" | "this week" | "this month" | "this year"
>("today");
  const [response, setResponse] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState("");
  const [controller, setController] = useState<AbortController | null>(null);

  useEffect(() => {
    document.title = "Recap & Forecast SERP Bot";
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    controller?.abort();

    const ctrl = new AbortController();
    setController(ctrl);
    setIsStreaming(true);
    setStatus("Connecting…");
    setResponse("");

    const payload = { message, mode, timeframe };
    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: ctrl.signal
      });

      if (!res.body) {
        throw new Error("No response stream.");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      setStatus("Generating…");
      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          // assume plain-text stream of tokens
          const chunk = decoder.decode(value);
          setResponse((prev) => prev + chunk);
        }
      }
      setIsStreaming(false);
      setController(null);
    } catch (err: any) {
      if (err.name === "AbortError") {
        setStatus("Cancelled");
      } else {
        setStatus("Error");
        console.error(err);
      }
    }
  };

  return (
    <div className="space-y-4 max-w-md mx-auto mt-10">
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          className="w-full p-2 border rounded"
          rows={4}
          placeholder="Enter a topic..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={isStreaming}
        />

        <select
          className="w-full p-2 border rounded"
          value={mode}
          onChange={(e) => setMode(e.target.value as any)}
          disabled={isStreaming}
        >
          <option value="recap">Recap</option>
          <option value="foresight">Foresight</option>
          <option value="general">General</option>
        </select>

        <select
          className="w-full p-2 border rounded"
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value as any)}
          disabled={isStreaming || mode === "general"}
        >
          <option value="today">Today</option>
          <option value="this week">This Week</option>
          <option value="this month">This Month</option>
          <option value="this year">This Year</option>
        </select>

        <button
          type={isStreaming ? "button" : "submit"}
          onClick={isStreaming ? () => controller?.abort() : undefined}
          className={`w-full py-2 px-4 rounded ${
            isStreaming
              ? "bg-gray-400 text-gray-700"
              : "bg-black text-white hover:bg-gray-800"
          }`}
        >
          {isStreaming ? "Cancel Response" : "Submit"}
        </button>
      </form>

      {isStreaming && (
        <p className="mt-2 text-sm italic">Status: {status}</p>
      )}

      {response && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <ReactMarkdown>{response}</ReactMarkdown>
        </div>
      )}
    </div>
  );
};

export default ChatForm;
