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
 
def policy_full_text(file_path:str):

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