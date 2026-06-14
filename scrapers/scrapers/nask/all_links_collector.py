import os
import requests
from bs4 import BeautifulSoup
import functools
import time
from playwright.sync_api import sync_playwright


# ---LOGGER SETUP ------------------------------------------------------------
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),  # Write logs to a file
        logging.StreamHandler()  # Print logs to the console
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

        # Filter only links that contain the article paths
        if href and ('/aktualnosci/' in href):
            # Build the full URL (since the hrefs are relative)
            full_url = f"https://www.nask.pl{href}"
            if full_url not in article_links:
                article_links.append(full_url)

    # Print the extracted links
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


