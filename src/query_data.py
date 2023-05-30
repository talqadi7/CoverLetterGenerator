from langchain.prompts.prompt import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

template = """You're a cover letter writer expert.

You are given a company name, position, job description, and resume information.

Please follow the following instructions at all times:
1. FOCUS ON THE JOB DESCRIPTION!
2. DON'T make up any information or an answer.
3. Any information should be coming directly from my resume or my cover letters.
4. You don't have to tackle every point in the job description.
5. Focus on my most recent experience.
6. If a skill is not listed in my resume or cover letter, then I don't have experience in it.

Focusing on the job description: write me professional and targeted cover letter for a {question}.
=========
{context}
=========
Cover Letter:"""
QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])


def get_chain(vectorstore):
    llm = OpenAI(
        streaming=True, temperature=0.05, max_tokens=600, model_name="text-davinci-003"
    )
    chain_type_kwargs = {"prompt": QA_PROMPT}
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs=chain_type_kwargs,
    )

    return qa_chain
