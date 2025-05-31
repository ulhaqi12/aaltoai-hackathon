import logging
import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load environment variables
load_dotenv()


from fastapi.middleware.cors import CORSMiddleware


# -----------------------------
# Configure Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("main-gateway")

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="Report Generation Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:3000"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class PipelineRequest(BaseModel):
    intent: str
    model: str

class PipelineResponse(BaseModel):
    success: bool
    original_intent: str
    reformulated_intent: str
    sql_query: str
    plots: List[str]
    html_report: str

# -----------------------------
# Orchestrator Class
# -----------------------------
class ReportPipelineOrchestrator:
    def __init__(self):
        self.reformulate_url = "http://reformulate-intent:8071"
        self.intent_to_query_url = "http://intent-to-query:8070"
        self.api_to_report_url = "http://report-generation:8073"
        self.query_to_plots_url = "http://query-to-plots:8072"

    async def reformulate_intent(self, original_intent: str, model: str) -> str:
        logger.info("Reformulating intent...")
        async with aiohttp.ClientSession() as session:
            payload = {
                "intent": original_intent,
                "model": model
            }
            try:
                async with session.post(f"{self.reformulate_url}/reformulate", json=payload) as response:
                    result = await response.json()
                    reformulated = result.get("reformulated_intent", original_intent)
                    logger.info(f"Reformulated: {reformulated}")
                    return reformulated
            except Exception as e:
                logger.error(f"Error during intent reformulation: {e}")
                return original_intent

    async def generate_sql_query(self, intent: str) -> Optional[str]:
        logger.info("Generating SQL query...")
        async with aiohttp.ClientSession() as session:
            payload = {"question": intent}
            try:
                async with session.post(f"{self.intent_to_query_url}/ask", json=payload) as response:
                    result = await response.json()
                    sql = result.get("sql_query")
                    logger.info(f"SQL Query: {sql}")
                    return sql
            except Exception as e:
                logger.error(f"Error generating SQL: {e}")
                return None

    async def generate_plots(self, sql_query: str, intent: str) -> Optional[Dict[str, Any]]:
        logger.info("Generating plots...")
        async with aiohttp.ClientSession() as session:
            payload = {
                "sql_query": sql_query,
                "intent": intent,
                "model": "gpt-4o-mini"
            }
            try:
                async with session.post(f"{self.query_to_plots_url}/visualize", json=payload) as response:
                    result = await response.json()
                    logger.info(f"Plot generation status: {result.get('status')}")
                    return {
                        "status": result.get("status"),
                        "html_plots": result.get("html_plots", []),
                        "image_urls": result.get("image_urls"),
                        "error_message": result.get("error_message")
                    }
            except Exception as e:
                logger.error(f"Error generating plots: {e}")
                return {
                    "status": "error",
                    "html_plots": [],
                    "image_urls": None,
                    "error_message": str(e)
                }

    async def generate_report(self, original_intent: str, reformulated_intent: str, sql_query: str, plots: List[str], image_urls: List[str]) -> Optional[str]:
        logger.info("Generating final report...")
        async with aiohttp.ClientSession() as session:
            payload = {
                "original_query": original_intent,
                "reformulated_query": reformulated_intent,
                "sql_query": sql_query,
                "plots": plots,
                "image_urls": image_urls,                
            }
            try:
                async with session.post(f"{self.api_to_report_url}/generate-report", json=payload) as response:
                    result = await response.json()
                    logger.info("Report successfully generated.")
                    return result.get("html_report")
            except Exception as e:
                logger.error(f"Error generating report: {e}")
                return None

# -----------------------------
# Main API Endpoint
# -----------------------------
@app.post("/pipeline/", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    logger.info(f"Pipeline triggered with intent: {request.intent}")
    orchestrator = ReportPipelineOrchestrator()

    reformulated_intent = await orchestrator.reformulate_intent(request.intent, request.model)
    
    sql_query = await orchestrator.generate_sql_query(reformulated_intent)
    if not sql_query:
        logger.error("Failed to generate SQL query")
        raise HTTPException(status_code=500, detail="Failed to generate SQL query")

    plot_response = await orchestrator.generate_plots(sql_query, reformulated_intent)
    if not plot_response or plot_response["status"] == "error":
        logger.error(f"Plot generation failed: {plot_response.get('error_message')}")
        raise HTTPException(status_code=500, detail="Failed to generate plots")

    html_report = await orchestrator.generate_report(
        request.intent,
        reformulated_intent,
        sql_query,
        plot_response["html_plots"],
        plot_response["image_urls"],
    )
    if not html_report:
        logger.error("Failed to generate report")
        raise HTTPException(status_code=500, detail="Failed to generate report")

    logger.info("Pipeline completed successfully.")
    return PipelineResponse(
        success=True,
        original_intent=request.intent,
        reformulated_intent=reformulated_intent,
        sql_query=sql_query,
        plots=plot_response["html_plots"],
        html_report=html_report
    )
