import os
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from openai import OpenAI, OpenAIError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    logger.critical("Failed to initialize OpenAI client: %s", e)
    raise

# PostgreSQL connection string
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@db:5432/northwind")

# Initialize FastAPI app
app = FastAPI(title="Intent Reformulation API")


# Function to extract PostgreSQL schema
def get_postgres_schema(uri: str) -> str:
    try:
        engine = create_engine(uri)
        inspector = inspect(engine)

        schema_parts = []
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            column_names = [col["name"] for col in columns]
            schema_parts.append(f"- {table_name}({', '.join(column_names)})")

        logger.info("Extracted schema from PostgreSQL")
        return "Tables:\n" + "\n".join(schema_parts)
    except Exception as e:
        logger.error("Failed to extract schema: %s", e)
        raise HTTPException(status_code=500, detail="Failed to extract schema from database")


# Retry logic for OpenAI API
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(OpenAIError),
    reraise=True,
)
def reformulate_intent(user_intent: str, schema: str, model: str = "gpt-4") -> str:
    system_prompt = f"""
You are a helpful assistant that reformulates vague or underspecified user intents into precise, well-structured, and SQL-queryable natural language questions. 
You are provided with a database schema. Use it to infer and clarify the user's likely intent as accurately as possible.

Your task is to:
- Reformulate vague questions into detailed, database-ready ones.
- Assume common-sense defaults where necessary (e.g., "top products" → "products with the highest total sales").
- Use relevant table and column names from the schema.
- Include filters or metrics implied by the question (e.g., totals, counts, dates).
- NEVER ask the user for clarification.
- NEVER return SQL.
- NEVER include markdown or meta commentary.
- ONLY return the rewritten, improved natural language question.

Schema:
{schema}
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_intent.strip()}
            ],
            temperature=0.3
        )
        result = response.choices[0].message.content.strip()
        logger.info("Reformulated intent successfully")
        return result
    except OpenAIError as e:
        logger.error("OpenAI API call failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate reformulated intent")


# Request and response models
class IntentRequest(BaseModel):
    intent: str
    model: Optional[str] = "gpt-4o-mini"


class ReformulatedResponse(BaseModel):
    reformulated_intent: str


@app.post("/reformulate", response_model=ReformulatedResponse)
def api_reformulate(request: IntentRequest):
    logger.info("Received reformulation request: intent='%s', model='%s'", request.intent, request.model)
    try:
        schema_text = get_postgres_schema(POSTGRES_URI)
        new_intent = reformulate_intent(request.intent, schema_text, model=request.model)
        return ReformulatedResponse(reformulated_intent=new_intent)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception("Unexpected error during reformulation")
        raise HTTPException(status_code=500, detail="Internal server error")
