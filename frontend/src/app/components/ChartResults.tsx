"use client";

import { useEffect, useState, useRef } from "react";

export default function ChartResults() {
  const [plots, setPlots] = useState<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/response.json")
      .then((res) => res.json())
      .then((data) => setPlots(data.html_plots || []));
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;

    const scripts = container.querySelectorAll("script");

    scripts.forEach((oldScript) => {
      const newScript = document.createElement("script");
      newScript.text = oldScript.text;
      oldScript.replaceWith(newScript);
    });
  }, [plots]);

  return (
    <div className="space-y-8" ref={containerRef}>
      {plots.map((html, idx) => (
        <div
          key={idx}
          className="border rounded-md p-4 bg-white"
          dangerouslySetInnerHTML={{ __html: html }}
        />
      ))}
    </div>
  );
}
