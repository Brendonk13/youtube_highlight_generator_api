# from dotenv import load_dotenv

# from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_core.pydantic_v1 import BaseModel, Field

from langchain_core.documents import Document
# from langchain_core.runnables import RunnablePassthrough

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
# from langchain_community.llms import GPT4All
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from youtube_clip_finder.get_data import get_data
# from youtube_clip_finder.config import CONFIG


def get_prompt():
    system_prompt = (
        "Use the given youtube transcript context to answer the question. "
        "If you don't know the answer, say you don't know. "
        "Use three sentence maximum and keep the answer concise. "
        "the format of the data within the context is as follows in backticks:"
        "```"
        "<7:58><6.13><Hey pal>"
        "```"
        "the following is ordered left to right"
        "where the content in the first <>  is the 'start time'"
        "where the content in the second <> is the 'duration'"
        "where the content in the third <>  is the 'line'"
        "this is a line, you need to return the start time and end time of each line used to determine the answer"
        "provide the time in start_time=hour:minute:second as well as just seconds: (seconds=second), use this format with no spaces so I can parse it out of your response"
        "you must also return the video id: video_id=id for the line"
        "Context: {context}"
    )

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
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)

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


def get_retrieval_chain():
    compression_retriever = get_compression_retriever()
    llm = get_llm()
    question_answer_chain = create_stuff_documents_chain(llm, get_prompt())
    return create_retrieval_chain(compression_retriever, question_answer_chain)


def format_docs_with_id(docs: list[Document]) -> str:
    formatted = [
        f"Source ID: {i}\nVideo Title: {doc.metadata['title']}\nTranscript Snippet: {doc.page_content}"
        for i, doc in enumerate(docs)
    ]
    return "\n\n" + "\n\n".join(formatted)

if __name__ == "__main__":
    query = "who is the king of the games"

    # structured_llm = llm.with_structured_output(QuotedAnswer)
    chain = get_retrieval_chain()

    result = chain.invoke({"input": query})

    print("result", result)
    print()
    print("answer", result["answer"])
