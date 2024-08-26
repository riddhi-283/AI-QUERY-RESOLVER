import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
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
def execute_query(user, password, host, database, query):
    try:
        conn = mysql.connector.connect(user=user, password=password, host=host, database=database)
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            column_names = [i[0] for i in cursor.description]
            conn.close()
            return result, column_names
    except Error as e:
        return f"Error: {e}", []

# Function to fetch table and column information
def fetch_db_schema(user, password, host, database):
    try:
        conn = mysql.connector.connect(user=user, password=password, host=host, database=database)
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s", (database,))
            tables = cursor.fetchall()
            schema_info = []
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
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
    prompt += "\nFor example, if the question is in English: 'Which t-shirts have discounts on them?' then the SQL command will be something like this: SELECT t_shirts.* FROM t_shirts INNER JOIN discounts ON t_shirts.id = discounts.t_shirt_id.\n"
    prompt += "If the question is in another language, first translate it to English and then convert it to the corresponding SQL query. Also, the SQL code should not have ``` in beginning or end and sql word in output."
    return prompt

# Streamlit app layout
st.title("Natural Language to SQL Query Executor")

# Taking user inputs
user = st.text_input("User")
password = st.text_input("Password", type="password")
host = st.text_input("Host")
database = st.text_input("Database")
question = st.text_area("Natural Language Query")

if st.button("Execute"):
    if user and password and host and database and question:
        schema_info = fetch_db_schema(user, password, host, database)
        if isinstance(schema_info, str):
            st.error(schema_info)
        else:
            prompt = generate_prompt(schema_info)
            # st.write(f"Generated Prompt: {prompt}")

            # Get SQL query from Gemini API
            sql_query = get_response(question, [prompt])
            st.write(f"Generated SQL Query: {sql_query}")

            # Execute the SQL query
            result, column_names = execute_query(user, password, host, database, sql_query)
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
