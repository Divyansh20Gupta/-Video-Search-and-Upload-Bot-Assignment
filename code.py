import os
import json
import asyncio
import aiohttp
from tqdm import tqdm
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Constants
UPLOAD_URL = "https://api.socialverseapp.com/posts/generate-upload-url"
CREATE_POST_URL = "https://api.socialverseapp.com/posts"
TOKEN = "<YOUR_TOKEN>"
VIDEO_DIR = "./videos"

# Function to get upload URL
async def get_upload_url(session):
    async with session.post(UPLOAD_URL, headers={
        "Flic-Token": TOKEN,
        "Content-Type": "application/json"
    }) as response:
        return await response.json()

# Function to upload video
async def upload_video(session, video_path, upload_url):
    with open(video_path, 'rb') as video_file:
        async with session.put(upload_url, data=video_file) as response:
            return await response.json()

# Function to create a post
async def create_post(session, title, hash_value, category_id):
    payload = {
        "title": title,
        "hash": hash_value,
        "is_available_in_public_feed": False,
        "category_id": category_id
    }
    async with session.post(CREATE_POST_URL, headers={
        "Flic-Token": TOKEN,
        "Content-Type": "application/json"
    }, json=payload) as response:
        return await response.json()

# Function to process video upload
async def process_video(video_path, title, category_id):
    async with aiohttp.ClientSession() as session:
        upload_info = await get_upload_url(session)
        upload_url = upload_info['upload_url']
        hash_value = upload_info['hash']

        # Upload video
        await upload_video(session, video_path, upload_url)

        # Create post
        await create_post(session, title, hash_value, category_id)

        # Delete local file after upload
        os.remove(video_path)

# Directory monitoring
class VideoHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.mp4'):
            title = os.path.basename(event.src_path)
            category_id = 1  # Example category ID
            asyncio.run(process_video(event.src_path, title, category_id))

def monitor_directory():
    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, VIDEO_DIR, recursive=False)
    observer.start()
    try:
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)
    monitor_directory()
