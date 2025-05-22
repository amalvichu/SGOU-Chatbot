from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import load_qa_chain
from langchain.llms import OpenAI
import os

VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), 'vector_store')

def answer_program_question(question: str) -> str:
    db = FAISS.load_local(VECTOR_STORE_DIR, OpenAIEmbeddings())
    docs = db.similarity_search(question, k=3)
    llm = OpenAI(temperature=0)
    chain = load_qa_chain(llm, chain_type="stuff")
    response = chain.run(input_documents=docs, question=question)
    return response