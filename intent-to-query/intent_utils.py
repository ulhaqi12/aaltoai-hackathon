import os
import sqlparse
from rich.console import Console
from rich.syntax import Syntax
from sqlalchemy import create_engine
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SQLQueryLogger(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self.intermediate_steps = []

    def on_agent_action(self, action, **kwargs):
        self.intermediate_steps.append(("action", action))

    def on_agent_finish(self, finish, **kwargs):
        self.intermediate_steps.append(("finish", finish))


def setup_postgres_agent(postgres_uri: str, include_tables=None) -> tuple:
    """Connects to existing Postgres DB and sets up the SQL agent."""
    engine = create_engine(postgres_uri)

    # Set up database with optional table scope
    db = SQLDatabase(engine=engine, include_tables=include_tables)

    # Configure OpenAI model
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",  # or "gpt-4"
        temperature=0,
    )

    # Enable logging
    query_logger = SQLQueryLogger()
    callback_manager = CallbackManager([query_logger])

    # Create the SQL agent
    agent_executor = create_sql_agent(
        llm,
        db=db,
        verbose=True,
        callback_manager=callback_manager,
        max_iterations=50,
        max_execution_time=120,
        early_stopping_method="generate"
    )

    return agent_executor, query_logger


def get_result(query: str, agent_executor: object, query_logger: SQLQueryLogger) -> tuple:
    query_logger.intermediate_steps.clear()
    result = agent_executor.invoke({"input": query})

    captured_query = None
    for event_type, event in query_logger.intermediate_steps:
        if event_type == "action" and getattr(event, "tool", None) == 'sql_db_query':
            captured_query = getattr(event, "tool_input", None)

    return result.get('output', None), captured_query


def pprint_sql(q):
    formatted_sql = sqlparse.format(q, reindent=True, keyword_case='upper')
    console = Console()
    syntax = Syntax(formatted_sql, "sql", theme="monokai", line_numbers=True)
    console.print(syntax)


# if __name__ == "__main__":
#     # Read environment variables
#     POSTGRES_URI = os.getenv("POSTGRES_URI")  # e.g. postgresql://user:pass@host:port/dbname
#     TABLE_SCOPE = ["retail_sales"]  # Optional: restrict agent to specific tables

#     # Setup agent
#     agent_executor, query_logger = setup_postgres_agent(POSTGRES_URI, include_tables=TABLE_SCOPE)

#     # Example query
#     question = "Which is the highest selling product category?"
#     answer, sql_query = get_result(question, agent_executor, query_logger)

#     print("Answer:", answer)
#     if sql_query:
#         pprint_sql(sql_query)