from pprint import pprint
from bs4 import BeautifulSoup
import asyncio
import random
from playwright.async_api import async_playwright, expect, Playwright
from playwright_stealth import stealth_async, StealthConfig
import logging
from datetime import datetime


# a semaphore to set a limit to concurrent pages to be processed
SEMAPHORE_LIMIT = 2 


async def process_article(context, url, semaphore, list_of_processed_articles):
    async with semaphore: 
        page = await context.new_page()
        await stealth_async(page)  
        
        try:
            await page.goto(url)

            await expect(page.locator('div#articlebody')).to_be_in_viewport()
            
            # Get the page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Here you can add your specific parsing logic
            # For example:
            creation_date = soup.select_one('span.author:nth-of-type(1)').text.strip()
            article_title = soup.select_one('h1.story-title').text.strip()
            article_text = soup.select_one('div.articlebody').text.strip()


            footer_markers = [
                "Found this article interesting?",
                "Follow us on Twitter",
                "Follow us on LinkedIn"
            ]

            for marker in footer_markers:
                if marker in article_text:
                    article_text = article_text.split(marker)[0].strip()
                    break

            
            article_dict_to_append = {
                'fetchingDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date of when WE fetched it
                'creationDate': creation_date, # date of when the article was published on the source page
                'author': 'The Hacker News',
                'authorLink': 'https://thehackernews.com',
                'articleLink': url,
                'articleTitle': article_title,
                'articleText': article_text,
            }
            list_of_processed_articles.append(article_dict_to_append)
        except Exception as e:
            logging.error(f"Error processing {url}: {str(e)}")
            return None
        finally:
            await asyncio.sleep(random.uniform(1.5, 3))
            await page.close()


async def process_articles(links):
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    
    async with async_playwright() as p:
        browser, context = await setup_browser_context(p)
        tasks = []
        list_of_processed_articles = []
        
        for link in links:
            task = asyncio.create_task(process_article(context, link, semaphore, list_of_processed_articles))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        await browser.close()
        return list_of_processed_articles
    

async def setup_browser_context(playwright: Playwright):
    browser = await playwright.chromium.launch(
        headless=False,
        channel='chrome',
        slow_mo=750,
        # if we'd ever need to use proxy -> uncomment below
        # proxy={
        #     "server": f"http://{proxy_dict['proxyaddr']}:{proxy_dict['proxyport']}",
        #     "username": proxy_dict['proxylogin'],
        #     "password": proxy_dict['proxypswd']
        # },
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            # '--disable-blink-features=AutomationControlled',
            '--start-maximized',
            '--disable-extensions',
            '--disable-infobars',
            # '--lang=en-US,en;q=0.9',
            '--disable-backgrounding-occluded-windows',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--ignore-certificate-errors',
            '--disable-popup-blocking',
            '--disable-notifications',
            '--disable-browser-side-navigation',
            # '--disable-features=IsolateOrigins,site-per-process',
        ]
    )

    context = await browser.new_context(
        locale='en-US',
        user_agent=None,
        no_viewport=True,  # Set to your desired window size
        ignore_https_errors=True,  # Ignore certificate errors
    )

    # Adding experimental features similar to Selenium's options
    await context.add_init_script("""
        delete window.__proto__.webdriver;
    """)

    # Disable `navigator.webdriver` (mimic undetectable-chromedriver behavior)
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    return browser, context


def test_article():
    # Example list of links
    links = [
        'https://thehackernews.com/2025/05/security-tools-alone-dont-protect-you.html',
        'https://thehackernews.com/2025/05/sonicwall-patches-3-flaws-in-sma-100.html',
        'https://thehackernews.com/2025/05/mirrorface-targets-japan-and-taiwan.html',
        'https://thehackernews.com/2025/05/ottokit-wordpress-plugin-with-100k.html',
        'https://thehackernews.com/2025/05/researchers-uncover-malware-in-fake.html'
    ]
    
    # Run the async function
    results = asyncio.run(process_articles(links))
    
    # Print results
    for result in results:
        if result:
            pprint(result)

if __name__ == "__main__":
    test_article()