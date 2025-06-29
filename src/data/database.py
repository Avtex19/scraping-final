import sqlite3
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime


class Database:
    def __init__(self, db_path="scraped_data.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.logger = logging.getLogger(__name__)
        self._create_tables()

    def _create_tables(self):
        """Creates normalized schema and job/task tracking."""
        cursor = self.conn.cursor()

        # Track scraping jobs (for queueing)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_term TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
        """)

        # Products table (can support multiple sources/search_terms)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            link TEXT UNIQUE,
            image TEXT,
            availability TEXT,
            scrape_time TEXT,
            search_term TEXT,
            source TEXT,
            job_id INTEGER,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
        """)
        
        # Add source column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN source TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
        self.conn.commit()

    def queue_job(self, search_term: str) -> int:
        """Insert a scraping job into queue and return job_id."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO jobs (search_term) VALUES (?)", (search_term,))
        self.conn.commit()
        job_id = cursor.lastrowid
        self.logger.info(f"Queued job {job_id} for term: '{search_term}'")
        return job_id

    def mark_job_complete(self, job_id: int):
        """Mark job as completed with timestamp."""
        now = datetime.utcnow().isoformat()
        self.conn.execute(
            "UPDATE jobs SET status = 'completed', completed_at = ? WHERE job_id = ?",
            (now, job_id)
        )
        self.conn.commit()
        self.logger.info(f"Job {job_id} marked as completed at {now}")

    def insert_products(self, products: List[Dict[str, Any]], job_id: Optional[int] = None):
        """Insert list of product dicts into DB."""
        query = """
        INSERT OR IGNORE INTO products (
            name, price, link, image, availability, scrape_time, search_term, source, job_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        to_insert = [
            (
                p.get('name'),
                self._parse_price(p.get('price')),
                p.get('link'),
                p.get('image'),
                p.get('availability'),
                p.get('scrape_time'),
                p.get('search_term'),
                p.get('source'),
                job_id
            )
            for p in products
        ]
        self.conn.executemany(query, to_insert)
        self.conn.commit()
        self.logger.info(f"Inserted {len(to_insert)} products (Job ID: {job_id})")

    def _parse_price(self, price_str: Optional[Any]) -> Optional[float]:
        """Convert '$1,299.00' → 1299.00 or pass through float values."""
        if price_str is None:
            return None
        if isinstance(price_str, (int, float)):
            return float(price_str)
        try:
            return float(price_str.replace('$', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            return None

    def get_pending_jobs(self) -> List[sqlite3.Row]:
        """Retrieve jobs not yet completed."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE status = 'pending'")
        return cursor.fetchall()

    def get_products(self, source: Optional[str] = None, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve products from database, optionally filtered by source or search_term."""
        cursor = self.conn.cursor()
        query = "SELECT * FROM products"
        params = []
        
        if search_term:
            query += " WHERE search_term = ?"
            params.append(search_term)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert sqlite3.Row objects to dictionaries
        return [dict(row) for row in rows]

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
