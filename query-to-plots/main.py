from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import os
import pandas as pd
import plotly.io as pio
from sqlalchemy import create_engine
from dotenv import load_dotenv
from openai import OpenAI
from utils import bar_chart, line_chart, pie_chart, scatter_plot, histogram, box_plot, heatmap
import re
import json
import base64
from io import BytesIO
from fastapi.middleware.gzip import GZipMiddleware


# === Load environment variables ===
load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Initialize OpenAI client ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === Initialize FastAPI app ===
app = FastAPI(title="Visualization Agent API")
app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress if response > 1KB

# === Chart functions registry ===
chart_map = {
    "bar_chart": bar_chart,
    "line_chart": line_chart,
    "pie_chart": pie_chart,
    "scatter_plot": scatter_plot,
    "histogram": histogram,
    "box_plot": box_plot,
    "heatmap": heatmap,
}

chart_descriptions = {
    "bar_chart": "Compare values across categories",
    "line_chart": "Show trends over time",
    "pie_chart": "Show proportions of a whole",
    "scatter_plot": "Show relationships between numeric variables",
    "histogram": "Show frequency distribution of a variable",
    "box_plot": "Show distribution with outliers",
    "heatmap": "Show matrix relationships using color"
}

# === Request and Response Schemas ===
class VisualizationRequest(BaseModel):
    sql_query: str
    intent: str
    model: Optional[str] = "gpt-4o"

class VisualizationResponse(BaseModel):
    html_plots: List[str]
    image_base64s: Optional[List[str]] = None


def suggest_chart(intent: str, data_preview: list, model: str) -> dict:
    prompt = f"""
    You are a data visualization expert.

    Based on the following:
    - User Intent: "{intent}"
    - Data preview: {data_preview}
    - Available chart types: {chart_descriptions}

    Suggest the best chart types and fields to use.
    Respond with a list of chart configurations in the following JSON format:

    [
        {{
            "chart_type": "bar_chart",
            "x": "category_name",
            "y": "product_count",
            "title": "Bar Chart of Products by Category",
            "group_by": "optional_grouping_column"
        }},
        {{
            "chart_type": "pie_chart",
            "names": "category_name",
            "values": "product_count",
            "title": "Pie Chart of Products by Category",
            "group_by": "optional_grouping_column"
        }}
    ]
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert at choosing the best chart for a dataset."},
            {"role": "user", "content": prompt.strip()}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()

    content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.MULTILINE).strip()

    return json.loads(content)

# === FastAPI Endpoint ===
@app.post("/visualize", response_model=VisualizationResponse)
def visualize_query(request: VisualizationRequest):
    engine = create_engine(POSTGRES_URI)
    df = pd.read_sql(request.sql_query, con=engine)

    if df.empty:
        return VisualizationResponse(html_plot="<p>No data returned from SQL query.</p>")

    preview_data = df.head(5).to_dict(orient="records")
    chart_infos = suggest_chart(request.intent, preview_data, model=request.model)

    html_plots = []
    image_base64s = []

    for chart_info in chart_infos:  # LLM returns a list of chart configs
        chart_type = chart_info.get("chart_type")
        title = chart_info.get("title", "Generated Chart")

        # Validate chart type
        if chart_type not in chart_map:
            continue

        # Prepare args: exclude known non-args like chart_type and title
        kwargs = {
            k: v for k, v in chart_info.items()
            if k not in ("chart_type", "title") and v is not None
        }

        # Dynamically call plotting function
        try:
            fig = chart_map[chart_type](df, title=title, **kwargs)
        except Exception as e:
            print(f"Failed to render chart {chart_type}: {e}")
            continue

        html = pio.to_html(fig, full_html=False)
        html_plots.append(html)

        try:
            image_bytes = fig.to_image(format="png", engine="kaleido")
            image_base64s.append(base64.b64encode(image_bytes).decode("utf-8"))
        except Exception as e:
            print(f"Failed to generate image: {e}")
            image_base64s.append("")

    
    return VisualizationResponse(
        html_plots=html_plots, 
        image_base64s=image_base64s
    )
