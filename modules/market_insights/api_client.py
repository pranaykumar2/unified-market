import httpx
import asyncio
from typing import Dict, Any, Optional
import logging
from config.settings import settings
from config.logger_config import setup_logger
from utils.resilience import retry_with_backoff, NETWORK_EXCEPTIONS

logger = setup_logger("API", settings.LOG_LEVEL)


class TrendlyneAPIClient:
    """Client for Trendlyne Market Insights API with Production Hardening"""
    
    def __init__(self):
        self.base_url = settings.TRENDLYNE_API_URL
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Referer": "https://trendlyne.com/market-insights/?start_date=2025-12-15&end_date=2025-12-15&defaultStockgroup=All",
            "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "X-Requested-With": "XMLHttpRequest",
            "DNT": "1"
        }
        self.timeout = 30.0 # Re-added timeout as it's used in fetch_market_insights
        
    @retry_with_backoff(retries=3, initial_delay=2, exceptions=NETWORK_EXCEPTIONS)
    async def fetch_market_insights(self) -> Optional[Dict[str, Any]]:
        """Fetch market insights from API with auto-retry."""
        params = {
            "rangeType": settings.API_RANGE_TYPE,
            "stockGroup": settings.API_STOCK_GROUP
        }
        try:
            logger.debug(f"📡 FETCHING market insights from Trendlyne API...")
            logger.debug(f"🌐 URL: {self.base_url}")
            logger.debug(f"📋 Params: {params}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Count insights
                insights_count = len(data.get('body', {}).get('marketInsights', []))
                
                logger.debug(f"✅ API SUCCESS: Received {insights_count} insights (Status: {response.status_code})")
                logger.debug(f"📦 Response data keys: {list(data.keys()) if data else 'None'}")
                
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP ERROR: {e.response.status_code} - {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"❌ REQUEST ERROR: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ UNEXPECTED ERROR: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        logger.info("🔍 TESTING Trendlyne API connection...")
        result = await self.fetch_market_insights()
        
        if result:
            logger.info("✅ SUCCESS: API connection test passed!")
            return True
        else:
            logger.error("❌ FAILED: API connection test failed!")
            return False
