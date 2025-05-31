import requests
import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")

# API endpoints
REFORMULATE_API_URL = "http://localhost:8071/reformulate"
SQL_QUERY_API_URL = "http://localhost:8070/ask"  # Updated to /sql

# Step 1: Original intent
original_intent = "give monthly orders count in 1997"
# original_intent = "top products"

# Step 2: Reformulate the intent
reformulate_response = requests.post(
    REFORMULATE_API_URL,
    json={"intent": original_intent}
)

if reformulate_response.status_code != 200:
    print("❌ Reformulation failed:", reformulate_response.text)
    exit()

reformulated_intent = reformulate_response.json()["reformulated_intent"]
print(f"✅ Reformulated Intent:\n{reformulated_intent}")

# Step 3: Get SQL from /sql endpoint
sql_response = requests.post(
    SQL_QUERY_API_URL,
    json={"question": reformulated_intent}
)

if sql_response.status_code != 200:
    print("❌ SQL generation failed:", sql_response.text)
    exit()

data = json.loads(sql_response.text.strip())
sql_query = data['sql_query']
print(f"\n🧠 SQL Query:\n{sql_query}")

