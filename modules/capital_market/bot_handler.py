"""
Bot handler for Capital Market news.
Handles message formatting and delivery using the shared Bot instance.
"""
import asyncio
from typing import List, Tuple
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.constants import ParseMode
import logging

from config.settings import settings
from config.logger_config import setup_logger
from .scraper import NewsArticle
from .renderer import EnhancedNewsImageGenerator

logger = setup_logger("CapitalMarketBot", settings.LOG_LEVEL)

from concurrent.futures import ThreadPoolExecutor
import asyncio

# Global executor for CPU-bound tasks (using ThreadPoolExecutor to avoid Windows multiprocessing issues)
thread_executor = ThreadPoolExecutor(max_workers=2)

class CapitalMarketBotHandler:
    """Handler for sending Capital Market news updates."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.image_generator = EnhancedNewsImageGenerator()
        logger.debug("CapitalMarketBotHandler initialized")
    
    def create_keyboard(self, article: NewsArticle) -> InlineKeyboardMarkup:
        """Create inline keyboard with article link."""
        keyboard = [[InlineKeyboardButton("Read Full Article", url=article.url)]]
        return InlineKeyboardMarkup(keyboard)
    
    async def send_news(self, article: NewsArticle) -> bool:
        """Send a news article to the Telegram channel as a branded image."""
        try:
            # Retry logic
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    # Generate image in a separate thread to avoid blocking event loop
                    loop = asyncio.get_running_loop()
                    
                    image_data = await loop.run_in_executor(
                        thread_executor,
                        self.image_generator.generate_news_image,
                        article.title,
                        article.description,
                        article.timestamp,
                        article.image_url
                    )
                    
                    # Keyboard
                    keyboard = None
                    if article.url and not article.url.startswith('javascript:'):
                        keyboard = self.create_keyboard(article)
                    
                    message = await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=image_data,
                        reply_markup=keyboard,
                        read_timeout=30,
                        write_timeout=30,
                        connect_timeout=30,
                        pool_timeout=30
                    )
                    
                    logger.sent(f"   ╰──> ✅ Sent: {article.title[:50]}...")
                    return True
                    
                except TelegramError as retry_error:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay}s: {retry_error}")
                        await asyncio.sleep(retry_delay)
                    else:
                        raise
            
        except TelegramError as e:
            logger.error(f"Failed to send news: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending news: {e}")
            return False
