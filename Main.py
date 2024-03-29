from model import GeneralModel
import streamlit as st
from model import GeneralModel
from support import get_chunks, policy_full_text, get_key, ref_task_list, full_task_list

st.session_state['key'] = False


if "ref" not in st.session_state:
    st.session_state.ref = False

# file_path = './data/Industrial_Decarbonisation_Strategy_10382.json'
# chunks = get_chunks(policy_full_text(file_path))

task_list = {
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
    # "Question Answering w/reference": "I am a highly intelligent bot for policy critique, specialized in climate change. Based on the policy text below, reference what sentence of the policy text can be used to answer the following question.\n\nPolicy text:{input}\n\nQuestion:\n{question}\n\nReference text in policy to answer the question:",
    "FAQ Generation": "faq_generation",
    "Criticize": "I am a highly intelligent bot for policy critique, specialized in climate change. Importantly, I also take into account the country that the policy is for. If you give me a country and a text that's a chunk of a policy related to climate change for that country, I'll generate critique for that text, trying to point out potential problems, risks, flaws and unintended consequences that such policy could cause. Then I'll propose changes to these issues, if I'll be sure of any.\nCountry: Great Britain.\nText:\n{input}\n\nMy critique:\n",
    "Policy Section Draft from Outline": "I am a highly intelligent bot for policy generation, specialized in climate change. If given a few outline points, I will use my own knowledge of existing climate policy and the provided outline points to generate a full draft of a climate policy section. The generated section will be at least 5 sentences long and in paragraph form. The section I generate will be more comprehensive and prescriptive than the points.\n\Outline points:{input}\n\nPolicy section:",
    "Similar Policies": "embedding_task",
    "Success prediction based on similar policies": "success_based_on_similar",
    "CO2 Reduction Commitments": "You're an expert policymaker that specializes in climate change. List up to 6 actions taken to reduce CO2 emission in the policy given below.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nActions taken:\n-",
    # "CO2 Reduction Commitment w/ reference": "You're an expert policymaker that specializes in climate change. List actions taken to reduce CO2 emission in the policy given below.\n\nPolicy:\n\"\"\"\n{input}\n\"\"\"\nActions taken:\n{question}\n\nFor each action taken, reference a single quote from the policy that confirms them:\n- \"",
    "Quote CO2 Reduction Commitments": "quote_co2_commitments",
    "Sentiment Analysis": "I am a highly intelligent bot for policy critique, specialized in climate change. Importantly, I also take into account the associated tweets sentiment.\nIf you give me a policy, I'll provide sentiment analysis, predicting what the sentiment of the public response to the policy will be.\n\nPolicy:\n{input}\n\nSentiment:\n",
}

country_list = [
    'AFG', 'AGO', 'ALB', 'AND', 'ARE', 'ARG', 'ARM', 'ATG', 'AUS', 'AUT', 'AZE', 'BDI', 'BEL', 'BEN', 'BFA', 'BGD', 'BGR', 'BHR',
    'BHS', 'BIH', 'BLR', 'BLZ', 'BOL', 'BRA', 'BRB', 'BRN', 'BTN', 'BWA', 'CAF', 'CAN', 'CHE', 'CHL', 'CHN', 'CIV', 'CMR', 'COD',
    'COG', 'COK', 'COL', 'COM', 'CPV', 'CRI', 'CUB', 'CYP', 'CZE', 'DEU', 'DJI', 'DMA', 'DNK', 'DOM', 'DZA', 'ECU', 'EGY', 'ERI',
    'ESP', 'EST', 'ETH', 'EUR', 'FIN', 'FJI', 'FRA', 'FSM', 'GAB', 'GBR', 'GEO', 'GHA', 'GIN', 'GMB', 'GNB', 'GNQ', 'GRC', 'GRD',
    'GTM', 'GUY', 'HND', 'HRV', 'HTI', 'HUN', 'IDN', 'IND', 'IRL', 'IRN', 'ISL', 'ISR', 'ITA', 'JAM', 'JOR', 'JPN', 'KAZ', 'KEN',
    'KGZ', 'KHM', 'KIR', 'KNA', 'KOR', 'KWT', 'LAO', 'LBN', 'LBR', 'LBY', 'LCA', 'LIE', 'LKA', 'LSO', 'LTU', 'LUX', 'LVA', 'MAR',
    'MCO', 'MDA', 'MDG', 'MDV', 'MEX', 'MHL', 'MKD', 'MLI', 'MLT', 'MMR', 'MNE', 'MNG', 'MOZ', 'MRT', 'MUS', 'MWI', 'MYS', 'NAM',
    'NER', 'NGA', 'NIC', 'NIU', 'NLD', 'NOR', 'NPL', 'NRU', 'NZL', 'OMN', 'PAK', 'PAN', 'PER', 'PHL', 'PLW', 'PNG', 'POL', 'PRK',
    'PRT', 'PRY', 'PSE', 'QAT', 'ROU', 'RUS', 'RWA', 'SAU', 'SDN', 'SEN', 'SGP', 'SLB', 'SLE', 'SLV', 'SMR', 'SOM', 'SRB', 'SSD',
    'SUR', 'SVK', 'SVN', 'SWE', 'SWZ', 'SYC', 'SYR', 'TCD', 'TGO', 'THA', 'TJK', 'TKM', 'TLS', 'TON', 'TTO', 'TUN', 'TUR', 'TUV',
    'TWN', 'TZA', 'UGA', 'UKR', 'URY', 'USA', 'UZB', 'VCT', 'VEN', 'VNM', 'VUT', 'WSM', 'XKX', 'YEM', 'ZAF', 'ZMB', 'ZWE',
]


