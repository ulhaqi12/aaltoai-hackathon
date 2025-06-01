"use client";

import { useState } from "react";
import ChartResults from "./components/ChartResults";
import QueryInput from "./components/QueryInput";
import { ArrowPathIcon } from "@heroicons/react/24/outline";

export default function Dashboard() {
  const [charts, setCharts] = useState<string[]>([]);
  const [report, setReport] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuerySubmit = async (query: string) => {
    setLoading(true);
    setError(null);
    setCharts([]);
    setReport("");

    try {
      const response = await fetch("http://localhost:8074/pipeline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ intent: query, model: "gpt-4o-mini" }),
      });

      const data = await response.json();

      console.log("FULL RESPONSE:", data);
      setCharts(data.plots || []);
      setReport(data.html_report);
    } catch (error) {
      console.error("Failed to fetch chart:", error);
      setError("Failed to generate report. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen h-full p-8 text-white bg-background flex flex-col gap-6">
      {/* Top section */}
      <div className="w-full max-w-5xl mx-auto flex flex-col items-center justify-center text-center bg-white bg-opacity-5 backdrop-blur-sm rounded-xl p-6 shadow-md animate-fade-in">
        <h1 className="text-5xl font-extrabold tracking-tight mb-2">
          <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            KHWARIZMI
          </span>
        </h1>
        <p className="text-base italic text-blue-300 mb-4">
          the shortest path from data to decision..
        </p>

        <QueryInput onSubmit={handleQuerySubmit} />
      </div>

      {/* Layout */}
      <div className="flex flex-col md:flex-row gap-6 w-full flex-1">
        {/* Left: Reports */}
        <div className="md:flex-1 bg-white bg-opacity-10 rounded-md p-4 flex flex-col">
          <h2 className="text-xl font-semibold mb-2">Reports</h2>
          {loading ? (
            <div className="flex flex-col items-center justify-center flex-1 gap-2 transition-opacity animate-fade-in text-yellow-100">
              <ArrowPathIcon className="h-6 w-6 animate-spin" />
              <p className="text-sm italic">Generating report and charts...</p>
              <p className="text-xs text-yellow-300 opacity-75">
                ∑ ∫ ∇ ⊕ — just a moment...
              </p>
            </div>
          ) : error ? (
            <p className="text-red-500 text-sm">{error}</p>
          ) : report ? (
            <div className="overflow-auto flex-1">
              <iframe
                className="w-full h-full min-h-[900px] bg-white rounded-md shadow border transition-opacity duration-500"
                srcDoc={report}
                sandbox="allow-scripts allow-same-origin"
              />
            </div>
          ) : (
            <div className="text-gray-300 italic text-sm flex-1 flex items-center justify-center">
              Your generated report will appear here once you submit a query.
            </div>
          )}
        </div>

        {/* Charts Section */}
        <div className="md:flex-1 flex flex-col gap-6 bg-white bg-opacity-10 rounded-md p-4">
          <h2 className="text-xl font-semibold mb-2">Charts</h2>
          {loading ? (
            <div className="flex flex-col items-center justify-center gap-2 text-white animate-fade-in">
              <ArrowPathIcon className="h-6 w-6 animate-spin" />
              <p className="text-sm italic">Drawing data... hang tight.</p>
              <p className="text-xs text-yellow-200 opacity-80">
                π, Σ, √, ⊗ — Math in motion...
              </p>
            </div>
          ) : charts.length > 0 ? (
            <div className="flex flex-col gap-4 transition-opacity duration-500">
              {charts.map((plot, index) => (
                <div
                  key={index}
                  className="flex flex-col gap-2 bg-white rounded-lg shadow-md p-4"
                >
                  <p className="text-sm text-gray-700 font-medium">
                    Figure {index + 1}
                  </p>
                  <iframe
                    className="w-full h-[400px] rounded border"
                    srcDoc={plot}
                    sandbox="allow-scripts"
                  />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-300 italic text-sm flex-1 flex items-center justify-center">
              Charts based on your query will show up here.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
