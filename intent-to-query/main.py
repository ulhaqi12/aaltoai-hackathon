import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

from intent_utils import setup_postgres_agent, get_result

# === Load environment variables ===
load_dotenv()

# === Configure logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# === FastAPI App ===
app = FastAPI(title="Postgres AI SQL Agent")

# === Config ===
POSTGRES_URI = os.getenv("POSTGRES_URI")

def get_table_names(uri: str) -> list[str]:
    """Connect to PostgreSQL and return list of table names."""
    try:
        engine = create_engine(uri)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info("Discovered tables: %s", tables)
        return tables
    except SQLAlchemyError as e:
        logger.exception("Failed to inspect PostgreSQL schema.")
        raise RuntimeError("Unable to connect to database or fetch tables.") from e

# === Initialize Agent ===
try:
    TABLE_SCOPE = get_table_names(POSTGRES_URI)
    agent_executor, query_logger = setup_postgres_agent(POSTGRES_URI, include_tables=TABLE_SCOPE)
except Exception as e:
    logger.critical("Agent initialization failed: %s", e)
    raise RuntimeError("Agent could not be initialized.") from e

# === Request & Response Models ===
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sql_query: Optional[str]

# === Endpoint ===
@app.post("/ask", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    try:
        logger.info("Received query: %s", request.question)
        answer, sql_query = get_result(request.question, agent_executor, query_logger)
        logger.info("Generated SQL: %s", sql_query)
        return QueryResponse(answer=answer, sql_query=sql_query)
    except Exception as e:
        logger.exception("Failed to process query: %s", request.question)
        raise HTTPException(status_code=500, detail="Failed to generate answer or SQL.")
