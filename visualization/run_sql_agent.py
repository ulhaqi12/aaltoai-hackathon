import os
import agent_tools
from langchain.agents import AgentExecutor
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from sqlalchemy import create_engine

from config import (
    openai_key,
    llm_model_id,
    llm_temperature,
    agent_max_execution_time,
    agent_max_iterations,
    database_url
)


def load_sql_database() -> SQLDatabase:
    engine = create_engine(database_url)
    return SQLDatabase(engine=engine)



def load_llm() -> ChatOpenAI:
    """
    Load the OpenAI model using the key and model_id specified in config.
    """
    os.environ["OPENAI_API_KEY"] = openai_key
    return ChatOpenAI(model=llm_model_id, temperature=llm_temperature)


def load_sql_agent(db: SQLDatabase, llm: ChatOpenAI) -> AgentExecutor:
    """
    Create the LangChain SQL AgentExecutor with custom tools for visualization.
    """
    extra_tools = [
        agent_tools.output_bar_plot,
        agent_tools.output_time_series_plot,
        agent_tools.output_table
    ]
    return create_sql_agent(
        llm,
        db=db,
        agent_type="openai-tools",
        max_iterations=agent_max_iterations,
        max_execution_time=agent_max_execution_time,
        extra_tools=extra_tools,
        verbose=True
    )


if __name__ == '__main__':
    # Connect to DB
    db = load_sql_database()

    # Load LLM
    llm = load_llm()

    # Build agent
    sql_agent = load_sql_agent(db, llm)

    # Test queries
    queries = [
        "Show total sales by country.",
        "Which customers placed the most orders?",
        "Display top 5 products by revenue in a bar plot.",
        "Show monthly order counts in 1997 as a time series chart."
    ]


    for query in queries:
        print(f"\n🔍 {query}")
        response = sql_agent.invoke({"input": query})["output"]
        print(f"✅ Response: {response}")
