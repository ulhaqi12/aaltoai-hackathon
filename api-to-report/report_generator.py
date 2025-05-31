from typing import Dict, List, Any, Tuple
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import pandas as pd
import plotly.graph_objects as go

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

    def generate_report(
        self,
        original_query: str,
        sql_results: pd.DataFrame,
        plots: List[go.Figure]
    ) -> Tuple[str, List[go.Figure]]:
        """Generate a comprehensive report based on the query, data, and plots.
        Returns both the markdown report text and the list of plots to be rendered."""
        
        # Prepare the data for the LLM
        data_summary = sql_results.describe().to_string()
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
"""
        }
        
        # Generate the report
        chain = self.report_prompt | self.llm
        report = chain.invoke(input_data)
        
        return report.content, plots

    def save_report(self, report_content: str, plots: List[go.Figure], output_path: str):
        """Save the generated report to an HTML file including both text and interactive plots."""
        html_content = f"""
        <html>
        <head>
            <title>Generated Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .report-content {{ max-width: 1200px; margin: 0 auto; }}
                .plot-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="report-content">
                {report_content}
            </div>
        """
        
        # Add each plot
        for i, plot in enumerate(plots):
            div = plot.to_html(full_html=False, include_plotlyjs=False)
            html_content += f'<div class="plot-container" id="plot-{i}">{div}</div>'
        
        html_content += """
        </body>
        </html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content) 