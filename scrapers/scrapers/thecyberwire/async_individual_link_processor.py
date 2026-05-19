import aiohttp
import asyncio
import random
import logging
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("processor.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# User agents list for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

class AsyncLinkProcessor:
    def __init__(self, 
                 proxy: Optional[str] = None, 
                 use_random_user_agent: bool = True,
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: int = 2):
        self.proxy = proxy
        self.use_random_user_agent = use_random_user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Create and return an aiohttp session with configured options"""
        headers = {}
        if self.use_random_user_agent:
            headers['User-Agent'] = random.choice(USER_AGENTS)
            
        return aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
    
    async def fetch_url(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Fetch a URL with retries"""
        for attempt in range(self.max_retries):
            try:
                proxy = self.proxy
                async with session.get(url, proxy=proxy) as response:
                    if response.status == 200:
                        return await response.text()
                    logger.warning(f"Received status code {response.status} for {url}")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt+1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)} (attempt {attempt+1}/{self.max_retries})")
                
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
                
        return None
    
    async def process_link(self, url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Process a single link and return the results"""
        html = await self.fetch_url(url, session)
        if not html:
            return {"url": url, "success": False, "error": "Failed to fetch content"}
            
        # Parsing the content
        try:
            news_bulk: list = []
            soup = BeautifulSoup(html, 'html.parser')

            creation_date_unparsed = soup.select_one('div.meta > div.meta-box > span.meta-text').text.strip()

            def _extract_american_date_and_convert_to_right_format(date_string):
                # Extract the date part (after the second pipe)
                parts = date_string.split('|')
                if len(parts) >= 3:
                    date_part = parts[2].strip()
                else:
                    # Try to find the date directly
                    date_part = date_string.strip()
        
                # Parse the date (format: MM.DD.YY)
                try:
                    # Handle format like "5.20.25"
                    month, day, year = date_part.split('.')
                    # Convert 2-digit year to 4-digit (assuming 20xx for years < 50)
                    full_year = f"20{year}" if int(year) < 50 else f"19{year}"
            
                    # Return in DD/MM/YYYY format
                    return f"{day}/{month}/{full_year}"
                except Exception as e:
                    logger.error(f"Error parsing date '{date_part}': {e}")
                    return None

            creation_date = _extract_american_date_and_convert_to_right_format(creation_date_unparsed)

            articles_container = soup.select_one('div.nl-section.summary > div.content')

            articles_unrefined = articles_container.select('div.text')
            
            # TODO: finish refinng logic to get rid of 'At glance' that is being added to every first article in the bulk
            # for article in articles_unrefined:
            #     if 

            articles = articles_unrefined

            for article in articles:
                
                h2_elements = article.select('h2')
                if h2_elements and h2_elements[0].text.strip() == 'At a glance.':
                    if len(h2_elements) > 1:
                        article_title = h2_elements[1].text.strip()
                    else:
                        # Handle case where there's no second h2
                        article_title = "Unknown title"
                else:
                    article_title = h2_elements[0].text.strip() if h2_elements else "Unknown title"

                article_text_unconcated = article.select('p')

                article_text = '\n'.join([p.text.strip() for p in article_text_unconcated])

                if not article_title or not article_text:
                    continue

                article_dict_to_append = {
                        'fetchingDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date of when WE fetched it
                        'creationDate': creation_date if creation_date else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date of when the article was published on the source page
                        'author': 'CyberWire',
                        'authorLink': 'https://www.thecyberwire.com/newsletters/daily-briefing',
                        'articleLink': url,
                        'articleTitle': article_title,
                        'articleText': article_text,
                    }
                
                news_bulk.append(article_dict_to_append)
            return news_bulk
        
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            return {"url": url, "success": False, "error": str(e)}
    
    async def process_links(self, urls: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:  # you can change the max_concurrent to any number you want here
        """Process multiple links concurrently with a limit on concurrent requests"""
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_process_link(url):
            async with semaphore:  # This limits concurrent execution
                return await self.process_link(url, session)
        
        async with await self._get_session() as session:
            tasks = [bounded_process_link(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            flattened_results = [item for sublist in results for item in sublist]
        return flattened_results

# Main function to process links
async def process_links_async(
    urls: List[str],
    proxy: Optional[str] = None,
    use_random_user_agent: bool = True,
    timeout: int = 30,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """Process a list of URLs asynchronously"""
    processor = AsyncLinkProcessor(
        proxy=proxy,
        use_random_user_agent=use_random_user_agent,
        timeout=timeout,
        max_retries=max_retries
    )
    return await processor.process_links(urls)

# Helper function for running from synchronous code
def process_links(
    urls: List[str], 
    proxy: Optional[str] = None,
    use_random_user_agent: bool = True
) -> List[Dict[str, Any]]:
    """Synchronous wrapper for async link processing"""
    return asyncio.run(process_links_async(
        urls, 
        proxy=proxy,
        use_random_user_agent=use_random_user_agent
    ))

# Example usage
if __name__ == "__main__":
    urls_to_process = [
        "https://thecyberwire.com/newsletters/daily-briefing/14/96",
        "https://thecyberwire.com/newsletters/daily-briefing/14/95"
    ]
    
    results = process_links(urls_to_process)
    for result in results:
        print(result)
