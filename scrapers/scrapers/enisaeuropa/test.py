import requests



def main():
    url = "https://www.enisa.europa.eu/news"
    response = requests.get(url)
    print(response.text)

    with open("enisa-europa/test.html", "w", encoding='utf-8') as file:
        file.write(response.text)

if __name__ == "__main__":
    main()