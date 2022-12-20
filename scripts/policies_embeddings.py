import os
import glob
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from model import get_embedding

def read_policy_radar_dataset(data_folderpath):

    pr_filepaths = glob.glob(data_folderpath + "/*/*.json", recursive=True)

    # read json of policies
    list_country, list_date, list_url, list_desc, list_name = [], [], [], [], []

    for filepath in pr_filepaths:

        try:
            with open(filepath, "r", encoding='utf-8') as f:
                f_json = json.load(f)

            list_country.append(f_json["document_country_code"])
            list_date.append(f_json["document_date"])
            list_name.append(f_json["document_name"])
            list_url.append(f_json["document_url"])
            list_desc.append(f_json["document_description"])

        except:
            print(f"Failed to read {filepath}")

    return pd.DataFrame({
        "country": list_country,
        "date": list_date,
        "name": list_name,
        "url": list_url,
        "desc": list_desc,
    })

if __name__ == "__main__":
    # read policy radar filepaths
    pr_data_folder = os.path.join(Path(os.getcwd()).parent, "open-data", "data")
    df = read_policy_radar_dataset(pr_data_folder)

    # exclude empty description policies
    df = df.loc[df.desc.str.len() > 0]

    # embed policy radar dataset
    df["embedding"] = np.nan
    df["embedding"] = df["embedding"].astype("object")

    for i, row in df.iterrows():
        print(f"{i+1}/{df.shape[0]}")
        try:
            time.sleep(1) # this one is to avoid hitting RateLimitError error of 60/min
            df.at[i, "embedding"] = get_embedding(row["desc"], engine="text-similarity-babbage-001")
        except:
            print("openai.error.RateLimitError raised - waiting 30 secs before retrying")
            time.sleep(30)
            df.at[i, "embedding"] = get_embedding(row["desc"], engine="text-similarity-babbage-001")

    df.to_pickle("data/policies_embeddings.p")
