import requests



def main():
    url = "https://sekurak.pl"
    response = requests.get(url)
    print(response.text)

    with open("sekurak/test.html", "w", encoding='utf-8') as file:
        file.write(response.text)

if __name__ == "__main__":
    main()