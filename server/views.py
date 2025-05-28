import os
from django.http import HttpResponse, FileResponse
from django.conf import settings
from yt_dlp import YoutubeDL
import yt_dlp

def youtube_audio(request):
    video_id = request.GET.get('videoId')
    if not video_id:
        return HttpResponse("videoId 파라미터가 필요합니다.", status=400)

    filename = f"{video_id}.mp3"
    download_path = os.path.join(settings.MEDIA_ROOT, filename)

    # media 폴더 없으면 생성
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

    # ✅ 절대 경로로 쿠키 파일 지정
    cookie_path = os.path.join(settings.BASE_DIR, 'server', 'cookies.txt')
    print(cookie_path)
    
    print("version", yt_dlp.version.__version__)

    # yt-dlp 옵션 설정
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': os.path.join(settings.MEDIA_ROOT, f'{video_id}.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': cookie_path,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=True)
            if not os.path.exists(download_path):
                return HttpResponse("다운로드 파일을 찾을 수 없습니다.", status=500)

        # 파일 응답
        return FileResponse(open(download_path, 'rb'), content_type='audio/mpeg', filename=filename)

    except Exception as e:
        return HttpResponse(f"예외 발생: {str(e)}", status=500)
