
# we want to make an api request to openai

from openai import OpenAI
from dotenv import load_dotenv
import os
from mydb import NotAllowedQueryError, execute_query, get_schema

load_dotenv()

#my_key = os.getenv('OPENAI_API_KEY')
#print(my_key)
#client = OpenAI(api_key = my_key)

client = OpenAI()

schema = get_schema('orders')

while True: #indefinite loop

    user_input = input("Ask your question:") #Give me top 5 states by sales

    if user_input=='exit':
        break

    final_prompt = f''' generate the mysql SQL based on below schema 
    {schema}
    question: {user_input}

    Only give SQL.

    '''

    #print(final_prompt)

    response = client.responses.create(model = 'gpt-5.6-sol', input = final_prompt)

    #print(response.output_text)

    query = response.output_text
    print(query)

    try:
        result = execute_query(query)
        print(result)
    except NotAllowedQueryError as error:
        print(f"🚫 Not allowed: {error}")


    result = execute_query(query)

    
    print(result)

#streamlit





