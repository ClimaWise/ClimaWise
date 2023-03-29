import json
import time
import openai

TWEETS_DUMP = "./output_kaggle.jsonl" # Too big to put on Git
BATCH_SIZE = 100 # Recommended size for Pinecone

openai.api_key = "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"
import pinecone

pinecone.init(api_key="16a7a0ba-c9d6-44ce-9dd8-9a88d8643660", environment="us-east1-gcp")

def get_embeddings(texts, engine="text-embedding-ada-002"):
    """
    Input:
        List of texts and name of the engine (model) to create embeddings.
    Output:
        List of embeddings for each text in the input.
    """
    texts = [text.replace("\n", " ") for text in texts]
    return [data["embedding"] for data in openai.Embedding.create(input=texts, engine=engine)["data"]]

# TODO: Retry should probably be done with e.g. tenacity
def upsert_into_pinecone(items, namespace):
    """
    Upserts items list into the given namespace
    """
    index = pinecone.Index("climawise")
    try:
        time.sleep(1)
        index.upsert(items, namespace=namespace)
    except Exception as E:
        print(E)
        time.sleep(30)
        time.sleep(1)
        index.upsert(items, namespace=namespace)

def process_batch(tweets):
    """_summary_
    Input:
        List of dicts with tweet informations, format straight from the twitter API.
    """
    texts = [tweet['text'] for tweet in tweets]
    embeddings = get_embeddings(texts)
    for idx in range(len(tweets)):
        tweets[idx]['embedding'] = embeddings[idx]
    
    items = [(tweet['id'], tweet['embedding'], {"id": tweet['id'], "date": tweet['created_at'], "lang":  tweet['lang'], "author_id": tweet['author_id'], "source": "twitter", "retweet_count": tweet['public_metrics']['retweet_count'], "reply_count": tweet['public_metrics']['reply_count'], "like_count": tweet['public_metrics']['like_count'], "quote_count": tweet['public_metrics']['quote_count'], "impression_count": tweet['public_metrics']['impression_count']}) for tweet in tweets]

    upsert_into_pinecone(items, 'twitter')

# Sample upload
count_target = 5000
with open(TWEETS_DUMP) as f:
    count = 0
    tweets = []
    for line in f.readlines():
        tweet = json.loads(line)
        tweets.append(tweet)
        if len(tweets) == BATCH_SIZE:
            process_batch(tweets)
            tweets = []
        count += 1
        if count >= count_target and len(tweets) == 0:
            break