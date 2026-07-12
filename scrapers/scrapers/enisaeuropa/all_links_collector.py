import requests
from bs4 import BeautifulSoup
import functools
import time


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
    url = "https://www.enisa.europa.eu/news"
    
    # fetching the the content

    try:
        response = requests.get(url)
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise

    if response.status_code == 200:
        html_content = response.text

    logger.debug("Page loaded successfully, proceeding to parse HTML content.")

    soup = BeautifulSoup(html_content, "html.parser")

    with open('scrapers/enisaeuropa/news_page.html', 'w', encoding='utf-8') as file:
        file.write(soup.prettify())

    logger.debug("HTML content parsed successfully.")

    article_links = []

    articles_container = soup.select_one('div.publications-list')

    logger.debug(f"Articles container found: {articles_container is not None}")

    articles = articles_container.select('div.publications-item')

    logger.debug(f"Number of articles found: {len(articles)}")
    
    for article in articles:
        link_element = article.select_one('a')
        logger.debug(f"Link element found: {link_element is not None}")
        if link_element:
            link = link_element.get('href')
            article_links.append(link)
            logger.info(f'link found: {link}')
        else:
            logger.warning(f"No link found in article")
    
    # getting the last saved link met | pobieranie ostatniego zapisanego linku
    with open("scrapers/enisaeuropa/lastsaved_articlelink.txt", "r") as file:
        lastsaved_articlelink = file.read()
    
    collected_links_list = []
    
    for link in article_links:
        if link == lastsaved_articlelink:
            break
        
        link = 'https://enisa.europa.eu' + link # robimy pelny link | making a full link

        collected_links_list.append(link.strip())

    if collected_links_list:
        lastsaved_articlelink = collected_links_list[0]

    with open("scrapers/enisaeuropa/lastsaved_articlelink.txt", "w") as file:
        file.write(lastsaved_articlelink)

    logger.info('collected links')
    
    for link in collected_links_list:
        print(link)

    return collected_links_list






if __name__ == "__main__":
    get_all_links_of_articles_until_lastsaved_met()


