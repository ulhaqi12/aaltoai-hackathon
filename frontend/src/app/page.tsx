"use client";

import { useState } from "react";
import ChartResults from "./components/ChartResults";
import QueryInput from "./components/QueryInput";

export default function Dashboard() {
  const [charts, setCharts] = useState<string[]>([]);

  const handleQuerySubmit = async (query: string) => {
    try {
      const response = await fetch("http://localhost:8000/query", {
        // change URL to your actual backend endpoint
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      setCharts(data.html_plots || []);
    } catch (error) {
      console.error("Failed to fetch chart:", error);
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
          <p className="text-sm">Results or explanations will go here.</p>
        </div>

        {/* Right */}
        <div className="md:w-2/3 flex flex-col gap-6">
          <ChartResults htmlPlots={charts} />
        </div>
      </div>
    </div>
  );
}
