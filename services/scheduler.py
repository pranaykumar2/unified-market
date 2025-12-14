"""
Unified Scheduler Service
Orchestrates schedules using APScheduler for robust, non-blocking execution.
"""
import asyncio
import logging
from datetime import datetime, time as dt_time, timedelta
from typing import Optional
from telegram import Bot
import pytz

# APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config.settings import settings
from config.logger_config import setup_logger

# Rich for clean panel displays
from rich.console import Console
from rich.panel import Panel

# Import Module Schedulers/Handlers
from modules.global_markets.bot_handler import send_global_markets_update
# For Market Insights, we use the classes directly as per unified-market design
from modules.market_insights.api_client import TrendlyneAPIClient
from modules.market_insights.data_processor import DataProcessor
# from modules.market_insights.database import NotificationDatabase # DEPRECATED
from services.database import UnifiedDatabase
from modules.market_insights.telegram_notifier import TelegramNotifier
# Capital Market
from modules.capital_market.scraper import NewsScraper
from modules.capital_market.tracker import NewsTracker
from modules.capital_market.bot_handler import CapitalMarketBotHandler

# Shared utilities
from cache_manager import CacheManager # We will need to copy/create this if not standard

logger = setup_logger("Scheduler", settings.LOG_LEVEL)
console = Console()
IST = pytz.timezone('Asia/Kolkata')

class UnifiedScheduler:
    """
    Central scheduler using APScheduler.
    Replaces custom while loops with a robust job queue.
    """
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.configure(timezone=IST)
        
        # --- Shared Services ---
        self.cache_manager = CacheManager() # Initialize here
        self.database = UnifiedDatabase()
        
        # --- Module: Global Markets ---
        # Logic handled in function send_global_markets_update
        
        # --- Module: Market Insights ---
        self.mi_api_client = TrendlyneAPIClient()
        self.mi_data_processor = DataProcessor()
        self.mi_notifier = TelegramNotifier(bot, self.database)
        self.mi_interval = settings.MARKET_INSIGHTS_INTERVAL_MINUTES
        
        # --- Module: Capital Market ---
        self.cm_scraper = NewsScraper()
        self.cm_tracker = NewsTracker()
        self.cm_handler = CapitalMarketBotHandler(bot)
        self.cm_interval = settings.CAPITAL_MARKET_INTERVAL_MINUTES

    # ================= JOB FUNCTIONS =================
    
    async def job_market_insights(self):
        """Job: Check and notify market insights."""
        try:
            api_response = await self.mi_api_client.fetch_market_insights()
            if not api_response: 
                return
            
            all_insights = self.mi_data_processor.extract_insights(api_response)
            if not all_insights: 
                return
            
            seen_ids = self.database.get_all_insight_ids()
            new_insights = self.mi_data_processor.filter_new_insights(all_insights, seen_ids)
            
            if not new_insights:
                return
            
            # Display compact panel
            panel = Panel(
                f"Queued:         {len(new_insights)} New Insights\n"
                f"Processing:     Sending",
                title="Source: Market Insights (Trendlyne)",
                border_style="magenta",
                expand=False
            )
            console.print(panel)
            
            await self.mi_notifier.send_batch_notifications(new_insights)
            
            # Save to DB
            for insight in new_insights:
                self.database.add_notification(
                    insight_id=insight.insight_id,
                    stock_name=insight.stock_name,
                    label=insight.label,
                    notification=insight.notification
                )
        except Exception as e:
            logger.error(f"❌ Error in Market Insights job: {e}")

    async def job_capital_market(self):
        """Job: Check and notify capital market news."""
        try:
            articles = await self.cm_scraper.scrape()
            
            if not articles:
                return
            
            new_articles = self.cm_tracker.filter_new_articles(articles)
            valid_articles = [a for a in new_articles if a.description]
            
            if not valid_articles:
                return
            
            if len(valid_articles) > settings.MAX_NEWS_PER_RUN:
                valid_articles = valid_articles[:settings.MAX_NEWS_PER_RUN]
            
            # Display compact panel
            panel = Panel(
                f"Queued:         {len(valid_articles)} New Articles\n"
                f"Processing:     Sending",
                title="Source: Capital Market News",
                border_style="blue",
                expand=False
            )
            console.print(panel)
            
            for i, article in enumerate(valid_articles, 1):
                logger.info(f"{article.title[:60]}...")
                success = await self.cm_handler.send_news(article)
                
                if success:
                    self.cm_tracker.mark_as_sent(article)
                    await asyncio.sleep(2)
                    
        except Exception as e:
            logger.error(f"❌ Error in Capital Market job: {e}")

    async def job_global_markets(self):
        """Job: Daily Global Markets Update."""
        try:
            # Display compact panel
            panel = Panel(
                f"Queued:         4 Market Categories\n"
                f"Processing:     Generating & Sending",
                title="Source: Global Markets (MoneyControl)",
                border_style="green",
                expand=False
            )
            console.print(panel)
            
            await send_global_markets_update(self.bot)
            
        except Exception as e:
            logger.error(f"❌ Error in Global Markets job: {e}")

    # ================= LIFECYCLE =================

    async def start(self):
        """Start the APScheduler."""
        logger.info("🚀 [bold]Starting Scheduler...[/bold]")
        
        active_modules = []
        
        # Add Market Insights job (runs every N minutes)
        if settings.ENABLE_MARKET_INSIGHTS:
            self.scheduler.add_job(
                self.job_market_insights,
                trigger=IntervalTrigger(minutes=self.mi_interval),
                id='market_insights',
                name='Market Insights Check',
                replace_existing=True
            )
            active_modules.append(f"Market Insights (every {self.mi_interval} min)")
        
        # Add Capital Market job (runs every N minutes)
        if settings.ENABLE_CAPITAL_MARKET:
            self.scheduler.add_job(
                self.job_capital_market,
                trigger=IntervalTrigger(minutes=self.cm_interval),
                id='capital_market',
                name='Capital Market News Check',
                replace_existing=True
            )
            active_modules.append(f"Capital Market (every {self.cm_interval} min)")
        
        # Add Global Markets job (runs daily at specified time)
        if settings.ENABLE_GLOBAL_MARKETS:
            hour, minute = map(int, settings.GLOBAL_MARKETS_DAILY_TIME.split(':'))
            self.scheduler.add_job(
                self.job_global_markets,
                trigger=CronTrigger(hour=hour, minute=minute, timezone=IST),
                id='global_markets',
                name='Daily Global Markets Update',
                replace_existing=True
            )
            active_modules.append(f"Global Markets (daily at {settings.GLOBAL_MARKETS_DAILY_TIME} IST)")
        
        # Start the scheduler
        self.scheduler.start()
        
        # Display active modules
        logger.info(f"✅ [bold green]{len(active_modules)}[/bold green] modules active:")
        for module in active_modules:
            logger.info(f"   • {module}")

    async def stop(self):
        """Stop the APScheduler."""
        logger.info("⏹️  [bold]Stopping scheduler...[/bold]")
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        logger.debug("✅ Scheduler stopped")
