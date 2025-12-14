from typing import List, Dict, Any, Optional
from datetime import datetime
from deep_translator import GoogleTranslator
import logging
import pytz
from config.settings import settings
from config.logger_config import setup_logger

logger = setup_logger("DataProcessor", settings.LOG_LEVEL)


class MarketInsight:
    """Represents a single market insight"""
    
    def __init__(self, stock_name: str, label: str, notification: str, 
                 insight_id: Optional[str] = None, timestamp: Optional[str] = None, 
                 news_date: Optional[str] = None):
        self.stock_name = stock_name
        self.label = label
        self.notification = notification
        self.insight_id = insight_id or self._generate_id()
        self.timestamp = timestamp or datetime.now().isoformat()
        self.news_date = news_date  # Store the original news date from API
    
    def _generate_id(self) -> str:
        """Generate a unique ID for this insight"""
        return f"{self.stock_name}_{self.label}_{self.notification[:50]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "stock_name": self.stock_name,
            "label": self.label,
            "notification": self.notification,
            "insight_id": self.insight_id,
            "timestamp": self.timestamp
        }
    
    def _translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language"""
        try:
            translator = GoogleTranslator(source='en', target=target_lang)
            return translator.translate(text)
        except Exception as e:
            logger.error(f"❌ Translation error for {target_lang}: {e}")
            return text  # Return original text if translation fails
    
    def format_message(self) -> str:
        """Format message for Telegram with multi-language support"""
        try:
            languages = {
                'telugu': {
                    'enabled': settings.ENABLE_TELUGU,
                    'code': 'te',
                    'header': 'స్టాక్ వార్తలలో',
                    'company': 'కంపెనీ పేరు',
                    'tag': 'విషయము',
                    'news': 'వార్త'
                },
                'hindi': {
                    'enabled': settings.ENABLE_HINDI,
                    'code': 'hi',
                    'header': 'स्टॉक समाचार में',
                    'company': 'कंपनी का नाम',
                    'tag': 'टैग',
                    'news': 'समाचार'
                },
                'bangla': {
                    'enabled': settings.ENABLE_BANGLA,
                    'code': 'bn',
                    'header': 'স্টক খবরে',
                    'company': 'কোম্পানির নাম',
                    'tag': 'ট্যাগ',
                    'news': 'খবর'
                },
                'tamil': {
                    'enabled': settings.ENABLE_TAMIL,
                    'code': 'ta',
                    'header': 'பங்கு செய்திகளில்',
                    'company': 'நிறுவனத்தின் பெயர்',
                    'tag': 'குறிச்சொல்',
                    'news': 'செய்தி'
                },
                'marathi': {
                    'enabled': settings.ENABLE_MARATHI,
                    'code': 'mr',
                    'header': 'स्टॉक बातम्यांमध्ये',
                    'company': 'कंपनीचे नाव',
                    'tag': 'टॅग',
                    'news': 'बातमी'
                },
                'kannada': {
                    'enabled': settings.ENABLE_KANNADA,
                    'code': 'kn',
                    'header': 'ಸ್ಟಾಕ್ ಸುದ್ದಿಯಲ್ಲಿ',
                    'company': 'ಕಂಪನಿ ಹೆಸರು',
                    'tag': 'ಟ್ಯಾಗ್',
                    'news': 'ಸುದ್ದಿ'
                },
                'malayalam': {
                    'enabled': settings.ENABLE_MALAYALAM,
                    'code': 'ml',
                    'header': 'സ്റ്റോക്ക് വാർത്തകളിൽ',
                    'company': 'കമ്പനിയുടെ പേര്',
                    'tag': 'ടാഗ്',
                    'news': 'വാർത്ത'
                }
            }
            
            message_parts = []
            
            # English section (always included)
            message_parts.append("*Stock In News*")
            message_parts.append("")
            message_parts.append(f"*Company Name:* {self.stock_name}")
            message_parts.append("")
            message_parts.append(f"*Tag:* {self.label}")
            message_parts.append("")
            message_parts.append(f"*News:* {self.notification}")
            
            # Add enabled language translations
            for lang_name, lang_config in languages.items():
                if lang_config['enabled']:
                    message_parts.append("")
                    message_parts.append("---------")
                    message_parts.append("")
                    
                    message_parts.append(f"*{lang_config['header']}*")
                    message_parts.append("")
                    
                    stock_name_translated = self._translate_text(self.stock_name, lang_config['code'])
                    label_translated = self._translate_text(self.label, lang_config['code'])
                    notification_translated = self._translate_text(self.notification, lang_config['code'])
                    
                    message_parts.append(f"*{lang_config['company']}:* {stock_name_translated}")
                    message_parts.append("")
                    message_parts.append(f"*{lang_config['tag']}:* {label_translated}")
                    message_parts.append("")
                    message_parts.append(f"*{lang_config['news']}:* {notification_translated}")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"❌ Error formatting multi-lingual message: {e}")
            # Fallback to simple English message
            message = (
                "*Stock In News*\n\n"
                f"*Company Name:* {self.stock_name}\n\n"
                f"*Tag:* {self.label}\n\n"
                f"*News:* {self.notification}"
            )
            return message
    
    def __repr__(self) -> str:
        return f"MarketInsight(stock={self.stock_name}, label={self.label})"


class DataProcessor:
    """Process market insights data from API"""
    
    def __init__(self):
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        logger.debug("🔧 DataProcessor initialized with IST timezone")
    
    def extract_insights(self, api_response: Dict[str, Any]) -> List[MarketInsight]:
        """Extract insights from API response"""
        insights = []
        
        try:
            logger.debug(f"🔍 Parsing API response structure...")
            body = api_response.get("body", {})
            market_insights = body.get("marketInsights", [])
            
            if not market_insights:
                logger.warning("⚠️ No market insights found in API response")
                return insights
            
            logger.info(f"📊 Processing {len(market_insights)} insights from API response...")
            
            for idx, item in enumerate(market_insights, 1):
                try:
                    stock_name = item.get("stockName", "Unknown")
                    label = item.get("label", "Unknown")
                    notification = item.get("notification", "No details available")
                    news_timestamp = item.get("timeStamp", "")
                    
                    logger.debug(f"🔄 [{idx}/{len(market_insights)}] Extracting: {stock_name} - {label} - {news_timestamp}")
                    
                    insight = MarketInsight(
                        stock_name=stock_name,
                        label=label,
                        notification=notification,
                        news_date=news_timestamp
                    )
                    
                    insights.append(insight)
                    logger.debug(f"✅ [{idx}/{len(market_insights)}] Extracted: {stock_name} - {label} | ID: {insight.insight_id[:30]}...")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing insight item: {e}")
                    continue
            
            logger.debug(f"✅ Successfully processed {len(insights)} insights")
            
        except Exception as e:
            logger.error(f"❌ Error extracting insights: {e}")
        
        return insights
    
    def _parse_news_date(self, timestamp_str: str) -> Optional[str]:
        """Parse Trendlyne timestamp format to date string (DD MMM, YYYY)"""
        try:
            # Example: "12 Dec, 2025  3:23 PM (IST)"
            # Extract just the date part: "12 Dec, 2025"
            if timestamp_str:
                date_part = timestamp_str.split('  ')[0].strip()  # Split by double space
                return date_part
        except Exception as e:
            logger.debug(f"Error parsing date from '{timestamp_str}': {e}")
        return None
    
    def _is_today_ist(self, news_date_str: str) -> bool:
        """Check if news date matches today's date in IST"""
        try:
            # Get current date in IST
            now_ist = datetime.now(self.ist_tz)
            today_str = now_ist.strftime("%d %b, %Y")  # Format: "14 Dec, 2025"
            
            # Parse news date (format: "12 Dec, 2025")
            parsed_date = self._parse_news_date(news_date_str)
            
            if parsed_date:
                # Direct string comparison
                is_today = (parsed_date == today_str)
                logger.debug(f"📅 Date check: News='{parsed_date}' vs Today='{today_str}' -> {is_today}")
                return is_today
            
        except Exception as e:
            logger.debug(f"Error checking date: {e}")
        
        # If we can't parse, assume it's today (fail-safe)
        return True
    
    def filter_new_insights(self, all_insights: List[MarketInsight], 
                           seen_ids: set) -> List[MarketInsight]:
        """Filter out insights that have already been sent and not from today"""
        # Get current IST date for logging
        now_ist = datetime.now(self.ist_tz)
        today_str = now_ist.strftime("%d %b, %Y")
        
        logger.debug(f"📅 Current IST Date: {today_str}")
        logger.debug(f"🔍 Filtering insights: {len(all_insights)} total vs {len(seen_ids)} already sent")
        
        new_insights = []
        duplicate_count = 0
        old_news_count = 0
        
        for insight in all_insights:
            # First check if it's from today
            if insight.news_date:
                if not self._is_today_ist(insight.news_date):
                    old_news_count += 1
                    logger.debug(f"📅 OLD NEWS skipped: {insight.stock_name} - {insight.news_date}")
                    continue
            
            # Then check if it's a duplicate
            if insight.insight_id not in seen_ids:
                new_insights.append(insight)
                logger.debug(f"🆕 NEW insight detected: {insight.stock_name} - {insight.label} - {insight.news_date}")
            else:
                duplicate_count += 1
                logger.debug(f"⏭️ DUPLICATE skipped: {insight.stock_name} - {insight.label}")
        
        if new_insights:
            logger.debug(f"🆕 Found {len(new_insights)} new insights from today (skipped {duplicate_count} duplicates, {old_news_count} old news)")
        else:
            logger.debug(f"ℹ️ No new insights from today (skipped {duplicate_count} duplicates, {old_news_count} old news)")
        
        return new_insights
