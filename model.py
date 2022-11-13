import numpy as np
import pandas as pd
import openai

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


class GeneralModel:
    def __init__(self):
        print("Model Intilization--->")
        # set_openai_key(API_KEY)

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
        return r

    def embedding_query(self, input):
        embedding_input = get_embedding(input, engine="text-similarity-babbage-001")

        df = pd.read_pickle("data/policies_embeddings.p")
        df["similarity"] = df["embedding"].apply(
            lambda x: cosine_similarity(x, embedding_input)
        )

        res = df.sort_values("similarity", ascending=False).head(5) # TODO: make this 5 variable?
        # df[df.country != country].sort_values("similarities", ascending=False) # TODO: display similar policies of different countries?

        return res.drop(columns=["embedding", "similarity"]).reset_index(drop=True)

    def model_prediction(self, task, input, api_key, temperature, question):
        """
        wrapper for the API to save the prompt and the result
        """
        if question:
            question = question.strip()

        # Setting the OpenAI API key got from the OpenAI dashboard
        set_openai_key(api_key)

        if task == "Embedding task":
            return self.embedding_query(input)
        else:
            return self.completion_query(task.format(input = input, question = question), myKwargs={"temperature":temperature})
