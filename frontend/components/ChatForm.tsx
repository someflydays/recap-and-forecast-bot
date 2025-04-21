"use client";

import { useState } from "react";

const ChatForm = () => {
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("general");
  const [timeframe, setTimeframe] = useState("today");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload = { message, mode, timeframe };
    const res = await fetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    console.log("Response:", data.response); // for now, just log it
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md mx-auto mt-10">
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
        <option value="general">General</option>
        <option value="recap">Recap</option>
        <option value="foresight">Foresight</option>
      </select>

      <select
        className="w-full p-2 border rounded"
        value={timeframe}
        onChange={(e) => setTimeframe(e.target.value)}
      >
        <option value="today">Today</option>
        <option value="this week">This Week</option>
        <option value="this month">This Month</option>
        <option value="next year">Next Year</option>
      </select>

      <button
        type="submit"
        className="w-full bg-black text-white py-2 px-4 rounded hover:bg-gray-800"
      >
        Submit
      </button>
    </form>
  );
};

export default ChatForm;
