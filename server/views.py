import os
import subprocess
from django.http import HttpResponse, FileResponse
from django.conf import settings

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

    # yt-dlp 명령어 구성
    cmd = [
        'yt-dlp',
        '--cookies', cookie_path,
        '-f', 'bestaudio',
        '--extract-audio',
        '--audio-format', 'mp3',
        '--audio-quality', '192K',
        '-o', os.path.join(settings.MEDIA_ROOT, f'{video_id}.%(ext)s'),
        f'https://www.youtube.com/watch?v={video_id}'
    ]

    try:
        # yt-dlp 실행
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            return HttpResponse(f"다운로드 실패: {result.stderr}", status=500)

        # 파일 응답
        if os.path.exists(download_path):
            return FileResponse(open(download_path, 'rb'), content_type='audio/mpeg', filename=filename)
        else:
            return HttpResponse("다운로드 파일을 찾을 수 없습니다.", status=500)

    except Exception as e:
        return HttpResponse(f"예외 발생: {str(e)}", status=500)
