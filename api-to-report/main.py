import os
import json
import logging
import tempfile
from typing import List, Dict, Any, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from report_generator import ReportGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("report-api")

# Create FastAPI app
app = FastAPI(title="API to Report Service", version="1.0.0")

# Data models
class ReportRequest(BaseModel):
    original_query: str
    reformulated_query: Optional[str] = None
    sql_query: str
    plots: List[str]
    image_urls: Optional[List[str]] = None  # Optional image URLs

class ReportResponse(BaseModel):
    html_report: str
    success: bool
    message: str

def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """Execute SQL query against PostgreSQL database."""
    try:
        postgres_uri = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@db:5432/northwind")
        if not postgres_uri:
            raise ValueError("POSTGRES_URI not found in environment variables")
        
        logger.info("Executing SQL query...")
        engine = create_engine(postgres_uri)
        df = pd.read_sql_query(text(sql_query), engine)
        logger.info(f"SQL query returned {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

@app.post("/generate-report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate a comprehensive report from SQL query and visualization output."""
    logger.info("Received report generation request")
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not configured")
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")

        report_generator = ReportGenerator(api_key)

        df = execute_sql_query(request.sql_query)
        if df.empty:
            logger.warning("SQL query returned no data")
            raise HTTPException(status_code=400, detail="SQL query returned no data")

        if not request.plots:
            logger.warning("No plots provided")
            raise HTTPException(status_code=400, detail="No plots provided")

        # Add image URLs if present
        logger.info(request.image_urls)
        image_urls = [url.replace("localhost", "minio") for url in request.image_urls if url]
        logger.info(image_urls)
        # if image_urls:
        #     logger.info(f"Appending {len(request.image_urls)} image URLs to plots")
        #     plots.extend([f'<img src="{url}" style="max-width:100%">' for url in request.image_urls])

        query_for_analysis = request.reformulated_query or request.original_query
        logger.info("Generating report content...")
        report_content, plots = report_generator.generate_report(
            original_query=query_for_analysis,
            sql_results=df,
            plots=request.plots,
            image_urls=image_urls
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            report_generator.save_report(report_content, plots, tmp.name)
            with open(tmp.name, 'r', encoding='utf-8') as f:
                html_content = f.read()
            os.unlink(tmp.name)

        logger.info("Report successfully generated and returned")
        return ReportResponse(
            html_report=html_content,
            success=True,
            message=f"Report generated successfully from {len(df)} rows of data and {len(plots)} plots"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during report generation")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {
        "status": "healthy", 
        "service": "api-to-report"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
