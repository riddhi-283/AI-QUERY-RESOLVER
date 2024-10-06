## this is a complete streamlit app that lets us choose to work with any of the three (mysql,postgresql,mongodb) database
import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error
from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
from pymongo import MongoClient
import psycopg2
from psycopg2 import Error

load_dotenv()
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

def get_m_response(question, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content([prompt[0], question])
    return response.text.strip()

# Function to execute the SQL query
def execute_m_query(user, password, host, database, query):
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
def fetch_m_db_schema(user, password, host, database):
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
def generate_m_prompt(schema_info):
    prompt = "You are an expert in converting questions to SQL Query in multiple languages. The SQL database has the following tables:\n"
    for table, columns in schema_info:
        prompt += f"Table {table} with columns {', '.join(columns)}.\n"
    prompt += "\nFor example, if the question is in English: 'Which t-shirts have discounts on them?' then the SQL command will be something like this: SELECT t_shirts.* FROM t_shirts INNER JOIN discounts ON t_shirts.id = discounts.t_shirt_id.\n"
    prompt += "If the question is in another language, first translate it to English and then convert it to the corresponding SQL query. Also, the SQL code should not have ``` in beginning or end and sql word in output."
    return prompt


def get_mg_response(question, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content([prompt[0], question])
    
    # Post-process the response to ensure valid JSON
    query_str = response.text.strip()
    st.write(f"Raw response from Gemini API: {query_str}")  # Log the raw response
    if not query_str:
        raise ValueError("The generated query string is empty.")
    
    # Cleaning up the query string to make it valid JSON
    query_str = query_str.replace("{{", "{").replace("}}", "}")
    try:
        # Attempt to parse the JSON to catch any errors
        query_dict = json.loads(query_str)
    except json.JSONDecodeError:
        # Fix common issues such as missing quotes around keys
        query_str = query_str.replace("'", '"')
        query_str = query_str.replace(": ", '": "').replace(", ", '", "').replace("{ ", '{"').replace(" }", '"}')
        try:
            query_dict = json.loads(query_str)  # Attempt to parse again
        except json.JSONDecodeError as e:
            raise ValueError(f"please define your question properly.")
    
    return json.dumps(query_dict)  # Return the valid JSON string

# Function to execute the MongoDB query
def execute_mg_query(host, port, database, collection, query):
    try:
        # Creating a pymongo client
        client = MongoClient(host, int(port))
        # Getting the database instance
        db = client[database]
        # Getting the collection
        coll = db[collection]
        
        # Convert the query to use case-insensitive regex for string fields
        query = {k: {"$regex": f"^{v}$", "$options": "i"} if isinstance(v, str) else v for k, v in query.items()}
        st.write(f"Executing MongoDB Query: {query}")  # Log the query

        # Executing the query
        cursor = coll.find(query)
        
        # Converting cursor to a list of dictionaries
        result = list(cursor)
        
        # Extracting column names
        if result:
            columns = result[0].keys()
        else:
            columns = []

        return result, columns
    except Exception as e:
        return f"Error: {e}", []

# Function to fetch collection schema
def fetch_mg_collection_schema(host, port, database, collection):
    try:
        client = MongoClient(host, int(port))
        db = client[database]
        coll = db[collection]
        
        # Get sample documents to infer schema
        sample_doc = coll.find_one()
        if sample_doc:
            columns = list(sample_doc.keys())
        else:
            columns = []
        
        return columns
    except Exception as e:
        return f"Error: {e}"

# Function to generate prompt based on schema
def generate_mg_prompt(collection, columns):
    prompt = f"You are an expert in converting questions to MongoDB queries in multiple languages. The MongoDB collection '{collection}' has the following fields:\n"
    prompt += ', '.join(columns) + "\n\n"
    prompt += "For example, if the question in English is: 'Show all records' then the MongoDB query will be something like this: {{}}.\n"
    prompt += "Ensure that the MongoDB query is in valid JSON format with double quotes around keys and values. Don't change any field value, keep them all same, like dont add any extra letter,punctuation mark or ' in any field value.\n"
    prompt += "Also, you must take care of neccessary conversion of uppercase and lowercase in feild values entered by user upon searching for them in database, like if user entered : 'show all puma records' and in databse 'Puma' is present then make neccessary changes in the query to be generated.\n"
    prompt += " If the question is in another language, first translate it to English and then convert it into its following MongoDB query ensuring that the query is completely correct. Also, the MongoDB code should not have ``` in beginning or end and sql word in output."
    return prompt


def get_p_response(question, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content([prompt[0], question])
    return response.text.strip()

# Function to execute the SQL query
def execute_p_query(user, password, host, port, database, query):
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
def fetch_p_db_schema(user, password, host, port, database):
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
def generate_p_prompt(schema_info):
    prompt = "You are an expert in converting questions to SQL Query in multiple languages. The SQL database has the following tables:\n"
    for table, columns in schema_info:
        prompt += f"Table {table} with columns {', '.join(columns)}.\n"
    prompt += "\nFor example, if the question in English is: 'Show all records from the employee table' then the SQL command will be something like this: SELECT * FROM employee.\n"
    prompt += "If the question is in another language, first translate it to English and then convert it to the corresponding SQL query. Also, the SQL code should not have ``` in beginning or end and sql word in output."
    return prompt

def work_with_mysql():
        schema_info = fetch_m_db_schema(user, password, host, database)
        if isinstance(schema_info, str):
            st.error(schema_info)
        else:
            prompt = generate_m_prompt(schema_info)
            # st.write(f"Generated Prompt: {prompt}")

            # Get SQL query from Gemini API
            sql_query = get_m_response(question, [prompt])
            st.write(f"Generated SQL Query: {sql_query}")

            # Execute the SQL query
            result, column_names = execute_m_query(user, password, host, database, sql_query)
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

def work_with_mongodb():
        columns = fetch_mg_collection_schema(host, port, database, collection)
        if isinstance(columns, str):
            st.error(columns)
        else:
            prompt = generate_mg_prompt(collection, columns)
            # st.write(f"Generated Prompt: {prompt}")

            # Get MongoDB query from Gemini API
            try:
                mongo_query = get_mg_response(question, [prompt])
                st.write(f"Generated MongoDB Query: {mongo_query}")

                # Convert the generated query from string to dictionary
                query_dict = json.loads(mongo_query)

                # Execute the MongoDB query
                result, columns = execute_mg_query(host, port, database, collection, query_dict)
                if isinstance(result, str):
                    st.error(result)
                else:
                    # Converting the result to a DataFrame for better display
                    df = pd.DataFrame(result, columns=columns)
                    st.dataframe(df)  # Displaying the result in a tabular format
                    st.write(f"Result Count: {len(result)}")  # Display the number of results
                    # Adding download button for CSV file
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='query_results.csv',
                    mime='text/csv',
                )
            except (ValueError, json.JSONDecodeError) as e:
                st.error(f"Error processing the query: {e}")


def work_with_postsql():
        schema_info = fetch_p_db_schema(user, password, host, port, database)
        if isinstance(schema_info, str):
            st.error(schema_info)
        else:
            prompt = generate_p_prompt(schema_info)
            # st.write(f"Generated Prompt: {prompt}")

            # Get SQL query from Gemini API
            sql_query = get_p_response(question, [prompt])
            st.write(f"Generated SQL Query: {sql_query}")

            # Execute the SQL query
            result, column_names = execute_p_query(user, password, host, port, database, sql_query)
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

st.title("QUERY RESOLVER")
option = st.selectbox("Select Database Type", ["Select", "MySQL", "PostgreSQL", "MongoDB"])

if option == "MySQL":
    user = st.text_input("User")
    password = st.text_input("Password", type="password")
    host = st.text_input("Host")
    database = st.text_input("Database")
    question = st.text_area("Natural Language Query")

if option == "PostgreSQL":
    user = st.text_input("User")
    password = st.text_input("Password", type="password")
    host = st.text_input("Host")
    port = st.text_input("Port", value="5432")
    database = st.text_input("Database")
    question = st.text_area("Natural Language Query")

if option == "MongoDB":
    host = st.text_input("Host", value="localhost")
    port = st.text_input("Port", value="27017")
    database = st.text_input("Database")
    collection = st.text_input("Collection")
    question = st.text_area("Natural Language Query")


if st.button("Execute"):
    if option == "MySQL" and user and password and host and database and question:
        work_with_mysql()
    if option == "PostgreSQL" and user and password and host and port and database and question:
        work_with_postsql()
    if option == "MongoDB" and host and port and database and collection and question:
        work_with_mongodb()
    
    else:
        st.error("Please provide all correct details.")
         

