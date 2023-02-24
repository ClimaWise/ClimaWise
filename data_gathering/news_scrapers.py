import requests
import datetime
import os.path
from bs4 import BeautifulSoup
import pandas as pd
from utils import get_url_soup, get_body_text


class NewsScraper:
    # TODO: add function to embed articles and push to Pinecone
    def __init__(self, identifier: str, archive_folder: os.path):
        self.identifier = identifier
        self.archive_path = os.path.join(
            archive_folder, self.identifier + "_archive.pkl"
        )
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
        else:
            raise Exception(f"Identifier {self.identifier} is not recognized")

    def start_scraper(self):
        """Start scraping"""
        print(f"Starting scraper of {self.identifier}...")
        self.results = self.scraper.scrape_all()
        print(f"Scraping of {self.results.shape[0]} articles completed")

    def update_archive(self):
        """Update archive with newly scraped articles"""
        if self.scraper.scraping_done:
            pd.concat([self.results, self.archive]).reset_index(drop=True).to_pickle(
                self.archive_path
            )
            print(f"Updated archive of {self.identifier} saved to pkl")
        else:
            print("Scraping has not been done yet")


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
        while not self.scraping_done or page > 100:

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
