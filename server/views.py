import os
from django.http import HttpResponse, FileResponse
from django.conf import settings
from yt_dlp import YoutubeDL
import yt_dlp
import boto3

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

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])

        # ✅ S3에 업로드
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

        # ✅ S3 경로: songs/ 폴더
        s3_key = f"{settings.AWS_REPO}/{filename}"

        s3.upload_file(download_path, settings.AWS_BUCKET, s3_key)

        # ✅ 업로드 후 로컬 파일 삭제
        os.remove(download_path)

        # ✅ S3 URL 반환
        s3_url = f"https://{settings.AWS_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

        return HttpResponse(f"S3 업로드 완료: {s3_url}")

    except Exception as e:
        return HttpResponse(f"예외 발생: {str(e)}", status=500)