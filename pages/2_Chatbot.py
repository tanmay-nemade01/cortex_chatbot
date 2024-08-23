# Import python packages
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import json
import time

# Get the current credentials
session = st.session_state['session']

ai_models = ('llama3-8b','llama3-70b','snowflake-arctic','reka-core','reka-flash','mistral-large','mixtral-8x7b','llama2-70b-chat','mistral-7b','gemma-7b','e5-base-v2','snowflake-arctic-embed-m','nv-embed-qa-4')
selected_model = st.selectbox('Select an AI Model',ai_models, index = ai_models.index('mistral-large') )

database_list = pd.DataFrame(session.sql('show databases;').collect())
database_list = database_list['name'].to_list()
database_list.insert(0,'')

query = ''

database = st.selectbox('select a Database to locate table details and column details table',tuple(database_list))
if database != '':
    schemas = pd.DataFrame(session.sql(f'show schemas in {database};').collect())
    schemas = schemas['name'].to_list()
    schemas.insert(0,'')
    schema = st.selectbox('Select a Schema Name',tuple(schemas))

if database != '' and schema != '':
    table_detail_prompt = []
    column_detail_prompt = []
    
    table_details = pd.DataFrame(session.sql(f'select * from {database}.{schema}.table_details;').collect())
    table_list = table_details['TABLE_NAME'].to_list()
    
    for i in range(len(table_list)):
        prompt = f"Description for table {table_details['TABLE_NAME'][i]} is {table_details['DESCRIPTION'][i]}"
        prompt = prompt.replace("'s",'')
        table_detail_prompt.append(prompt)
    
    column_details = pd.DataFrame(session.sql(f'select * from {database}.{schema}.COLUMN_DETAILS;').collect())
    for i in range(len(table_list)):
        prompt = f"Descriptions and example data for columns of table {table_details['TABLE_NAME'][i]} are "
        column_list_df = column_details[column_details['TABLE_NAME'] == table_list[i]].reset_index()
        column_list = column_list_df['COLUMN_NAME'].to_list()
        for j in range(len(column_list)):
            prompt = prompt + f"{column_list_df['COLUMN_NAME'][j]} - {column_list_df['COLUMN_TYPE'][j]} - {column_list_df['DESCRIPTION'][j]} - example - {column_list_df['EXAMPLE'][j]} "
        prompt = prompt.replace("'s",'')
        column_detail_prompt.append(prompt)
    
    
    
    instructions = '''You are a Snowflake developer who has to follow the following rules. 
    1. Generate one and only one Snowflake SQl query wherever requested.
    2. Please provide a short explaination of the SQL query as well
    3. Use only the provided tables and columns. 
    4. Do not use any table or column not provided to you.
    5. Include database name and schema wherever possible. 
    6. Strictly provide only one SQL query in your response.
    7. Modify SQL query depending on the datatype of the column, use quotes for string datatype.
    8. Remember all instructions in the chat history'''
    instructions = instructions + f"Database is {database}  and Schema is {schema}"
    for i in range(len(table_detail_prompt)):
        instructions = instructions + table_detail_prompt[i]
    for i in range(len(column_detail_prompt)):
        instructions = instructions + column_detail_prompt[i]
    # Details of table and fields can be found out in table sap_data.sap_data.llm_catalog"
    
    if "messages" not in st.session_state.keys():
        st.session_state.messages = []
        st.session_state.messages.append({'role': 'system', 'content': instructions})
        st.session_state.messages.append({'role': 'user', 'content': "Are you ready to answer few of my questions?"})
        st.session_state.messages.append({'role': 'assistant', 'content': "Sure. How can I help?"})

    
    # st.chat_message("user").write(prompt)
    temperature_set = {'temperature': 0.7,'max_tokens': 1000}
    for message in st.session_state.messages:
        if message['role'] == 'system':
            pass
        else:
            with st.chat_message(message["role"]):
              st.markdown(message["content"])
    prompt = st.chat_input('Write Your Question Here')
    if prompt:
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner(f"{selected_model} thinking..."):
            df = session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{selected_model}',{st.session_state.messages},{temperature_set}) as response;").collect()
            ai_response = str(df[0][0])
            # Parse the JSON string
            data_dict = json.loads(ai_response)
            # Extract the message
            ai_response = data_dict["choices"][0]["messages"]
            token_info = data_dict["usage"]
            if "```sql" in ai_response:
                indices = []
                for i in range(len(ai_response)-2):
                    if ai_response[i:i+3] == "```":
                        indices.append(i)
                query = ai_response[indices[0]+6:indices[1]]
            elif "```" in ai_response:
                indices = []
                for i in range(len(ai_response)-2):
                    if ai_response[i:i+3] == "```":
                        indices.append(i)
                query = ai_response[indices[0]+3:indices[1]]
                query = query.replace('vbnet','')
            ai_response = ai_response.replace("'",'')
            st.session_state.messages.append({'role': 'assistant', 'content': ai_response})

            if query != '' and "```" in ai_response:
                try:
                    output = session.sql(query).collect()
                    st.markdown('Result:')
                    st.table(output)
                except:
                    st.error('Something went wrong')
                with st.expander("See Explaination"):
                    st.write(ai_response)
                with st.expander("See Token Usage"):
                    token_info