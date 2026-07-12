from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
load_dotenv()  # load HEADLESS (from scrapers/.env) regardless of which entry point runs this
import functools
import time
from playwright.sync_api import sync_playwright, expect


# ---LOGGER SETUP ------------------------------------------------------------
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),  # Write logs to a file
        logging.StreamHandler(sys.stdout)  # stdout: stderr renders red in PyCharm (DYP-31)  # Print logs to the console
    ]
)

logger = logging.getLogger(__name__)
# -----------------------------------------------------------------------------


# ---RETRY DECORATOR ----------------------------------------------------------
def retry(exceptions=(Exception,), max_attempts=2, delay=1):
    """
    Retry decorator that retries the decorated function only when specific exceptions occur.
    
    Args:
        exceptions: Tuple of exception classes that should trigger retry
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
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
                    # For any other exceptions, don't retry
                    logger.error(f"Failed with non-retryable exception: {e}")
                    raise
        return wrapper
    return decorator


# custom exception
class AbsentAnchorElementException(Exception):
    pass



# MAIN FUNCTION 
@retry(exceptions=(AbsentAnchorElementException,), max_attempts=2, delay=1)
def get_all_links_of_articles_until_lastsaved_met():
    # here using simple requests is sufficient 
    url = "https://www.securityweek.com/"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.getenv("HEADLESS", "").lower() == "true")
        context = browser.new_context()
        page = context.new_page()
        try:
            page.goto(url)
            page.wait_for_load_state("load")
        except Exception as e:
            logger.critical(f"Failed to load page {url}: {e}")
            raise AbsentAnchorElementException(f"Failed to load page {url}: {e}") from e

        logger.debug("Page loaded, checking for popups.")
        
        try:
            close_btn = page.locator('button.pum-close')
            expect(close_btn).to_be_visible(timeout=5000)
            close_btn.highlight()
            close_btn.click()
            logger.debug("Closed the popup successfully.")
        except Exception as e: 
            logger.info("No ad popup appeared or failed to close popup: " + str(e))
            
        page.wait_for_load_state('load')

        html_content = page.content()
        browser.close()

    logger.debug("Page loaded successfully, proceeding to parse HTML content.")

    soup = BeautifulSoup(html_content, "html.parser")

    logger.debug("HTML content parsed successfully.")

    article_links = []

    articles_container = soup.select_one('div.wp-block-columns')    # the general containing all the sides (left, centre, right)

    logger.debug(f"Articles container found: {articles_container is not None}")

    articles_subcontainer = articles_container.select_one('div:nth-of-type(1)')    #  those are on the left side, potentially add those in the centre and maybe from the right side

    articles = articles_subcontainer.select('section')

    logger.debug(f"Number of articles found: {len(articles)}")
    
    for article in articles:
        link_element = article.select_one('a')
        logger.debug(f"Link element found: {link_element is not None}")
        if link_element:
            link = link_element.get('href')
            logger.info('found a link: ' + link)
            article_links.append(link)
        else:
            logger.warning(f"No link found in article")

    
    # getting the last saved link met | pobieranie ostatniego zapisanego linku
    with open("scrapers/securityweek/lastsaved_articlelink.txt", "r") as file:
        lastsaved_articlelink = file.read()
    
    collected_links_list = []
    
    for link in article_links:
        if link == lastsaved_articlelink:
            break
        
        collected_links_list.append(link)

    if collected_links_list:
        lastsaved_articlelink = collected_links_list[0]

    with open("scrapers/securityweek/lastsaved_articlelink.txt", "w") as file:
        file.write(lastsaved_articlelink)

    for link in collected_links_list:
        print(link)
        time.sleep(0.5)

    return collected_links_list






if __name__ == "__main__":
    get_all_links_of_articles_until_lastsaved_met()


