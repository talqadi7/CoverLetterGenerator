import json
import os
from langchain.agents.conversational.base import ConversationalAgent
from langchain.indexes import VectorstoreIndexCreator
from langchain.agents import load_tools, initialize_agent, AgentType, AgentExecutor
from langchain.document_loaders import TextLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma, FAISS
from langchain.text_splitter import CharacterTextSplitter
import pickle
from src.query_data import get_chain
from langchain.chains.summarize import load_summarize_chain

import configparser

def query(company_name, position, job_descript):
    # Create a new ConfigParser object
    config = configparser.ConfigParser()

    # Read the configuration file
    config.read('secrets.ini')
    
    os.environ["OPENAI_API_KEY"] = config['DEFAULT']['OPENAI_API_KEY']
    os.environ["GOOGLE_CSE_ID"] = config['DEFAULT']['GOOGLE_CSE_ID']
    os.environ["GOOGLE_API_KEY"] = config['DEFAULT']['GOOGLE_API_KEY']

    text_splitter = CharacterTextSplitter()

    loaders = []
    data_dir = 'Data'
    
    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)
        _, file_extension = os.path.splitext(file_path)
    
        if file_extension.lower() == '.txt':
            loaders.append(TextLoader(file_path))
        elif file_extension.lower() == '.pdf':
            loaders.append(PyPDFLoader(file_path))
    docs = []
    for loader in loaders:
        docs.extend(loader.load())
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
    documents = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)
    with open("vectorstore.pkl", "wb") as f:
        pickle.dump(vectorstore, f)

    with open("vectorstore.pkl", "rb") as f:
        vectorstore = pickle.load(f)
        qa_chain = get_chain(vectorstore)
        # chat_history = []
        print("Chat with your docs!")
        query = f"{position} at {company_name}. The job description is: {job_descript}"
        print("Human: ", query)
        result = qa_chain.run(query)

        # chat_history.append((result, result["answer"]))
        print("AI:", result)

        return result
    
if __name__ == "__main__":
    #main()
    pass
