import hashlib
import requests
import os
import json
from textwrap import dedent

from typing import Dict, List, Tuple, Generator

from fastembed import TextEmbedding
import scrapetube
from qdrant_client import QdrantClient
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document



def get_openai_chat(messages:list) -> str:
    """
    https://github.com/openai/openai-python?tab=readme-ov-file#async-usage

    docs: https://platform.openai.com/docs/api-reference/chat/create
    """
    print("messages", messages)
    model = "gpt-4o"
    data = {
        "model": model,
        "messages": messages,
    }
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
    }
    response = requests.post(api_url, headers=headers, data=json.dumps(data)).json()
    print("response")
    print(response)
    return response['choices'][0]['message']['content']


def get_qdrant_client(docs, metadata, ids):
    # Initialize the client
    # client = QdrantClient("localhost", port=6333) # For production
    client = QdrantClient(":memory:") # For small experiments

    client.set_model("sentence-transformers/all-MiniLM-L6-v2")
    # comment this line to use dense vectors only
    # client.set_sparse_model("prithivida/Splade_PP_en_v1")

    collection_name = "demo_collection"
    client.create_collection(
        collection_name=collection_name,
        vectors_config=client.get_fastembed_vector_params(),
        # comment this line to use dense vectors only
        # sparse_vectors_config=client.get_fastembed_sparse_vector_params(),
    )


    # client = QdrantClient(url="http://localhost:6333")
    # client.create_collection(
    #     collection_name="{collection_name}",
    #     vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
    #     quantization_config=models.ScalarQuantization(
    #         scalar=models.ScalarQuantizationConfig(
    #             type=models.ScalarType.INT8,
    #             quantile=0.99,
    #             always_ram=True,
    #         ),
    #     ),
    # )

    client.add(
        collection_name=collection_name,
        documents=docs,
        metadata=metadata,
        ids=ids,
        # parallel=0,  # Use all available CPU cores to encode data. -- this bricks my cpu/ram (without wrapping in ifmain block)
        # Requires wrapping code into if __name__ == '__main__' block
    )
    return client


def get_system_prompt() -> str:
    return dedent("""
        You are a bot which answers questions about youtube videos and provides timestamps to indicate to the user where the answer to their question was derived from.
        You will be given additional context from some youtube video transcripts to help you give informed answers to the user's questions.
        The additional context will be gathered by a RAG system.

        The format of the questions will be like the following example delimited by backticks:

        ```
        User's question goes here
        --------------------------------
        Additional Context:
        context goes here
        --------------------------------
        ```

        the format of the context is as follows in backticks:
        ```
        <7:58><6.13><Hey pal>
        ```
        the following is ordered left to right
        where the content in the first <>  is the 'start time'
        where the content in the second <> is the 'duration'
        where the content in the third <>  is the 'line'

        Note that start time is the timestamp at which the line occurs in the youtube video

        If the user's question is ambigious, then you should prompt the user for additional information.

        Do not rely solely on the additional context, although the context should have relevant information to answer the prompt.

        When the answer is found in the context, provide the title of the context used to produce the answer as well as a start time and end time for lines which were used to answer this question.

        Feel free to merge lines from the context to give a better answer, as long as the correct start time is given.
    """).strip()
        # When the answer is found in the context, please provide the title of the context used to produce the answer as well as a quote from the context that is relevant to answering the user's question.

        # where the 's' in <s:7:58> stands for 'start time'
        # and   the 'd' in <d:6.13> stands for 'duration'
        # and   the 't' in <l:Hey pal> stands for 'line'


def get_initial_messages() -> List[Dict[str,str]]:
    return [
        {"role": "system", "content": get_system_prompt()},
        {"role": "assistant", "content": "Hello!"}
    ]

def generate_content(query, metadata):
    new_metadata = ""
    for metadata in metadata:
        new_metadata += f"title: {metadata['title']}, document: {metadata['document']}"
        new_metadata += "\n"

    return dedent(f"""
        {query}
        --------------------------------
        Additional Context:

        {new_metadata}
        --------------------------------
    """).strip()

def generate_ai_data(search_result, query_text) -> Tuple[List[Dict[str,str]], str]:
    metadata = [hit.metadata for hit in search_result]
    content = generate_content(query_text, metadata)
    return get_initial_messages(), content



if __name__ == "__main__":
    client = get_qdrant_client(*get_data())

    query_text="who is the king of the games"

    search_result = client.query(
        collection_name="demo_collection",
        query_text=query_text,
        query_filter=None,
        limit=5,
    )

    messages, content = generate_ai_data(search_result, query_text)

    messages.append({"role":"user", "content": content})
    chatgpt_answer = get_openai_chat(messages)
    print(f"\nBot: {chatgpt_answer}\n")
    messages.append({'role':'assistant','content':chatgpt_answer})
