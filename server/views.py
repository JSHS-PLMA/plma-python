from django.http import StreamingHttpResponse, HttpResponseServerError
from yt_dlp import YoutubeDL
import requests

def youtube_audio(request):
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # 예시 영상

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'outtmpl': '-',
        'cookiefile': '/home/ubuntu/Server/plma_python/server/cookies.txt',  # 필요시 쿠키 사용
    }

    def generate(audio_url):
        with requests.get(audio_url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                yield chunk

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            ext = info.get('ext', 'mpeg')
            content_type = f'audio/{ext}' if ext != 'webm' else 'audio/webm'

        return StreamingHttpResponse(generate(audio_url), content_type=content_type)
    except Exception as e:
        return HttpResponseServerError(f"오류 발생: {str(e)}")
