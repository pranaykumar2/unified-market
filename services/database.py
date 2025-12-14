"""
Unified Database Service
Handles SQLite storage for all modules, replacing JSON history files.
"""
import sqlite3
import logging
from typing import Set, List, Optional
from datetime import datetime
import os
from pathlib import Path

from config.settings import settings
from config.logger_config import setup_logger

logger = setup_logger("Database", settings.LOG_LEVEL)

class UnifiedDatabase:
    """Unified SQLite database for all modules."""
    
    def __init__(self, db_file: str = None):
        self.db_file = db_file or settings.DATABASE_FILE
        self._ensure_db_dir()
        self._init_tables()
    
    def _ensure_db_dir(self):
        """Ensure database directory exists."""
        db_path = Path(self.db_file)
        db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        """Get a configured database connection."""
        conn = sqlite3.connect(
            self.db_file, 
            timeout=10.0, # Wait up to 10s for locks
            check_same_thread=False
        )
        # 100x Optimization: WAL Mode for concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        """Initialize all tables."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # --- Table: Notifications (Market Insights) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    insight_id TEXT UNIQUE NOT NULL,
                    stock_name TEXT NOT NULL,
                    label TEXT,
                    notification TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'sent'
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notify_id ON notifications(insight_id)")

            # --- Table: Capital Market News (New) ---
            # Replaces JSON history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS capital_market_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    news_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    url TEXT,
                    timestamp TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_id ON capital_market_news(news_id)")

            conn.commit()
            conn.close()
            logger.debug(f"✅ Database ready: {self.db_file}")
            
        except Exception as e:
            logger.error(f"❌ Database init failed: {e}")
            raise

    # ================= CAPITAL MARKET METHODS =================
    
    def is_news_sent(self, news_id: str) -> bool:
        """Check if capital market news has already been sent."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM capital_market_news WHERE news_id = ?", (news_id,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"Error checking news ID {news_id}: {e}")
            return False

    def add_sent_news(self, news_id: str, title: str, url: str, timestamp: str) -> bool:
        """Mark capital market news as sent."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO capital_market_news (news_id, title, url, timestamp) VALUES (?, ?, ?, ?)",
                (news_id, title, url, timestamp)
            )
            conn.commit()
            conn.close()
            # logger.debug(f"Saved news ID: {news_id}")
            return True
        except sqlite3.IntegrityError:
            # Already exists
            return False
        except Exception as e:
            logger.error(f"Error saving news ID {news_id}: {e}")
            return False

    # ================= MARKET INSIGHTS METHODS =================
    
    def get_all_insight_ids(self) -> Set[str]:
        """Get all sent insight IDs."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT insight_id FROM notifications")
            rows = cursor.fetchall()
            conn.close()
            return {row['insight_id'] for row in rows}
        except Exception as e:
            logger.error(f"Error fetching insight IDs: {e}")
            return set()

    def add_notification(self, insight_id: str, stock_name: str, label: str, notification: str) -> bool:
        """Add sent notification."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO notifications (insight_id, stock_name, label, notification) VALUES (?, ?, ?, ?)",
                (insight_id, stock_name, label, notification)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            logger.error(f"Error saving notification {insight_id}: {e}")
            return False
