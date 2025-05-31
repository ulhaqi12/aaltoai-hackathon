import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def bar_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """Creates a bar chart using Plotly."""
    return px.bar(df, x=x, y=y, title=title)

def line_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """Creates a line chart using Plotly."""
    return px.line(df, x=x, y=y, title=title)

def pie_chart(df: pd.DataFrame, names: str, values: str, title: str) -> go.Figure:
    """Creates a pie chart using Plotly."""
    return px.pie(df, names=names, values=values, title=title)

def scatter_plot(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """Creates a scatter plot using Plotly."""
    return px.scatter(df, x=x, y=y, title=title)

def histogram(df: pd.DataFrame, x: str, title: str) -> go.Figure:
    """Creates a histogram using Plotly."""
    return px.histogram(df, x=x, title=title)

def box_plot(df: pd.DataFrame, y: str, x: str = None, title: str = "") -> go.Figure:
    """Creates a box plot using Plotly."""
    return px.box(df, y=y, x=x, title=title)

def heatmap(df: pd.DataFrame, x: str, y: str, z: str, title: str) -> go.Figure:
    """Creates a heatmap using Plotly from a pivoted DataFrame."""
    pivot_table = df.pivot(index=y, columns=x, values=z)
    return go.Figure(data=go.Heatmap(
        z=pivot_table.values,
        x=pivot_table.columns,
        y=pivot_table.index,
        colorscale='Viridis'
    )).update_layout(title=title)

def area_chart(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    """Creates an area chart using Plotly."""
    return px.area(df, x=x, y=y, title=title)

def treemap(df: pd.DataFrame, path: str, values: str, title: str) -> go.Figure:
    """Creates a treemap using Plotly."""
    # Ensure path is a list (Plotly expects a list of column names)
    path = [path] if isinstance(path, str) else path
    return px.treemap(df, path=path, values=values, title=title)
