import yt_dlp as yt
import os

YT_VIDEO = "https://www.youtube.com/watch?v=QizCgI6igT0"

# Ensure data/samples directory exists
os.makedirs('inputs', exist_ok=True)

opts = {
    'outtmpl': 'inputs/video.mkv',
    'restrictfilenames': True
}

# downloading the youtube video
with yt.YoutubeDL(opts) as ydl:
    ydl.download([YT_VIDEO])

