from snowflake.snowpark.session import Session
import pandas as pd
import streamlit as st

st.set_page_config(
    layout = "wide",
)

st.title('App Setup')

def connector_parameters():
    account = st.text_input('Enter Account',placeholder='evb84982',help='Enter Locator variable in account section')
    user = st.text_input('Enter Username')
    password = st.text_input('Enter Password',type ='password')
    conn = {
        "account":account,
        "user":user,
        "password":password,
        "role":'ACCOUNTADMIN',
        "warehouse":'COMPUTE_WH'
    }
    return conn

conn = connector_parameters()
if st.button('Login'):
    session = Session.builder.configs(conn).create()
    st.session_state['session'] = session
    st.success('Connection Successful')
    st.switch_page("pages/1_Setup_Database.py")

st.info('Default role selected is Accountadmin and default warehouse is COMPUTE_WH. Make sure you have access to both.')