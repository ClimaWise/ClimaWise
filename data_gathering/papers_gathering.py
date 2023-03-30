import io

import pandas as pd
import requests
from pdfminer.high_level import extract_text  # might become unnecessary

# define search parameters
KEYWORDS = ["climate", "change"]
ARTICLES_PER_SEARCH = 3  # must be less than 1000
ARTICLES_TOTAL = 3

# search for papers based on keywords (only papers with open access pdf)
search_url = "https://api.semanticscholar.org/graph/v1/paper/search?query={keywords}&limit={limit}&offset={offset}&openAccessPdf&fields=url,title,year,abstract,openAccessPdf"

offset = 0
article_results = []
while offset < ARTICLES_TOTAL:
    search_response = requests.get(
        search_url.format(
            keywords="+".join(KEYWORDS), limit=ARTICLES_PER_SEARCH, offset=offset
        )
    ).json()

    for article in search_response["data"]:
        # get corpus text from pdf
        article_response = requests.get(article["openAccessPdf"]["url"])
        pdf_file = io.BytesIO(article_response.content)
        pdf_text = extract_text(pdf_file)
        # TODO: extract only the corpus and not everything

        article_results.append(
            [article["year"], article["title"], article["url"], pdf_text]
        )

    offset = search_response["next"]

results = pd.DataFrame(data=article_results, columns=["year", "title", "url", "text"])
