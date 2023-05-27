from langchain.prompts.prompt import PromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import ChatVectorDBChain
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


template = """You're a cover letter writer expert. You are given a company name, position, job description, and resume information.
Focusing on my most recent experience, please write me a professional and targeted cover letter. You don't have to tackle every point in the job description.


DON'T make up any information or an answer. Any information should be coming directly from my resume or my cover letters. If I am not qualified enough or don't have the skills for certain points in the job description, ignore them.
Question: {question}
=========
{context}
=========
Answer in Markdown:"""
QA_PROMPT = PromptTemplate(template=template, input_variables=["question", "context"])


def get_chain(vectorstore):
    llm = ChatOpenAI(model_name = 'gpt-3.5-turbo', temperature=0.15)
    qa_chain = ChatVectorDBChain.from_llm(
        llm,
        vectorstore,
        qa_prompt=QA_PROMPT
    )
    qa_chain.run()
    return qa_chain
