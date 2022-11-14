import json
import nltk
from transformers import GPT2Tokenizer

tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

# function to return key for any value


def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key
    return "key doesn't exist"


def policy_full_text(file_path: str):

    with open(file_path, encoding='utf-8') as f:
        policy_raw = json.load(f)
    text_blocks = policy_raw['text_blocks']
    policy_text = ''

    for idx, text_block in enumerate(text_blocks):
        id, text = text_block['text_block_id'], text_block['text']

        policy_text += text
    return policy_text


def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))


def get_chunks(text: str, max_chunk_length: int = 3500):
    sentences = nltk.sent_tokenize(text)
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
    return chunks


ref_task_list = {
    "Question Answering": "I am a highly intelligent bot for policy critique, specialized in climate change. Based on the policy text below, reference what sentence of the policy text can be used to answer the following question.\n\nPolicy text:{input}\n\nQuestion:\n{question}\n\nReference text in policy to answer the question:",
    "CO2 Reduction Commitments": "You're an expert policymaker that specializes in climate change. List actions taken to reduce CO2 emission in the policy given below.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nActions taken:\n{question}\n\nFor each action taken, reference a single quote from the policy that confirms them:\n- \"",
}


full_task_list = {
    # "Summary - Finetuned": "summarization_finetuned",
    # "Summary": "{input}\n\nTl;dr",
    "Summary": "summarization_finetuned",
    "Summary - simplified": "Summarize the following text for a second-grade student:\n\n{input}.\n",
    "The policy discusses...": "You're an expert policymaker specialized in climate change. Summarize the following policy text for a knowledgeable audience: {input}\n\nThe policy discusses",
    "Bullet Points": "You're an expert policymaker specialized in climate change. What are the 5 key points I should know about the policy below.\n\n{input}\n\n-",
    # "Bullet Points": "You're an expert policymaker specialized in climate change. Given the policy below, summarize its content in a bullet point list.\n\n{input}\n\n-",
    "Keywords Extraction": "You're an expert policymaker specialized in climate change. Extract the most relevant keywords from the following text:\n\n{input}\n-",
    "Questions Generation": "You're an expert policymaker that specializes in climate change. Given the policy below, generate questions about it for a FAQ, but only if they're answerable based on the policy.\n\nPolicy:\n\{input}\n\nQuestions:\n-",
    "Question Answering": "I am a highly intelligent bot for policy critique, specialized in climate change. Based on the policy text below, answer the following question.\n\nPolicy Text:{input}\n\nQuestion:\n\n{question}Answer:",
    "Question Answering w/reference": "I am a highly intelligent bot for policy critique, specialized in climate change. Based on the policy text below, reference what sentence of the policy text can be used to answer the following question.\n\nPolicy text:{input}\n\nQuestion:\n{question}\n\nReference text in policy to answer the question:",
    "FAQ Generation": "faq_generation",
    "Criticize": "I am a highly intelligent bot for policy critique, specialized in climate change. Importantly, I also take into account the country that the policy is for. If you give me a country and a text that's a chunk of a policy related to climate change for that country, I'll generate critique for that text, trying to point out potential problems, risks, flaws and unintended consequences that such policy could cause. Then I'll propose changes to these issues, if I'll be sure of any.\nCountry: Great Britain.\nText:\n{input}\n\nMy critique:\n",
    "Policy Section Draft from Outline": "I am a highly intelligent bot for policy generation, specialized in climate change. If given a few outline points, I will use my own knowledge of existing climate policy and the provided outline points to generate a full draft of a climate policy section. The generated section will be at least 5 sentences long and in paragraph form. The section I generate will be more comprehensive and prescriptive than the points.\n\Outline points:{input}\n\nPolicy section:",
    "Similar Policies": "embedding_task",
    "Success prediction based on similar policies": "success_based_on_similar",
    "CO2 Reduction Commitments": "You're an expert policymaker that specializes in climate change. List up to 6 actions taken to reduce CO2 emission in the policy given below.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nActions taken:\n-",
    "CO2 Reduction Commitment w/ reference": "You're an expert policymaker that specializes in climate change. List actions taken to reduce CO2 emission in the policy given below.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nActions taken:\n{question}\n\nFor each action taken, reference a single quote from the policy that confirms them:\n- \"",
    "Quote CO2 Reduction Commitments": "quote_co2_commitments",
    "Sentiment Analysis": "I am a highly intelligent bot for policy critique, specialized in climate change. Importantly, I also take into account the associated tweets sentiment.\nIf you give me a policy, I'll provide sentiment analysis, predicting what the sentiment of the public response to the policy will be.\n\nPolicy:\n{input}\n\nSentiment:\n",
}
