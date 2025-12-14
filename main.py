"""
Unified News Bot - Main Entry Point
Combines Capital Market News, Global Markets, and Market Insights.
"""
import asyncio
import logging
import os
from datetime import datetime # Kept datetime as it's likely needed and 'from datetime import asyncio' is a typo
import signal # Added signal import
from telegram import Bot

from config.settings import settings, validate_config
from config.logger_config import setup_logger
from services.scheduler import UnifiedScheduler
from utils.banner import print_banner # Added print_banner import

# Initialize Logger
logger = setup_logger("Main", settings.LOG_LEVEL, settings.LOG_FILE) # Modified setup_logger call

async def test_bot_connection(bot: Bot) -> bool:
    """Test Telegram bot connection."""
    try:
        me = await bot.get_me()
        logger.info(f"🤖 Bot Connected: [bold cyan]@{me.username}[/bold cyan]")
        return True
    except Exception as e:
        logger.error(f"❌ Bot Connection Failed: {e}")
        return False

async def main():
    """Main function."""
    print_banner()
    
    logger.info("⚙️  [bold]Initializing System...[/bold]")
    validate_config()
    
    # Ensure data directories exist
    os.makedirs(settings.MARKET_DATA_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_IMAGES_DIR, exist_ok=True)
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    if await test_bot_connection(bot):
        scheduler = UnifiedScheduler(bot)
        
        try:
            await scheduler.start()
            
            logger.info("")
            logger.info("✅ [bold green]BOT IS RUNNING[/bold green] • Press [bold red]Ctrl+C[/bold red] to stop")
            logger.info("")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("⏹️  [bold yellow]Bot stopping...[/bold yellow]")
        except KeyboardInterrupt:
            logger.info("👋 [bold yellow]Shutdown requested by user[/bold yellow]")
        finally:
            await scheduler.stop()
            logger.info("✅ [bold green]Shutdown complete[/bold green]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
