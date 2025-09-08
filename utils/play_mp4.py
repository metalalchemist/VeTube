import yt_dlp
from helpers.sound_helper import playsound

def play_video_url(youtube_url, reproductor):
    """
    Uses the yt_dlp library to get the direct stream URL for the mp4 format.
    """
    try:
        ydl_opts = {
            'format': 'mp4',
            'quiet': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            reproductor.playsound(info.get('url'), block=False)
    except Exception as e:
        print(f"Error extracting URL with yt-dlp library: {e}")
        return None
