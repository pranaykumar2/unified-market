import httpx
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import hashlib
from typing import List, Dict, Optional
from config.settings import settings
from config.logger_config import setup_logger
from utils.resilience import retry_with_backoff, NETWORK_EXCEPTIONS

logger = setup_logger("CapitalMarketScraper", settings.LOG_LEVEL)

# Request headers for scraping
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

class NewsArticle:
    """Data class representing a news article."""
    
    def __init__(self, title: str, url: str, timestamp: str, 
                 description: str = "", image_url: str = "", news_id: str = ""):
        self.title = title.strip()
        self.url = url
        self.timestamp = timestamp
        self.description = description.strip()
        self.image_url = image_url
        self.news_id = news_id
        self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert article to dictionary."""
        return {
            'title': self.title,
            'url': self.url,
            'timestamp': self.timestamp,
            'description': self.description,
            'image_url': self.image_url,
            'news_id': self.news_id,
            'scraped_at': self.scraped_at
        }

class NewsScraper:
    """Scraper for Capital Market news."""
    
    def __init__(self):
        self.base_url = "https://www.capitalmarket.com"
        # We don't keep a persistent session to avoid connection issues over long periods 
        # but httpx.AsyncClient is efficient when used in context
        
    @retry_with_backoff(retries=3, initial_delay=2, exceptions=NETWORK_EXCEPTIONS)
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content asynchronously."""
        try:
            async with httpx.AsyncClient(headers=REQUEST_HEADERS, timeout=30.0, follow_redirects=True) as client:
                logger.debug(f"📡 Fetching URL: {url}")
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP {e.response.status_code} Error: {e}")
            raise # Let retry handle it
        except Exception as e:
            logger.error(f"❌ Error fetching page: {e}")
            raise

    async def scrape(self) -> List[NewsArticle]:
        """Scrape news articles asynchronously."""
        url = settings.NEWS_URL
        
        try:
            content = await self.fetch_page(url)
            if not content:
                logger.warning("⚠️ No content received from scraper.")
                return []
            
            return self.parse_news(content)
            
        except Exception as e:
            logger.error(f"❌ Error during scraping: {e}")
            return []

    def parse_news(self, html: str) -> List[NewsArticle]:
        """Parse HTML and extract news articles (Original Logic Preserved)."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            articles = []
            
            # Find news table
            news_table = soup.find('table', class_='footable table common-table')
            if not news_table:
                # Fallback or just warn
                logger.warning("Could not find 'footable table common-table', trying generic parsing...")
                return self._parse_generic_fallback(soup)
            
            tbody = news_table.find('tbody')
            if not tbody:
                return articles
            
            rows = tbody.find_all('tr', recursive=False)
            
            for idx, row in enumerate(rows):
                try:
                    article = self._parse_news_row(row)
                    if article:
                        articles.append(article)
                except Exception as e:
                    # logger.warning(f"Error parsing row {idx}: {e}")
                    continue
            
            if articles:
                logger.info(f"✅ Successfully scraped {len(articles)} articles")
            else:
                logger.warning("No articles found after parsing")
                
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []

    def _parse_news_row(self, row) -> Optional[NewsArticle]:
        """Parse a single news row (Original Logic)."""
        try:
            # Extract image URL
            image_url = ""
            img_td = row.find('td', class_='Newsimg')
            if img_td:
                img_tag = img_td.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag['src']
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif image_url.startswith('/'):
                        image_url = 'https://www.capitalmarket.com' + image_url
            
            # Extract content
            tds = row.find_all('td')
            content_td = tds[1] if len(tds) > 1 else None
            if not content_td:
                return None
            
            # Timestamp
            timestamp = ""
            timestamp_elem = content_td.find('p', class_='dtstyle')
            if timestamp_elem:
                timestamp = timestamp_elem.get_text(strip=True)
            
            # Title and URL
            news_link_div = content_td.find('div', class_='NewsLink')
            if not news_link_div:
                return None
            
            link = news_link_div.find('a')
            if not link:
                return None
            
            title = link.get_text(strip=True)
            url = link.get('href', '')
            
            if url and url.startswith('/'):
                url = 'https://www.capitalmarket.com' + url
            elif url and not url.startswith('http') and not url.startswith('javascript:'):
                url = 'https://www.capitalmarket.com/' + url
            
            if not title: return None

            # Generate ID
            id_string = f"{title}_{timestamp}".encode('utf-8')
            news_id = hashlib.md5(id_string).hexdigest()[:16]
            
            # Description
            description = ""
            desc_span = news_link_div.find('span')
            if desc_span:
                description = desc_span.get_text(strip=True)
            
            return NewsArticle(
                title=title,
                url=url,
                timestamp=timestamp,
                description=description,
                image_url=image_url,
                news_id=news_id
            )
            
        except Exception as e:
            return None

    def _parse_generic_fallback(self, soup) -> List[NewsArticle]:
        """Fallback parsing if table structure changed."""
        articles = []
        seen_urls = set()
        news_items = soup.find_all('a', href=True)
        
        for link in news_items:
            try:
                href = link['href']
                title = link.get_text().strip()
                
                if not title or len(title) < 10: continue
                if "news" not in href.lower() and "article" not in href.lower(): continue
                
                full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                
                if full_url in seen_urls: continue
                seen_urls.add(full_url)
                
                timestamp = datetime.now().strftime("%I:%M %p")
                news_id = hashlib.md5(full_url.encode()).hexdigest()
                
                article = NewsArticle(
                    title=title,
                    url=full_url,
                    timestamp=timestamp,
                    description=title,
                    news_id=news_id
                )
                articles.append(article)
                if len(articles) >= 20: break
            except: continue
        return articles
