## a streamlit app to query postgresql database using natural language
import streamlit as st
import psycopg2
import pandas as pd
from psycopg2 import Error
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# Function to get response from Gemini API
def get_response(question, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content([prompt[0], question])
    return response.text.strip()

# Function to execute the SQL query
def execute_query(user, password, host, port, database, query):
    try:
        conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cursor = conn.cursor()
        print(f"Executing query: {query}")  # Debugging step
        cursor.execute(query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        conn.close()
        return result, column_names
    except Error as e:
        return f"Error: {e}", []

# Function to fetch table and column information
def fetch_db_schema(user, password, host, port, database):
    try:
        conn = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        schema_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """)
            columns = cursor.fetchall()
            column_info = [column[0] for column in columns]
            schema_info.append((table_name, column_info))
        conn.close()
        return schema_info
    except Error as e:
        return f"Error: {e}"

# Function to generate prompt based on schema
def generate_prompt(schema_info):
    prompt = "You are an expert in converting questions to SQL Query in multiple languages. The SQL database has the following tables:\n"
    for table, columns in schema_info:
        prompt += f"Table {table} with columns {', '.join(columns)}.\n"
    prompt += "\nFor example, if the question in English is: 'Show all records from the employee table' then the SQL command will be something like this: SELECT * FROM employee.\n"
    prompt += "If the question is in another language, first translate it to English and then convert it to the corresponding SQL query. Also, the SQL code should not have ``` in beginning or end and sql word in output."
    return prompt

# Streamlit app layout
st.title("Natural Language to SQL Query Executor for PostgreSQL")

# Taking user inputs
user = st.text_input("User")
password = st.text_input("Password", type="password")
host = st.text_input("Host")
port = st.text_input("Port", value="5432")
database = st.text_input("Database")
question = st.text_area("Natural Language Query")

if st.button("Execute"):
    if user and password and host and port and database and question:
        schema_info = fetch_db_schema(user, password, host, port, database)
        if isinstance(schema_info, str):
            st.error(schema_info)
        else:
            prompt = generate_prompt(schema_info)
            # st.write(f"Generated Prompt: {prompt}")

            # Get SQL query from Gemini API
            sql_query = get_response(question, [prompt])
            st.write(f"Generated SQL Query: {sql_query}")

            # Execute the SQL query
            result, column_names = execute_query(user, password, host, port, database, sql_query)
            if isinstance(result, str):
                st.error(result)
            else:
                # Converting the result to a DataFrame for better display
                df = pd.DataFrame(result, columns=column_names)
                st.dataframe(df)  # Displaying the result in a tabular format

                # Adding download button for CSV file
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='query_results.csv',
                    mime='text/csv',
                )
    else:
        st.error("Please provide all the details.")
