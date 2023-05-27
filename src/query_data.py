from langchain.prompts.prompt import PromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.question_answering import load_qa_chain


template = """You're a cover letter writer expert. You are given a company name, position, job description, and resume information.

Please follow the following steps: DON'T make up any information or an answer. Any information should be coming directly from my resume or my cover letters. You don't have to tackle every point in the job description. Focus on my most recent experience.

Write me professional and targeted cover letter for a {question}.
=========
{context}
=========
Cover Letter:"""
QA_PROMPT = PromptTemplate(template=template,
                           input_variables=["context", "question"])


def get_chain(vectorstore):
    llm = ChatOpenAI(temperature=0.0)
    
    chain_type_kwargs = {"prompt": QA_PROMPT}
    qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff",
                                     retriever = vectorstore.as_retriever(),
                                     chain_type_kwargs=chain_type_kwargs)

    return qa_chain
