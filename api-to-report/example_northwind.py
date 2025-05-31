import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import numpy as np
from report_generator import ReportGenerator

# Load environment variables from .env file
load_dotenv()

# Verify API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables or .env file")
if api_key.startswith('sk-') is False:
    raise ValueError("OPENAI_API_KEY seems invalid. It should start with 'sk-'")

def get_northwind_data():
    """Generate sample Northwind data"""
    # Create date range for a year of data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate sample data with realistic patterns
    base_sales = np.linspace(1000, 1500, len(dates))  # Slight upward trend
    weekly_pattern = np.array([1.0, 0.8, 0.9, 1.0, 1.1, 1.3, 1.4] * 53)[:len(dates)]
    seasonal_pattern = 1 + 0.3 * np.sin(np.linspace(0, 2*np.pi, len(dates)))
    
    # Combine patterns with noise
    total_sales = (base_sales * weekly_pattern * seasonal_pattern + 
                  np.random.normal(0, 100, len(dates))).round(2)
    
    unique_customers = (20 + 5 * weekly_pattern + np.random.randint(-3, 4, len(dates))).astype(int)
    num_orders = (unique_customers * 1.5 + np.random.randint(-5, 6, len(dates))).astype(int)
    total_items = (num_orders * 5 + np.random.randint(-10, 11, len(dates))).astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        'order_date': dates,
        'total_sales': total_sales,
        'unique_customers': unique_customers,
        'num_orders': num_orders,
        'total_items': total_items
    })
    
    # Calculate derived metrics
    df['avg_order_value'] = (df['total_sales'] / df['num_orders']).round(2)
    
    return df

def create_northwind_plots(df):
    """Create visualizations from Northwind data"""
    # Plot 1: Daily Sales Trend with 7-day moving average
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df['order_date'],
        y=df['total_sales'],
        mode='markers+lines',
        name='Daily Sales',
        line=dict(color='#2E86C1', width=1),
        marker=dict(size=4)
    ))
    fig1.add_trace(go.Scatter(
        x=df['order_date'],
        y=df['total_sales'].rolling(7).mean(),
        mode='lines',
        name='7-day Moving Average',
        line=dict(color='#E74C3C', width=3)
    ))
    fig1.update_layout(
        title='Daily Sales with 7-day Moving Average',
        xaxis_title='Date',
        yaxis_title='Total Sales ($)',
        template='plotly_white'
    )
    
    # Plot 2: Customer Activity
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=df['order_date'],
        y=df['unique_customers'],
        name='Unique Customers',
        marker_color='#27AE60'
    ))
    fig2.add_trace(go.Scatter(
        x=df['order_date'],
        y=df['num_orders'],
        name='Number of Orders',
        mode='lines',
        line=dict(color='#8E44AD', width=2),
        yaxis='y2'
    ))
    fig2.update_layout(
        title='Daily Customer Activity',
        xaxis_title='Date',
        yaxis_title='Unique Customers',
        yaxis2=dict(
            title='Number of Orders',
            overlaying='y',
            side='right'
        ),
        template='plotly_white'
    )
    
    # Plot 3: Order Metrics
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df['order_date'],
        y=df['avg_order_value'],
        mode='lines+markers',
        name='Average Order Value',
        line=dict(color='#F39C12', width=2),
        marker=dict(size=6)
    ))
    fig3.add_trace(go.Scatter(
        x=df['order_date'],
        y=df['total_items'] / df['num_orders'],
        mode='lines+markers',
        name='Items per Order',
        line=dict(color='#16A085', width=2),
        marker=dict(size=6),
        yaxis='y2'
    ))
    fig3.update_layout(
        title='Order Value and Size Metrics',
        xaxis_title='Date',
        yaxis_title='Average Order Value ($)',
        yaxis2=dict(
            title='Items per Order',
            overlaying='y',
            side='right'
        ),
        template='plotly_white'
    )
    
    return [fig1, fig2, fig3]

def main():
    """Generate a sample report using the ReportGenerator template"""
    try:
        # Initialize the report generator
        report_generator = ReportGenerator(api_key)
        
        # Get mock data from Northwind
        df = get_northwind_data()
        
        # Create visualizations
        plots = create_northwind_plots(df)
        
        # Define the original query (simulating what would come from user intent)
        original_query = "Show me the sales performance trends for the past year, including customer activity patterns and order value analysis"
        
        # Generate the report using the ReportGenerator template
        report_content, plots = report_generator.generate_report(
            original_query=original_query,
            sql_results=df,
            plots=plots
        )
        
        # Save the report using the ReportGenerator
        output_file = 'northwind_report.html'
        report_generator.save_report(report_content, plots, output_file)
        print(f"Report generated successfully! Open {output_file} in your browser to view it.")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()