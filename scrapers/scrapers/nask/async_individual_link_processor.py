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
    format='%(asctime)s - %(levelname)s - %(lineno)d - %(message)s',
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
        
        logger.info('Successfully fetched content, processing HTML...')
            
        # Parsing the content
        try:
            soup = BeautifulSoup(html, 'html.parser')

            creation_date = soup.select_one('span.text-tiny.text-theme-text-secondary.md\\:text-small:nth-child(1)').text.strip()
            print(creation_date)
            article_title = soup.select_one('h1.mb-size-04.text-h2.text-theme-text').text.strip()
            print(article_title)
            article_pretext = soup.select_one('p.text-medium.text-theme-text-secondary').text.strip()
            print(article_pretext)
            article_maintext = soup.select_one('div.inner-post').text.strip()
            print(article_maintext)
            article_text = article_pretext + "\n\n" + article_maintext


            # TODO: clean the article_text from the "div.boxBlue" inside of it


            article_dict = {
                    'fetchingDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date of when WE fetched it
                    'creationDate': creation_date if creation_date else datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date of when the article was published on the source page
                    'author': 'sekurak',
                    'authorLink': 'https://www.sekurak.pl',
                    'articleLink': url,
                    'articleTitle': article_title,
                    'articleText': article_text,
                }
            
            return article_dict
            
        
        except Exception as e:
            logger.exception(f"Error processing {url}: {str(e), }")
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
        return results

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
        "https://nask.pl/aktualnosci/fakty-nie-mity-nask-i-umb-wspolnie-przeciw-dezinformacji-medycznej",
        "https://nask.pl/aktualnosci/szkoly-coraz-blizej-technologicznej-rewolucji-znamy-oferty-na-szkolne-laboratoria-przyszlosci"
    ]
    
    results = process_links(urls_to_process)
    for result in results:
        print(result)
