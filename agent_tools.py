from dotenv import load_dotenv
from agents import function_tool
import requests
import os
from typing import Dict, Optional, Any, List, TypedDict
import json
import asyncio
import base64
import sqlite3

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

from atlassian import Confluence
from sqlite_memory import SQLiteMemory

# Laad omgevingsvariabelen
load_dotenv(override=True)

# Helper om async functie te runnen, ook in bestaande event loop
async def _run_async_or_sync(coro):
    try:
        loop = asyncio.get_running_loop()
        return await coro
    except RuntimeError:
        return asyncio.run(coro)


# Zorg dat het pad naar de database klopt
DB_PATH = os.path.join(os.path.dirname(__file__), "agent_memory.db")
memory = SQLiteMemory(DB_PATH)

def init_kennisbank():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS kennis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            onderwerp TEXT,
            inhoud TEXT
        )
    """)
    conn.commit()
    conn.close()

init_kennisbank()

@function_tool
def kennisbank_opslaan(onderwerp: str, inhoud: str) -> str:
    """Sla kennis op in de kennisbank onder een onderwerp."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO kennis (onderwerp, inhoud) VALUES (?, ?)", (onderwerp, inhoud))
    conn.commit()
    conn.close()
    return f"Kennis opgeslagen onder onderwerp: {onderwerp}"

@function_tool
def kennisbank_zoeken(zoekterm: str) -> str:
    """Zoek naar kennis in de kennisbank op basis van een zoekterm."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT onderwerp, inhoud FROM kennis WHERE onderwerp LIKE ? OR inhoud LIKE ? LIMIT 5", (f"%{zoekterm}%", f"%{zoekterm}%"))
    resultaten = c.fetchall()
    conn.close()
    if not resultaten:
        return "Geen kennis gevonden."
    return "\n\n".join([f"Onderwerp: {r[0]}\nInhoud: {r[1]}" for r in resultaten])

@function_tool
def haal_confluence_pagina_op(page_id: str) -> dict:
    """
    Haalt de inhoud op van een Confluence-pagina op basis van page_id.
    Vereist CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL en CONFLUENCE_API_TOKEN in de .env.

    Argumenten:
        page_id (str): De ID van de Confluence-pagina die opgehaald moet worden.
            Deze parameter wordt gevuld door de gebruiker of door een andere functie die deze tool aanroept.

    Returns:
        dict: Resultaat van de API-call, met status en inhoud of foutmelding.
    """
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

@function_tool
def confluence_pagina_opslaan_en_indexeren(page_id: str, title: str, content: str) -> str:
    """Sla een opgehaalde Confluence-pagina op in de database."""
    memory.add_confluence_page(page_id, title, content)
    return f"Confluence-pagina '{title}' opgeslagen."

def confluence_zoeken_in_db(zoekterm: str) -> str:
    """Zoek in de opgeslagen Confluence-pagina's in de database."""
    resultaten = memory.search_confluence_pages(zoekterm)
    if not resultaten:
        return "Geen relevante Confluence-pagina's gevonden."
    return "\n\n".join([f"Titel: {r[1]}\nInhoud: {r[2][:500]}..." for r in resultaten])

