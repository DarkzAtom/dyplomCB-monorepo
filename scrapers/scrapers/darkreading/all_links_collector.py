import feedparser


def get_all_links_of_articles_until_lastsaved_met():
    # here the rss feed is being taken to be parsed | tutaj bierzemy rss feed do dalniejszego parsowania 
    url = "https://www.darkreading.com/rss.xml"
    feed = feedparser.parse(url)
    
    article_links = []
    for entry in feed.entries:
        if 'link' in entry:
            article_links.append(entry.link)
    
    
    # getting the last saved link met | pobieranie ostatniego zapisanego linku
    with open("scrapers/darkreading/lastsaved_articlelink.txt", "r") as file:
        lastsaved_articlelink = file.read()
    
    collected_links_list = []
    
    for link in article_links:
        if link == lastsaved_articlelink:
            break
        
        collected_links_list.append(link)

    if collected_links_list:
        lastsaved_articlelink = collected_links_list[0]

    with open("scrapers/darkreading/lastsaved_articlelink.txt", "w") as file:
        file.write(lastsaved_articlelink)

    for link in collected_links_list:
        print(link)

    return collected_links_list



if __name__ == "__main__":
    get_all_links_of_articles_until_lastsaved_met()


