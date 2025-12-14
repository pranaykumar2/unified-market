# Unified News Bot

A comprehensive Telegram bot that aggregates and delivers market news from multiple sources.

## Features

### 📰 Three News Sources
1. **Capital Market News** - Latest stock market news from Capital Market website
2. **Market Insights** - Real-time insights from Trendlyne API (filtered by current date IST)
3. **Global Markets** - Daily market updates from MoneyControl (indices, commodities, forex, bonds)

### ⚡ Key Capabilities
- ✅ Automated scheduling with APScheduler
- ✅ Duplicate detection using unified SQLite database
- ✅ IST timezone support with date filtering
- ✅ Rich console logging with colored panels
- ✅ Retry logic with exponential backoff
- ✅ Multi-language support (7 languages)
- ✅ Image generation for global markets data

## Project Structure

```
unified-news-bot/
├── config/
│   ├── logger_config.py       # Logging configuration
│   └── settings.py             # Application settings
├── data/
│   ├── fonts/                  # Fonts for image generation
│   ├── market_data/            # Market data storage
│   └── notifications_history.db # SQLite database
├── modules/
│   ├── capital_market/         # Capital Market news module
│   ├── global_markets/         # Global Markets module
│   └── market_insights/        # Trendlyne insights module
├── services/
│   ├── database.py             # Unified database service
│   └── scheduler.py            # Job scheduler
├── utils/
│   ├── banner.py               # Startup banner
│   └── resilience.py           # Retry decorators
├── fonts_cache/                # Cached fonts
├── temp_images/                # Temporary image storage
├── .env                        # Environment variables
├── cache_manager.py            # Cache management
├── main.py                     # Application entry point
└── requirements.txt            # Python dependencies
```

## Setup

### 1. Prerequisites
- Python 3.13+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Telegram Chat ID

### 2. Installation

```powershell
# Clone or download the project
cd unified-news-bot

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Module Enable/Disable
ENABLE_MARKET_INSIGHTS=True
ENABLE_CAPITAL_MARKET=True
ENABLE_GLOBAL_MARKETS=True

# Schedule Configuration
MARKET_INSIGHTS_INTERVAL_MINUTES=2
CAPITAL_MARKET_INTERVAL_MINUTES=5
GLOBAL_MARKETS_DAILY_TIME=13:53

# Optional Settings
MAX_NEWS_PER_RUN=10
LOG_LEVEL=INFO
```

### 4. Run the Bot

```powershell
python main.py
```

## Scheduling

- **Market Insights**: Every 2 minutes (configurable)
- **Capital Market**: Every 5 minutes (configurable)
- **Global Markets**: Once daily at 13:53 IST (configurable)

## Logging

The bot uses Rich library for beautiful console output:

```
╭─── Source: Capital Market News ───╮
│  Queued:         6 New Articles   │
│  Processing:     Sending          │
╰───────────────────────────────────╯
```

## Database

SQLite database with WAL mode for better concurrency:
- Stores notification history
- Prevents duplicate notifications
- Tracks sent news articles

## Technologies

- **python-telegram-bot 21.0** - Telegram Bot API
- **APScheduler 3.10.4** - Job scheduling
- **httpx** - Async HTTP client
- **BeautifulSoup4** - HTML parsing
- **Pillow** - Image generation
- **Rich** - Console formatting
- **pytz** - Timezone handling

## License

MIT License
