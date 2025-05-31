from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from sqlalchemy import create_engine, text
from report_generator import ReportGenerator
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="API to Report Service", version="1.0.0")

class ReportRequest(BaseModel):
    original_query: str
    reformulated_query: Optional[str] = None
    sql_query: str
    plots: List[str]

class ReportResponse(BaseModel):
    html_report: str
    success: bool
    message: str

def execute_sql_query(sql_query: str) -> pd.DataFrame:
    """Execute SQL query against PostgreSQL database"""
    try:
        postgres_uri = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@db:5432/northwind")
        print(postgres_uri)

        if not postgres_uri:
            raise ValueError("POSTGRES_URI not found in environment variables")
        
        engine = create_engine(postgres_uri)
        df = pd.read_sql_query(text(sql_query), engine)
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

def reconstruct_plotly_figures(plots_html: List[str]) -> List[str]:
    return plots_html

@app.post("/generate-report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """Generate a comprehensive report from SQL query and plots from visualization agent."""
    try:
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        # Initialize report generator
        report_generator = ReportGenerator(api_key)
        
        # Execute SQL query to get data
        df = execute_sql_query(request.sql_query)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="SQL query returned no data")
        
        if not request.plots:
            raise HTTPException(status_code=400, detail="No plots provided")
        
        plots = reconstruct_plotly_figures(request.plots)
        
        # Use reformulated query if available, otherwise original
        query_for_analysis = request.reformulated_query or request.original_query
        
        # Generate the report
        report_content, plots = report_generator.generate_report(
            original_query=query_for_analysis,
            sql_results=df,
            plots=plots
        )
        
        # Convert to HTML
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            report_generator.save_report(report_content, plots, tmp.name)
            
            # Read the generated HTML file
            with open(tmp.name, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Clean up the temporary file
            os.unlink(tmp.name)
        
        return ReportResponse(
            html_report=html_content,
            success=True,
            message=f"Report generated successfully from {len(df)} rows of data and {len(plots)} plots"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "api-to-report",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)