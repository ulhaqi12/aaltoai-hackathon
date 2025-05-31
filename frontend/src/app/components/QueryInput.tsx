"use client";

import { useState } from "react";

type Props = {
  onSubmit: (query: string) => void;
};

export default function QueryInput({ onSubmit }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (trimmed) {
      onSubmit(trimmed);
      setInput("");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full max-w-2xl mx-auto bg-white rounded-xl overflow-hidden shadow-md"
    >
      <input
        type="text"
        placeholder="Ask a data question..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="flex-1 px-4 py-3 text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button
        type="submit"
        className="bg-blue-600 px-6 text-white font-medium hover:bg-blue-700 transition-all duration-200"
      >
        Run
      </button>
    </form>
  );
}
