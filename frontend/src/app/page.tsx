"use client";

import { useState } from "react";
import ChartResults from "./components/ChartResults";
import QueryInput from "./components/QueryInput";

export default function Dashboard() {
  const [charts, setCharts] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleQuerySubmit = async (query: string) => {
    setLoading(true); // Start loading

    try {
      const response = await fetch("http://localhost:8074/pipeline/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ intent: query, model: "gpt-4o" }),
      });

      const data = await response.json();
      setCharts(data.html_plots || []);
    } catch (error) {
      console.error("Failed to fetch chart:", error);
    } finally {
      setLoading(false); // Stop loading after fetch
    }
  };

  return (
    <div className="min-h-screen p-8 text-white bg-background flex flex-col gap-6">
      {/* Top section */}
      <div className="w-full">
        <h1 className="text-4xl font-bold mb-2">Khawarizmi</h1>
        <p className="text-lg mb-4">Charts generated from LLM SQL responses.</p>
        <QueryInput onSubmit={handleQuerySubmit} />
      </div>

      {/* Layout */}
      <div className="flex flex-col md:flex-row gap-6 w-full">
        {/* Left */}
        <div className="md:w-2/3 bg-white bg-opacity-10 rounded-md p-4">
          <h2 className="text-xl font-semibold mb-2">Reports</h2>
          {loading ? (
            <p className="text-sm italic text-yellow-200">⏳ Generating charts...</p>
          ) : (
            <p className="text-sm">Results or explanations will go here.</p>
          )}
        </div>

        {/* Right */}
        <div className="md:w-2/3 flex flex-col gap-6">
          {loading ? (
            <div className="text-center text-lg animate-pulse text-white">Loading...</div>
          ) : (
            <ChartResults htmlPlots={charts} />
          )}
        </div>
      </div>
    </div>
  );
}