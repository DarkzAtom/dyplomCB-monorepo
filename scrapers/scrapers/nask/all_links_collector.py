import os
from dotenv import load_dotenv
load_dotenv()  # load HEADLESS (from scrapers/.env) regardless of which entry point runs this
import requests
from bs4 import BeautifulSoup
import functools
import time
from playwright.sync_api import sync_playwright


# ---LOGGER SETUP ------------------------------------------------------------
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # stdout: stderr renders red in PyCharm
    ]
)

logger = logging.getLogger(__name__)
# -----------------------------------------------------------------------------


# ---RETRY DECORATOR ----------------------------------------------------------
def retry(exceptions=(Exception,), max_attempts=2, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts > max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempts} failed with {e.__class__.__name__}: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"Failed with non-retryable exception: {e}")
                    raise
        return wrapper
    return decorator


class AbsentAnchorElementException(Exception):
    pass



@retry(exceptions=(AbsentAnchorElementException,), max_attempts=2, delay=1)
def get_all_links_of_articles_until_lastsaved_met():
    url = "https://nask.pl/aktualnosci"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.getenv("HEADLESS", "").lower() == "true")
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url)
            page.wait_for_load_state("networkidle")
        except Exception as e:
            logger.critical(f"Failed to load page {url}: {e}")
            raise AbsentAnchorElementException(f"Failed to load page {url}: {e}") from e

        html_content = page.content()
        browser.close()

    logger.debug("Page loaded successfully, proceeding to parse HTML content.")

    soup = BeautifulSoup(html_content, "html.parser")

    with open('scrapers/nask/debug.html', 'w') as f:
        f.write(soup.prettify())

    logger.debug("HTML content parsed successfully.")

    article_links: list = []

    for a_tag in soup.find_all('a'):
        href = a_tag.get('href')

        if href and ('/aktualnosci/' in href):
            full_url = f"https://www.nask.pl{href}"
            if full_url not in article_links:
                article_links.append(full_url)

    for link in article_links:
        print(link)


    
    # getting the last saved link met | pobieranie ostatniego zapisanego linku
    with open("scrapers/nask/lastsaved_articlelink.txt", "r") as file:
        lastsaved_articlelink = file.read()
    
    collected_links_list = []
    
    for link in article_links:
        if link == lastsaved_articlelink:
            break
        
        collected_links_list.append(link)

    if collected_links_list:
        lastsaved_articlelink = collected_links_list[0]

    with open("scrapers/nask/lastsaved_articlelink.txt", "w") as file:
        file.write(lastsaved_articlelink)

    for link in collected_links_list:
        print(link)
        time.sleep(0.5)

    return collected_links_list






if __name__ == "__main__":
    get_all_links_of_articles_until_lastsaved_met()


