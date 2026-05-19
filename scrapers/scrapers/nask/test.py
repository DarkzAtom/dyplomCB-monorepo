import requests



def main():
    url = "https://www.nask.pl/aktualnosci/fakty-nie-mity-nask-i-umb-wspolnie-przeciw-dezinformacji-medycznej"
    response = requests.get(url)
    print(response.text)

    with open("nask/test.html", "w", encoding='utf-8') as file:
        file.write(response.text)

if __name__ == "__main__":
    main()