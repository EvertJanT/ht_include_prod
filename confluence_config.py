"""
Configuratiebestand voor voorgedefinieerde Confluence pagina's die automatisch geladen worden bij opstart.
Voeg hier je gewenste Confluence pagina's toe.
"""

# Voorgedefinieerde Confluence pagina's die automatisch geladen worden bij opstart
PREDEFINED_CONFLUENCE_PAGES = [
    {
        "page_id": "4151280097",
        "title": "API 101 - Understanding APIs and API Management",
        "description": "Basis informatie over APIs en API management"
    },
    {
        "page_id": "4282548747",
        "title": "Exposing+your+API+via+API+Management",
        "description": "Basis informatie over APIs en API management"
    },    
        {
        "page_id": "4359651961",
        "title": "Incident+Management",
        "description": "Basis informatie over APIs en API management"
    },
    {
        "page_id": "4311613884",
        "title": "Exposing+your+API+via+API+Management",
        "description": "Basis informatie over APIs en API management"
    },
     {
        "page_id": "4311613884",
        "title": "Connecting+to+Internal+APIs#1.-How-can-I-get-my-API-Keys?",
        "description": "Basis informatie over APIs en API management"
    },


    # Voeg hier meer pagina's toe naar wens
    # Voorbeeld van hoe je meer pagina's kunt toevoegen:
    # {
    #     "page_id": "1234567890",
    #     "title": "Voorbeeld Pagina 2",
    #     "description": "Beschrijving van pagina 2"
    # },
    # {
    #     "page_id": "9876543210",
    #     "title": "Voorbeeld Pagina 3",
    #     "description": "Beschrijving van pagina 3"
    # },
]

# Configuratie opties
CONFLUENCE_CONFIG = {
    "auto_load_on_startup": True,  # Zet op False om automatisch laden uit te schakelen
    "check_existing_pages": True,  # Controleer of pagina's al bestaan voordat ze geladen worden
    "verbose_logging": True,       # Toon gedetailleerde logging tijdens het laden
    "max_retries": 3,             # Maximum aantal pogingen per pagina
    "retry_delay": 2,             # Wachtijd tussen pogingen in seconden
}

CONFLUENCE_PAGES_DIR = "./confluence_pages"  # Update this path as needed

def get_pages_dir():
    return CONFLUENCE_PAGES_DIR

def get_predefined_pages():
    """Haal de lijst van voorgedefinieerde pagina's op."""
    return PREDEFINED_CONFLUENCE_PAGES

def get_config():
    """Haal de configuratie op."""
    return CONFLUENCE_CONFIG

def add_predefined_page(page_id: str, title: str, description: str = ""):
    """Voeg een nieuwe voorgedefinieerde pagina toe aan de lijst."""
    new_page = {
        "page_id": page_id,
        "title": title,
        "description": description
    }
    PREDEFINED_CONFLUENCE_PAGES.append(new_page)
    print(f"✅ Pagina toegevoegd: {title} (ID: {page_id})")

def remove_predefined_page(page_id: str):
    """Verwijder een pagina uit de lijst van voorgedefinieerde pagina's."""
    global PREDEFINED_CONFLUENCE_PAGES
    original_length = len(PREDEFINED_CONFLUENCE_PAGES)
    PREDEFINED_CONFLUENCE_PAGES = [page for page in PREDEFINED_CONFLUENCE_PAGES if page["page_id"] != page_id]
    
    if len(PREDEFINED_CONFLUENCE_PAGES) < original_length:
        print(f"✅ Pagina met ID {page_id} verwijderd uit de lijst")
    else:
        print(f"❌ Pagina met ID {page_id} niet gevonden in de lijst")

def list_predefined_pages():
    """Toon alle voorgedefinieerde pagina's."""
    if not PREDEFINED_CONFLUENCE_PAGES:
        print("📝 Geen voorgedefinieerde Confluence pagina's geconfigureerd.")
        return
    
    print("📝 Voorgedefinieerde Confluence pagina's:")
    for i, page in enumerate(PREDEFINED_CONFLUENCE_PAGES, 1):
        print(f"  {i}. {page['title']}")
        print(f"     ID: {page['page_id']}")
        if page['description']:
            print(f"     Beschrijving: {page['description']}")
        print() 