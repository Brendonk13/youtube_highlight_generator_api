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


def get_openai_chat(messages:list) -> str:
    """
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


def get_numeric_uuid(id: str) -> int:
    """
    convert string id to numeric (for youtube video id's)
    """

    # Convert the alphanumeric string to bytes
    s_bytes = id.encode('utf-8')
    # Calculate the SHA-256 hash of the bytes
    hash_object = hashlib.sha256(s_bytes)
    hex_digest = hash_object.hexdigest()
    # Convert the hexadecimal digest to an integer
    numeric_uuid = int(hex_digest, 16)
    # self.numeric_uuid = numeric_uuid
    return numeric_uuid

def get_data():
    print("before getting data")
    video_ids = ["9kWEHv8ZXKc", "7jFBDbU0KcE"]
    titles = [
        "Ep 413 - King Of The Games (feat. Lil Sasquatch)",
        "MSSP - Shane Rages During Monopoly With Family"
    ]
    all_data = list(download_transcripts(video_ids, titles))
    print("done getting data")
    docs     = (data["text"] for data in all_data)
    metadata = ({"title": data["title"]} for data in all_data)
    ids      = (get_numeric_uuid(data["video_id"]) for data in all_data)
    return docs, metadata, ids

def download_transcripts(video_ids: list, titles: list) -> Generator[Dict[str, str], None, None]:
    """
    todo: add download limiter so that you only download like 5 at a time
    move this into a class so we can save the state on how much has been downloaded
    """
    for video_id, title in zip(video_ids, titles):
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(line["text"] for line in transcript)
        yield {"text": text, "title": title, "video_id": video_id}

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
        You are a bot which answers questions about youtube videos.
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

        If the user's question is ambigious, then you should prompt the user for additional information.

        Do not rely solely on the additional context, although the context should have relevant information to answer the prompt.

        When the answer is found in the context, please provide the title of the context used to produce the answer as well as a quote from the context that is relevant to answering the user's question.
    """).strip()

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
