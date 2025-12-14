"""
News tracker module for managing sent news history.
Refactored for Unified News Bot.
"""
import json
from pathlib import Path
from typing import Set, List, Dict
from datetime import datetime, timedelta
from config.settings import settings
from config.logger_config import setup_logger
from .scraper import NewsArticle
from services.database import UnifiedDatabase

logger = setup_logger("CapitalMarketTracker", settings.LOG_LEVEL)

class NewsTracker:
    """Tracks sent news to avoid duplicates."""
    
    def __init__(self, history_file: str = None):
        self.history_file = history_file or settings.NEWS_HISTORY_FILE
        self.sent_news_ids: Set[str] = set()
        self.news_history: List[Dict] = []
        self._ensure_data_dir()
        self.load_history()
    
    def _ensure_data_dir(self):
        """Ensure the directory for history file exists."""
        try:
            path = Path(self.history_file)
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating data directory: {e}")

    def load_history(self):
        """No-op for database compatibility."""
        pass
    def __init__(self):
        self.db = UnifiedDatabase()
        
    def is_sent(self, news_id: str) -> bool:
        """Check if news ID has already been sent."""
        return self.db.is_news_sent(news_id)

    def mark_as_sent(self, article: NewsArticle):
        """Mark article as sent in database."""
        success = self.db.add_sent_news(
            news_id=article.news_id,
            title=article.title,
            url=article.url,
            timestamp=article.timestamp
        )
        if success:
            logger.debug(f"Marked as sent: {article.news_id}")

    def filter_new_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filter out articles that have already been sent."""
        new_articles = []
        for article in articles:
            if not self.is_sent(article.news_id):
                new_articles.append(article)
        
        if len(articles) != len(new_articles):
            logger.info(f"Filtered {len(articles)} articles -> {len(new_articles)} new articles")
        return new_articles
