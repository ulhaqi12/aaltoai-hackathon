from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os

from utils import setup_postgres_agent, get_result

# Load env variables (for POSTGRES_URI and OPENAI_API_KEY)
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Postgres AI SQL Agent")

# Read DB URI
POSTGRES_URI = os.getenv("POSTGRES_URI")

# Optionally restrict to specific tables
TABLE_SCOPE = [
    "categories",
    "customer_customer_demo",
    "customer_demographics",
    "customers",
    "employee_territories",
    "employees",
    "order_details",
    "orders",
    "products",
    "region",
    "shippers",
    "suppliers",
    "territories",
    "us_states"
]

# Load agent once at startup
agent_executor, query_logger = setup_postgres_agent(POSTGRES_URI, include_tables=TABLE_SCOPE)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str]


@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    answer, sql_query = get_result(request.question, agent_executor, query_logger)
    return QueryResponse(answer=answer, sql_query=sql_query)
