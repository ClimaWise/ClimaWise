import datetime
import os.path
import re
import time

import pandas as pd
import pinecone
import requests
from bs4 import BeautifulSoup

from data_gathering.utils import get_body_text, get_url_soup
from model import get_embedding


class NewsScraper:
    def __init__(
        self, identifier: str, archive_folder: os.path, pinecone_index: pinecone.Index
    ):
        self.identifier = identifier
        self.archive_path = os.path.join(
            archive_folder, self.identifier + "_archive.pkl"
        )
        self.pinecone_index = pinecone_index
        self.set_archive()
        self.set_scraper()
        self.results = pd.DataFrame()

    def set_archive(self):
        """Read and set articles archive"""
        if os.path.isfile(self.archive_path):
            self.archive = pd.read_pickle(self.archive_path)
        else:
            self.archive = pd.DataFrame()

    def set_scraper(self):
        """Set appropriate scraper class"""
        if self.archive.empty:
            date, title = datetime.datetime(2015, 1, 1).date(), ""
        else:
            date, title = self.archive.iloc[0]["date"], self.archive.iloc[0]["title"]

        if self.identifier == "lifegate":
            self.scraper = LifegateScraper(date, title)
        elif self.identifier == "nasa":
            self.scraper = NasaScraper(date, title)
        elif self.identifier == "bbc":
            self.scraper = BbcScraper(date, title)
        else:
            raise Exception(f"Identifier {self.identifier} is not recognized")

    def start_scraper(self):
        """Start scraping"""
        print(f"Starting scraper of {self.identifier}...")
        self.results = self.scraper.scrape_all()
        print(f"Scraped {self.results.shape[0]} articles")

        # reset index to match with archive's
        archive_last_idx = self.archive.index.max()
        self.results = self.results.set_index(
            pd.RangeIndex(
                archive_last_idx + self.results.shape[0], archive_last_idx, -1
            )
        )

    def get_embeddings(self):
        """Get embeddings of the scraped articles"""
        print("Getting embeddings of scraped articles...")
        self.results = self.results.assign(embedding=None, id=None).astype("object")

        for count, (i, row) in enumerate(self.results.iterrows()):
            print(f"Embedding article {count + 1} of {self.results.shape[0]}")

            # get embedding
            try:
                try:
                    time.sleep(1)  # to avoid hitting RateLimitError error of 60/min
                    self.results.at[i, "embedding"] = get_embedding(
                        row.title + "/n" + row.text, engine="text-embedding-ada-002"
                    )
                except:
                    print("Embedding failed, waiting 60 seconds before retrying...")
                    time.sleep(60)
                    self.results.at[i, "embedding"] = get_embedding(
                        row.title + "/n" + row.text, engine="text-embedding-ada-002"
                    )

            except Exception as e:
                raise Exception(
                    f"Upsertion stopped at results index {i} because of failed embedding",
                    e,
                )

            # create a unique id
            self.results.at[i, "id"] = "_".join(
                [
                    self.identifier,
                    row.date.strftime("%Y%m%d"),
                    "".join(
                        [
                            w[0]
                            for w in re.sub(
                                r"[^a-z0-9 ]", "", row.title.lower()
                            ).split()
                        ]
                    ),
                ]
            )

    def update_archive(self):
        """Update archive with newly scraped articles"""
        if self.results.empty:
            print("Nothing to add to the archive")
        else:
            pd.concat([self.results, self.archive]).to_pickle(self.archive_path)
            print(f"Updated archive of {self.identifier} saved to pickle")

    def upsert_to_pinecone(self):
        """Upsert the embedding vectors into Pinecone"""
        vectors_to_upsert = []
        for _, row in self.results.iterrows():
            vectors_to_upsert.append(
                {
                    "id": row.id,
                    "values": row.embedding,
                    "metadata": {
                        "text": row.text,
                        "title": row.title,
                        "year": row.date.year,
                        "month": row.date.month,
                        "day": row.date.day,
                        "url": row.url,
                        "source": self.identifier,
                    },
                }
            )

        if len(vectors_to_upsert):
            self.pinecone_index.upsert(vectors=vectors_to_upsert, namespace="news")
            print(f"Upserted {len(vectors_to_upsert)} articles into Pinecone")
        else:
            print("Nothing to upsert to Pinecone")

    def run(self):
        """Run scraping, get embeddings, update local archive, and upsert them into Pinecone"""
        self.start_scraper()
        if self.results.empty:
            print(f"No results from scraping - ending run of {self.identifier}")
        else:
            self.get_embeddings()
            self.update_archive()
            self.upsert_to_pinecone()
            print(f"Run completed of {self.identifier}")


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
