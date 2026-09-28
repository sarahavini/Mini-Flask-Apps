import os
import sqlite3
from crew_ai_bot import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
load_dotenv()

#configure ketys
API_KEY = os.getenv("NVIDIA_API_KEY")
# Nemotron 3 Ultra - frontier reasoning and agentic workflows
nvidia_llm = ChatNVIDIA(model="nvidia/nemotron-3-ultra-550b-a55b")

@tool("Execute SQL Query")
def execute_sql(query:str) -> str:
    """Executes query on db and returns result"""
    print(f"tool active! Executing query: {query}")
    try:
        conn = sqllite3.connect('myDB.db')
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return str(result) if result else "No results found"
    except Exception as e:
        return f"SQL Error: {e}"

#AI AGENTS
sql_developer = Agent(
    role='Senior SQL Developer',
    goal='Write and execute exact SQL queries to fetch requested data.',
    backstory="You are a master database engineer. The database is SQlite. There are two tables. The first table is 'ToolsLibrary' with columns 'id', 'tool_name', 'tool_description', tool_condition', 'tool_available', 'owner_id', 'checked_out_to'" \
    "The second table is 'Users' with columns 'id', 'user_name', 'password_hash', 'email', 'tools', 'checked_out_tools'.",
    verbose=True,
    tools=[execute_sql],
    llm=nvidia_llm
)

#agent 2
data_analyst = Agent(
    role = 'IT Data Analyst',
    goal = 'translate raw database rows into a profesional, easy to read report.',
    backstory = 'You take messy database outputs and write clean summaries of the information.',
    verbose=True,
    llm=nvidia_llm
)

#define tasks
user_question = None

sql_task = Task(
    description=f'Based on this question: "{user_question}", write and execute a SQL query using your tool to get the data.',
    expected_output = 'Raw data rows returned from the database.',
    agent = sql_developer
)

report_task = Task(
    description = 'Taske the raw data from the SQL developer and write a short description of the findings',
    expected_output='A clear report summarizing in one line the findings',
    agent = data_analyst
)

#assemble the crew
sql_crew = Crew(
    agents = [sql_developer, data_analyst],
    tasks = [sql_task, report_task],
    process=Process.sequential
)

final_report = sql_crew.kickoff()