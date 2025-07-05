from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
import asyncio
from datetime import datetime
import gradio as gr
import os
from confluence_config import get_predefined_pages
import sqlite3

# https://platform.openai.com/traces om naar de trace te gaan
# Load environment variables (make sure your .env has OPENAI_API_KEY)
load_dotenv(override=True)

# Import tools from the separate agent-tools module
from agent_tools import (

    kennisbank_opslaan,
    kennisbank_zoeken,
    haal_confluence_pagina_op,
    confluence_pagina_opslaan_en_indexeren,
    confluence_zoeken_in_db
)

# Wrap the function as a tool
confluence_zoeken_in_db_tool = function_tool(confluence_zoeken_in_db)

# Add import for SQLiteMemory
from sqlite_memory import SQLiteMemory

# Use absolute path for persistent memory
db_path = os.path.join(os.path.dirname(__file__), "agent_memory.db")
memory = SQLiteMemory(db_path)

# Create a tool instance for the specific Confluence page
# confluence_api_101_tool = haal_confluence_pagina_op("API+101+Understanding+APIs+and+API+Management")

# Create the first agent (pro-regulation)
agent_researcher = Agent(
    name="Researcher",
    #instructions="You are a diligent and objective researcher with expertise in gathering, analyzing, and synthesizing information from credible sources. you will make frequent use of the intenet search tool to verify your answers When the user asks a question, you should use the tools provided to you to find the answer. Your task is to provide well-researched, balanced, and evidence-based insights on complex topics. Focus on presenting relevant facts, recent studies, and multiple perspectives without taking a personal stance.",
    instructions=f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    IMPORTANT: You must ALWAYS first search the preloaded Confluence files (from the config) for context and information to answer the user's question. Only if you cannot find sufficient information there, you may use other tools (such as internet search or code execution).
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}""",
    model="gpt-4o-mini",
    tools=[
  
        kennisbank_opslaan,
        kennisbank_zoeken,
        haal_confluence_pagina_op,
        confluence_pagina_opslaan_en_indexeren,
        confluence_zoeken_in_db_tool  # Use the wrapped tool here
    ]
)

def run_agent_sync(agent, message):
    """Synchronous wrapper for Runner.run()"""
    return asyncio.run(Runner.run(agent, message))

def chat(message, history):
    # Store user message
    memory.add_message("user", message)
    # Retrieve last 10 messages for context
    history_messages = memory.get_history(limit=10)
    # Format history as a string
    history_str = "\n".join([f"{role}: {msg}" for role, msg in history_messages])
    # Prepend history to the user message
    contextual_message = f"Conversation history:\n{history_str}\nUser: {message}"
    with trace("personal assistant"):
        result = run_agent_sync(agent_researcher, contextual_message)
    # Store agent response
    memory.add_message("agent", result.final_output)
    return result.final_output

# Helper to store knowledge directly in the kennisbank table
def store_knowledge_direct(subject, content):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO kennis (onderwerp, inhoud) VALUES (?, ?)", (subject, content))
    conn.commit()
    conn.close()
    print(f"[Direct DB insert] Kennis opgeslagen onder onderwerp: {subject}")

def auto_prompt_confluence_pages():
    pages = get_predefined_pages()
    for page in pages:
        page_id = page["page_id"]
        prompt = f"show confluence {page_id}"
        print(f"[Auto-prompt] {prompt}")
        try:
            result = run_agent_sync(agent_researcher, prompt)
            print(f"[Loaded] {page['title']} (ID: {page_id})\n{result}\n")
            # Store in knowledge base if result is not empty
            if result and hasattr(result, 'final_output') and result.final_output:
                store_knowledge_direct(page["title"], result.final_output)
                print(f"[Stored in knowledge base] {page['title']}")
        except Exception as e:
            print(f"[Error loading page {page_id}]: {e}")

def main():
    prompt = input("Enter your question for the agent: ")
    memory.add_message("user", prompt)
    history_messages = memory.get_history(limit=10)
    history_str = "\n".join([f"{role}: {msg}" for role, msg in history_messages])
    contextual_prompt = f"Conversation history:\n{history_str}\nUser: {prompt}"
    result = run_agent_sync(agent_researcher, contextual_prompt)
    print(result)
    memory.add_message("agent", result)
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    auto_prompt_confluence_pages()
    # Uncomment the next line to use the CLI
    # main()
    with gr.Blocks() as demo:
        gr.Markdown("# PostNL API KnowledgeBase")
        gr.ChatInterface(chat, type="messages")
    demo.launch()
    