from typing import Dict, List, Any, Tuple
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import pandas as pd
import plotly.graph_objects as go
import markdown

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
            3. The visualizations created
            
            Create a report that explains the insights, trends, and answers the original query in a clear,
            professional manner. Include specific data points and reference the visualizations by their figure numbers.
            
            The report should have: (Based on the original intent largely)
            - A clear title
            - An executive summary
            - Main findings/analysis with references to specific plots (e.g. "As shown in Figure 1...")
            - Data averages, distributions and comparisons
            - Conclusion
            
            Use markdown formatting for better readability.
            
            The plots will be rendered in the final report, so focus on analyzing them rather than describing their appearance."""),
            ("human", "{input}")
        ])

    def _get_plot_metadata(self, plots: List[go.Figure]) -> List[Dict[str, str]]:
        """Extract metadata from plotly figures for context."""
        metadata = []
        for i, plot in enumerate(plots):
            info = {
                "figure_number": i + 1,
                "title": plot.layout.title.text if plot.layout.title else f"Figure {i+1}",
                "type": plot.data[0].type if plot.data else "unknown",
                "x_axis": plot.layout.xaxis.title.text if hasattr(plot.layout, 'xaxis') and plot.layout.xaxis.title else "",
                "y_axis": plot.layout.yaxis.title.text if hasattr(plot.layout, 'yaxis') and plot.layout.yaxis.title else ""
            }
            metadata.append(info)
        return metadata

    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        """Prepare a comprehensive data summary for the LLM."""
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Dataset contains {len(df)} rows and {len(df.columns)} columns.")
        
        # Numeric columns summary
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_parts.append("\nNumeric columns summary:")
            for col in numeric_cols:
                stats = df[col].describe()
                summary_parts.append(f"- {col}: mean={stats['mean']:.2f}, std={stats['std']:.2f}, min={stats['min']:.2f}, max={stats['max']:.2f}")
        
        # Date columns info
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) > 0:
            summary_parts.append("\nDate columns:")
            for col in date_cols:
                summary_parts.append(f"- {col}: from {df[col].min()} to {df[col].max()}")
        
        return "\n".join(summary_parts)

    def generate_report(
        self,
        original_query: str,
        sql_results: pd.DataFrame,
        plots: List[go.Figure]
    ) -> Tuple[str, List[go.Figure]]:
        """Generate a comprehensive report based on the query, data, and plots.
        Returns both the markdown report text and the list of plots to be rendered."""
        
        # Prepare the data for the LLM
        data_summary = self._prepare_data_summary(sql_results)
        plot_metadata = self._get_plot_metadata(plots)
        
        # Prepare the input for the LLM
        input_data = {
            "input": f"""
Original Query: {original_query}

Data Summary:
{data_summary}

Available Visualizations:
{json.dumps(plot_metadata, indent=2)}

Please generate a comprehensive report analyzing this data and answering the original query.
Reference the figures by their figure numbers when discussing insights from the visualizations.
Include specific metrics, trends, and actionable insights.
"""
        }
        
        # Generate the report
        chain = self.report_prompt | self.llm
        report = chain.invoke(input_data)
        
        return report.content, plots

    def save_report(self, report_content: str, plots: List[go.Figure], output_path: str):
        """Save the generated report to an HTML file including both text and interactive plots."""
        
        # Convert markdown to HTML
        html_report = markdown.markdown(report_content)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Data Analysis Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .report-content {{
                    background-color: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    margin-bottom: 30px;
                }}
                .plot-container {{
                    background-color: white;
                    margin: 30px 0;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 30px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 35px;
                    margin-bottom: 20px;
                }}
                h3 {{
                    color: #7f8c8d;
                    margin-top: 25px;
                }}
                ul, ol {{
                    padding-left: 25px;
                }}
                li {{
                    margin-bottom: 8px;
                }}
                .metric {{
                    background-color: #ecf0f1;
                    padding: 10px 15px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 5px;
                }}
                .highlight {{
                    background-color: #fff3cd;
                    padding: 15px;
                    border-left: 4px solid #ffc107;
                    margin: 20px 0;
                }}
                code {{
                    background-color: #f8f9fa;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                .footer {{
                    text-align: center;
                    color: #7f8c8d;
                    margin-top: 40px;
                    padding: 20px;
                    border-top: 1px solid #ecf0f1;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="report-content">
                    {html_report}
                </div>
        """
        
        # Add each plot with figure labels
        for i, plot in enumerate(plots):
            plot_title = plot.layout.title.text if plot.layout.title else f"Figure {i+1}"
            div = plot.to_html(full_html=False, include_plotlyjs=False)
            html_content += f'''
                <div class="plot-container">
                    <h3 style="text-align: center; color: #2c3e50; margin-bottom: 20px;">
                        Figure {i+1}: {plot_title}
                    </h3>
                    {div}
                </div>
            '''
        
        html_content += """
                <div class="footer">
                    <p>Report generated automatically using AI-powered data analysis</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)