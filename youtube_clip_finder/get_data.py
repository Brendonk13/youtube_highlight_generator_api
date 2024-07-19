import hashlib
from typing import Generator, Tuple
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document
from youtube_clip_finder.config import CONFIG

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


def get_data(download_name = 'test') -> list[Document]:
    # todo: pass in the name of the youtuber or playlist/channel first into scrapetube
    print("before getting data")
    video_ids = ["9kWEHv8ZXKc", "7jFBDbU0KcE"]
    titles = [
        "Ep 413 - King Of The Games (feat. Lil Sasquatch)",
        "MSSP - Shane Rages During Monopoly With Family"
    ]
    docs = []
    for text, title, video_id, id in download_transcripts(video_ids, titles):
        metadata = {
            "id": id,
            "title": title,
            "video_id": video_id,
        }
        docs.append(Document(page_content=text, metadata=metadata))
    print("done downloading transcript")
    return docs

def download_transcripts(video_ids: list[str], titles: list[str]) -> Generator[Tuple[str, str, str, int], None, None]:
    for video_id, title in zip(video_ids, titles):
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # text = " ".join(f"<{int(line['start'])}><{int(line['duration'])}><{line['text']}>" for line in transcript)
        # print(type(transcript), len(transcript), transcript)
        idx = 0
        curr_lines = []
        num_documents = 0
        while idx < len(transcript):
            line = transcript[idx]
            # convert to int to save data
            curr_lines.append(f"<{int(line['start'])}><{int(line['duration'])}><{line['text']}>")
            if idx % CONFIG.document_size == 0:
                id = get_numeric_uuid(f"{video_id}{num_documents}")
                yield " ".join(curr_lines), title, video_id, id
                num_documents += 1
            idx += 1
        # text = " ".join(f"<{int(line['start'])}><{int(line['duration'])}><{line['text']}>" for line in transcript)

        # dont want to forget these !
        if curr_lines:
            id = get_numeric_uuid(f"{video_id}{num_documents}")
            yield " ".join(curr_lines), title, video_id, id
