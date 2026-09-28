import os
import re
import sqlite3

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "myDB.db"))

API_KEY = os.getenv("NVIDIA_API_KEY")
nvidia_llm = LLM(
    model="openai/nvidia/nemotron-3-super-120b-a12b",
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.2,
)


def _is_read_only(query: str) -> bool:
    cleaned = query.strip().rstrip(";")
    cleaned = re.sub(r"^(/\*.*?\*/|--[^\n]*\n|\s)+", "", cleaned, flags=re.DOTALL)
    first = cleaned.split(None, 1)[0].upper() if cleaned else ""
    if first not in {"SELECT", "WITH", "PRAGMA"}:
        return False
    if ";" in cleaned:
        return False
    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|VACUUM)\b",
        re.IGNORECASE,
    )
    return not forbidden.search(cleaned)


@tool("Execute SQL Query")
def execute_sql(query: str) -> str:
    """Execute a read-only SQL query against the tools database and return rows."""
    print(f"tool active! Executing query: {query}")
    if not _is_read_only(query):
        return "SQL Error: only a single read-only SELECT/WITH query is allowed."
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "No results found."
        columns = rows[0].keys()
        formatted = [dict(zip(columns, row)) for row in rows]
        return str(formatted)
    except Exception as e:
        return f"SQL Error: {e}"


SCHEMA_BACKSTORY = """
You are a master database engineer. The database is SQLite.

Table ToolsLibrary:
  id INTEGER PRIMARY KEY
  tool_name TEXT
  tool_description TEXT
  tool_condition TEXT
  tool_available INTEGER  -- 1 = available, 0 = checked out
  owner_id INTEGER        -- FK to Users.id
  checked_out_to INTEGER  -- FK to Users.id, NULL if available

Table Users:
  id INTEGER PRIMARY KEY
  user_name TEXT
  password_hash TEXT      -- NEVER select or return this column
  email TEXT
  tools TEXT
  checked_out_tools TEXT

Join rules:
  ToolsLibrary.owner_id = Users.id
  ToolsLibrary.checked_out_to = Users.id

Always write valid SQLite. Prefer JOINs over guessing names from ids.
Never SELECT password_hash.
"""

sql_developer = Agent(
    role="Senior SQL Developer",
    goal="Write and execute exact SQL queries to fetch the requested data.",
    backstory=SCHEMA_BACKSTORY,
    verbose=True,
    tools=[execute_sql],
    llm=nvidia_llm,
    allow_delegation=False,
)

data_analyst = Agent(
    role="IT Data Analyst",
    goal="Translate raw database rows into a professional, easy-to-read answer.",
    backstory=(
        "You take messy database outputs and write clean summaries. "
        "Answer the user's question directly. If there are no rows, say so. "
        "Never invent tools or users that were not in the query result."
    ),
    verbose=True,
    llm=nvidia_llm,
    allow_delegation=False,
)

sql_task = Task(
    description=(
        "Based on this user question: '{user_question}', write and execute "
        "one SQLite SELECT using the Execute SQL Query tool. "
        "Do not invent data. If the question is not about tools or users, "
        "say you can only answer questions about the inventory database."
    ),
    expected_output="Raw data rows returned from the database, or a short note that nothing matched.",
    agent=sql_developer,
)

report_task = Task(
    description=(
        "Take the raw data from the SQL developer and answer the original "
        "question: '{user_question}'. Write a short, clear response a person "
        "could read in a chat window. Use bullet points if there are several items."
    ),
    expected_output="A clear chat-style answer summarizing the findings.",
    agent=data_analyst,
    context=[sql_task],
)

sql_crew = Crew(
    agents=[sql_developer, data_analyst],
    tasks=[sql_task, report_task],
    process=Process.sequential,
    verbose=True,
)


def ask_database(user_question: str) -> str:
    question = (user_question or "").strip()
    if not question:
        return "Please ask a question about tools or users."
    if not API_KEY:
        return "Server is missing NVIDIA_API_KEY. Add it to your .env file."
    if not os.path.exists(DB_PATH):
        return f"Database file not found at {DB_PATH}."

    result = sql_crew.kickoff(inputs={"user_question": question})
    return str(result)