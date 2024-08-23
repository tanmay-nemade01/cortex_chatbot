import streamlit as st
import pandas as pd
from pathlib import Path

session = st.session_state['session']

databases = pd.DataFrame(session.sql('show databases;').collect())
database_list = list(databases['name'])
database_list.insert(0,'')
database = st.selectbox('Select a database to setup', database_list)

if database != '':
    schemas = pd.DataFrame(session.sql(f'show schemas in {database};').collect())
    schema_list = list(schemas['name'])
    schema_list.insert(0,'')
    schema = st.selectbox('Select a schema to setup',schema_list)


if database != '' and schema != '':
    with st.status("Setting Up Database...", expanded=True) as status:
        st.write("Gathering required data...")
        main_path = Path(__file__).parents[1]
        column_details = main_path / "setup_files/COLUMN_DETAILS.csv"
        with open(column_details,"r") as c:
            column_details_table = pd.read_csv(c)
            column_details_table = pd.DataFrame(column_details_table)

        table_details = main_path / "setup_files/TABLE_DETAILS.csv"
        with open(table_details,"r") as t:
            table_details_table = pd.read_csv(t)
            table_details_table = pd.DataFrame(table_details_table)

        data_table = main_path / "setup_files/DATA_TABLE.csv"
        with open(data_table,"r") as d:
            data_table_data = pd.read_csv(d)
            data_table_data = pd.DataFrame(data_table_data)
        st.write("Creating required objects...")

        setup_file = main_path / "setup_files/setup_sql.txt"
        with open(setup_file,"r") as s:
            setup_script = s.read()
        setup_script = setup_script.replace('{database}.{schema}',f'{database}.{schema}')
        setup_sql = setup_script.split(';')

        for i in range(3):
            setup = session.sql(setup_sql[i]).collect()
        
        st.write("Setting up required tables...")
        session.write_pandas(
            df = column_details_table,
            table_name = 'COLUMN_DETAILS',
            database = database,
            schema = schema,
            overwrite = True
        )
        st.write("Uploading sample data...")
        session.write_pandas(
            df = table_details_table,
            table_name = 'TABLE_DETAILS',
            database = database,
            schema = schema,
            overwrite = True
        )
        st.write("Finishing up...")
        session.write_pandas(
            df = data_table_data,
            table_name = 'DATA_TABLE',
            database = database,
            schema = schema,
            overwrite = True
        )
        status.update(
        label="Setup Complete. Proceed to the chatbot", state="complete", expanded=False
    )


