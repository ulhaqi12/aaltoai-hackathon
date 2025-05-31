import os
import logging
import sqlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from rich.console import Console
from rich.syntax import Syntax

from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class SQLQueryLogger(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self.intermediate_steps = []

    def on_agent_action(self, action, **kwargs):
        self.intermediate_steps.append(("action", action))

    def on_agent_finish(self, finish, **kwargs):
        self.intermediate_steps.append(("finish", finish))


def setup_postgres_agent(postgres_uri: str, include_tables=None, model="gpt-4o-mini") -> tuple:
    """
    Initializes the SQL agent using the provided PostgreSQL URI.
    Returns the agent executor and query logger.
    """
    try:
        if not postgres_uri:
            raise ValueError("POSTGRES_URI is not set in environment variables.")

        logger.info("Creating SQLAlchemy engine...")
        engine = create_engine(postgres_uri)

        logger.info("Connecting to SQLDatabase...")
        db = SQLDatabase(engine=engine, include_tables=include_tables)

        logger.info("Initializing OpenAI LLM...")
        llm = ChatOpenAI(
            model=model,
            temperature=0,
        )

        query_logger = SQLQueryLogger()
        callback_manager = CallbackManager([query_logger])

        logger.info("Creating LangChain SQL agent...")
        agent_executor = create_sql_agent(
            llm,
            db=db,
            verbose=True,
            callback_manager=callback_manager,
            max_iterations=50,
            max_execution_time=120,
            early_stopping_method="generate"
        )

        logger.info("SQL agent successfully initialized.")
        return agent_executor, query_logger

    except SQLAlchemyError as e:
        logger.exception("Database connection failed.")
        raise RuntimeError("Failed to connect to the PostgreSQL database.") from e
    except Exception as e:
        logger.exception("Failed to set up SQL agent.")
        raise RuntimeError("Failed to initialize SQL agent.") from e


def get_result(query: str, agent_executor: object, query_logger: SQLQueryLogger) -> tuple:
    """
    Executes the query using the agent and returns the result and SQL query used.
    """
    try:
        query_logger.intermediate_steps.clear()
        logger.info("Invoking SQL agent with query: %s", query)

        result = agent_executor.invoke({"input": query})

        captured_query = None
        for event_type, event in query_logger.intermediate_steps:
            if event_type == "action" and getattr(event, "tool", None) == 'sql_db_query':
                captured_query = getattr(event, "tool_input", None)

        logger.info("Query executed successfully.")
        return result.get('output', None), captured_query

    except Exception as e:
        logger.exception("Failed to execute query.")
        raise RuntimeError("Failed to execute query using agent.") from e


def pprint_sql(q):
    """
    Pretty-prints the SQL query using Rich.
    """
    if not q:
        logger.warning("No SQL query provided for printing.")
        return

    formatted_sql = sqlparse.format(q, reindent=True, keyword_case='upper')
    console = Console()
    syntax = Syntax(formatted_sql, "sql", theme="monokai", line_numbers=True)
    console.print(syntax)
    