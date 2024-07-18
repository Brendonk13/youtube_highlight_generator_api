import hashlib
from typing import Generator
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document


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


# def get_data(download_name = 'test') -> tuple[list[str], list[dict[str,str]], list[int]]:
# def get_data(download_name = 'test') -> tuple[list[dict[str,str]], dict[str, int]]:
def get_data(download_name = 'test') -> list[Document]:
    # todo: pass in the name of the youtuber or playlist/channel first into scrapetube
    print("before getting data")
    video_ids = ["9kWEHv8ZXKc", "7jFBDbU0KcE"]
    titles = [
        "Ep 413 - King Of The Games (feat. Lil Sasquatch)",
        "MSSP - Shane Rages During Monopoly With Family"
    ]
    docs: list[Document] = []
    # ids = []
    # ids = {}
    for data in download_transcripts(video_ids, titles):
        text, title, id = data["text"], data["title"], get_numeric_uuid(data["video_id"])
        # docs.append({"text": text, "metadata": title})
        docs.append(Document(page_content=text, metadata={"title": title, "id": id}))
        # docs[-1].metadata = title
        # docs[-1].id = id
        # docs.append({"page_content": text, "metadata": title})
        # ids[title] = id
        # ids.append(id)
    print("done getting data")
    # docs     = [data["text"] for data in all_data]
    # metadata = [{"title": data["title"]} for data in all_data]
    # ids      = [get_numeric_uuid(data["video_id"]) for data in all_data]
    # return docs, metadata, ids
    return docs
            # document = Document(
            #     page_content="Hello, world!",
            #     metadata={"source": "https://example.com"}
            # )

def download_transcripts(video_ids: list, titles: list) -> Generator[dict[str, str], None, None]:
    """
    todo: add download limiter so that you only download like 5 at a time
    move this into a class so we can save the state on how much has been downloaded
    """
    for video_id, title in zip(video_ids, titles):
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # convert to int to save data
        text = " ".join(f"<{int(line['start'])}><{int(line['duration'])}><{line['text']}>" for line in transcript)
        yield {"text": text, "title": title, "video_id": video_id}

