import os
import json
import re
import time

from model import get_embedding
import pinecone

pinecone.init(api_key="16a7a0ba-c9d6-44ce-9dd8-9a88d8643660", environment="us-east1-gcp")


def get_data(filename: str) -> tuple:
    final_data = ''
    with open(filename, "r", encoding='utf-8') as file:
        data = json.load(file)
        country_code = data["document_country_code"]
        date = data["document_date"]
        name = data["document_name"]
        url = data["document_url"]
        for item in data["text_blocks"]:
            if item["text"] != '':
                item["text"] = re.sub('\s+', ' ', item["text"])
                final_data = final_data + ' ' + item["text"].strip().encode('ascii', 'ignore').decode()

    return country_code, date, name, url, final_data

def upsert_into_pinecone(country_code, date, name, url, embedding):
    index = pinecone.Index("climawise")
    index.upsert([
        (name, embedding, {"date": date, "country_code": country_code, "url": url})
    ])


for dir_name in os.listdir('./data'):
    if dir_name == 'ALB':
        folder_path = os.path.join('./data', dir_name)
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.json'):
                country_code, date, name, url, full_text = get_data(os.path.join(folder_path, file_name))
                if len(full_text) > 0:
                    try:
                        time.sleep(1)  # this one is to avoid hitting RateLimitError error of 60/min
                        embedding = get_embedding(full_text, engine="text-similarity-babbage-001")
                        upsert_into_pinecone(country_code, date, name, url, embedding)
                    except Exception as E:
                        print(E)
                        time.sleep(30)
                        embedding = get_embedding(full_text, engine="text-similarity-babbage-001")
                        upsert_into_pinecone(country_code, date, name, url, embedding)

