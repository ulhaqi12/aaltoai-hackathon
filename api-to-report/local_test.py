import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables or .env file")
if api_key.startswith('sk-') is False:
    raise ValueError("OPENAI_API_KEY seems invalid. It should start with 'sk-'")

def generate_mock_data():
    """Generate mock sales data for testing"""
    # Create date range for the last 30 days
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Generate some realistic-looking data with a slight upward trend and weekly patterns
    np.random.seed(42)  # For reproducibility
    
    # Base values
    base_sales = np.linspace(1000, 1200, 30)  # Slight upward trend
    base_customers = np.linspace(50, 60, 30)   # Slight upward trend
    
    # Add weekly patterns (higher on weekends)
    weekly_pattern = np.array([1.0, 0.8, 0.9, 1.0, 1.1, 1.3, 1.4] * 5)[:30]
    
    # Add random noise
    noise_sales = np.random.normal(0, 100, 30)
    noise_customers = np.random.normal(0, 5, 30)
    
    # Combine components
    sales = (base_sales * weekly_pattern + noise_sales).round(2)
    customers = (base_customers * weekly_pattern + noise_customers).round(0)
    avg_transaction = (sales / customers).round(2)
    
    data = {
        'date': dates,
        'sales': sales,
        'customers': customers,
        'avg_transaction': avg_transaction,
        'items_per_order': np.random.normal(3, 0.5, 30).round(1)  # Random items per order
    }
    
    return pd.DataFrame(data)

def create_plots(df):
    """Create visualizations from the data"""
    # Plot 1: Sales Trend with 7-day moving average
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df['date'],
        y=df['sales'],
        mode='markers+lines',
        name='Daily Sales',
        line=dict(color='#2E86C1', width=1),
        marker=dict(size=6)
    ))
    fig1.add_trace(go.Scatter(
        x=df['date'],
        y=df['sales'].rolling(7).mean(),
        mode='lines',
        name='7-day Moving Average',
        line=dict(color='#E74C3C', width=3)
    ))
    fig1.update_layout(
        title='Daily Sales with 7-day Moving Average',
        xaxis_title='Date',
        yaxis_title='Total Sales ($)',
        template='plotly_white',
        hovermode='x unified'
    )
    
    # Plot 2: Customer Activity
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df['date'],
        y=df['customers'],
        name='Daily Customers',
        marker_color='#27AE60'
    ))
    fig2.update_layout(
        title='Daily Customer Count',
        xaxis_title='Date',
        yaxis_title='Number of Customers',
        template='plotly_white',
        hovermode='x unified'
    )
    
    # Plot 3: Metrics per Order
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df['date'],
        y=df['avg_transaction'],
        mode='lines+markers',
        name='Average Transaction',
        line=dict(color='#8E44AD', width=2),
        marker=dict(size=6)
    ))
    fig3.add_trace(go.Scatter(
        x=df['date'],
        y=df['items_per_order'],
        mode='lines+markers',
        name='Items per Order',
        line=dict(color='#F39C12', width=2),
        marker=dict(size=6),
        yaxis='y2'
    ))
    fig3.update_layout(
        title='Order Metrics Over Time',
        xaxis_title='Date',
        yaxis_title='Average Transaction ($)',
        yaxis2=dict(
            title='Items per Order',
            overlaying='y',
            side='right'
        ),
        template='plotly_white',
        hovermode='x unified'
    )
    
    return [fig1, fig2, fig3]

def generate_report(df, plots):
    """Generate analysis report using OpenAI"""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert data analyst and report writer. Analyze the provided sales data and create 
        a comprehensive report that includes:
        
        1. Executive Summary
        2. Key Findings
           - Sales Trends
           - Customer Patterns
           - Order Metrics
        3. Detailed Analysis
           - Weekly Patterns
           - Growth Trends
           - Areas for Improvement
        4. Recommendations
        
        Use specific numbers and reference the visualizations in your analysis.
        Format the report in markdown for better readability."""),
        ("human", "{input}")
    ])
    
    # Prepare data summary for the LLM
    data_summary = {
        "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
        "total_sales": f"${df['sales'].sum():,.2f}",
        "avg_daily_sales": f"${df['sales'].mean():,.2f}",
        "total_customers": int(df['customers'].sum()),
        "avg_transaction": f"${df['avg_transaction'].mean():,.2f}",
        "avg_items_per_order": f"{df['items_per_order'].mean():.1f}"
    }
    
    # Generate the report
    input_data = {
        "input": f"""
Please analyze this sales data and create a report:

Date Range: {data_summary['date_range']}

Key Metrics:
- Total Sales: {data_summary['total_sales']}
- Average Daily Sales: {data_summary['avg_daily_sales']}
- Total Customers Served: {data_summary['total_customers']}
- Average Transaction Value: {data_summary['avg_transaction']}
- Average Items per Order: {data_summary['avg_items_per_order']}

The visualizations show:
Figure 1: Daily sales trend with 7-day moving average
Figure 2: Daily customer count
Figure 3: Average transaction value and items per order over time

Please provide insights about trends, patterns, and recommendations.
"""
    }
    
    chain = prompt | llm
    report_content = chain.invoke(input_data)
    
    return report_content.content

def save_report(report_content, plots, output_path='local_report.html'):
    """Save the report and plots as an HTML file"""
    html_content = f"""
    <html>
    <head>
        <title>Sales Analysis Report</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .report-content {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .plot-container {{
                margin: 30px 0;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{
                color: #2C3E50;
            }}
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

def main():
    try:
        # Generate mock data
        df = generate_mock_data()
        
        # Create visualizations
        plots = create_plots(df)
        
        # Generate the report
        report_content = generate_report(df, plots)
        
        # Save everything as an HTML file
        save_report(report_content, plots)
        
        print("Report generated successfully! Open local_report.html in your browser to view it.")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 