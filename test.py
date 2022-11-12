

task_list = {
    "Summary":"{input}\n\nTl;dr",
    "Summary for 2nd Grade":"Summarize this for a second-grade student:\n\n{input}.",
    "Keywords Extraction":"Extract the most relevant keywords from the following text:\n\n{input}",
    "Bullet Points":"You're an expert policymaker that specializes in climate change. Given the policy below, generate questions about it for a FAQ, but only if they're answerable based on the policy.\n\nPolicy:\n\{input}\n\nQuestions:\n\n - ",
    "Questions Generation":"You're an expert policymaker that specializes in climate change. Given the policy below, generate questions about it for a FAQ, but only if they're answerable based on the policy.\n\nPolicy:\n\{input}\n\nQuestions:\n\n - ",
    "Criticize":"I am a highly intelligent bot for policy critique, specialized in climate change. Importantly, I also take into account the country that the policy is for. If you give me a country and a text that's a chunk of a policy related to climate change for that country, I'll generate critique for that text, trying to point out potential problems, risks, flaws and unintended consequences that such policy could cause. Then I'll propse changes to these issues, if I'll be sure of any. I'll end my critique with 'END' after I generate everything that I'm sure of.  Country: Great Britain.  Text:{input}" 
      }

display = list(task_list.keys())
print (display)

# options = list(range(len(display)))

options = list(task_list.values())

print (options)



# function to return key for any value
def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key
 
    return "key doesn't exist"

print(get_key(task_list,"{input}\n\nTl;dr"))



# a = task_list[options.index("Summary")]
# print(a)
# value = st.selectbox("Task", options, format_func=lambda x: display[x])

# print (value)