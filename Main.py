import streamlit as st
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from model import GeneralModel
import os

task_list = {
    "Summary":"{input}\n\nTl;dr",
    "Summary - Knowledgeable Audience":"You're an expert policymaker specialized in climate change. Summarize the following policy text for a knowledgeable audience: {input}\n\nThe policy discusses...",
    "Summary - 2nd Grade":"Summarize the following text for a second-grade student:\n\n{input}.",
    "Keywords Extraction":"You're an expert policymaker specialized in climate change. Extract the most relevant keywords from the following text:\n\n{input}",
    "Bullet Points":"You're an expert policymaker specialized in climate change. Given the policy below, summarize its content in a bullet point list.\n\n{input}\n\n-",
    "Questions Generation":"You're an expert policymaker that specializes in climate change. Given the policy below, generate questions about it for a FAQ, but only if they're answerable based on the policy.\n\nPolicy:\n\{input}\n\nQuestions:\n\n- ",
    "Criticize":"I am a highly intelligent bot for policy critique, specialized in climate change. Importantly, I also take into account the country that the policy is for. If you give me a country and a text that's a chunk of a policy related to climate change for that country, I'll generate critique for that text, trying to point out potential problems, risks, flaws and unintended consequences that such policy could cause. Then I'll propose changes to these issues, if I'll be sure of any. Country: Great Britain.  Text:{input} \n\n\ My critique:\n-", 
    "Question Answering": "I am a highly intelligent bot for policy critique, specialized in climate change. Based on the policy text below, answer the following question.\n\nPolicy Text:{input}\n\nQuestion:\n\n{question}Answer: "
      }
# You're an expert policymaker that specializes in climate change.Given the policy below and questions about it, answer them in order.If unsure about a question, reply with \'DONT KNOW\' instead.\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nQuestion:\n{question}
def app():

    # Creating an object of prediction service
    pred = GeneralModel()

    # Using the streamlit cache
    @st.cache
    def process_prompt(task, input, temperature, question=None):
        return pred.model_prediction(task = task, input=input.strip(), api_key=api_key, temperature=temperature, question=question)

    # with st.sidebar:
    #     api_key = st.sidebar.text_input("APIkey", type="password")

    # api_key = os.environ.get("OPENAI_KEY")
    api_key = st.secrets["OPENAI_KEY"]

    if api_key:
        #MAIN
        st.title("Climate Policy Copilot")
        s_example = """Industrial products are vital to life in the UK, from the fabric of our buildings to the materials we use in our daily life. Without manufacturing industry, there would be no cars, no COVID-19 vaccine, no food or the packaging it goes in. UK industries combine high end technology and highly skilled workers with ingenuity to make products that are traded all over the world. Industry plays an essential role in society, contributing £170 billion to the overall economy. It is a high value area of employment, directly accounting for 9% of the UK’s GDP and providing 2.6 million direct jobs (ONS, Annual Business Survey, 2020) as well as over 5 million jobs across the value chain (UK in a Changing Europe, Manufacturing and Brexit, 2020). These businesses are disproportionately important to regions outside the South East, providing well paid jobs in areas such as the North West, Yorkshire and South Wales. This strategy covers the full range of UK industry sectors: metals and minerals, chemicals, food and drink, paper and pulp, ceramics, glass, oil refineries and less energy-intensive manufacturing1 . It also covers the new emerging industries, which will be the hallmarks of the net zero transition, including low carbon hydrogen and carbon capture, usage and storage.\n\nThis strategy comes at a time of substantial economic challenge and decreased ability of companies to invest. COVID-19 has resulted in a fall in production output, exports, and turnover growth across many of our industries. In the short term, industry has been able to access a range of cross economy government support, and in the longer term we are pursuing a green response to this crisis, including through the actions detailed in this strategy. At the same time, there are significant positive changes taking place in the global fight against climate change, which will support industry’s net zero transition. In November 2021, the UK will host the 26th UN Climate Change Conference of Parties (COP26), through which we are committed to reaching a constructive, negotiated outcome that drives forward collective climate action globally in line with the temperature goal of the Paris Agreement. The UK is also implementing and negotiating new free trade agreements following our exit from the EU, growing our decarbonisation export and collaboration opportunities in turn.\n\nSupporting the sectors to reach net zero carbon emissions by 2050 will provide new opportunities to level up the economy across all nations and regions of the country. Enabling investment in decarbonised technologies can drive job creation and new inward investment in the UK, and create new markets for our manufacturers. Decarbonisation also creates challenges for industry. Many essential low carbon5 technologies are in earlier stages of development, and not yet deployed regularly at a commercial level. Low carbon manufacturing will also be more expensive for some sectors, leading to an increase in their costs, and therefore risking a reduction in their competitiveness. This creates a risk of “carbon leakage” (Chapter 2), which could impact both our domestic and global climate goals. We need to work with industry to overcome these barriers in the coming decades. Any action taken will need to be consistent with our international obligations, both under the Paris Agreement and wider international trade rules. To meet net zero, our modelling shows industrial emissions will need to fall by at least 90% by 2050 (Chapter 4), equivalent to taking all the cars off the roads today. Any remaining emissions will need to be offset by separate methods, such as planting trees and capturing carbon from the air. All industrial sectors will need to act to meet this challenge. We need to transform how industry uses energy and makes products, and rethink the way consumers buy industrial products."""
        # s_example = "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei."
        input = st.text_area(
            '',
            value=s_example,
            max_chars=8000,
            height=350,
        )
        
        #SIDEBAR 
        with st.sidebar:
            options = list(task_list.values())
            value = st.selectbox("Task", options, format_func=lambda x: get_key(task_list,x))

            temperature = st.slider('Temperature', 0.0, 1.0, 0.45)

            print(value)

            if (get_key(task_list,value)=='Question Answering'):
                question = st.text_input('Question:')
            else:
                question = None

            if st.button("Run"):
                with st.spinner(text="In progress"):
                    response_text = process_prompt(value, input,temperature, question)
                    st.markdown(response_text)
    else:
        st.error("🔑 Please enter API Key")


# function to return key for any value
def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key
    return "key doesn't exist"