class ResponseOutput:
    def __init__(self):
        self.responses = []
        self.tasks = []
        self.model = None
        self.api_key = None

    # Using the streamlit cache
    @st.cache
    def process_prompt(self, task, input, temperature, question):
        return self.model.model_prediction(
            task=task,
            input=input.strip(),
            api_key=self.api_key,
            temperature=temperature,
            question=question,
        )

    def get_response(self, input, task, temperature, question):
        response = self.process_prompt(
            task, input, temperature, question)

        self.responses.append(response)
        self.tasks.append(task)

    def stream_responses(self):

        for response, task in zip(self.responses[::-1], self.tasks[::-1]):
            st.markdown("***")
            st.subheader(get_key(full_task_list, task))

            if task == "embedding_task":
                st.caption("Same country")
                st.dataframe(response[0])
                st.caption("Other countries")
                st.dataframe(response[1])
            elif task == "keyword_chunking_task":
                for keyword in response:
                    st.markdown("- " + keyword)
            else:
                st.markdown(response)

    def clear_responses(self):
        self.responses = []
        self.tasks = []


output = ResponseOutput()


def change_ref():
    if "ref" not in st.session_state:
        st.session_state.ref = True

    if st.session_state.ref == True:
        st.session_state.ref = False
    else:
        st.session_state.ref = True


