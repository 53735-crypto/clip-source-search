from fastapi import FastAPI, UploadFile, File
import sqlite3
import openai
import yt_dlp
from typing import List
import numpy as np
from fastapi.responses import HTMLResponse

app = FastAPI()

# SQLite database setup
conn = sqlite3.connect('videos.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS videos (id INTEGER PRIMARY KEY, title TEXT, url TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, video_id INTEGER, transcript TEXT, FOREIGN KEY (video_id) REFERENCES videos (id))''')
conn.commit()

# Function to fetch video metadata and save in database
async def fetch_video_metadata(video_url: str):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        title = info['title']
        cursor.execute('INSERT INTO videos (title, url) VALUES (?, ?)', (title, video_url))
        conn.commit()

# Function to chunk transcript with specific window and stride
def chunk_transcript(transcript: str, window: int = 15, stride: int = 5) -> List[str]:
    words = transcript.split()
    chunks = []
    for i in range(0, len(words), stride):
        chunk = ' '.join(words[i:i+window])
        if chunk:
            chunks.append(chunk)
    return chunks

# Function to calculate cosine similarity
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# YouTube Data API integration for transcriptions and embeddings
@app.post('/index')
async def index_video(video_url: str):
    await fetch_video_metadata(video_url)
    # additional logic for downloading and processing video to get transcript
    transcript = '...'  # Placeholder for actual transcript fetching logic
    chunks = chunk_transcript(transcript)
    for chunk in chunks:
        cursor.execute('INSERT INTO chunks (video_id, transcript) VALUES (?, ?)', (video_id, chunk))
    conn.commit()
    return {'message': 'Video indexed successfully'}

@app.get('/search/text')
async def text_search(query: str):
    # Logic for exact and semantic search using SQLite FTS5 and OpenAI embeddings
    return {'results': []}

@app.post('/search/clip')
async def clip_search(file: UploadFile = File(...)):  
    # Logic for audio transcription using OpenAI Whisper and searching
    return {'transcription': '', 'results': []}

@app.get('/static')
async def static_ui():
    html_content = '''<html><body>
    <h2>Video Indexer</h2>
    <form action="/index" method="post">
        <input type="text" name="video_url" placeholder="Video URL" required>
        <button type="submit">Index</button>
    </form>
    <form action="/search/text" method="get">
        <input type="text" name="query" placeholder="Search text" required>
        <button type="submit">Search</button>
    </form>
    <form action="/search/clip" method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <button type="submit">Upload and Search</button>
    </form>
</body></html>'''  
    return HTMLResponse(content=html_content)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)