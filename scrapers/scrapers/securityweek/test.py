import requests
from bs4 import BeautifulSoup



def test_security_week_scraper():
    url = 'https://www.securityweek.com/'
    response = requests.get(url)
    if response.status_code != 200:
        print('failed to retrieve the content')

    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    print(soup)

    with open('./test_output.html', 'w', encoding='utf-8') as file:
        file.write(soup.prettify())



if __name__ == '__main__':
    test_security_week_scraper()