import datetime
import os.path
import re
import time

import openai
import pandas as pd
import pinecone
import tiktoken
from dotenv import load_dotenv

from constants import OPENAI_MODEL, OPENAI_TOKENS_LIMIT, PINECONE_ENV, PINECONE_INDEX
from exceptions import APIKeyNotFoundError
from news_scrapers import BbcScraper, LifegateScraper, NasaScraper
from utils import get_embedding, remove_emoji

# import secrets from .env file
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class NewsGatherer:
    """Gatherer class for news data feed"""

    _supported_sources = {
        "lifegate": LifegateScraper,
        "nasa": NasaScraper,
        "bbc": BbcScraper,
    }

    # Common metadata fields
    _supported_metadata_fields = [
        "text", "year", "month", "day", "url", "title", "lang", "keywords"
    ]

    def __init__(self, archive_folder: os.path):
        self._identifier = None
        self._scraper = None
        self._archive_folder = archive_folder
        self.archive = pd.DataFrame()
        self.results = pd.DataFrame()

        # set pinecone API
        if PINECONE_API_KEY is None:
            raise APIKeyNotFoundError(
                "Pinecone API key must be set as an environment variable"
            )
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        self._pinecone_index = pinecone.Index(PINECONE_INDEX)

        # set openai API
        if OPENAI_API_KEY is None:
            raise APIKeyNotFoundError(
                "OpenAI API key must be set as an environment variable"
            )
        openai.api_key = OPENAI_API_KEY

        # Adding source specific metadata fields
        self._supported_metadata_fields.extend(["source"])

    def set_source(self, identifier: str):
        """Set source by setting the relative articles archive and scraper class"""

        self._identifier = identifier

        # set archive
        self._archive_path = os.path.join(
            self._archive_folder, self._identifier + "_archive.pkl"
        )
        if os.path.isfile(self._archive_path):
            self.archive = pd.read_pickle(self._archive_path)
            date, title = self.archive.iloc[0]["date"], self.archive.iloc[0]["title"]
        else:
            self.archive = pd.DataFrame()
            date, title = datetime.datetime(2015, 1, 1).date(), ""

        # set scraper class
        if self._identifier not in self._supported_sources.keys():
            raise Exception(f"Source identifier {self._identifier} is not supported")
        else:
            self._scraper = self._supported_sources[self._identifier](
                last_date=date, last_title=title
            )

    def chunk_text(self, mask):
        """Chunk text in smaller parts"""
        # TODO: apply the actual chunking - for now too long articles are skipped
        self.results = self.results[~mask]

    def parse_data(self):
        """Cleaning of texts and chunking if needed"""

        # remove particular spacings
        self.results["text"] = (
            self.results["text"]
            .str.replace("\n", " ")
            .str.replace("\xa0", " ")
            .str.replace("\u200b", "")
        )

        # remove emojis
        self.results["text"].apply(lambda x: remove_emoji(x))

        # apply chunking if needed
        mask_chunking_needed = self.results["text"].apply(
            lambda x: len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(x))
            > OPENAI_TOKENS_LIMIT
        )
        if any(mask_chunking_needed):
            self.chunk_text(mask_chunking_needed)

        # Preprocessing of date and source, TODO: Move it elsewhere?
        # Extract year, month, day out of date field
        if 'date' in self.results:
            # Assuming the date is dateutils.date type
            self.results['year'] = self.results['date'].apply(lambda x: x.year)
            self.results['month'] = self.results['date'].apply(lambda x: x.month)
            self.results['day'] = self.results['date'].apply(lambda x: x.day)
        
        # Add source column
        self.results['source'] = self._identifier

    def start_scraper(self):
        """Run scraping from the current source and uniform the output"""
        print(f"Starting scraper of {self._identifier}...")
        self.results = self._scraper.scrape_all()
        print(f"Scraped {self.results.shape[0]} articles")

        self.parse_data()

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
                        row.title + " " + row.text, engine=OPENAI_MODEL
                    )
                except:
                    print("Embedding failed, waiting 60 seconds before retrying...")
                    time.sleep(60)
                    self.results.at[i, "embedding"] = get_embedding(
                        row.title + " " + row.text, engine=OPENAI_MODEL
                    )

            except Exception as e:
                raise Exception(
                    f"Embedding failed at results index {i} after {count+1} succeeded embeddings",
                    e,
                )

            # create a unique id
            self.results.at[i, "id"] = "_".join(
                [
                    self._identifier,
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
            pd.concat([self.results, self.archive]).to_pickle(self._archive_path)
            print(f"Updated archive of {self._identifier} saved to pickle")

    def upsert_to_pinecone(self):
        """Upsert the embedding vectors into Pinecone"""
        vectors_to_upsert = []

        columns_to_upsert = [col for col in self.results.columns.values \
                             if col in self._supported_metadata_fields]

        for _, row in self.results.iterrows():
            vectors_to_upsert.append(
                {
                    "id": row['id'],
                    "values": row["embedding"],
                    "metadata": {col: row[col] for col in columns_to_upsert}
                }
            )

        if len(vectors_to_upsert):
            self._pinecone_index.upsert(vectors=vectors_to_upsert, namespace="news")
            print(f"Upserted {len(vectors_to_upsert)} articles into Pinecone")
        else:
            print("Nothing to upsert to Pinecone")

    def run(self):
        """Run scraping, get embeddings, update local archive, and upsert them into Pinecone"""
        if self._identifier is None:
            raise Exception("Source is not set yet")

        self.start_scraper()
        if self.results.empty:
            print(f"No results from scraping - ending run of {self._identifier}")
        else:
            self.get_embeddings()
            self.update_archive()
            self.upsert_to_pinecone()
            print(f"Run completed of {self._identifier}")

    def run_all(self):
        """Call self.run for each supported source"""
        for identifier in self._supported_sources.keys():
            self.set_source(identifier)
            self.run()
