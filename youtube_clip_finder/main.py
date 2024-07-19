# from dotenv import load_dotenv

# from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.pydantic_v1 import BaseModel, Field

from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_community.llms import GPT4All
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from youtube_clip_finder.get_data import get_data
from youtube_clip_finder.config import CONFIG


def get_prompt():
    system_prompt = (
        "Use the given context to answer the question. "
        "If you don't know the answer, say you don't know. "
        "Use three sentence maximum and keep the answer concise. "
        "Context: {context}"
    )

    # return the start and end times of everyting

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )
    prompt.pretty_print()
    return prompt

def get_base_retriever():
    # pass youtuber name here later
    documents = get_data(download_name="test")
    # I split the documents myself when downloading so we get better metadata
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)
    # texts = text_splitter.split_documents(documents)

    embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
    # what is search_kwargs
    base_retriever = FAISS.from_documents(documents, embedding).as_retriever(search_kwargs={"k": 20})
    return base_retriever

def get_compression_retriever():
    base_retriever = get_base_retriever()

    compressor = FlashrankRerank()
    return ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=base_retriever
    )

def get_llm():
    return ChatOpenAI(temperature=0, model="gpt-4o")

def get_retrieval_chain(llm):
    compression_retriever = get_compression_retriever()
    question_answer_chain = create_stuff_documents_chain(llm, get_prompt())
    return create_retrieval_chain(compression_retriever, question_answer_chain)

class Citation(BaseModel):
    source_id: int = Field(
        ...,
        description="The integer ID of a SPECIFIC source which justifies the answer.",
    )
    quote: str = Field(
        ...,
        description="The VERBATIM quote from the specified source that justifies the answer.",
    )


class QuotedAnswer(BaseModel):
    """Answer the user question based only on the given sources, and cite the sources used."""

    answer: str = Field(
        ...,
        description="The answer to the user question, which is based only on the given sources.",
    )
    citations: list[Citation] = Field(
        ..., description="Citations from the given sources that justify the answer."
    )


def format_docs_with_id(docs: list[Document]) -> str:
    formatted = [
        f"Source ID: {i}\nVideo Title: {doc.metadata['title']}\nTranscript Snippet: {doc.page_content}"
        for i, doc in enumerate(docs)
    ]
    return "\n\n" + "\n\n".join(formatted)

if __name__ == "__main__":
    query = "who is the king of the games"
    llm = get_llm()

    structured_llm = llm.with_structured_output(QuotedAnswer)
    chain = get_retrieval_chain(llm)
    prompt = get_prompt()

    rag_chain_from_docs = (
    RunnablePassthrough.assign(context=(lambda x: format_docs_with_id(x["context"])))
    | prompt
    | llm.with_structured_output(QuotedAnswer)
    )

    retrieve_docs = (lambda x: x["input"]) | retriever

    chain = RunnablePassthrough.assign(context=retrieve_docs).assign(
        answer=rag_chain_from_docs
    )

    result = chain.invoke({"input": query})

    print("result", result)
    print()
    print("answer", result["answer"])
