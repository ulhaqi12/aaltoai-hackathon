from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Report Generation Pipeline API")

class PipelineRequest(BaseModel):
    intent: str

class PipelineResponse(BaseModel):
    success: bool
    original_intent: str
    reformulated_intent: str
    sql_query: str
    plots: List[str]
    html_report: str

class ReportPipelineOrchestrator:
    def __init__(self):
        self.reformulate_url = "http://reformulate-intent:8071"
        self.intent_to_query_url = "http://intent-to-query:8070"
        self.api_to_report_url = "http://report-generation:8073"
        self.query_to_plots_url = "http://query-to-plots:8072"

    async def reformulate_intent(self, original_intent: str) -> str:
        async with aiohttp.ClientSession() as session:
            payload = {"intent": original_intent}
            async with session.post(f"{self.reformulate_url}/reformulate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("reformulated_intent", original_intent)
                return original_intent

    async def generate_sql_query(self, intent: str) -> Optional[str]:
        async with aiohttp.ClientSession() as session:
            payload = {"question": intent}
            async with session.post(f"{self.intent_to_query_url}/ask", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("sql_query")
                return None

    async def generate_plots(self, sql_query: str, intent: str) -> Optional[List[str]]:
        async with aiohttp.ClientSession() as session:
            payload = {
                "sql_query": sql_query,
                "intent": intent,
                "model": "gpt-4o-mini"
            }
            async with session.post(f"{self.query_to_plots_url}/visualize", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("html_plots", [])
                return None

    async def generate_report(self, original_intent: str, reformulated_intent: str, sql_query: str, plots: List[str]) -> Optional[str]:
        async with aiohttp.ClientSession() as session:
            payload = {
                "original_query": original_intent,
                "reformulated_query": reformulated_intent,
                "sql_query": sql_query,
                "plots": plots
            }
            async with session.post(f"{self.api_to_report_url}/generate-report", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("html_report")
                return None

@app.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    orchestrator = ReportPipelineOrchestrator()
    
    # Step 1: Reformulate Intent
    reformulated_intent = await orchestrator.reformulate_intent(request.intent)

    # Step 2: Generate SQL Query
    sql_query = await orchestrator.generate_sql_query(reformulated_intent)
    if not sql_query:
        raise HTTPException(status_code=500, detail="Failed to generate SQL query")

    # Step 3: Generate Plots
    plots = await orchestrator.generate_plots(sql_query, reformulated_intent)
    if plots is None:
        raise HTTPException(status_code=500, detail="Failed to generate plots")

    # Step 4: Generate Report
    html_report = await orchestrator.generate_report(request.intent, reformulated_intent, sql_query, plots)
    if not html_report:
        raise HTTPException(status_code=500, detail="Failed to generate report")

    return PipelineResponse(
        success=True,
        original_intent=request.intent,
        reformulated_intent=reformulated_intent,
        sql_query=sql_query,
        plots=plots,
        html_report=html_report
    )
