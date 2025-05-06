from django.http import StreamingHttpResponse
import yt_dlp
import requests

def youtube_audio(request):
    url = 'https://www.youtube.com/watch?v=TeccAtqd5K8'  # 예시 YouTube 링크

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'outtmpl': '-',
    }

    def generate():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            with requests.get(audio_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    yield chunk

    return StreamingHttpResponse(generate(), content_type='audio/mpeg')