import os
import json
import shutil
import time
import zipfile
import openai
import requests
from bs4 import BeautifulSoup
from model import get_embedding
import pinecone
from langcodes import Language

openai.api_key = "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"
pinecone.init(api_key="16a7a0ba-c9d6-44ce-9dd8-9a88d8643660", environment="us-east1-gcp")


class CprScraper:
    GITHUB_API = "https://api.github.com"
    REPO_OWNER = "climatepolicyradar"
    REPO_NAME = "open-data"
    TOKEN = "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"
    FILE_NAME = "commit_hash.txt"

    def __init__(self, token):
        self.token = token

    def get_commit_hash(self):
        url = f"{self.GITHUB_API}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/commits"
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)

        if response.status_code == 200:
            return data[0]["sha"]
        else:
            print(f"Error: Unable to fetch commit hash. Status code {response.status_code}")
            return None

    def read_commit_hash_from_file(self):
        if os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, "r") as file:
                return file.read().strip()
        return None

    def write_commit_hash_to_file(self, commit_hash):
        with open(self.FILE_NAME, "w") as file:
            file.write(commit_hash)

    def download_and_extract_repo(self):
        url = f"{self.GITHUB_API}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/zipball"
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open("repo.zip", "wb") as file:
                file.write(response.content)

            with zipfile.ZipFile("repo.zip", "r") as zip_ref:
                zip_ref.extractall("repo")

            os.remove("repo.zip")
            repo_folder = os.path.join("repo", os.listdir("repo")[0])
            src_data_folder = os.path.join(repo_folder, "data")
            dest_data_folder = "data"
            if os.path.exists(dest_data_folder):
                shutil.rmtree(dest_data_folder)
            shutil.move(src_data_folder, dest_data_folder)
            shutil.rmtree('repo')
        else:
            print(f"Error: Unable to download repo. Status code {response.status_code}")


