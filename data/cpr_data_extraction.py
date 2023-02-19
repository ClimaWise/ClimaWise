import os
import json
import re
import time
import openai
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

openai.api_key = "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"
from model import get_embedding
import pinecone

pinecone.init(api_key="16a7a0ba-c9d6-44ce-9dd8-9a88d8643660", environment="us-east1-gcp")


# Check if it's only summary
def is_fulltext(filename: str) -> bool:
    with open(filename, "r", encoding='utf-8') as file:
        data = json.load(file)
        if len(data['text_blocks']) > 0:
            return True
        else:
            return False


# Chunking the text in p paragraphs. Do the histogram of paragraph dimensions
def get_fulltext_data(filename: str) -> tuple:
    with open(filename, "r", encoding='utf-8') as file:
        data = json.load(file)
        country_code = data["document_country_code"]
        date = data["document_date"]
        name = data["document_name"]
        url = data["document_url"]

        paragraphs = {}
        for item in data["text_blocks"]:
            p_value = item["text_block_id"].split("_")[0]
            text = item["text"]
            soup = BeautifulSoup(text, "html.parser")
            text_no_tags = soup.get_text()
            # if p_value in paragraphs:
            #     paragraphs[p_value].append(item["text"].strip().encode('ascii', 'ignore').decode())
            # else:
            #     paragraphs[p_value] = [item["text"].strip().encode('ascii', 'ignore').decode()]
            if p_value in paragraphs:

                paragraphs[p_value] += " " + text_no_tags.strip().replace("\n", " ").encode('ascii', 'ignore').decode()
            else:
                paragraphs[p_value] = text_no_tags.strip().replace("\n", " ").encode('ascii', 'ignore').decode()

    # paragraph_lengths = [len(paragraph) for paragraph in paragraphs.values()]
    #
    # # Plot a histogram of the paragraph lengths
    # plt.hist(paragraph_lengths, bins=range(0, 200, 10))
    # plt.title("Histogram of Paragraph Lengths")
    # plt.xlabel("Number of Characters")
    # plt.ylabel("Number of Paragraphs")
    # plt.show()

    return country_code, date, "fulltext_"+name, url, list(paragraphs.values())


def get_description(filename: str) -> tuple:
    with open(filename, "r", encoding='utf-8') as file:
        data = json.load(file)
        country_code = data["document_country_code"]
        date = data["document_date"]
        name = data["document_name"]
        url = data["document_url"]
        text = data["document_description"]
        soup = BeautifulSoup(text, "html.parser")
        text_no_tags = soup.get_text()
        description = text_no_tags.strip().replace("\n", " ").encode('ascii', 'ignore').decode()

    return country_code, date, "description"+name, url, description


def upsert_into_pinecone(country_code, date, name, url, text):
    index = pinecone.Index("climawise")
    try:
        if type(text) is list:
            for elem in text:
                time.sleep(1)
                embedding = get_embedding(elem, engine="text-similarity-babbage-001")
                index.upsert([(name, embedding, {"name": name, "date": date, "country_code": country_code, "url": url})])
        else:
            time.sleep(1)
            embedding = get_embedding(text, engine="text-similarity-babbage-001")
            index.upsert([(name, embedding, {"name": name, "date": date, "country_code": country_code, "url": url})])
    except Exception as E:
        print(E)
        time.sleep(30)
        if type(text) is list:
            for elem in text:
                time.sleep(1)
                embedding = get_embedding(elem, engine="text-similarity-babbage-001")
                index.upsert([(name, embedding, {"name": name, "date": date, "country_code": country_code, "url": url})])
        else:
            time.sleep(1)
            embedding = get_embedding(text, engine="text-similarity-babbage-001")
            index.upsert([(name, embedding, {"name": name, "date": date, "country_code": country_code, "url": url})])


for dir_name in os.listdir('./data'):
    if dir_name == 'ALB':
        folder_path = os.path.join('./data', dir_name)
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.json'):
                filename_path = os.path.join(folder_path, file_name)
                if is_fulltext(filename_path):
                    country_code, date, name, url, full_text = get_fulltext_data(filename_path)
                    #upsert_into_pinecone(country_code, date, name, url, full_text)
                    country_code, date, name, url, description = get_description(filename_path)
                    #upsert_into_pinecone(country_code, date, name, url, description)
                else:
                    country_code, date, name, url, description = get_description(filename_path)
                    #upsert_into_pinecone(country_code, date, name, url, description)
