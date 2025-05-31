from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import pandas as pd
import plotly.graph_objects as go
from report_generator import ReportGenerator
import os
import tempfile

app = FastAPI()

# Initialize the report generator with the API key from environment variable
report_generator = ReportGenerator(os.getenv("OPENAI_API_KEY"))

class ReportRequest(BaseModel):
    original_query: str
    sql_results: List[Dict[str, Any]]  # List of dictionaries representing the DataFrame
    plot_data: List[Dict[str, Any]]    # Serialized plotly figures

@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    try:
        # Convert the SQL results to a pandas DataFrame
        df = pd.DataFrame(request.sql_results)
        
        # Convert the plot data back to plotly figures
        plots = [go.Figure(fig) for fig in request.plot_data]
        
        # Generate the report
        report_content, plots = report_generator.generate_report(
            original_query=request.original_query,
            sql_results=df,
            plots=plots
        )
        
        # Create a temporary file to store the HTML report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            report_generator.save_report(report_content, plots, tmp.name)
            
            # Read the generated HTML file
            with open(tmp.name, 'r') as f:
                html_content = f.read()
            
            # Clean up the temporary file
            os.unlink(tmp.name)
            
            return HTMLResponse(content=html_content, status_code=200)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 