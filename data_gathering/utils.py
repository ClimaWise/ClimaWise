import re

import openai
import requests
from bs4 import BeautifulSoup


def get_url_soup(url: str):
    response = requests.get(url)
    return BeautifulSoup(response.content, "html.parser")


def get_body_text(soup: BeautifulSoup):
    text = ""
    for content in soup.find_all(["h2", "p"]):
        text += content.get_text() + " "
    return text


def get_embedding(text: str, engine="text-embedding-ada-002"):
    """It takes a string of text and returns embeddings for the text"""
    return openai.Embedding.create(input=[text], engine=engine)["data"][0]["embedding"]


def remove_emoji(text):
    """Remove emojis from text"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # chinese char
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)
