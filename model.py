import nltk
import numpy as np
import pandas as pd
import openai
import streamlit as st
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
from transformers import GPT2Tokenizer


def set_openai_key(key):
    """Sets OpenAI key."""
    openai.api_key = key


def get_embedding(text: str, engine="text-similarity-ada-001"):
    """
    It takes a string of text and returns embeddings for the text

    :param text: The text to embed
    :type text: str
    :param engine: The name of the engine to use, defaults to text-similarity-ada-001 (optional)
    :return: A list of floats.
    """
    # replace newlines, which can negatively affect performance.
    text = text.replace("\n", " ")

    return openai.Embedding.create(input=[text], engine=engine)["data"][0]["embedding"]


def cosine_similarity(a, b):
    """
    It takes two vectors, a and b, and returns the cosine of the angle between them

    :param a: the first vector
    :param b: the number of bits to use for the hash
    :return: The cosine similarity between two vectors.
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def get_chunks(str, max_chunk_length: int = 2000):
    nltk.download("punkt")
    sentences = nltk.sent_tokenize(str)
    sentence_lengths = list(map(count_tokens, sentences))
    chunks = []
    chunk = []
    chunk_len = 0
    for i in range(len(sentences)):
        if chunk_len + sentence_lengths[i] > max_chunk_length or i == len(sentences) - 1:
            chunks.append(' '.join(chunk))
            chunk = []
            chunk_len = 0
        else:
            chunk.append(sentences[i])
            chunk_len += sentence_lengths[i]
    print(
        f"Split {len(sentences)} sentences into {len(chunks)} chunks")
    return chunks


tokenizer = GPT2Tokenizer.from_pretrained('gpt2')


def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
@st.cache(suppress_st_warning=True, persist=True)
def completion_with_backoff(**kwargs):
    return openai.Completion.create(**kwargs)


def gen_keywords_for_chunks(chunks: list, temperature):
    keywords = set()
    for chunk in chunks:
        print('chunk ', type(chunk), temperature)
        keyword = gen_keywords(chunk, temperature)
        if keyword in keywords:
            continue
        keywords.add(keyword)
    return keywords


def keyword_chunking_query(input, temperature=0.85):
    text = open('assets/example_policy.txt', 'r').read()
    chunks = get_chunks(text)
    keywords = gen_keywords_for_chunks(chunks, temperature)
    return keywords


@st.cache(suppress_st_warning=True, persist=True)
def gen_keywords(
    chunk: str, temperature: int
) -> list:

    response = completion_with_backoff(
        model="text-davinci-002",
        prompt=f'I am a highly intelligent bot for policy analysis, specialized in climate change. If given an excerpt, I will extract a single key word from the excerpt. The key word must be relevant to the excerpt and/or common in the excerpt. If I cannot exctract a single key word from the excerpt, I will return "No keywords found"' f"\n###\nExcerpt:{chunk}\n###\n-",
        temperature=temperature,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    keyword = response["choices"][0]["text"].strip().split("\n")[0]

    return keyword


class GeneralModel:
    def __init__(self):
        print("Model Intilization--->")
        # set_openai_key(API_KEY)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
    @st.cache(suppress_st_warning=True, persist=True)
    def completion_query(self, prompt, myKwargs={}):
        """
        wrapper for the API to save the prompt and the result
        """

        # arguments to send the API
        kwargs = {
            "engine": "text-davinci-002",
            "temperature": 0.85,
            "max_tokens": 600,
            "best_of": 1,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop": ["###"],
        }

        for kwarg in myKwargs:
            kwargs[kwarg] = myKwargs[kwarg]

        r = openai.Completion.create(prompt=prompt, **kwargs)["choices"][0][
            "text"
        ].strip()
        # Add the initial hyphen, if it was in the prompt
        if prompt[-1] == '-':
            r = '-' + r
        return r.replace('-', '- ')

    def embedding_query(self, input, country, n_results):
        embedding_input = get_embedding(
            input, engine="text-similarity-babbage-001")

        df = pd.read_pickle("data/policies_embeddings.p")
        df["similarity"] = df["embedding"].apply(
            lambda x: cosine_similarity(x, embedding_input)
        )

        res = df.sort_values("similarity", ascending=False).drop(
            columns=["embedding", "similarity"])

        res_1 = res[res.country == country].head(n_results).reset_index(drop=True)
        res_2 = res[res.country != country].head(n_results).reset_index(drop=True)
        return [res_1, res_2]
    
    def success_based_on_similar(self, input, country, n_results=9):
        similar_policies = self.embedding_query(input, country, n_results)

        policy_names = []
        countries = []
        for df in similar_policies:
            policy_names.extend(df['name'].tolist())
            countries.extend(df['country'].tolist())

        verified_policy_names = []
        verified_countries = []
        for name, temp_country in zip(policy_names, countries):
            prompt = f"You're an climate change policy expert. Given a policy name and 3 letter code of country of it's origin, answer what you know about that policy. If nothing, instead of guessing, write \"NOTHING\".\nWhat do you know about {name} by {temp_country}?\n"
            result = self.completion_query(prompt, myKwargs={"temperature": 0.25})
            print('Prompt:\n', prompt)
            print('\n\nResult:\n', result)
            if 'NOTHING' not in result:
                verified_policy_names.append(name)
                verified_countries.append(country)
        if len(verified_countries) == 0:
            return "Can't make a certain prediction, sorry!"
        
        prompt = "You're an climate change policy expert. Your task is to predict whether a new policy will be successful, based on a list of policies (with their 3 letter code of country of origin), that the new policy is similar to. If you're unsure of the prediction, write \"DON'T KNOW\", otherwise predict whether it will be successful or not with a lengthy explanation to your answer, mention similar policies.\n\nThe new policy is most similar to:"
        for name, temp_country in zip(verified_policy_names, verified_countries):
            # TODO: Swap country code to normal country name - don't forget to change that in the prompt !!!
            prompt += f'\n- {name} - {temp_country}'
        prompt += '\n\nPredictions:'
        return self.completion_query(prompt, myKwargs={"temperature": 0.9})

    def faq_generation(self, input, temperature):
        prompt = f"You're an expert policymaker that specializes in climate change. Given the policy below, generate questions about it for a FAQ, but only if they're answerable based on the policy.\n\nPolicy:\n\"\"\"\"\"\"\n{input}\n\"\"\"\"\"\"\nQuestions:\n-"
        questions = self.completion_query(prompt, myKwargs={"temperature": temperature}).replace('-', '- ')

        prompt = f"You're an expert policymaker that specializes in climate change. Given the policy below and questions about it, answer them in order. If unsure about a question, reply with \"DON'T KNOW\" instead.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nQuestions:\n{questions}\nAnswers:\n-"
        answers = self.completion_query(prompt, myKwargs={"temperature": temperature})

        ordered_faq = ''
        for question, answer in zip(questions.split('\n'), answers.split('\n')):
            if answer != "DON'T KNOW":
                ordered_faq += question + '\n' + answer + '\n\n---\n'
        return ordered_faq

    def quote_co2_commitments(self, input, temperature):
        prompt = f"You're an expert policymaker that specializes in climate change. List up to 6 actions taken to reduce CO2 emission in the policy given below.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nActions taken:\n-"
        commitments = '- ' + self.completion_query(prompt, myKwargs={"temperature": temperature}).replace('-', '- ')

        prompt = f"You're an expert policymaker that specializes in climate change. List actions taken to reduce CO2 emission in the policy given below.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nActions taken:\n{commitments}\n\nFor each action taken, reference a single quote from the policy that confirms them:\n- \""
        quotes = '- "' + self.completion_query(prompt, myKwargs={"temperature": temperature})

        return quotes

    def sentiment_analysis(self, input, temperature):
        prompt = f"I am a highly intelligent bot for policy critique, specialized in climate change. Importantly, I also take into account the associated tweet's sentiment.\n\nIf you give me the topic of the policy, I'll provide a sentiment analysis in the general public, deciding whether a the sentiment is positive, neutral, or negative.\n\nText:\n{input}\n\nSentiment:\n"
        sentiment = self.completion_query(prompt, myKwargs={"temperature": temperature})

        return sentiment

    def summarization_finetuned(self,input,temperature):
        prompt = f"{input}\n\n###\n\n"
        r = openai.Completion.create(
            model="curie:ft-oai-hackathon-2022-team-35-2022-11-13-16-05-07",
            prompt=prompt,
            max_tokens=400,
            temperature=temperature,
            stop=['\n\n-->']
            )["choices"][0]["text"].strip()
        return r

    def model_prediction(self, task, input, api_key, temperature, question):
        """
        wrapper for the API to save the prompt and the result
        """
        if question:
            question = question.strip()

        # Setting the OpenAI API key got from the OpenAI dashboard
        set_openai_key(api_key)

        if task == "embedding_task":
            return self.embedding_query(input, question, temperature)
        elif task == "success_based_on_similar":
            return self.success_based_on_similar(input, question, temperature)
        elif task == "keyword_chunking_task":
            return keyword_chunking_query(input, temperature)
        elif task == "faq_generation":
            return self.faq_generation(input, temperature)
        elif task == "quote_co2_commitments":
            return self.quote_co2_commitments(input, temperature)
        elif task == "Sentiment Analysis":
            return self.sentiment_analysis(input, temperature)
        elif task == "summarization_finetuned":
            return self.summarization_finetuned(input,temperature)
        else:
            return self.completion_query(task.format(input=input, question=question), myKwargs={"temperature": temperature})

