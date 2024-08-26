# AI-QUERY-RESOLVER
This repository contains a streamlit app for querying any mysql/postgresql/mongodb database using natural language by leveraging the power of LLMs like GPT and GEMINI.
Combined.py contains a streamlit app that lets a user select a database among Mysql/ PostgreSQL/ MongoDB and query them using natural language.
test_llm1.py, test_llm2.py, test_llm3.py are individual streamlit app that lets a user query Mysql, PostgreSQL and MongoDB database using natural language respectively.

# Installation
To run this project in your laptop:
```sh
git clone git@github.com:riddhi-283/AI-QUERY-RESOLVER.git
```

# Setting-up the application

### Establishing connection 
Make sure that the database server (which you want to use) is running on your local machine while running this application.

### Setting up LLM model
Get your free google-api key from "makersuite.google.com"
<br> 
Create a .env file in the same folder and paste your google api key.
```sh
GOOGLE_API_KEY=''
```

### Running the application
```sh
pip install -r requirements.txt
streamlit run combined.py
```
<br>