class PineconeDataUploader:
    GITHUB_API = "https://api.github.com"
    REPO_OWNER = "climatepolicyradar"
    REPO_NAME = "open-data"
    FILE_NAME = "commit_hash.txt"

    def __init__(self, token):
        self.token = token
        self.index = pinecone.Index("climawise")

    def get_commit_hash(self):
        url = f"{self.GITHUB_API}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/commits"
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)

        if response.status_code == 200:
            return data[0]["sha"]
        else:
            print(f"Error: Unable to fetch commit hash. Status code {response.status_code}")
            return None

    def read_commit_hash_from_file(self):
        if os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, "r") as file:
                return file.read().strip()
        return None

    def write_commit_hash_to_file(self, commit_hash):
        with open(self.FILE_NAME, "w") as file:
            file.write(commit_hash)

    def download_and_extract_repo(self):
        url = f"{self.GITHUB_API}/repos/{self.REPO_OWNER}/{self.REPO_NAME}/zipball"
        headers = {"Authorization": f"token {self.token}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            with open("repo.zip", "wb") as file:
                file.write(response.content)

            with zipfile.ZipFile("repo.zip", "r") as zip_ref:
                zip_ref.extractall("repo")

            os.remove("repo.zip")
            repo_folder = os.path.join("repo", os.listdir("repo")[0])
            src_data_folder = os.path.join(repo_folder, "data")
            dest_data_folder = "data"
            if os.path.exists(dest_data_folder):
                shutil.rmtree(dest_data_folder)
            shutil.move(src_data_folder, dest_data_folder)
            shutil.rmtree('repo')
        else:
            print(f"Error: Unable to download repo. Status code {response.status_code}")

    def is_fulltext(self, filename: str) -> bool:
        with open(filename, "r", encoding='utf-8') as file:
            data = json.load(file)
            if len(data['text_blocks']) > 0:
                return True
            else:
                return False

    def get_fulltext_data(self, filename: str) -> tuple:
        with open(filename, "r", encoding='utf-8') as file:
            data = json.load(file)
            country_code = data["document_country_code"]
            date = data["document_date"]
            name = data["document_name"]
            url = data["document_url"]
            lang = Language.find(data["document_language"]).to_tag()
            keywords = data["document_keyword"]

            paragraphs = {}
            for item in data["text_blocks"]:
                p_value = item["text_block_id"].split("_")[0]
                text = item["text"]
                soup = BeautifulSoup(text, "html.parser")
                text_no_tags = soup.get_text()

                if p_value in paragraphs:
                    paragraphs[p_value] += " " + text_no_tags.strip().replace("\n", " ").encode('ascii', 'ignore').decode()
                else:
                    paragraphs[p_value] = text_no_tags.strip().replace("\n", " ").encode('ascii', 'ignore').decode()

        return country_code, date, "fulltext_" + name, url, list(paragraphs.values()), lang, keywords

    def get_description(self, filename: str) -> tuple:
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
            lang = Language.find(data["document_language"]).to_tag()
            keywords = data["document_keyword"]

        return country_code, date, "description_" + name, url, description, lang, keywords

    def upsert_into_pinecone(self, country_code, date, name, url, text, lang, keywords):
        year = date.split("/")[2]
        month = date.split("/")[1]
        day = date.split("/")[0]
        words = name.split()
        first_three_letters = words[0][0].lower() + words[1][0].lower() + words[2][0].lower()
        id = "cpr_" + year + month + day + "_" + first_three_letters

        try:
            if isinstance(text, list):
                for elem in text:
                    time.sleep(1)
                    embedding = get_embedding(elem, engine="text-embedding-ada-002")
                    self.index.upsert([(name + "_" + str(text.index(elem)), embedding,
                                        {"id": id + "_p" + str(text.index(elem)), "text": text, "year": year,
                                         "month": month, "day": day, "url": url, "title": name, "lang": lang,
                                         "keywords": keywords, "country code": country_code})],
                                        namespace='policies')
            else:
                time.sleep(1)
                embedding = get_embedding(text, engine="text-embedding-ada-002")
                self.index.upsert([(name, embedding,
                                    {"id": id + "_dsc", "text": text, "year": year, "month": month, "day": day,
                                     "url": url, "title": name, "lang": lang, "keywords": keywords,
                                     "country code": country_code})],
                                    namespace='policies')
        except Exception as E:
            print(E)
            time.sleep(30)
            if isinstance(text, list):
                for elem in text:
                    time.sleep(1)
                    embedding = get_embedding(elem, engine="text-embedding-ada-002")
                    self.index.upsert([(name + "_" + str(text.index(elem)), embedding,
                                        {"id": id + "_p" + str(text.index(elem)), "text": text, "year": year,
                                         "month": month, "day": day, "url": url, "title": name, "lang": lang,
                                         "keywords": keywords, "country code": country_code})],
                                        namespace='policies')
            else:
                time.sleep(1)
                embedding = get_embedding(text, engine="text-embedding-ada-002")
                self.index.upsert([(name, embedding,
                                    {"id": id + "_dsc", "text": text, "year": year, "month": month, "day": day,
                                     "url": url, "title": name, "lang": lang, "keywords": keywords,
                                     "country code": country_code})],
                                    namespace='policies')

    def upload_data(self):
        commit_hash = self.get_commit_hash()
        last_commit_hash = self.read_commit_hash_from_file()

        if commit_hash and commit_hash != last_commit_hash:
            self.download_and_extract_repo()
            data_folder = "data"

            for filename in os.listdir(data_folder):
                if filename.endswith(".json"):
                    filepath = os.path.join(data_folder, filename)

                    if self.is_fulltext(filepath):
                        country_code, date, name, url, text, lang, keywords = self.get_fulltext_data(filepath)
                        self.upsert_into_pinecone(country_code, date, name, url, text, lang, keywords)
                    else:
                        country_code, date, name, url, description, lang, keywords = self.get_description(filepath)
                        self.upsert_into_pinecone(country_code, date, name, url, description, lang, keywords)

            self.write_commit_hash_to_file(commit_hash)
            shutil.rmtree(data_folder)
        else:
            print("No new commits to process.")