import requests



def main():
    url = "https://thecyberwire.com/newsletters/daily-briefing/14/97"
    response = requests.get(url)
    print(response.text)

    with open("test.html", "w") as file:
        file.write(response.text)

if __name__ == "__main__":
    main()