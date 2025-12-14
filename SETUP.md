# Unified News Bot - Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.13 or higher
- Telegram Bot Token from [@BotFather](https://t.me/botfather)
- Your Telegram Chat ID

### 2. Installation

```powershell
# Navigate to project directory
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
# Required: Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Module Control (True/False)
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

## Features

### 📊 Market Insights (Trendlyne API)
- **Source**: Trendlyne API
- **Schedule**: Every 2 minutes (configurable)
- **Features**:
  - Real-time market insights
  - IST timezone date filtering (only today's news)
  - Duplicate detection via SQLite database
  - Automatic retry on failures

### 📰 Capital Market News
- **Source**: Capital Market website scraping
- **Schedule**: Every 5 minutes (configurable)
- **Features**:
  - Latest stock market news
  - Multi-language support (7 languages)
  - News tracking to prevent duplicates
  - Rich HTML rendering

### 🌍 Global Markets
- **Source**: MoneyControl website
- **Schedule**: Once daily at 13:53 IST (configurable)
- **Features**:
  - Global indices (US, Europe, Asia)
  - Commodity prices
  - Forex rates
  - Bond yields
  - Image generation with charts

## Project Structure

```
unified-news-bot/
├── .env                        # Environment variables (create this)
├── .gitignore                  # Git ignore file
├── README.md                   # Main documentation
├── SETUP.md                    # This file
├── requirements.txt            # Python dependencies
├── main.py                     # Entry point
├── cache_manager.py            # Cache management
│
├── config/
│   ├── logger_config.py        # Logging setup
│   └── settings.py             # Application settings
│
├── modules/
│   ├── capital_market/         # Capital Market news module
│   │   ├── __init__.py
│   │   ├── bot_handler.py      # Telegram message handler
│   │   ├── renderer.py         # HTML rendering
│   │   ├── scraper.py          # Web scraping
│   │   └── tracker.py          # Duplicate tracking
│   │
│   ├── global_markets/         # Global Markets module
│   │   ├── __init__.py
│   │   ├── bot_handler.py      # Telegram handler
│   │   ├── data_fetcher.py     # Data fetching
│   │   └── image_generator.py  # Chart generation
│   │
│   └── market_insights/        # Market Insights module
│       ├── __init__.py
│       ├── api_client.py       # Trendlyne API client
│       ├── data_processor.py   # Data processing & date filtering
│       └── telegram_notifier.py # Notification sender
│
├── services/
│   ├── database.py             # Unified SQLite database
│   └── scheduler.py            # APScheduler job orchestration
│
├── utils/
│   ├── banner.py               # Startup banner
│   └── resilience.py           # Retry decorators
│
├── data/
│   ├── fonts/                  # Fonts for image generation
│   ├── market_data/            # Market data storage
│   └── notifications_history.db # SQLite database (auto-created)
│
├── fonts_cache/                # Cached fonts for rendering
└── temp_images/                # Temporary image storage
```

## Advanced Configuration

### Module Control

Enable or disable individual modules in `.env`:

```env
ENABLE_MARKET_INSIGHTS=True    # Trendlyne insights
ENABLE_CAPITAL_MARKET=True     # Capital Market news
ENABLE_GLOBAL_MARKETS=True     # Global Markets data
```

### Schedule Customization

Adjust check intervals:

```env
MARKET_INSIGHTS_INTERVAL_MINUTES=2    # Check every 2 minutes
CAPITAL_MARKET_INTERVAL_MINUTES=5     # Check every 5 minutes
GLOBAL_MARKETS_DAILY_TIME=13:53       # Daily at 1:53 PM IST
```

### Logging

Set log level (DEBUG, INFO, WARNING, ERROR):

```env
LOG_LEVEL=INFO
```

## Logging Output

The bot uses Rich library for beautiful console output:

```
╭─── Source: Capital Market News ───╮
│  Queued:         6 New Articles   │
│  Processing:     Sending          │
╰───────────────────────────────────╯

╭─ Source: Market Insights (Trendlyne) ─╮
│  Queued:         5 New Insights       │
│  Processing:     Sending              │
╰───────────────────────────────────────╯

╭─ Source: Global Markets (MoneyControl) ─╮
│  Queued:         4 Market Categories    │
│  Processing:     Generating & Sending   │
╰─────────────────────────────────────────╯
```

## Database

The bot uses SQLite with WAL mode for better concurrency:

- **File**: `data/notifications_history.db`
- **Purpose**: Track sent notifications to prevent duplicates
- **Tables**: Stores insight IDs, stock names, labels, and timestamps

## Troubleshooting

### Bot Not Starting

1. Check `.env` file exists with valid tokens
2. Verify virtual environment is activated
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

### No News Received

1. Check bot is running without errors
2. Verify schedule intervals in `.env`
3. Check Telegram Chat ID is correct
4. Review logs for errors

### Date Filtering Issues

The bot filters news by IST timezone:
- Only sends news from current date (IST)
- Uses pytz library for timezone conversion
- Check system time is correctly synced

## Stopping the Bot

Press `Ctrl+C` to gracefully stop the bot:

```
[14:20:45] INFO     👋 Shutdown requested by user
[14:20:45] INFO     ⏹️  Stopping scheduler...
[14:20:45] INFO     ✅ Shutdown complete
```

## Production Deployment

### Windows Service

Use NSSM (Non-Sucking Service Manager) to run as a service:

```powershell
nssm install UnifiedNewsBot "C:\path\to\venv\Scripts\python.exe" "C:\path\to\main.py"
nssm start UnifiedNewsBot
```

### Linux Service (systemd)

Create `/etc/systemd/system/unified-news-bot.service`:

```ini
[Unit]
Description=Unified News Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/unified-news-bot
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable unified-news-bot
sudo systemctl start unified-news-bot
```

## Updates & Maintenance

### Update Dependencies

```powershell
pip install --upgrade -r requirements.txt
```

### Clear Database

To reset notification history:

```powershell
Remove-Item data\notifications_history.db
# Database will be recreated on next run
```

### Clear Cache

```powershell
Remove-Item fonts_cache\* -Recurse
Remove-Item temp_images\* -Recurse
```

## Support & Issues

For issues or questions:
1. Check logs in `data/app.log`
2. Verify `.env` configuration
3. Ensure all dependencies are installed
4. Check internet connectivity

## License

MIT License
