## a streamlit app to query mongodb database using natural language
import streamlit as st
from pymongo import MongoClient
import pandas as pd
from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
import re

# Load environment variables
load_dotenv()
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# Function to get response from Gemini API
def get_response(question, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content([prompt[0], question])
    
    # Post-process the response to ensure valid JSON
    query_str = response.text.strip()
    st.write(f"Raw response from Gemini API: {query_str}")  
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
def execute_query(host, port, database, collection, query):
    try:
        # Creating a pymongo client
        client = MongoClient(host, int(port))
        # Getting the database instance
        db = client[database]
        # Getting the collection
        coll = db[collection]
        
        # Convert the query to use case-insensitive regex for string fields
        query = {k: {"$regex": f"^{v}$", "$options": "i"} if isinstance(v, str) else v for k, v in query.items()}
        st.write(f"Executing MongoDB Query: {query}") 

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
def fetch_collection_schema(host, port, database, collection):
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
def generate_prompt(collection, columns):
    prompt = f"You are an expert in converting questions to MongoDB queries in multiple languages. The MongoDB collection '{collection}' has the following fields:\n"
    prompt += ', '.join(columns) + "\n\n"
    prompt += "For example, if the question in English is: 'Show all records' then the MongoDB query will be something like this: {{}}.\n"
    prompt += "Ensure that the MongoDB query is in valid JSON format with double quotes around keys and values. Don't change any field value, keep them all same, like dont add any extra letter,punctuation mark or ' in any field value.\n"
    prompt += "Also, you must take care of neccessary conversion of uppercase and lowercase in feild values entered by user upon searching for them in database, like if user entered : 'show all puma records' and in databse 'Puma' is present then make neccessary changes in the query to be generated.\n"
    prompt += " If the question is in another language, first translate it to English and then convert it into its following MongoDB query ensuring that the query is completely correct. Also, the MongoDB code should not have ``` in beginning or end and sql word in output."
    return prompt

# Streamlit app layout
st.title("Natural Language to MongoDB Query Executor")

# Taking user inputs
host = st.text_input("Host", value="localhost")
port = st.text_input("Port", value="27017")
database = st.text_input("Database")
collection = st.text_input("Collection")
question = st.text_area("Natural Language Query")

if st.button("Execute"):
    if host and port and database and collection and question:
        columns = fetch_collection_schema(host, port, database, collection)
        if isinstance(columns, str):
            st.error(columns)
        else:
            prompt = generate_prompt(collection, columns)
            # st.write(f"Generated Prompt: {prompt}")

            # Get MongoDB query from Gemini API
            try:
                mongo_query = get_response(question, [prompt])
                st.write(f"Generated MongoDB Query: {mongo_query}")

                # Convert the generated query from string to dictionary
                query_dict = json.loads(mongo_query)

                # Execute the MongoDB query
                result, columns = execute_query(host, port, database, collection, query_dict)
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
    else:
        st.error("Please provide all the details.")
