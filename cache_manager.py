"""
Cache Manager to prevent duplicate sends on restart
Stores timestamps for when updates were last sent
"""
import os
import json
import logging
from datetime import datetime, time as dt_time
from typing import Optional
import pytz
from config.logger_config import setup_logger

logger = setup_logger("Cache", "INFO")

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


class CacheManager:
    """Manages cache for tracking sent updates"""
    
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "send_cache.json")
        self._ensure_cache_dir()
        self._load_cache()
        
        logger.debug(f"📦 Cache manager initialized: {self.cache_file}")
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_cache(self) -> dict:
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                logger.debug(f"✅ Loaded cache from file: {self.cache_file}")
                logger.debug(f"📦 Cache entries: {len(self.cache)} items")
            else:
                self.cache = {}
                logger.debug(f"📝 Cache starting fresh: {self.cache_file}")
        except Exception as e:
            logger.error(f"❌ Error loading cache from {self.cache_file}: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.debug("💾 Cache saved")
        except Exception as e:
            logger.error(f"❌ Error saving cache: {e}")
    
    def _get_current_date_ist(self) -> str:
        """Get current date in IST timezone (YYYY-MM-DD format)"""
        now_ist = datetime.now(IST)
        return now_ist.strftime('%Y-%m-%d')
    
    def _get_current_datetime_ist(self) -> datetime:
        """Get current datetime in IST timezone"""
        return datetime.now(IST)
    
    def was_sent_today(self, key: str) -> bool:
        """Check if update was already sent today"""
        current_date = self._get_current_date_ist()
        
        logger.info(f"🔍 Checking cache for key: {key}")
        logger.info(f"📅 Current date (IST): {current_date}")
        logger.info(f"📦 Cache contents: {self.cache}")
        
        if key not in self.cache:
            logger.info(f"❌ Cache miss: {key} not found in cache")
            return False
        
        cache_entry = self.cache[key]
        last_sent_date = cache_entry.get('date')
        last_sent_time = cache_entry.get('time', 'unknown')
        
        logger.info(f"📝 Cache entry for {key}: date={last_sent_date}, time={last_sent_time}")
        
        if last_sent_date == current_date:
            logger.info(f"✅ Cache hit: {key} was already sent today at {last_sent_time} IST")
            return True
        else:
            logger.info(f"🔍 Cache expired: {key} was last sent on {last_sent_date}, today is {current_date}")
            return False
    
    def mark_as_sent(self, key: str):
        """Mark an update as sent with current timestamp"""
        now_ist = self._get_current_datetime_ist()
        
        cache_entry = {
            'date': now_ist.strftime('%Y-%m-%d'),
            'time': now_ist.strftime('%H:%M:%S'),
            'timestamp': now_ist.isoformat()
        }
        
        logger.debug(f"💾 Writing cache entry for key: {key}")
        self.cache[key] = cache_entry
        
        self._save_cache()
        logger.info(f"✅ Marked as sent in cache: {key} at {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST")
        logger.debug(f"📦 Cache now contains {len(self.cache)} entries")
    
    def clear_cache(self):
        """Clear all cache entries"""
        self.cache = {}
        self._save_cache()
        logger.info("🗑️ Cache cleared")
    
    def should_clear_cache(self) -> bool:
        """Check if we should clear cache (after midnight IST)"""
        now_ist = self._get_current_datetime_ist()
        current_time = now_ist.time()
        
        # Check if it's past midnight (between 00:00 and 00:05)
        midnight = dt_time(0, 0)
        five_am = dt_time(0, 5)
        
        if midnight <= current_time < five_am:
            # Check if we already cleared today
            last_clear = self.cache.get('_last_clear_date')
            current_date = self._get_current_date_ist()
            
            if last_clear != current_date:
                logger.info("🕛 Time to clear cache (past midnight IST)")
                return True
        
        return False
    
    def perform_scheduled_clear(self):
        """Perform the scheduled cache clear at midnight"""
        if self.should_clear_cache():
            current_date = self._get_current_date_ist()
            logger.info(f"🗑️ Performing scheduled cache clear for new day: {current_date}")
            
            # Clear all except metadata
            old_cache = self.cache.copy()
            self.cache = {
                '_last_clear_date': current_date
            }
            self._save_cache()
            
            logger.info(f"✅ Cache cleared: {len(old_cache)} old entries removed")
    
    def get_cache_info(self) -> dict:
        """Get information about cache state"""
        return {
            'total_entries': len(self.cache),
            'cache_file': self.cache_file,
            'entries': self.cache
        }
