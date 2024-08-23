import streamlit as st
import pandas as pd

session = st.session_state['session']

databases = pd.DataFrame(session.sql('show databases;').collect())
database_list = tuple(databases['name'])
database = st.selectbox('Select a database to setup', database_list)

schemas = pd.DataFrame(session.sql(f'show schemas in {database};').collect())
schema_list = tuple(schemas['name'])
schema = st.selectbox('Select a schema to setup',schema_list)

