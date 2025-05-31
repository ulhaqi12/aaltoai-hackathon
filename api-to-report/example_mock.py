import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timedelta

# Mock data generation
def generate_mock_data():
    # Create date range for the last 12 months
    dates = pd.date_range(end=datetime.now(), periods=12, freq='M')
    
    # Generate mock sales data
    data = {
        'date': dates,
        'sales': [15000, 17000, 14500, 21000, 19500, 22000, 23000, 20000, 25000, 24000, 26000, 28000],
        'customers': [150, 165, 140, 190, 180, 210, 220, 200, 240, 230, 250, 270],
        'avg_transaction': [100, 103, 104, 111, 108, 105, 105, 100, 104, 104, 104, 104]
    }
    
    return pd.DataFrame(data)

# Create mock visualizations
def create_mock_plots(df):
    # Plot 1: Sales trend
    fig1 = px.line(df, x='date', y='sales', 
                   title='Monthly Sales Trend',
                   labels={'date': 'Month', 'sales': 'Total Sales ($)'},
                   template='plotly_white')
    fig1.update_traces(line_color='#2E86C1', line_width=3)
    
    # Plot 2: Customer growth
    fig2 = px.bar(df, x='date', y='customers',
                  title='Monthly Customer Count',
                  labels={'date': 'Month', 'customers': 'Number of Customers'},
                  template='plotly_white')
    fig2.update_traces(marker_color='#27AE60')
    
    # Plot 3: Average transaction value
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df['date'],
        y=df['avg_transaction'],
        mode='lines+markers',
        name='Average Transaction',
        line=dict(color='#8E44AD', width=2),
        marker=dict(size=8)
    ))
    fig3.update_layout(
        title='Average Transaction Value Over Time',
        xaxis_title='Month',
        yaxis_title='Average Transaction ($)',
        template='plotly_white'
    )
    
    return [fig1, fig2, fig3]

def main():
    # Generate mock data
    df = generate_mock_data()
    
    # Create mock plots
    plots = create_mock_plots(df)
    
    # Original query that would come from the English-to-SQL part
    original_query = "Show me the sales performance over the last year, including customer growth and average transaction value"
    
    # Prepare the request data
    request_data = {
        "original_query": original_query,
        "sql_results": df.to_dict('records'),
        "plot_data": [fig.to_dict() for fig in plots]
    }
    
    # Make request to the API
    try:
        response = requests.post(
            "http://localhost:8000/generate-report",
            json=request_data
        )
        
        if response.status_code == 200:
            # Save the HTML report
            with open('mock_report.html', 'w') as f:
                f.write(response.text)
            print("Report generated successfully! Open mock_report.html in your browser to view it.")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the FastAPI server is running.")

if __name__ == "__main__":
    main() 