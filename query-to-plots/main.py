from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import os
import pandas as pd
import plotly.io as pio
from sqlalchemy import create_engine
from dotenv import load_dotenv
from openai import OpenAI
from utils import bar_chart, line_chart, pie_chart, scatter_plot, histogram, box_plot, heatmap, treemap, area_chart
import re
import json
import base64
from io import BytesIO
from fastapi.middleware.gzip import GZipMiddleware


# === Load environment variables ===
load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@db:5432/northwind")
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
    "treemap": treemap,
    "area_chart": area_chart
}

chart_descriptions = {
    "bar_chart": (
        "Bar Chart – Used to compare numeric values across different categories. "
        "Best for showing totals, counts, or averages for each group."
    ),
    "line_chart": (
        "Line Chart – Ideal for visualizing trends or patterns over a continuous variable, usually time."
    ),
    "pie_chart": (
        "Pie Chart – Shows proportions of a whole. Each slice represents a category's share of the total. "
        "Best used when comparing a small number of categories."
    ),
    "scatter_plot": (
        "Scatter Plot – Displays the relationship between two numeric variables. "
        "Useful for spotting correlations, clusters, or anomalies."
    ),
    "histogram": (
        "Histogram – Shows the frequency distribution of a single numeric variable. "
        "Helps understand how values are spread or grouped."
    ),
    "box_plot": (
        "Box Plot – Visualizes the distribution and variability of a numeric variable. "
        "Highlights medians, quartiles, and outliers across categories."
    ),
    "heatmap": (
        "Heatmap – Uses color to represent values in a grid. "
        "Best for visualizing relationships between two categories and their associated values."
    ),
    "area_chart": (
        "Area Chart – Similar to a line chart, but fills the area under the curve. "
        "Effective for showing stacked or cumulative trends over time."
    ),
    "treemap": (
        "Treemap – Uses nested rectangles to represent hierarchical data and relative sizes. "
        "Useful for exploring parts of a whole with multiple levels."
    )
}

# === Request and Response Schemas ===
class VisualizationRequest(BaseModel):
    sql_query: str
    intent: str
    model: Optional[str] = "gpt-4o-mini"

class VisualizationResponse(BaseModel):
    status: str  # "success", "partial", "error"
    html_plots: List[str]
    image_base64s: Optional[List[str]] = None
    error_message: Optional[str] = None


def suggest_chart(intent: str, data_preview: list, model: str) -> dict:
    prompt = f"""
        You are a skilled data visualization assistant.

        Your task is to analyze a given user intent and a preview of query result data, and then suggest the most relevant chart configurations. These charts will be rendered using Plotly in a dashboard.

        You are provided with:
        - A user intent describing what the person wants to see
        - A sample of the SQL query result data (first 5 rows)
        - A list of supported chart types and their purposes

        Your job:
        - Suggest the 2 to 3 most appropriate chart configurations
        - Use only the available chart types listed below
        - Use the actual column names from the data preview
        - Include an appropriate chart title for each chart
        - If a grouping column is relevant (e.g., for color), include it
        - Respond **only** in valid JSON (no markdown, no comments, no extra text)

        ---

        User Intent:
        "{intent}"

        Data Preview:
        {data_preview}

        Supported Chart Types:
        {chart_descriptions}

        ---

        Respond with a JSON list like this:

        [
        {{
            "chart_type": "bar_chart",
            "x": "category_name",
            "y": "product_count",
            "title": "Bar Chart of Products by Category",
            "group_by": optional_grouping_column
        }},
        {{
            "chart_type": "treemap",
            "path": ["category_name"],
            "values": "product_count",
            "title": "Treemap of Products by Category"
        }},
        {{
            "chart_type": "area_chart",
            "x": "date",
            "y": "sales",
            "title": "Area Chart of Sales Over Time"
        }},
        {{
            "chart_type": "pie_chart",
            "names": "category_name",
            "values": "product_count",
            "title": "Pie Chart of Products by Category",
            "group_by": optional_grouping_column
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
    try:
        engine = create_engine(POSTGRES_URI)
        df = pd.read_sql(request.sql_query, con=engine)
    except Exception as e:
        return VisualizationResponse(
            status="error",
            html_plots=["<p>Failed to execute SQL query.</p>"],
            error_message=str(e)
        )

    if df.empty:
        return VisualizationResponse(
            status="error",
            html_plots=["<p>No data returned from SQL query.</p>"],
            error_message="No Data returned from SQL query."
        )

    preview_data = df.head(5).to_dict(orient="records")

    try:
        chart_infos = suggest_chart(request.intent, preview_data, model=request.model)
    except Exception as e:
        return VisualizationResponse(
            status="error",
            html_plots=["<p>Chart suggestion failed.</p>"],
            error_message=str(e)
        )

    html_plots = []
    image_base64s = []

    for chart_info in chart_infos:
        chart_type = chart_info.get("chart_type")
        title = chart_info.get("title", "Generated Chart")

        if chart_type not in chart_map:
            continue

        kwargs = {
            k: v for k, v in chart_info.items()
            if k not in ("chart_type", "title") and v is not None
        }

        try:
            fig = chart_map[chart_type](df, title=title, **kwargs)
            html = pio.to_html(fig, full_html=False)
            html_plots.append(html)

            image_bytes = fig.to_image(format="png", engine="kaleido")
            image_base64s.append(base64.b64encode(image_bytes).decode("utf-8"))
        except Exception as e:
            html_plots.append(f"<p>Failed to render {chart_type}: {str(e)}</p>")
            image_base64s.append("")

    if not html_plots:
        return VisualizationResponse(
            status="error",
            html_plots=["<p>No charts could be generated from the input.</p>"],
            error_message="All suggested charts failed to render."
        )

    status = "partial" if any("Failed to render" in html for html in html_plots) else "success"
    return VisualizationResponse(
        status=status,
        html_plots=html_plots,
        image_base64s=image_base64s,
    )
