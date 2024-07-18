from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.llms import GPT4All

from langchain_openai import ChatOpenAI


# # llm = ChatOpenAI(model="gpt-3.5-turbo-0125")

# def get_prompt():
#     system_prompt = (
#         "Use the given context to answer the question. "
#         "If you don't know the answer, say you don't know. "
#         "Use three sentence maximum and keep the answer concise. "
#         "Context: {context}"
#     )

#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", system_prompt),
#             ("human", "{input}"),
#         ]
#     )
#     prompt.pretty_print()
#     return prompt

# # store this in s3 ?
# # documents = TextLoader(
# #     "../../how_to/state_of_the_union.txt",
# # ).load()

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
# texts = text_splitter.split_documents(documents)

# for idx, text in enumerate(texts):
#     text.metadata["id"] = idx

# embedding = OpenAIEmbeddings(model="text-embedding-ada-002")
# # todo: what is search_kwargs
# base_retriever = FAISS.from_documents(texts, embedding).as_retriever(search_kwargs={"k": 20})

# # https://python.langchain.com/v0.2/docs/integrations/retrievers/flashrank-reranker/

# # use a llamafile or ollama instead?
# # i dont wanna run more servers so no llamafile
# # llm = GPT4All(
# #     model="/Users/rlm/Desktop/Code/gpt4all/models/nous-hermes-13b.ggmlv3.q4_0.bin",
# #     temperature=0
# # )

# llm = ChatOpenAI(temperature=0)

# compressor = FlashrankRerank()
# compression_retriever = ContextualCompressionRetriever(
#     base_compressor=compressor, base_retriever=base_retriever
# )

# question_answer_chain = create_stuff_documents_chain(llm, get_prompt())
# chain = create_retrieval_chain(compression_retriever, question_answer_chain)

# chain.invoke({"input": query})
