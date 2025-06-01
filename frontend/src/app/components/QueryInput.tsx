"use client";

import { useState } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";

type Props = {
  onSubmit: (query: string) => void;
};

export default function QueryInput({ onSubmit }: Props) {
  const [input, setInput] = useState("");
  const [shake, setShake] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (trimmed) {
      onSubmit(trimmed);
      setInput("");
    } else {
      // Feedback animation if input is empty
      setShake(true);
      setTimeout(() => setShake(false), 300);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`flex w-full max-w-2xl mx-auto bg-white bg-opacity-10 backdrop-blur-md border border-white/10 rounded-xl overflow-hidden shadow-md transition-all duration-300 animate-fade-in ${
        shake ? "animate-shake" : ""
      }`}
    >
      <input
        type="text"
        placeholder="Ask a data question..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="flex-1 px-4 py-3 text-white placeholder-gray-300 bg-transparent focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-300"
      />
      <button
        type="submit"
        className="bg-blue-600 px-5 flex items-center justify-center hover:bg-blue-700 transition-colors duration-200"
      >
        <PaperAirplaneIcon className="h-5 w-5 text-white rotate-90" />
      </button>
    </form>
  );
}
