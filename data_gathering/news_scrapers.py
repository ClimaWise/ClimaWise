import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

from utils import get_body_text, get_url_soup


class LifegateScraper:
    def __init__(self, last_date: datetime.date, last_title: str):
        self.root_url = "https://www.lifegate.com/environment"
        self.search_url = self.root_url + "/page/{page}"
        self.last_date = last_date
        self.last_title = last_title
        self.scraping_done = False

    def scrape_article(self, article):
        """Scrape article to get its content"""
        # get title, url and date
        title_section = article.find(True, {"class": "card__title"})
        title = str(title_section.find("h3").contents[0])
        url = str(title_section["href"])
        date = datetime.datetime.strptime(
            article.find(True, {"class": "entry-date published"}).contents[0],
            "%d %B %Y",
        ).date()

        if (date < self.last_date) or (
            date == self.last_date and title == self.last_title
        ):
            self.scraping_done = True
            return [-1]

        # get article full text
        soup = get_url_soup(url)
        text = get_body_text(soup.find(True, {"class": "post__content editorial"}))
        # TODO: remove <p class="licence">

        return [date, title, url, text]

    def scrape_all(self):
        """Scrape all articles"""
        # query first page to get maximum number of pages
        soup = get_url_soup(self.root_url)
        last_page = int(soup.find(True, {"class": "last"}).contents[0])

        # loop over all the pages
        articles_list = []
        for page in range(1, last_page + 1):
            print(f"Scraping page {page} of {last_page}")

            try:
                if page > 1:
                    soup = get_url_soup(self.search_url.format(page=page))

                # scrape each article
                for article in soup.find_all("article"):
                    try:
                        article_out = self.scrape_article(article)
                        if self.scraping_done:
                            break

                        articles_list.append(article_out)
                    except Exception as e:
                        print("Article scraping failed:", e)
                        pass

            except Exception as e:
                print("Page scraping failed:", e)
                pass

            if self.scraping_done:
                break

        return pd.DataFrame(
            data=articles_list, columns=["date", "title", "url", "text"]
        )


class NasaScraper:
    def __init__(self, last_date: datetime.date, last_title: str):
        self.root_url = "https://climate.nasa.gov"
        self.search_url = (
            self.root_url
            + "/api/v1/news_items/?page={page}&per_page=40&order=publish_date+desc"
        )
        self.last_date = last_date
        self.last_title = last_title
        self.scraping_done = False

    def get_article(self, article):
        """Get article content from json response"""
        date = datetime.datetime.strptime(
            article["date"],
            "%B %d, %Y",
        ).date()
        title = article["title"]
        url = self.root_url + article["url"]
        text = get_body_text(BeautifulSoup(article["body"], "html.parser"))

        if (date < self.last_date) or (
            date == self.last_date and title == self.last_title
        ):
            self.scraping_done = True

        return [date, title, url, text]

    def scrape_all(self):
        """Scrape all articles"""
        # loop over pages until the given date
        page = 0
        articles_list = []
        while not self.scraping_done and page <= 100:
            print(f"Scraping page {page}")
            try:
                response = requests.get(self.search_url.format(page=page))

                # get articles from response json
                for article in response.json()["items"]:
                    article_out = self.get_article(article)
                    if self.scraping_done:
                        break

                    articles_list.append(article_out)

            except Exception as e:
                print("Page scraping failed:", e)

            page += 1

        return pd.DataFrame(
            data=articles_list, columns=["date", "title", "url", "text"]
        )


class BbcScraper:
    def __init__(self, last_date: datetime.date, last_title: str):
        self.root_url = "https://www.bbc.com"
        self.search_url = "https://push.api.bbci.co.uk/batch?t=%2Fdata%2Fbbc-morph-lx-commentary-data-paged%2Fabout%2Fe6369e45-f838-49cc-b5ac-857ed182e549%2Flimit%2F20%2FnitroKey%2Flx-nitro%2FpageNumber%2F{page}"
        self.last_date = last_date
        self.last_title = last_title
        self.scraping_done = False

    def scrape_article(self, article_json):
        """Scrape article to get its content"""
        date = datetime.datetime.strptime(
            article_json["dateAdded"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).date()
        title = article_json["title"]
        url = self.root_url + article_json["url"]

        if (date < self.last_date) or (
            date == self.last_date and title == self.last_title
        ):
            self.scraping_done = True
            return [-1]

        soup = get_url_soup(url)
        block_soups = soup.find_all("div", {"data-component": "text-block"})
        text = ""
        for s in block_soups:
            text += get_body_text(s)

        return [date, title, url, text]

    def scrape_all(self):
        """Scrape all articles"""
        # query first page to get maximum number of pages
        response_json = requests.get(self.search_url.format(page=1)).json()
        last_page = response_json["payload"][0]["body"]["numberOfPages"]

        # loop over all the pages
        articles_list = []
        for page in range(1, last_page + 1):
            print(f"Scraping page {page} of {last_page}")

            try:
                if page > 1:
                    response_json = requests.get(
                        self.search_url.format(page=page)
                    ).json()

                # scrape each article
                for i in range(20):
                    try:
                        article = response_json["payload"][0]["body"]["results"][i]
                        # scrape only articles (no videos or other)
                        if article["type"] == "STY":
                            article_out = self.scrape_article(article)
                            if self.scraping_done:
                                break

                            articles_list.append(article_out)
                    except Exception as e:
                        print("Article scraping failed:", e)
                        pass

            except Exception as e:
                print("Page scraping failed:", e)
                pass

            if self.scraping_done:
                break

        return pd.DataFrame(
            data=articles_list, columns=["date", "title", "url", "text"]
        )
