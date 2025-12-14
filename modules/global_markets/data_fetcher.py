import httpx
import logging
import json
import asyncio
from pathlib import Path
from config.settings import settings
from utils.resilience import retry_with_backoff, NETWORK_EXCEPTIONS

logger = logging.getLogger(__name__)


def ensure_data_directories():
    """Create necessary directories for data storage."""
    Path(settings.MARKET_DATA_DIR).mkdir(parents=True, exist_ok=True)


@retry_with_backoff(retries=3, initial_delay=2, exceptions=NETWORK_EXCEPTIONS)
async def fetch_api_data(api_url, section_name):
    """
    Async function to fetch data from MoneyControl API with Retry Logic.
    
    Args:
        api_url: API endpoint URL
        section_name: Name of the section (for logging)
        
    Returns:
        list: List of market items or empty list if failed
    """
    try:
        logger.info(f"📡 Fetching {section_name} from API...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.moneycontrol.com/",
            "Origin": "https://www.moneycontrol.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(api_url, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        if data.get("success") == 1 and data.get("data"):
            items = data["data"]
            logger.info(f"✅ SUCCESS: Fetched {len(items)} items for {section_name}")
            return items
        else:
            logger.warning(f"⚠️ WARNING: No data in response for {section_name}")
            return []
            
    except httpx.TimeoutException:
        logger.error(f"❌ FAILED: Timeout fetching {section_name}")
        return []
    except httpx.HTTPError as e:
        logger.error(f"❌ FAILED: Error fetching {section_name}: {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"❌ FAILED: Invalid JSON response for {section_name}: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ FAILED: Unexpected error fetching {section_name}: {e}")
        return []


async def fetch_all_market_data():
    """
    Fetch all market data from 4 APIs concurrently (non-blocking).
    
    Returns:
        dict: Dictionary with keys 'major_indices', 'indian_indices', 'commodities', 'currencies'
    """
    logger.info("🌍 Fetching all market data from 4 APIs concurrently...")
    
    # Run all 4 fetches at the same time for maximum performance
    results = await asyncio.gather(
        fetch_api_data(settings.MAJOR_INDICES_API_URL, "Major Indices"),
        fetch_api_data(settings.INDIAN_INDICES_API_URL, "Indian Indices"),
        fetch_api_data(settings.COMMODITIES_API_URL, "Commodities"),
        fetch_api_data(settings.CURRENCIES_API_URL, "Currencies")
    )
    
    all_data = {
        "major_indices": results[0],
        "indian_indices": results[1],
        "commodities": results[2],
        "currencies": results[3],
    }
    
    total_items = sum(len(v) for v in all_data.values())
    logger.info(f"✅ Total items fetched: {total_items}")
    
    return all_data
