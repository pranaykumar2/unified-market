"""
Capital Market Module
Handles scraping, tracking, and rendering of news from Capital Market.
"""
from .scraper import NewsScraper, NewsArticle
from .tracker import NewsTracker
from .renderer import EnhancedNewsImageGenerator
