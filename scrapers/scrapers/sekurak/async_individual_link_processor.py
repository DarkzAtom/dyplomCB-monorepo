import aiohttp
import asyncio
import random
import re
import sys
import logging
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("processor.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # stdout: stderr renders red in PyCharm
    ]
)

logger = logging.getLogger(__name__)

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
        headers = {}
        if self.use_random_user_agent:
            headers['User-Agent'] = random.choice(USER_AGENTS)
            
        return aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
    
    async def fetch_url(self, url: str, session: aiohttp.ClientSession) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                proxy = self.proxy
                async with session.get(url, proxy=proxy) as response:
                    if response.status == 200:
                        return await response.text()
                    if response.status == 429:
                        # too many requests - honor Retry-After, else exponential backoff
                        retry_after = response.headers.get('Retry-After')
                        wait = int(retry_after) if retry_after and retry_after.isdigit() else self.retry_delay * (2 ** attempt)
                        logger.warning(f"429 Too Many Requests for {url}, backing off {wait}s (attempt {attempt+1}/{self.max_retries})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(wait)
                        continue
                    logger.warning(f"Received status code {response.status} for {url}")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt+1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)} (attempt {attempt+1}/{self.max_retries})")
                
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay)
                
        return None
    
    async def process_link(self, url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        html = await self.fetch_url(url, session)
        if not html:
            return {"url": url, "success": False, "error": "Failed to fetch content"}
            
        try:
            soup = BeautifulSoup(html, 'html.parser')

            creation_date = soup.select_one('div.meta').text.strip().split('|')[0].strip()
            article_title = soup.select_one('article#articleContent > h1').text.strip()
            entry = soup.select_one('article#articleContent > div.entry')
            # drop the blue promo/callout boxes before flattening to text
            for box in entry.select('div.boxBlue'):
                box.decompose()
            article_text = entry.text.strip()
            # collapse the layout-newline runs, keep paragraph breaks
            article_text = re.sub(r'[ \t]+\n', '\n', article_text)
            article_text = re.sub(r'\n{3,}', '\n\n', article_text)


            article_dict = {
                    'fetchingDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'creationDate': creation_date if creation_date else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'author': 'sekurak',
                    'authorLink': 'https://www.sekurak.pl',
                    'articleLink': url,
                    'articleTitle': article_title,
                    'articleText': article_text,
                }
            
            return article_dict
            
        
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            return {"url": url, "success": False, "error": str(e)}
    
    async def process_links(self, urls: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        results = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_process_link(url):
            async with semaphore:
                return await self.process_link(url, session)
        
        async with await self._get_session() as session:
            tasks = [bounded_process_link(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def process_links_async(
    urls: List[str],
    proxy: Optional[str] = None,
    use_random_user_agent: bool = True,
    timeout: int = 30,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    processor = AsyncLinkProcessor(
        proxy=proxy,
        use_random_user_agent=use_random_user_agent,
        timeout=timeout,
        max_retries=max_retries
    )
    return await processor.process_links(urls)

def process_links(
    urls: List[str], 
    proxy: Optional[str] = None,
    use_random_user_agent: bool = True
) -> List[Dict[str, Any]]:
    return asyncio.run(process_links_async(
        urls, 
        proxy=proxy,
        use_random_user_agent=use_random_user_agent
    ))

if __name__ == "__main__":
    urls_to_process = [
        "https://sekurak.pl/platforma-e-commerce-sky-shop-pl-informuje-swoich-klientow-o-ataku/",
        "https://sekurak.pl/przelaczniki-bez-tajemnic-szkolenie-ktore-moze-zaskoczyc-nawet-doswiadczonych-adminow/"
    ]
    
    results = process_links(urls_to_process)
    for result in results:
        print(result)
