from django.http import StreamingHttpResponse
from yt_dlp import YoutubeDL
import requests

def youtube_audio(request):
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Example video

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'outtmpl': '-',
    }

    def generate():
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            with requests.get(audio_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    yield chunk

    return StreamingHttpResponse(generate(), content_type='audio/mpeg')
