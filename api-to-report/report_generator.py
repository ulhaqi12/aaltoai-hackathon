import logging
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
            ("system", """
        You are a professional data analyst and report writer. Your task is to generate a concise, well-structured report that addresses the user's original query using:

        1. The original user intent
        2. A summary of the SQL query results
        3. Context from supporting visualizations (e.g., figures — referenced only by number)

        The report must include the following sections:

        - **Title**: Clear and focused
        - **Executive Summary**: A brief overview of the main insights (3–4 sentences)
        - **Main Findings**: Key observations from the data (e.g., top items, totals, comparisons)
        - **Trends and Comparisons**:
            - Include relevant metrics like averages, variations, and distributions
            - Reference standard deviation or rankings if useful
        - **Visual References**: Mention figures by number only (e.g., “Figure 1”) — **do not describe or include the images**
        - **Conclusion**: Summarize the findings and suggest possible actions or decisions

        Guidelines:
        - Write in clear, professional English
        - Use markdown for structure and emphasis
        - Do **not** include images or their descriptions
        - Do **not** output raw SQL or HTML
        - Focus on actionable insights, not visual design

        Your audience is business decision-makers seeking clarity and recommendations.
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

        logging.info("original len: " + str(len(input_text)))
        MAX_CHARS = 100000 * 3  # Approx 400,000 characters (~128K token context)

        image_blobs, temp_files = self._download_images_as_bytes(image_urls)

        # Prepare image part size
        serialized_image_blobs = [json.dumps(blob) for blob in image_blobs]
        image_blobs_size = sum(len(blob) for blob in serialized_image_blobs)

        # Estimate max text size allowed
        max_text_size = MAX_CHARS - image_blobs_size

        # Truncate input text so that combined JSON fits in MAX_CHARS
        truncated_text = input_text
        while True:
            text_payload = {"type": "text", "text": truncated_text}
            serialized_text = json.dumps(text_payload)
            total_size = len(serialized_text) + image_blobs_size

            if total_size <= MAX_CHARS:
                break

            # Reduce text length by 10% iteratively if still too long
            truncated_text = truncated_text[:int(len(truncated_text) * 0.9)]
        
        logging.info("After truncaiton len: " + str(len(truncated_text)))
        
        # logging.info("image blobs:" + str(len(image_blobs)))
        # logging.info(type(image_blobs))

        # Final payload to LLM
        message_content = [{"type": "text", "text": truncated_text}] #+ image_blobs
        message = HumanMessage(content=message_content)

        try:
            chain = self.report_prompt | self.llm
            response = chain.invoke(message)
            return response.content, plots
        finally:
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
