from langchain.prompts.prompt import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

template = """You're a cover letter writer expert. Use the details and instructions below to write me a professional and tailored cover letter.

Details:
Job position, company name, and job description: {question}
Resume and Information: {context}

Instructions:
1. FOCUS ON THE JOB DESCRIPTION! But you don't have to address every point in the job description.
2. Figure out what skills that job requires, and match it with the provided information.
3. Use the details provided as a guide, but DO NOT COPY DIRECTLY. Paraphrase and present the information in a unique and original manner.
4. DON'T make up any information or an answer.
5. You don't have to address every point in the job description.
6. If possible, focus on my most recent experience
7. If a skill is not listed in the provided information, then I don't have experience in it.

Cover Letter:"""
QA_PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])


def get_chain(vectorstore):
    llm = OpenAI(
        streaming=True, temperature=0.2, max_tokens=600, model_name="text-davinci-003"
    )
    chain_type_kwargs = {"prompt": QA_PROMPT}
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs=chain_type_kwargs,
    )

    return qa_chain
