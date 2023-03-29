from kaggle.api.kaggle_api_extended import KaggleApi
import os
import zipfile
import csv
import requests
from tqdm import tqdm
import json
import time

SAVE_DIR = './datasets/'

bearer_token = #
lookup_url = "https://api.twitter.com/2/tweets/"
query_params = {'tweet.fields': 'author_id,created_at,geo,lang,public_metrics,text'}
ids_per_request = 100

def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r


# Do a request with the given params on the given endpoint, return a json
def connect_to_endpoint(url, params):
    response = requests.get(url, auth=bearer_oauth, params=params)
    if response.status_code != 200:
        if response.status_code == 429: # Hit the 900/15 min limit
            time.sleep(60) # Wait a minute
            return connect_to_endpoint(url, params) # Try again
        else:
            raise Exception(response.status_code, response.text)
    return response.json()

def main():
    # Authentication
    api = KaggleApi()
    api.authenticate()

    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # Download the climate change datasets
    api.dataset_download_file('edqian/twitter-climate-change-sentiment-dataset',
                          file_name='twitter_sentiment_data.csv',
                          path=SAVE_DIR)
    api.dataset_download_file('deffro/the-climate-change-twitter-dataset',
                          file_name='The Climate Change Twitter Dataset.csv',
                          path=SAVE_DIR)

    # Unzip datasets
    for filename in os.listdir(SAVE_DIR):
        if filename[-4:] == '.zip':
            zip_path = os.path.join(SAVE_DIR, filename)
            with zipfile.ZipFile(zip_path)as f:
                f.extractall(SAVE_DIR)

    # Scrap tweet IDs
    ids = set()
    for filename in os.listdir(SAVE_DIR):
        if filename[-4:] != '.zip':
            with open(os.path.join(SAVE_DIR, filename), encoding="utf8") as f:
                reader = csv.DictReader(f)
                id_field_name = next((fn for fn in reader.fieldnames if 'id' in fn), None)

                for row in reader:
                    ids.add(row[id_field_name])

    with open("output_kaggle.jsonl") as f:
        json_lines = f.readlines()
        for line in json_lines:
            id = json.loads(line)['id']
            ids.remove(id)

    ids = list(ids)
    since_id = max(ids)
    params = query_params
        
    print(f'Got {len(ids)} tweets.')
    print(f'Latest id: {since_id}.')

    with open("output_kaggle.jsonl", "a") as f:
        for i in tqdm(range(0, len(ids), ids_per_request)):
            params['ids'] = ','.join(ids[i:min(len(ids), i + ids_per_request)])
            json_response = connect_to_endpoint(lookup_url, params)

            tweets = json_response['data']
            for tweet in tweets:
                f.write(json.dumps(tweet) + "\n")

if __name__ == '__main__':
    main()