import requests
from bs4 import BeautifulSoup
from lxml import etree


def get_all_links_of_articles_until_lastsaved_met():
    # here the rss feed is being taken to be parsed | tutaj bierzemy rss feed do dalniejszego parsowania 
    url = "https://feeds.feedburner.com/TheHackersNews"
    response = requests.get(url)
    # parsing | parsowanie

    from bs4 import XMLParsedAsHTMLWarning
    import warnings
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

    soup = BeautifulSoup(response.text, "lxml")

    article_links = []
    for item in soup.select('item'):
        link_tag = item.find('link')
        if link_tag and link_tag.next_sibling:
            url = link_tag.next_sibling.strip()
            article_links.append(url)
    
    
    # getting the last saved link met | pobieranie ostatniego zapisanego linku
    with open("scrapers/thehackernews/lastsaved_articlelink.txt", "r") as file:
        lastsaved_articlelink = file.read()
    
    collected_links_list = []
    
    for link in article_links:
        if link == lastsaved_articlelink:
            break
        
        collected_links_list.append(link)

    if collected_links_list:
        lastsaved_articlelink = collected_links_list[0]

    with open("scrapers/thehackernews/lastsaved_articlelink.txt", "w") as file:
        file.write(lastsaved_articlelink)

    for link in collected_links_list:
        print(link)

    return collected_links_list



if __name__ == "__main__":
    get_all_links_of_articles_until_lastsaved_met()


