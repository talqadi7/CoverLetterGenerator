import os
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
import pickle
from src.query_data import get_chain
import configparser
import queue
from langchain.callbacks.base import BaseCallbackHandler
import threading


class QueueCallbackHandler(BaseCallbackHandler):
    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.lock = threading.Lock()

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        with self.lock:
            self.message_queue.put(token)


class CoverLetterGenerator:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.cover_letter = ""
        config = configparser.ConfigParser()
        config.read("secrets.ini")
        self.lock = threading.Lock()

        if config.has_option("DEFAULT", "OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = config["DEFAULT"]["OPENAI_API_KEY"]
        else:
            raise ValueError("OPENAI_API_KEY is not found in secrets.ini")

        os.environ["GOOGLE_CSE_ID"] = config["DEFAULT"]["GOOGLE_CSE_ID"]
        os.environ["GOOGLE_API_KEY"] = config["DEFAULT"]["GOOGLE_API_KEY"]

        self.text_splitter = CharacterTextSplitter()
        self.vectorstore = None

    def load_documents(self):
        loaders = []
        data_dir = "Data"

        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            _, file_extension = os.path.splitext(file_path)

            if file_extension.lower() == ".txt":
                loaders.append(TextLoader(file_path))
            elif file_extension.lower() == ".pdf":
                loaders.append(PyPDFLoader(file_path))
        docs = []
        for loader in loaders:
            docs.extend(loader.load())
        documents = self.text_splitter.split_documents(docs)

        embeddings = OpenAIEmbeddings()
        self.vectorstore = FAISS.from_documents(documents, embeddings)
        with open("vectorstore.pkl", "wb") as f:
            pickle.dump(self.vectorstore, f)

    def embeddings_exists(self):
        """
        Check if the embeddings file exists.
        """
        return os.path.exists("vectorstore.pkl")

    def query(self, company_name, position, job_descript):
        with self.lock:
            if os.path.exists("vectorstore.pkl"):
                with open("vectorstore.pkl", "rb") as f:
                    self.vectorstore = pickle.load(f)
            else:
                self.load_documents()

            qa_chain = get_chain(self.vectorstore)
            # chat_history = []
            print("Chat with your docs!")
            query = (
                f"{position} at {company_name}. The job description is: {job_descript}"
            )
            print("Human: ", query)

            callback = QueueCallbackHandler(self.message_queue)
            # Use the custom handler to stream the response
            result = qa_chain.run(query, callbacks=[callback])

            self.cover_letter = result
            print("AI: ", self.cover_letter)
            return result

    def query_final(self):
        return self.cover_letter

    def get_streamed_messages(self):
        while True:
            msg = self.message_queue.get()
            yield msg

    if __name__ == "__main__":
        # main()
        pass
