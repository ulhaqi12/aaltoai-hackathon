import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import boto3
from botocore.client import Config
import uuid
import os

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

s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv("MINIO_ENDPOINT", 'http://minio:9000'),  # inside Docker use service name, for local use 'localhost'
    aws_access_key_id=os.getenv("MINIO_USRER", 'minioadmin'),
    aws_secret_access_key=os.getenv("MINIO_PWD", 'minioadmin'),
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

def upload_image_to_minio(image_bytes: bytes, bucket: str = "charts", suffix: str = "png") -> str:
    key = f"{uuid.uuid4()}.{suffix}"

    try:
        s3_client.head_bucket(Bucket=bucket)
    except s3_client.exceptions.NoSuchBucket:
        s3_client.create_bucket(Bucket=bucket)

    s3_client.put_object(Bucket=bucket, Key=key, Body=image_bytes, ContentType="image/png")

    return f"http://localhost:9000/{bucket}/{key}"
