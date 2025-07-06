from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool
import asyncio
from datetime import datetime
import gradio as gr
import os

# https://platform.openai.com/traces om naar de trace te gaan
# Load environment variables (make sure your .env has OPENAI_API_KEY)
load_dotenv(override=True)

# Import tools from the separate agent-tools module
from agent_tools import (

    kennisbank_opslaan,
    kennisbank_zoeken,
    haal_confluence_pagina_op    # Just the function reference
)

# Add import for SQLiteMemory
from sqlite_memory import SQLiteMemory

# Import confluence configuration
from confluence_config import get_predefined_pages

# Use absolute path for persistent memory
db_path = os.path.join(os.path.dirname(__file__), "agent_memory.db")
memory = SQLiteMemory(db_path)

def get_confluence_page_content(page_id: str) -> dict:
    """
    Retrieve content from a Confluence page by page_id.
    This is a regular function (not a tool) that can be called directly.
    """
    from atlassian import Confluence
    
    url = os.environ.get("CONFLUENCE_BASE_URL")
    email = os.environ.get("CONFLUENCE_EMAIL")
    api_token = os.environ.get("CONFLUENCE_API_TOKEN")
    
    if not url or not email or not api_token:
        return {"status": "fout", "bericht": "Ontbrekende Confluence API credentials in .env"}
    
    try:
        confluence = Confluence(
            url=url,
            username=email,
            password=api_token
        )
        pagina = confluence.get_page_by_id(page_id, expand="body.storage")
        if pagina and "body" in pagina and "storage" in pagina["body"]:
            inhoud = pagina["body"]["storage"]["value"]
            titel = pagina.get("title", f"Confluence pagina {page_id}")
            # Automatisch opslaan in de database
            memory.add_confluence_page(page_id, titel, inhoud)
            return {"status": "succes", "inhoud": inhoud, "titel": titel}
        else:
            return {"status": "fout", "bericht": f"Pagina met ID '{page_id}' niet gevonden."}
    except Exception as e:
        return {"status": "fout", "bericht": f"Fout bij ophalen Confluence-pagina: {str(e)}"}

