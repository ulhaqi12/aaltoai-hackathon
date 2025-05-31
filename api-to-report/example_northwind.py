import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

def get_northwind_data():
    """Connect to Northwind DB and get relevant sales data"""
    # Create SQLAlchemy engine - using the exposed port from docker-compose
    engine = create_engine('postgresql://postgres:postgres@localhost:55432/northwind')
    
    # Query to get order details with dates, amounts, and customer info
    query = """
    SELECT 
        o.order_date,
        SUM(od.quantity * od.unit_price * (1 - od.discount)) as total_sales,
        COUNT(DISTINCT o.customer_id) as unique_customers,
        SUM(od.quantity * od.unit_price * (1 - od.discount)) / COUNT(DISTINCT o.order_id) as avg_order_value,
        COUNT(DISTINCT o.order_id) as num_orders,
        SUM(od.quantity) as total_items
    FROM orders o
    JOIN order_details od ON o.order_id = od.order_id
    WHERE o.order_date IS NOT NULL
    GROUP BY o.order_date
    ORDER BY o.order_date;
    """
    
    # Execute query and load into DataFrame
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    # Convert order_date to datetime if it isn't already
    df['order_date'] = pd.to_datetime(df['order_date'])
    
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
    try:
        # Get real data from Northwind
        df = get_northwind_data()
        
        # Create visualizations
        plots = create_northwind_plots(df)
        
        # Original query that would come from the English-to-SQL part
        original_query = """Analyze our sales performance, including:
        - Daily sales trends and moving averages
        - Customer activity patterns
        - Order value and size metrics"""
        
        # Prepare the request data
        request_data = {
            "original_query": original_query,
            "sql_results": df.to_dict('records'),
            "plot_data": [fig.to_dict() for fig in plots]
        }
        
        # Make request to the API
        response = requests.post(
            "http://localhost:8000/generate-report",
            json=request_data
        )
        
        if response.status_code == 200:
            # Save the HTML report
            with open('northwind_report.html', 'w') as f:
                f.write(response.text)
            print("Report generated successfully! Open northwind_report.html in your browser to view it.")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure the database is running (docker-compose up) and the FastAPI server is running.")

if __name__ == "__main__":
    main() 