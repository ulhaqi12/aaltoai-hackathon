import json
import pandas as pd
import plotly.graph_objects as go
from plotly.express.colors import qualitative as colors
import plotly.io as pio
from langchain.agents import tool

# Set Plotly to open plots in the system default browser
pio.renderers.default = "browser"


@tool
def output_table(data: str) -> str:
    """
    Displays a table using Plotly.

    Args:
        data: JSON-formatted string with column names as keys and lists of values.

    Example:
        data = '{"year": [2019, 2020, 2021], "price": [43.3, 53.4, 34.1]}'
    """
    if isinstance(data, dict):
        data = json.dumps(data)
    data = json.loads(data)
    df = pd.DataFrame(data)

    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df.columns),
                    fill_color=colors.Set2[5],
                    align='left'),
        cells=dict(values=[df[col] for col in df.columns],
                   fill_color=colors.Pastel2[5],
                   align='left'))
    ])
    fig.update_layout(title_text="Table View")
    fig.show()
    return "Displayed table."


@tool
def output_bar_plot(data: str, title: str) -> str:
    """
    Displays a bar chart using Plotly.

    Args:
        data: JSON-formatted string with two keys, where the first is x-axis and the second is y-axis.
        title: Title of the chart.

    Example:
        data = '{"category": ["A", "B", "C"], "count": [10, 20, 15]}'
    """
    if isinstance(data, dict):
        data = json.dumps(data)
    data = json.loads(data)

    x_key, y_key = list(data.keys())
    x_vals = data[x_key]
    y_vals = data[y_key]

    fig = go.Figure([go.Bar(x=x_vals, y=y_vals)])
    fig.update_layout(title=title, xaxis_title=x_key, yaxis_title=y_key)
    fig.show()
    return f"Displayed bar plot: {title}"


@tool
def output_time_series_plot(data: str, title: str) -> str:
    """
    Displays a time series line chart using Plotly.

    Args:
        data: JSON-formatted string where the first key is the x-axis (e.g., time),
              and the remaining keys are multiple series to plot.
        title: Title of the chart.

    Example:
        data = '{"year": [2019, 2020, 2021], "price": [43.3, 53.4, 34.1], "sales": [100, 150, 200]}'
    """
    if isinstance(data, dict):
        data = json.dumps(data)
    data = json.loads(data)

    x_key = list(data.keys())[0]
    x_vals = data[x_key]

    fig = go.Figure()
    for y_key in list(data.keys())[1:]:
        fig.add_trace(go.Scatter(
            x=x_vals, y=data[y_key],
            mode='lines+markers',
            name=y_key
        ))

    fig.update_layout(title=title,
                      xaxis_title=x_key,
                      yaxis_title="Values",
                      xaxis=dict(tickmode="array", tickvals=x_vals))
    fig.show()
    return f"Displayed time series plot: {title}"
