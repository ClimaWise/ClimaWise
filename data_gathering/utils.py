import requests
from bs4 import BeautifulSoup


def get_url_soup(url: str):
    response = requests.get(url)
    return BeautifulSoup(response.content, "html.parser")


def get_body_text(soup: BeautifulSoup):
    text = ""
    for content in soup.find_all(["h2", "p"]):
        text += content.getText() + "\n"
    return text
