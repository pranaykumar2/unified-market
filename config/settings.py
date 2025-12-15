import os
from typing import Optional, Tuple
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Unified configuration for Unified News Bot"""
    
    # ============== TELEGRAM CONFIGURATION ==============
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # ============== FEATURE TOGGLES ==============
    ENABLE_GLOBAL_MARKETS: bool = True
    ENABLE_MARKET_INSIGHTS: bool = True
    ENABLE_CAPITAL_MARKET: bool = True  # NEW: For market-news functionality
    
    # ============== GLOBAL MARKETS CONFIGURATION (from unified-market) ==============
    ENABLE_GLOBAL_INDICES: bool = True
    ENABLE_INDIAN_INDICES: bool = True
    ENABLE_GLOBAL_COMMODITIES: bool = True
    ENABLE_GLOBAL_CURRENCIES: bool = True
    
    MAJOR_INDICES_API_URL: str = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=mi"
    INDIAN_INDICES_API_URL: str = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=ii"
    COMMODITIES_API_URL: str = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=co"
    CURRENCIES_API_URL: str = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=cu"
    
    GLOBAL_MARKETS_DAILY_TIME: str = "08:30"
    
    # ============== MARKET INSIGHTS CONFIGURATION (from unified-market) ==============
    TRENDLYNE_API_URL: str = "https://trendlyne.com/equity/api/market-insight/"
    API_RANGE_TYPE: str = "today"
    API_STOCK_GROUP: str = "All"
    MARKET_INSIGHTS_INTERVAL_MINUTES: int = 5
    RATE_LIMIT_DELAY: int = 3
    
    ENABLE_TELUGU: bool = True
    ENABLE_HINDI: bool = False
    ENABLE_BANGLA: bool = False
    ENABLE_TAMIL: bool = False
    ENABLE_MARATHI: bool = False
    ENABLE_KANNADA: bool = False
    ENABLE_MALAYALAM: bool = False
    
    # ============== CAPITAL MARKET CONFIGURATION (from market-news) ==============
    NEWS_URL: str = "https://www.capitalmarket.com/markets/news/live-news"
    CAPITAL_MARKET_INTERVAL_MINUTES: int = 5
    MAX_NEWS_PER_RUN: int = 10
    
    # Image Generation Config (Colors & Fonts)
    # Default colors (R, G, B)
    BG_BLACK: Tuple[int, int, int] = (20, 20, 25)
    BG_GREY: Tuple[int, int, int] = (45, 45, 50)
    CARD_BG: Tuple[int, int, int] = (255, 255, 255)
    
    TAG_BG_COLOR: Tuple[int, int, int] = (30, 30, 35)
    TAG_TEXT_COLOR: Tuple[int, int, int] = (255, 255, 255)
    
    TITLE_COLOR: Tuple[int, int, int] = (0, 51, 102)
    DESCRIPTION_COLOR: Tuple[int, int, int] = (80, 80, 85)
    BRAND_COLOR: Tuple[int, int, int] = (20, 20, 25)
    
    SKY_BLUE: Tuple[int, int, int] = (87, 167, 255)
    LIGHT_GREEN: Tuple[int, int, int] = (50, 205, 50)
    
    # Font Sizes
    FONT_TAG_SIZE: int = 54
    FONT_TITLE_SIZE: int = 68
    FONT_DESCRIPTION_SIZE: int = 54
    FONT_BRAND_SIZE: int = 32
    
    # Font Styles
    FONT_TAG_STYLE: str = 'bold'
    FONT_TITLE_STYLE: str = 'bold'
    FONT_DESCRIPTION_STYLE: str = 'normal'
    FONT_BRAND_STYLE: str = 'italic'
    
    # Font Families (Defaults to Google Fonts for auto-download)
    FONT_TAG_FAMILY: str = 'Poppins'
    FONT_TITLE_FAMILY: str = 'Plus Jakarta Sans'
    FONT_DESCRIPTION_FAMILY: str = 'Roboto'
    FONT_BRAND_FAMILY: str = 'Poppins'
    
    # ============== SHARED STORAGE CONFIGURATION ==============
    DATA_DIR: str = "data"
    FONTS_DIR: str = "data/fonts"  # Centralized fonts directory
    MARKET_DATA_DIR: str = "data/market_data"
    TEMP_IMAGES_DIR: str = "data/temp_images"
    LOG_FILE: str = "data/app.log"
    DATABASE_FILE: str = "data/notifications.db"
    NEWS_HISTORY_FILE: str = "data/sent_news.json"
    
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow" # Allow extra fields in .env

settings = Settings()

def validate_config():
    """Validate configuration and warn about missing values"""
    import logging
    logger = logging.getLogger("Config")
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set. Bot will not send notifications.")
    
    if not settings.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ TELEGRAM_CHAT_ID not set. Bot will not send notifications.")
    
    logger.info(f"Feature Toggles:")
    logger.info(f"  • Global Markets: {'ENABLED' if settings.ENABLE_GLOBAL_MARKETS else 'DISABLED'}")
    logger.info(f"  • Market Insights: {'ENABLED' if settings.ENABLE_MARKET_INSIGHTS else 'DISABLED'}")
    logger.info(f"  • Capital Market: {'ENABLED' if settings.ENABLE_CAPITAL_MARKET else 'DISABLED'}")
