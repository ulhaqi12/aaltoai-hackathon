import os
import pandas as pd
import sqlparse
from rich.console import Console
from rich.syntax import Syntax
from sqlalchemy import create_engine
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama

from dotenv import load_dotenv
load_dotenv()

from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)


class SQLQueryLogger(BaseCallbackHandler):
    def __init__(self):
        super().__init__()
        self.intermediate_steps = []

    def on_agent_action(self, action, **kwargs):
        # Record each agent action (the SQL query should be one of these actions)
        self.intermediate_steps.append(("action", action))

    def on_agent_finish(self, finish, **kwargs):
        # Optionally, record when the agent finishes processing.
        self.intermediate_steps.append(("finish", finish))


def setup_database(csv_path: str, db_name: str) -> object:
    """Loads CSV data into a SQLite database and returns the engine."""
    db_path = f"sqlite:///{db_name}.db"
    df = pd.read_csv(csv_path)
    engine = create_engine(db_path)
    df.to_sql(db_name, engine, index=False, if_exists='replace')
    return engine


def setup_agent(engine: object, api_key : str) -> tuple:
    """Sets up the SQL agent along with the callback logger. Returns the agent_executor and query_logger."""
    query_logger = SQLQueryLogger()
    callback_manager = CallbackManager([query_logger])
    # Initialize the SQL database interface
    db = SQLDatabase(engine=engine)    
    # Set up the language model
    # llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0, google_api_key=api_key)
    llm = ChatOllama(model="llama3.2:3b", temperature=0)

    # system_message = SystemMessagePromptTemplate.from_template(
    # "Do NOT use markdown formatting."
    # "Do NOT wrap queries in triple backticks including the string '```sql'.")
    
    # human_message = HumanMessagePromptTemplate.from_template("{input}")
    # chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    
    # Create the SQL agent
    agent_executor = create_sql_agent(llm, db=db, verbose=True, callback_manager=callback_manager)
    #, agent_prompt=chat_prompt)
    
    return agent_executor, query_logger


def get_result(query: str, agent_executor: object, query_logger: SQLQueryLogger) -> tuple:
    """
    Executes the agent with the given query, then extracts the SQL query generated from the logger. 
    Returns a tuple of (agent_output, sql_query).
    """
    # Clear previous intermediate steps
    query_logger.intermediate_steps.clear()

    # Invoke the agent with the provided query
    result = agent_executor.invoke({"input": query})
    
    # Look through logged events to capture the SQL query
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