# Developer Guide: AI Agent with Confluence Integration

## Overview

This application is an AI-powered assistant that integrates with Confluence to provide intelligent responses based on your organization's knowledge base. The system uses OpenAI's GPT models, maintains conversation memory, and can access both local knowledge storage and Confluence pages.

## Architecture

### Core Components

1. **Main Application** (`app.py`)
   - Gradio web interface for user interaction
   - Agent initialization and conversation management
   - Confluence content loading and memory management

2. **Agent Tools** (`agent_tools.py`)
   - Knowledge bank operations (save/search)
   - Confluence page retrieval
   - Database interaction utilities

3. **Memory Management** (`sqlite_memory.py`)
   - SQLite-based conversation memory
   - Confluence page storage and retrieval
   - Database backup and restore functionality

4. **Configuration** (`confluence_config.py`)
   - Predefined Confluence pages configuration
   - System settings and options

### Data Flow

```
User Input → Memory Context → Agent → Tools → Response → Memory Storage
                ↓
        Confluence Knowledge Base
```

## Setup Instructions

### 1. Environment Setup

Create a `.env` file in the project root with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Confluence Configuration
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your_email@domain.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
```

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For development, you might also need:
pip install jupyter notebook
```

### 3. Confluence API Token Setup

1. Go to your Atlassian account settings
2. Navigate to Security → Create and manage API tokens
3. Create a new API token
4. Copy the token to your `.env` file

## Configuration

### Confluence Pages Configuration

Edit `confluence_config.py` to add your Confluence pages:

```python
PREDEFINED_CONFLUENCE_PAGES = [
    {
        "page_id": "1234567890",
        "title": "Your Page Title",
        "description": "Description of the page content"
    },
    # Add more pages as needed
]
```

### Agent Configuration

The agent is configured in `app.py` with these key settings:

- **Model**: `gpt-4o-mini` (can be changed to other OpenAI models)
- **Instructions**: Customizable system prompt
- **Tools**: Knowledge bank and Confluence tools

## Usage

### Running the Application

```bash
# Start the Gradio web interface
python app.py
```

The application will:
1. Load predefined Confluence pages into memory
2. Initialize the AI agent with knowledge base
3. Launch a web interface at `http://localhost:7860`

### Available Functions

#### For Users:
- **Chat Interface**: Interact with the AI agent through the web UI
- **Knowledge Queries**: Ask questions about stored Confluence content
- **Conversation Memory**: The agent remembers previous interactions

#### For Developers:

**CLI Mode** (uncomment in `app.py`):
```python
if __name__ == "__main__":
    main()  # Uncomment for CLI mode
```

**Test Confluence Loading**:
```python
if __name__ == "__main__":
    test_load_confluence_pages()  # Uncomment to test
```

## Development Workflow

### Adding New Tools

1. Create the tool function in `agent_tools.py`:
```python
@function_tool
def your_new_tool(param: str) -> str:
    """Description of what your tool does."""
    # Your tool logic here
    return "Result"
```

2. Import and add to the agent in `app.py`:
```python
from agent_tools import your_new_tool

agent_researcher = Agent(
    # ... other config
    tools=[kennisbank_opslaan, kennisbank_zoeken, haal_confluence_pagina_op, your_new_tool]
)
```

### Database Management

The application uses SQLite for memory storage. Key tables:

- **memory**: Conversation history
- **facts**: User-specific facts
- **confluence_pages**: Cached Confluence content
- **kennis**: Knowledge bank entries

**Backup Database**:
```python
from sqlite_memory import SQLiteMemory
memory = SQLiteMemory("agent_memory.db")
memory.backup_database("my_backup.db")
```

**Restore Database**:
```python
memory.restore_database("backups/my_backup.db")
```

### Memory Operations

```python
# Add a message to memory
memory.add_message("user", "Hello")

# Get conversation history
history = memory.get_history(limit=10)

# Store user facts
memory.set_fact("user_preference", "prefers detailed responses")

# Add Confluence page
memory.add_confluence_page("page_id", "title", "content")
```

## Troubleshooting

### Common Issues

1. **Confluence Connection Errors**
   - Verify API credentials in `.env`
   - Check network connectivity to Atlassian
   - Ensure page IDs are correct

2. **Memory Issues**
   - Database file permissions
   - Disk space availability
   - SQLite WAL mode conflicts

3. **Agent Response Issues**
   - Check OpenAI API key validity
   - Verify model availability
   - Review tool function implementations

### Debug Mode

Enable verbose logging by modifying `confluence_config.py`:

```python
CONFLUENCE_CONFIG = {
    "verbose_logging": True,
    # ... other settings
}
```

### Performance Optimization

1. **Database Indexing**: Already implemented for confluence_pages
2. **Content Hashing**: Prevents duplicate content storage
3. **Lazy Loading**: Confluence pages loaded on demand
4. **Memory Limits**: Configurable conversation history limits

## File Structure

```
ht_include_prod/
├── app.py                 # Main application
├── agent_tools.py         # Tool implementations
├── sqlite_memory.py       # Memory management
├── confluence_config.py   # Configuration
├── requirements.txt       # Dependencies
├── agent_memory.db       # SQLite database
├── confluence_content.txt # Cached Confluence content
├── backups/              # Database backups
└── .env                  # Environment variables
```

## API Reference

### Core Classes

#### SQLiteMemory
- `add_message(role, message)`: Store conversation message
- `get_history(limit=10)`: Retrieve conversation history
- `add_confluence_page(page_id, title, content)`: Cache Confluence page
- `search_confluence_pages(query, limit=5)`: Search cached pages
- `backup_database(backup_name)`: Create database backup

#### Agent Tools
- `kennisbank_opslaan(onderwerp, inhoud)`: Save knowledge
- `kennisbank_zoeken(zoekterm)`: Search knowledge base
- `haal_confluence_pagina_op(page_id)`: Fetch Confluence page

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `CONFLUENCE_BASE_URL` | Atlassian instance URL | Yes |
| `CONFLUENCE_EMAIL` | Atlassian account email | Yes |
| `CONFLUENCE_API_TOKEN` | Atlassian API token | Yes |

## Best Practices

1. **Security**: Never commit `.env` files to version control
2. **Backups**: Regularly backup the `agent_memory.db` file
3. **Monitoring**: Check Confluence API rate limits
4. **Testing**: Use `test_load_confluence_pages()` before deployment
5. **Documentation**: Update `confluence_config.py` when adding new pages

## Deployment

### Local Development
```bash
python app.py
```

### Production Considerations
- Use environment variables for all secrets
- Implement proper logging
- Set up database backups
- Monitor API usage and costs
- Consider using a production WSGI server

## Contributing

1. Follow the existing code structure
2. Add proper error handling to new tools
3. Update documentation for new features
4. Test with various Confluence page types
5. Maintain backward compatibility

---

For additional support, check the logs in the console output or review the database contents directly using SQLite tools. 