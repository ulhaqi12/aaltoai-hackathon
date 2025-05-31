from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import os
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

# Load environment variables
load_dotenv()

# Init OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@db:5432/northwind")

# Init FastAPI app
app = FastAPI(title="Intent Reformulation API")

# === Schema extractor ===
def get_postgres_schema(uri: str) -> str:
    engine = create_engine(uri)
    inspector = inspect(engine)

    schema_parts = []
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        column_names = [col["name"] for col in columns]
        schema_parts.append(f"- {table_name}({', '.join(column_names)})")

    return "Tables:\n" + "\n".join(schema_parts)

# === LLM reformulation ===
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

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_intent.strip()}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


# === FastAPI schema ===
class IntentRequest(BaseModel):
    intent: str
    model: Optional[str] = "gpt-4o-mini"


class ReformulatedResponse(BaseModel):
    reformulated_intent: str


@app.post("/reformulate", response_model=ReformulatedResponse)
def api_reformulate(request: IntentRequest):
    schema_text = get_postgres_schema(POSTGRES_URI)
    new_intent = reformulate_intent(request.intent, schema_text, model=request.model)
    return ReformulatedResponse(reformulated_intent=new_intent)
