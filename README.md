# AI-QUERY-RESOLVER
This repository contains a streamlit app for querying any mysql/postgresql/mongodb database using natural language by leveraging the power of GEMINI-PRO Model.
Combined.py contains a streamlit app that lets a user select a database among Mysql/ PostgreSQL/ MongoDB and query them using natural language.
test_llm1.py, test_llm2.py, test_llm3.py are individual streamlit app that lets a user query Mysql, PostgreSQL and MongoDB database using natural language respectively.

# Screenshots
![Screenshot 2024-10-06 213854](https://github.com/user-attachments/assets/ccd1c30b-2e2e-4247-9c81-3bbfe1b744ac)

![Screenshot 2024-10-06 214445](https://github.com/user-attachments/assets/c7813150-9ebc-4189-9a2d-b46b40013431)
![Screenshot 2024-10-06 214455](https://github.com/user-attachments/assets/edd5fd3c-fc2b-4013-a44b-f32f5e2b25b9)

![Screenshot 2024-10-06 220529](https://github.com/user-attachments/assets/18e0f841-44d8-413d-abdb-80827d60f6fb)

![Screenshot 2024-10-06 220556](https://github.com/user-attachments/assets/8e101ddb-626c-4e1c-86c5-6d60d23d6a3d)
![Screenshot 2024-10-06 215640](https://github.com/user-attachments/assets/b2af2c68-be50-46b3-a173-54c9ff1284a8)
![Screenshot 2024-10-06 215653](https://github.com/user-attachments/assets/f1f011e9-a81a-40af-8ca2-fd4b9415680f)




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