def app():

    # Creating an object of prediction service
    output.model = GeneralModel()

    with st.sidebar:
        output.api_key = st.sidebar.text_input("APIkey", type="password")

    # output.api_key = st.secrets["OPENAI_KEY"]

    if output.api_key:
        # MAIN
        st.title("Climate Policy Copilot 🤖")
        s_example = """Industrial products are vital to life in the UK, from the fabric of our buildings to the materials we use in our daily life. Without manufacturing industry, there would be no cars, no COVID-19 vaccine, no food or the packaging it goes in. UK industries combine high end technology and highly skilled workers with ingenuity to make products that are traded all over the world. Industry plays an essential role in society, contributing £170 billion to the overall economy. It is a high value area of employment, directly accounting for 9% of the UK’s GDP and providing 2.6 million direct jobs (ONS, Annual Business Survey, 2020) as well as over 5 million jobs across the value chain (UK in a Changing Europe, Manufacturing and Brexit, 2020). These businesses are disproportionately important to regions outside the South East, providing well paid jobs in areas such as the North West, Yorkshire and South Wales. This strategy covers the full range of UK industry sectors: metals and minerals, chemicals, food and drink, paper and pulp, ceramics, glass, oil refineries and less energy-intensive manufacturing1 . It also covers the new emerging industries, which will be the hallmarks of the net zero transition, including low carbon hydrogen and carbon capture, usage and storage.\n\nThis strategy comes at a time of substantial economic challenge and decreased ability of companies to invest. COVID-19 has resulted in a fall in production output, exports, and turnover growth across many of our industries. In the short term, industry has been able to access a range of cross economy government support, and in the longer term we are pursuing a green response to this crisis, including through the actions detailed in this strategy. At the same time, there are significant positive changes taking place in the global fight against climate change, which will support industry’s net zero transition. In November 2021, the UK will host the 26th UN Climate Change Conference of Parties (COP26), through which we are committed to reaching a constructive, negotiated outcome that drives forward collective climate action globally in line with the temperature goal of the Paris Agreement. The UK is also implementing and negotiating new free trade agreements following our exit from the EU, growing our decarbonisation export and collaboration opportunities in turn.\n\nSupporting the sectors to reach net zero carbon emissions by 2050 will provide new opportunities to level up the economy across all nations and regions of the country. Enabling investment in decarbonised technologies can drive job creation and new inward investment in the UK, and create new markets for our manufacturers. Decarbonisation also creates challenges for industry. Many essential low carbon5 technologies are in earlier stages of development, and not yet deployed regularly at a commercial level. Low carbon manufacturing will also be more expensive for some sectors, leading to an increase in their costs, and therefore risking a reduction in their competitiveness. This creates a risk of “carbon leakage” (Chapter 2), which could impact both our domestic and global climate goals. We need to work with industry to overcome these barriers in the coming decades. Any action taken will need to be consistent with our international obligations, both under the Paris Agreement and wider international trade rules. To meet net zero, our modelling shows industrial emissions will need to fall by at least 90% by 2050 (Chapter 4), equivalent to taking all the cars off the roads today. Any remaining emissions will need to be offset by separate methods, such as planting trees and capturing carbon from the air. All industrial sectors will need to act to meet this challenge. We need to transform how industry uses energy and makes products, and rethink the way consumers buy industrial products."""
        # s_example = "A neutron star is the collapsed core of a massive supergiant star, which had a total mass of between 10 and 25 solar masses, possibly more if the star was especially metal-rich.[1] Neutron stars are the smallest and densest stellar objects, excluding black holes and hypothetical white holes, quark stars, and strange stars.[2] Neutron stars have a radius on the order of 10 kilometres (6.2 mi) and a mass of about 1.4 solar masses.[3] They result from the supernova explosion of a massive star, combined with gravitational collapse, that compresses the core past white dwarf star density to that of atomic nuclei."
        input = st.text_area(
            '',
            value=s_example,
            max_chars=8000,
            height=350,
        )

        # SIDEBAR
        with st.sidebar:

            options = list(task_list.values())
            value = st.selectbox(
                "Task", options, format_func=lambda x: get_key(task_list, x))

            ref_placeholder = st.empty()
            ref_checkbox = ref_placeholder.checkbox("Reference", value=False,
                                                    key="disabled", disabled=True, help="Select this to request references from the input text.",
                                                    )

            if get_key(task_list, value) == 'Question Answering' or get_key(task_list, value) == 'CO2 Reduction Commitments':
                ref_placeholder.checkbox("Reference", value=False,
                                         key="enabled", disabled=False, on_change=change_ref, help="Select this to request references from the input text.",
                                         )

            if get_key(task_list, value) == 'Similar Policies':
                temperature = st.slider(
                    'Number of similar policies to show', 0, 5, 3)
            elif get_key(task_list, value) == 'Success prediction based on similar policies':
                temperature = st.slider(
                    'Number of similar policies to base on', 0, 5, 3)
            else:
                # TODO: Experiment with default temperatures more
                temperature = 0.45
                if get_key(task_list, value) in ["Sentiment Analysis", "FAQ Generation", "Questions Generation"]:
                    temperature = 0.8
                elif get_key(task_list, value) == "Criticize":
                    temperature = 0.9
                elif get_key(task_list, value) in ["CO2 Reduction Commitments", "CO2 Reduction Commitment Ref", "Quote CO2 Reduction Commitments"]:
                    temperature = 0.25

                temperature = st.slider('Temperature', 0.0, 1.0, temperature)

            if ((get_key(task_list, value) == 'Question Answering') | (get_key(task_list, value) == 'Question Answering w/reference')):
                question = st.text_input('Question:')
            elif get_key(task_list, value) == 'CO2 Reduction Commitment Ref':
                question = st.text_input('Commitment:')
            elif get_key(task_list, value) in ['Similar Policies', 'Success prediction based on similar policies']:
                question = st.selectbox(
                    "Country of policy being written", country_list)
            else:
                question = None

            if st.button("Run 🧠"):
                with st.spinner(text="In progress"):
                    if (get_key(task_list, value) in ["Question Answering", "CO2 Reduction Commitments"] and st.session_state.ref == True):
                        output.get_response(
                            input, ref_task_list[get_key(task_list, value)], temperature, question)
                    else:
                        output.get_response(
                            input, value, temperature, question)

            if st.button("Clear ✂️"):
                output.clear_responses()

            output.stream_responses()

    else:
        st.error("🔑 Please enter API Key")
