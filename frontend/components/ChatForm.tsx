"use client";

import { useState } from "react";

const ChatForm = () => {
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("recap");
  const [timeframe, setTimeframe] = useState("today");
  const [response, setResponse] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = { message, mode, timeframe };
    const res = await fetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    setResponse(data.response);
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
        />

        <select
          className="w-full p-2 border rounded"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
        >
          <option value="recap">Recap</option>
          <option value="foresight">Foresight</option>
          <option value="general">General</option>
        </select>

        <select
          className="w-full p-2 border rounded"
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
        >
          <option value="today">Today</option>
          <option value="this week">This Week</option>
          <option value="this month">This Month</option>
          <option value="this year">This Year</option>
        </select>

        <button
          type="submit"
          className="w-full bg-black text-white py-2 px-4 rounded hover:bg-gray-800"
        >
          Submit
        </button>
      </form>

      {response && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <p className="font-semibold">Response:</p>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
};

export default ChatForm;
