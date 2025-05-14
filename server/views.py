import os
import yt_dlp
from django.http import HttpResponse
from django.conf import settings

def youtube_audio(request):
    video_id = request.GET.get('videoId')
    if not video_id:
        return HttpResponse("videoId 파라미터가 필요합니다.", status=400)
        
    print("MEDIA_ROOT:", settings.MEDIA_ROOT)
    print("다운로드 경로:", os.path.join(settings.MEDIA_ROOT, f"{video_id}.%(ext)s"))

    filename = f"{video_id}.mp3"
    download_path = os.path.join(settings.MEDIA_ROOT, filename)

    if not os.path.exists(settings.MEDIA_ROOT):
        os.makedirs(settings.MEDIA_ROOT)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(settings.MEDIA_ROOT, f"{video_id}.%(ext)s"),
        'ffmpeg_location': '/usr/bin/ffmpeg',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': '/home/ubuntu/cookies.txt',
        'verbose': True,  # verbose 모드 활성화
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])

        with open(download_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='audio/mpeg')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    except Exception as e:
        return HttpResponse(f"다운로드 실패: {str(e)}", status=500)
