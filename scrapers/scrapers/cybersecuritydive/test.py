import requests


def main(listlinks):
    base_url = "https://www.cybersecuritydive.com/"

    list_of_urls = []

    for linkhref in listlinks:
        url = base_url + linkhref
        list_of_urls.append(url)


    for index, url in enumerate(list_of_urls):
        response = requests.get(url)
        print(response.text)

        with open(f"scrapers/cybersecuritydive/test{index}.html", "w", encoding='utf-8') as file:
            file.write(response.text)





if __name__ == "__main__":
    listoflinks = [
        '/news/ransomware-extortion-bec-arctic-wolf/812321/',
        '/news/ransomware-attacks-it-food-sectors/812210/',
        '/news/critical-flaw-beyondtrust-remote-support-early-exploitation/812215/'
    ]
    main(listoflinks)