def load_all_confluence_pages():
    """
    Load all Confluence pages from confluence_config.py by page_id and store their content
    in confluence_content.txt. If the file already exists, it will be overwritten.
    """
    try:
        # Get predefined pages from configuration
        predefined_pages = get_predefined_pages()
        
        if not predefined_pages:
            print("No predefined Confluence pages found in configuration.")
            return
        
        # Initialize content string
        all_content = ""
        
        print(f"Loading {len(predefined_pages)} Confluence pages...")
        
        # Process each page
        for i, page in enumerate(predefined_pages, 1):
            page_id = page["page_id"]
            title = page["title"]
            
            print(f"Loading page {i}/{len(predefined_pages)}: {title} (ID: {page_id})")
            
            # Get page content using the regular function
            result = get_confluence_page_content(page_id)
            
            if result.get("status") == "succes":
                content = result.get("inhoud", "")
                page_title = result.get("titel", title)
                
                # Add page content to the overall content
                page_section = "\n" + "="*80 + "\n"
                page_section += f"PAGE: {page_title}\n"
                page_section += f"PAGE ID: {page_id}\n"
                page_section += f"ORIGINAL TITLE: {title}\n"
                page_section += "="*80 + "\n\n"
                page_section += content
                page_section += "\n\n" + "-"*80 + "\n"
                
                all_content += page_section
                print(f"✅ Successfully loaded: {page_title}")
            else:
                error_msg = result.get("bericht", "Unknown error")
                print(f"❌ Failed to load page {page_id}: {error_msg}")
                
                # Add error information to content
                error_section = "\n" + "="*80 + "\n"
                error_section += "ERROR LOADING PAGE\n"
                error_section += f"PAGE ID: {page_id}\n"
                error_section += f"ORIGINAL TITLE: {title}\n"
                error_section += f"ERROR: {error_msg}\n"
                error_section += "="*80 + "\n\n"
                
                all_content += error_section
        
        # Write content to file
        output_file = os.path.join(os.path.dirname(__file__), "confluence_content.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("CONFLUENCE PAGES CONTENT\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total pages in config: {len(predefined_pages)}\n")
            f.write("="*80 + "\n\n")
            f.write(all_content)
        
        print(f"✅ All Confluence pages content saved to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error loading Confluence pages: {str(e)}")
        return None

def load_confluence_content_to_memory():
    """
    Load the confluence_content.txt file into the agent's memory so it has access to all
    the confluence content before starting conversations.
    """
    confluence_file = os.path.join(os.path.dirname(__file__), "confluence_content.txt")
    
    if not os.path.exists(confluence_file):
        print("❌ confluence_content.txt not found. Loading Confluence pages first...")
        load_all_confluence_pages()
    
    try:
        with open(confluence_file, 'r', encoding='utf-8') as f:
            confluence_content = f.read()
        
        # Store the confluence content in memory with a special key
        memory.add_message("system", f"CONFLUENCE KNOWLEDGE BASE:\n{confluence_content}")
        print(f"✅ Loaded confluence content into agent memory ({len(confluence_content)} characters)")
        return True
        
    except Exception as e:
        print(f"❌ Error loading confluence content to memory: {str(e)}")
        return False

def initialize_agent_with_confluence():
    """
    Initialize the agent with confluence content loaded into memory.
    This ensures the agent has access to all confluence knowledge before starting.
    """
    print("🔄 Initializing agent with Confluence knowledge...")
    
    # First, ensure confluence content is available
    if not load_confluence_content_to_memory():
        print("⚠️ Warning: Failed to load confluence content to memory")
    
    print("✅ Agent initialized with Confluence knowledge")

# Create a tool instance for the specific Confluence page
# confluence_api_101_tool = haal_confluence_pagina_op("API+101+Understanding+APIs+and+API+Management")

# Initialize agent with confluence knowledge
initialize_agent_with_confluence()

# Create the first agent (pro-regulation)
agent_researcher = Agent(
    name="Researcher",
    #instructions="You are a diligent and objective researcher with expertise in gathering, analyzing, and synthesizing information from credible sources. you will make frequent use of the intenet search tool to verify your answers When the user asks a question, you should use the tools provided to you to find the answer. Your task is to provide well-researched, balanced, and evidence-based insights on complex topics. Focus on presenting relevant facts, recent studies, and multiple perspectives without taking a personal stance.",
    instructions=f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    You have access to a comprehensive knowledge base of Confluence pages that has been loaded into your memory.
    When answering questions, you can reference this knowledge base to provide accurate and detailed information.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}""",
    model="gpt-4o-mini",
    tools=[

        kennisbank_opslaan,
        kennisbank_zoeken,
        haal_confluence_pagina_op    # Just the function reference
    ]
)

def run_agent_sync(agent, message):
    """Synchronous wrapper for Runner.run()"""
    return asyncio.run(Runner.run(agent, message))

def chat(message, history):
    # Store user message
    memory.add_message("user", message)
    
    # Get confluence knowledge from memory - search ALL messages, not just last 10
    confluence_knowledge = ""
    all_messages = memory.get_history(limit=1000)  # Get all messages to find confluence knowledge
    for role, msg in all_messages:
        if role == "system" and "CONFLUENCE KNOWLEDGE BASE:" in msg:
            confluence_knowledge = msg
            break
    
    # Retrieve last 10 messages for conversation context (excluding system messages)
    history_messages = memory.get_history(limit=10)
    # Format history as a string, excluding system messages
    conversation_history = []
    for role, msg in history_messages:
        if role != "system":  # Exclude system messages from conversation history
            conversation_history.append(f"{role}: {msg}")
    history_str = "\n".join(conversation_history)
    
    # Prepend confluence knowledge and history to the user message
    contextual_message = f"{confluence_knowledge}\n\nConversation history:\n{history_str}\nUser: {message}"
    with trace("personal assistant"):
        result = run_agent_sync(agent_researcher, contextual_message)
    # Store agent response
    memory.add_message("agent", result.final_output)
    return result.final_output

def main():
    # Initialize agent with confluence knowledge
    initialize_agent_with_confluence()
    
    prompt = input("Enter your question for the agent: ")
    memory.add_message("user", prompt)
    
    # Get confluence knowledge from memory - search ALL messages, not just last 10
    confluence_knowledge = ""
    all_messages = memory.get_history(limit=1000)  # Get all messages to find confluence knowledge
    for role, msg in all_messages:
        if role == "system" and "CONFLUENCE KNOWLEDGE BASE:" in msg:
            confluence_knowledge = msg
            break
    
    # Retrieve last 10 messages for conversation context (excluding system messages)
    history_messages = memory.get_history(limit=10)
    # Format history as a string, excluding system messages
    conversation_history = []
    for role, msg in history_messages:
        if role != "system":  # Exclude system messages from conversation history
            conversation_history.append(f"{role}: {msg}")
    history_str = "\n".join(conversation_history)
    
    contextual_prompt = f"{confluence_knowledge}\n\nConversation history:\n{history_str}\nUser: {prompt}"
    result = run_agent_sync(agent_researcher, contextual_prompt)
    print(result)
    memory.add_message("agent", result)
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def test_load_confluence_pages():
    """Test function to load all Confluence pages without running the full application."""
    print("Testing Confluence pages loading...")
    result = load_all_confluence_pages()
    if result:
        print(f"✅ Test completed successfully. Content saved to: {result}")
    else:
        print("❌ Test failed.")

if __name__ == "__main__":
    # Uncomment the next line to use the CLI
    # main()
    
    # Uncomment the next line to test Confluence pages loading
    # test_load_confluence_pages()
    
    gr.ChatInterface(chat, type="messages").launch()
    