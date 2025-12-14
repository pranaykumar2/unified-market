import asyncio
from typing import List
import logging
from config.settings import settings
# from cache_manager import CacheManager # Deprecated
from config.logger_config import setup_logger
from .data_processor import MarketInsight
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = setup_logger("Telegram", settings.LOG_LEVEL)


from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

class TelegramNotifier:
    """Handle sending notifications to Telegram"""
    
    def __init__(self, bot: Bot, database=None):
        self.bot = bot
        self.database = database
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.rate_limit_delay = settings.RATE_LIMIT_DELAY
        
        if self._validate_config():
            logger.debug(f"✅ Telegram notifier ready (rate limit: {self.rate_limit_delay}s)")
        else:
            logger.warning("⚠️ WARNING: Telegram configuration incomplete - Notifications disabled")
    
    def _validate_config(self) -> bool:
        """Validate that required config is present"""
        return bool(self.chat_id)
    
    async def send_notification(self, insight: MarketInsight) -> bool:
        """Send a single notification using the shared Bot instance"""
        if not self._validate_config():
            logger.warning("⚠️ WARNING: Telegram not configured - Skipping notification")
            return False
        
        try:
            logger.debug(f"🔄 Formatting message for: {insight.stock_name}")
            
            # Run translation in a separate thread to prevent blocking
            # This is critical when using deep_translator with multiple languages
            loop = asyncio.get_running_loop()
            message_body = await loop.run_in_executor(None, insight.format_message)
            
            logger.info(f"{insight.stock_name} | {insight.label}")
            
            # Use the shared Bot instance (more efficient connection pooling)
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message_body,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.sent(f"   ╰──> ✅ Sent: {insight.stock_name}")
            return True
                    
        except TelegramError as e:
            logger.error(f"❌ TELEGRAM ERROR: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ FAILED to send notification: {str(e)}")
            return False
    
    async def send_batch_notifications(self, insights: List[MarketInsight]) -> dict:
        """Send multiple notifications with rate limiting"""
        if not insights:
            logger.info("ℹ️ INFO: No insights to send")
            return {"sent": 0, "failed": 0}
        
        # NOTE: Cache check removed - database handles duplicate detection at insight level
        # This allows new insights to be sent throughout the day
        logger.info(f"📤 SENDING BATCH: {len(insights)} notifications with rate limiting...")
        logger.info(f"⏱️ ESTIMATE: ~{len(insights) * self.rate_limit_delay} seconds total time")
        logger.debug(f"📋 Insights to send: {[f'{i.stock_name}-{i.label}' for i in insights]}")
        
        sent = 0
        failed = 0
        
        for i, insight in enumerate(insights, 1):
            logger.info(f"📨 [{i}/{len(insights)}] Processing: {insight.stock_name} - {insight.label}")
            success = await self.send_notification(insight)
            
            if success:
                sent += 1
                logger.info(f"✅ [{i}/{len(insights)}] Success: {insight.stock_name}")
            else:
                failed += 1
                logger.error(f"❌ [{i}/{len(insights)}] Failed: {insight.stock_name}")
            
            # Rate limiting: wait between messages
            if i < len(insights):
                logger.debug(f"⏳ Rate limiting: waiting {self.rate_limit_delay} seconds before next message...")
                await asyncio.sleep(self.rate_limit_delay)
        
        logger.info(f"✅ BATCH COMPLETE: {sent} sent, {failed} failed")
        
        # NOTE: Cache marking removed - not needed since database tracks individual insights
        # Database provides permanent, granular tracking of each insight
        
        return {"sent": sent, "failed": failed}
    
    async def send_test_message(self) -> bool:
        """Send a test message"""
        if not self._validate_config():
            logger.error("❌ FAILED: Cannot send test message - Telegram not configured")
            return False
        
        try:
            test_message = (
                "*Market Insights Monitor Active*\n\n"
                "Your market insights monitor is now running!\n\n"
                "You'll receive notifications when new market insights are detected."
            )
            
            logger.info("📤 SENDING test Telegram message...")
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=test_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ SUCCESS: Test message sent!")
            return True
                    
        except Exception as e:
            logger.error(f"❌ FAILED to send test message: {str(e)}")
            return False
