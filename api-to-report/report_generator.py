import json
import markdown
import pandas as pd
import requests
import tempfile
import os
import base64
from typing import List, Tuple, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage


class ReportGenerator:
    def __init__(self, openai_api_key: str):
        """Initialize the report generator with OpenAI API key."""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=openai_api_key
        )

        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert data analyst and report writer. Your task is to create a cohesive, 
            well-structured report based on:
            1. The original English query/intent
            2. The data retrieved from the SQL query
            3. The visualizations created and provided images

            Create a report that explains the insights, trends, and answers the original query in a clear,
            professional manner. Include specific data points and reference the visualizations by their figure numbers.

            The report should have:
            - A clear title
            - An executive summary
            - Main findings/analysis with references to specific plots or images
            - Data averages, distributions and comparisons
            - Conclusion

            Use markdown formatting for better readability.
            """),
            ("human", "{input}")
        ])

    def _get_plot_metadata(self, plots: List[str], image_urls: List[str]) -> List[Dict[str, str]]:
        return [
            {
                "figure_number": i + 1,
                "title": f"Figure {i + 1}",
                "type": "plotly+image",
                "image_url": url
            } for i, url in enumerate(image_urls)
        ]

    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        summary_parts = [f"Dataset contains {len(df)} rows and {len(df.columns)} columns."]

        numeric_cols = df.select_dtypes(include=['number']).columns
        if numeric_cols.any():
            summary_parts.append("\nNumeric columns summary:")
            for col in numeric_cols:
                stats = df[col].describe()
                summary_parts.append(
                    f"- {col}: mean={stats['mean']:.2f}, std={stats['std']:.2f}, "
                    f"min={stats['min']:.2f}, max={stats['max']:.2f}"
                )

        date_cols = df.select_dtypes(include=['datetime64']).columns
        if date_cols.any():
            summary_parts.append("\nDate columns:")
            for col in date_cols:
                summary_parts.append(f"- {col}: from {df[col].min()} to {df[col].max()}")

        return "\n".join(summary_parts)

    import base64

    def _download_images_as_bytes(self, image_urls: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
        image_blobs = []
        temp_files = []

        for idx, url in enumerate(image_urls):
            try:
                response = requests.get(url)
                response.raise_for_status()

                # Write to temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                temp_file.write(response.content)
                temp_file.close()
                temp_files.append(temp_file.name)

                # Read and encode image to base64
                with open(temp_file.name, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    image_blobs.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded}"
                        }
                    })

            except Exception as e:
                print(f"⚠️ Failed to download or read image {url}: {e}")

        return image_blobs, temp_files


    def generate_report(
        self,
        original_query: str,
        sql_results: pd.DataFrame,
        plots: List[str],
        image_urls: List[str]
    ) -> Tuple[str, List[str]]:
        # Summary and metadata
        data_summary = self._prepare_data_summary(sql_results)
        plot_metadata = self._get_plot_metadata(plots, image_urls)

        input_text = f"""
Original Query: {original_query}

Data Summary:
{data_summary}

Available Visualizations:
{json.dumps(plot_metadata, indent=2)}

Please generate a comprehensive report analyzing this data and answering the original query.
Reference the figures by their figure numbers when discussing insights from the visualizations and images.
Include specific metrics, trends, and actionable insights.
"""

        image_blobs, temp_files = self._download_images_as_bytes(image_urls)
        message = HumanMessage(content=[{"type": "text", "text": input_text}] + image_blobs)

        try:
            chain = self.report_prompt | self.llm
            response = chain.invoke(message)
            return response.content, plots
        finally:
            # Cleanup temp files
            for f in temp_files:
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"⚠️ Failed to delete temp file {f}: {e}")

    def save_report(self, report_content: str, plots: List[str], output_path: str):
        html_report = markdown.markdown(report_content)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Analysis Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; background-color: #f8f9fa; }}
                .container {{ max-width: 1200px; margin: auto; padding: 20px; }}
                .report-content, .plot-container {{ background: #fff; padding: 20px; margin-bottom: 30px; border-radius: 8px; }}
                .footer {{ text-align: center; color: #888; margin-top: 40px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="report-content">{html_report}</div>
        """

        for i, plot_html in enumerate(plots):
            html_content += f"""
                <div class="plot-container">
                    <h3 style="text-align: center;">Figure {i + 1}</h3>
                    {plot_html}
                </div>
            """

        html_content += """
                <div class="footer">
                    <p>Report generated using AI-based analysis pipeline.</p>
                </div>
            </div>
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)