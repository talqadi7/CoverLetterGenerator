import os
import pickle
import queue
import threading
import datetime
import logging
import configparser
import json
import openai
from src.query_data import generate_cover_letter

logging.basicConfig(level=logging.INFO)

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Build the path to the secrets file
secrets_file = os.path.join(script_dir, "../secrets.ini")


class MessageStreamHandler:
    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.lock = threading.Lock()

    def handle_chunk(self, chunk):
        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
            content = chunk.choices[0].delta.content
            if content:
                with self.lock:
                    self.message_queue.put(content)


class CoverLetterGenerator:
    def __init__(self):
        self.reset()

    def load_documents(self):
        """
        Load documents from the Data directory and store their content,
        categorized by document type
        """
        documents = {
            "resume": [],
            "cover_letter": [],
            "other": []
        }
        data_dir = "Data"
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            return documents

        for filename in os.listdir(data_dir):
            file_path = os.path.join(data_dir, filename)
            _, file_extension = os.path.splitext(file_path)
            
            # Skip directories, only process files
            if not os.path.isfile(file_path):
                continue

            try:
                content = ""
                # Extract content based on file type
                if file_extension.lower() == ".txt":
                    logging.info(f"Loading text file: {file_path}")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                elif file_extension.lower() == ".pdf":
                    logging.info(f"Loading PDF file: {file_path}")
                    # Placeholder for PDF content extraction
                    content = f"[PDF content from {file_path}]"
                elif file_extension.lower() == ".docx":
                    logging.info(f"Loading DOCX file: {file_path}")
                    # Placeholder for DOCX content extraction
                    content = f"[DOCX content from {file_path}]"
                else:
                    logging.warning(f"Unsupported file format: {file_path}")
                    continue
                
                # Categorize document based on filename prefix
                if filename.startswith("resume"):
                    documents["resume"].append({
                        "content": content,
                        "source": file_path
                    })
                    logging.info(f"Added {file_path} as resume document")
                elif filename.startswith("cover_letter"):
                    documents["cover_letter"].append({
                        "content": content, 
                        "source": file_path
                    })
                    logging.info(f"Added {file_path} as cover letter sample")
                else:
                    documents["other"].append({
                        "content": content,
                        "source": file_path
                    })
                    logging.info(f"Added {file_path} as other document")
                    
            except Exception as e:
                logging.error(f"Error loading file {file_path}: {e}")

        # Save the categorized documents for later use
        with open("documents.pkl", "wb") as f:
            pickle.dump(documents, f)

        return documents

    def documents_exist(self):
        """
        Check if the documents file exists.
        """
        return os.path.exists("documents.pkl")

    def query(self, company_name, position, job_descript, user_name, user_address, user_email):
        with self.lock:
            if self.is_running:
                return
            self.is_running = True

        self.company_name = company_name
        self.user_name = user_name
        self.user_address = user_address
        self.user_email = user_email

        try:
            with self.lock:
                # Load or create the documents
                if os.path.exists("documents.pkl"):
                    with open("documents.pkl", "rb") as f:
                        documents = pickle.load(f)
                else:
                    documents = self.load_documents()

                # Separate documents by type
                resume_text = "\n\n".join([doc["content"] for doc in documents["resume"]]) if documents["resume"] else ""
                cover_letter_samples = "\n\n===NEXT SAMPLE===\n\n".join([doc["content"] for doc in documents["cover_letter"]]) if documents["cover_letter"] else ""
                other_docs = "\n\n".join([doc["content"] for doc in documents["other"]]) if documents["other"] else ""
                
                # Combine resume and other documents as context
                context_text = ""
                if resume_text:
                    context_text += "RESUME:\n" + resume_text + "\n\n"
                if other_docs:
                    context_text += "ADDITIONAL INFORMATION:\n" + other_docs
                
                # Format the input query
                input_query = f"Date: {datetime.date.today().strftime('%Y-%m-%d')}, {position}, {company_name}, Job Description: \n {job_descript}"
                logging.info(f"Human: {input_query}")

                # Create the handler for streaming
                stream_handler = MessageStreamHandler(self.message_queue)

                # Call the function to generate the cover letter with streaming
                self.cover_letter = generate_cover_letter(
                    input_query,
                    context_text,
                    cover_letter_samples,
                    user_name,
                    user_address,
                    user_email, 
                    stream=True, 
                    stream_handler=stream_handler
                )

                logging.info(f"AI: {self.cover_letter}")
                self.message_queue.put("END")
                return self.cover_letter

        finally:
            self.is_running = False

    def query_final(self):
        return self.cover_letter

    def reset(self):
        self.message_queue = queue.Queue()
        self.cover_letter = ""
        self.company_name = ""
        self.user_name = ""
        self.user_address = ""
        self.user_email = ""
        config = configparser.ConfigParser()
        config.read(secrets_file)
        self.lock = threading.Lock()
        self.is_running = False

        if config.has_option("DEFAULT", "OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = config["DEFAULT"]["OPENAI_API_KEY"]
        else:
            raise ValueError("OPENAI_API_KEY is not found in secrets.ini")

        os.environ["GOOGLE_CSE_ID"] = config["DEFAULT"]["GOOGLE_CSE_ID"]
        os.environ["GOOGLE_API_KEY"] = config["DEFAULT"]["GOOGLE_API_KEY"]

    def get_streamed_messages(self):
        while True:
            msg = self.message_queue.get()
            yield msg
            if msg == "END":
                logging.info("I found the END.")
                self.message_queue = queue.Queue()
                break

if __name__ == "__main__":
    # main()
    pass