import sqlite3
from datetime import datetime
import os
import shutil
import hashlib

class SQLiteMemory:
    def __init__(self, db_path="agent_memory.db"):
        self.db_path = db_path
        self.create_table()
        # Create backup directory
        self.backup_dir = os.path.join(os.path.dirname(self.db_path), "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            # Enable foreign keys and WAL mode for better data integrity
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    role TEXT,
                    message TEXT
                )
            """)
            # Create a table for user facts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # Create a table for Confluence pages with better indexing
            conn.execute("""
                CREATE TABLE IF NOT EXISTS confluence_pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id TEXT UNIQUE,
                    title TEXT,
                    content TEXT,
                    content_hash TEXT,
                    timestamp TEXT,
                    last_accessed TEXT
                )
            """)
            # Create indexes for better search performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_confluence_page_id ON confluence_pages(page_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_confluence_title ON confluence_pages(title)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_confluence_timestamp ON confluence_pages(timestamp)")

    def add_message(self, role, message):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memory (timestamp, role, message) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), role, message)
            )

    def get_history(self, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, message FROM memory ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()[::-1]  # Return in chronological order

    def clear(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memory") 
            conn.execute("DELETE FROM facts")

    def set_fact(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "REPLACE INTO facts (key, value) VALUES (?, ?)",
                (key, value)
            )

    def get_fact(self, key):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM facts WHERE key = ?",
                (key,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def get_all_facts(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM facts")
            return dict(cursor.fetchall())

    def add_confluence_page(self, page_id, title, content):
        """Add a Confluence page with duplicate prevention and content hashing."""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        current_time = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if page already exists
            cursor = conn.cursor()
            cursor.execute("SELECT content_hash FROM confluence_pages WHERE page_id = ?", (page_id,))
            existing = cursor.fetchone()
            
            if existing:
                if existing[0] == content_hash:
                    # Content hasn't changed, just update last_accessed
                    conn.execute(
                        "UPDATE confluence_pages SET last_accessed = ? WHERE page_id = ?",
                        (current_time, page_id)
                    )
                    return f"Page '{title}' already exists with same content. Updated access time."
                else:
                    # Content has changed, update it
                    conn.execute(
                        "UPDATE confluence_pages SET title = ?, content = ?, content_hash = ?, timestamp = ?, last_accessed = ? WHERE page_id = ?",
                        (title, content, content_hash, current_time, current_time, page_id)
                    )
                    return f"Page '{title}' updated with new content."
            else:
                # New page
                conn.execute(
                    "INSERT INTO confluence_pages (page_id, title, content, content_hash, timestamp, last_accessed) VALUES (?, ?, ?, ?, ?, ?)",
                    (page_id, title, content, content_hash, current_time, current_time)
                )
                return f"New page '{title}' added successfully."

    def search_confluence_pages(self, query, limit=5):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT page_id, title, content FROM confluence_pages WHERE title LIKE ? OR content LIKE ? ORDER BY last_accessed DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit)
            )
            return cursor.fetchall()

    def get_confluence_page_by_id(self, page_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT page_id, title, content FROM confluence_pages WHERE page_id = ?",
                (page_id,)
            )
            result = cursor.fetchone()
            if result:
                # Update last_accessed time
                conn.execute(
                    "UPDATE confluence_pages SET last_accessed = ? WHERE page_id = ?",
                    (datetime.now().isoformat(), page_id)
                )
            return result

    def get_all_confluence_pages(self):
        """Get all stored Confluence pages with metadata."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT page_id, title, timestamp, last_accessed FROM confluence_pages ORDER BY last_accessed DESC"
            )
            return cursor.fetchall()

    def backup_database(self, backup_name=None):
        """Create a backup of the database."""
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        # Create backup
        shutil.copy2(self.db_path, backup_path)
        
        # Also backup WAL and SHM files if they exist
        wal_path = self.db_path + "-wal"
        shm_path = self.db_path + "-shm"
        
        if os.path.exists(wal_path):
            shutil.copy2(wal_path, backup_path + "-wal")
        if os.path.exists(shm_path):
            shutil.copy2(shm_path, backup_path + "-shm")
            
        return f"Database backed up to: {backup_path}"

    def restore_database(self, backup_path):
        """Restore database from backup."""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Close any existing connections
        import gc
        gc.collect()
        
        # Restore main database
        shutil.copy2(backup_path, self.db_path)
        
        # Restore WAL and SHM files if they exist
        wal_backup = backup_path + "-wal"
        shm_backup = backup_path + "-shm"
        
        if os.path.exists(wal_backup):
            shutil.copy2(wal_backup, self.db_path + "-wal")
        if os.path.exists(shm_backup):
            shutil.copy2(shm_backup, self.db_path + "-shm")
            
        return f"Database restored from: {backup_path}"

    def get_database_stats(self):
        """Get statistics about the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count records in each table
            cursor.execute("SELECT COUNT(*) FROM memory")
            memory_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM facts")
            facts_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM confluence_pages")
            confluence_count = cursor.fetchone()[0]
            
            # Get database size
            db_size = os.path.getsize(self.db_path)
            
            return {
                "memory_records": memory_count,
                "facts_count": facts_count,
                "confluence_pages": confluence_count,
                "database_size_mb": round(db_size / (1024 * 1024), 2)
            } 