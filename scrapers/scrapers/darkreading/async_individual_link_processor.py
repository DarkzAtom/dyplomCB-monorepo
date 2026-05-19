from pprint import pprint
from bs4 import BeautifulSoup
import asyncio
import random
from playwright.async_api import async_playwright, expect, Playwright
from playwright_stealth import stealth_async, StealthConfig
import logging
from datetime import datetime


# THIS IS CONST VALUE DON'T TOUCH IT OR YOU WILL BREAK IT AAARRGH!!!!!!    I'll leave it this way for better days, when I'll be able to find faster concurrent solution while bypassing cloudflare at the same time on their page. For now, this configuration works, and SINCE IT WORKS -> dont touch it. Thank you love you. You absolutely can experiment with it by yourself, just remember this setup to be able to go back to working version after you fail (or maybe not, who knows please dont beat me up alright buddy I'll call the mossad for the help)
SEMAPHORE_LIMIT = 1


async def process_article(url, semaphore, list_of_processed_articles, browser, context):
    async with semaphore: 
        async with async_playwright() as p:
            page = await context.new_page()
            await stealth_async(page)  
            
            try:
                await page.goto(url)
                await page.wait_for_load_state('networkidle')

                await expect(page.locator('span[data-testid="article-title"]')).to_be_in_viewport()
                
                # Get the page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                
                # Here you can add your specific parsing logic
                # For example:
                creation_date = soup.select_one('p[data-testid="contributors-date"]').text.strip()
                article_title = soup.select_one('span[data-testid="article-title"]').text.strip()
                article_header_summary = soup.select_one('p[data-testid="article-summary"]').text.strip()
                article_base = soup.select_one('div[data-module="content"]').text.strip()
                article_text = article_header_summary + '\n' + article_base

                article_dict_to_append = {
                    'fetchingDate': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # date of when WE fetched it
                    'creationDate': creation_date, # date of when the article was published on the source page
                    'author': 'Dark Reading',
                    'authorLink': 'https://www.darkreading.com',
                    'articleLink': url,
                    'articleTitle': article_title,
                    'articleText': article_text,
                }

                # debug
                print(article_dict_to_append)

                list_of_processed_articles.append(article_dict_to_append)
            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")
                return None
            finally:
                await browser.close()
                await asyncio.sleep(random.uniform(30, 40))


async def collect_and_save_cookies(base_url="https://www.darkreading.com", state_file="scrapers/darkreading/cf_state.json"):
    """
    Visits the base URL, waits for Cloudflare to validate the browser,
    and saves the clearance cookies to a JSON file.
    """
    logging.info(f"Starting cookie collection for {base_url}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Keep headless=False for the initial CF solve
            args=[
                '--disable-blink-features=AutomationControlled',
                '--window-size=1920,1080',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )

        context = await browser.new_context(
            locale='en-US',
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            ignore_https_errors=True,
        )

        page = await context.new_page()
        await stealth_async(page)

        try:
            await page.goto(base_url)
            logging.info("Waiting 10 seconds for Cloudflare challenge to clear...")

            # Wait for CF to process. You can also wait for a specific homepage element here.
            await page.wait_for_timeout(10000)

            # SAVE THE STATE (Cookies + LocalStorage)
            await context.storage_state(path=state_file)
            logging.info(f"Successfully saved session state to {state_file}")

        except Exception as e:
            logging.error(f"Failed to collect cookies: {e}")
        finally:
            await browser.close()


async def process_articles(links):
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

    await collect_and_save_cookies(state_file="scrapers/darkreading/cf_state.json")

    async with async_playwright() as p:
        browser, context = await setup_browser_context(p)
        tasks = []
        list_of_processed_articles = []

        for link in links:
            task = asyncio.create_task(process_article(link, semaphore, list_of_processed_articles, browser, context))
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
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080',
            '--lang=en-US,en;q=0.9',
            '--disable-features=IsolateOrigins,site-per-process',
            '--enable-javascript',
            '--hide-scrollbars',
            '--mute-audio',
            '--disable-infobars',
            '--disable-notifications',
            '--disable-popup-blocking',
        ]
    )

    context = await browser.new_context(
        locale='en-US',
        user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        no_viewport=True,
        ignore_https_errors=True,  
    )

    # some selenium-like features
    await context.add_init_script("""
        delete window.__proto__.webdriver;
    """)

    # Disable `navigator.webdriver` (mimic undetectable-chromedriver behavior) (sometimes it helps, don't really mind why?? please, i dont know why as well im not that autistic, and since in this case it helped, as the proud true OG programmer-engineer, please, i beg you, dont touch it alright. thank you darling my love)
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });


        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });


        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: Promise.resolve({ state: 'granted' })
            }),
        });
    """)

    return browser, context


def test_article():
    # Example list of links
    links = [
        'https://www.darkreading.com/threat-intelligence/fake-kling-ai-malvertisements-lure-victims',
        'https://www.darkreading.com/vulnerabilities-threats/virgin-media-02-call-recipient-location',
        'https://www.darkreading.com/cyber-risk/tenable-third-party-connectors-exposure-management',
        'https://www.darkreading.com/data-privacy/regeneron-pledge-privacy-23andme-acquisition',
        'https://www.darkreading.com/cyberattacks-data-breaches/bumblebee-malware-trojanized-vmware-utility'
    ]
    
    # Run the async function
    results = asyncio.run(process_articles(links))
    
    # Print results
    for result in results:
        if result:
            pprint(result)

if __name__ == "__main__":
    test_article()