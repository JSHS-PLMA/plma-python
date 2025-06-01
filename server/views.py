import os
import tempfile
from django.http import HttpResponse
from django.conf import settings
from yt_dlp import YoutubeDL
import boto3

def youtube_audio(request):
    video_id = request.GET.get('videoId')
    if not video_id:
        return HttpResponse("videoId 파라미터가 필요합니다.", status=400)

    filename = f"{video_id}.mp3"

    # ✅ 절대 경로로 쿠키 파일 지정
    cookie_path = os.path.join(settings.BASE_DIR, 'server', 'cookies.txt')

    # ✅ S3 클라이언트
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    try:
        # ✅ 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # ✅ yt-dlp 옵션 설정
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': os.path.join(temp_dir, f'{video_id}.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'cookiefile': cookie_path,
                # ✅ ffmpeg CPU 사용량 제한
                'postprocessor_args': ['-threads', '1'],
            }

            # ✅ 다운로드 및 mp3 변환
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])

            # ✅ mp3 파일 경로
            mp3_path = os.path.join(temp_dir, filename)

            # ✅ S3 경로
            s3_key = f"{settings.AWS_REPO}/{filename}"

            # ✅ S3에 업로드
            with open(mp3_path, 'rb') as f:
                s3.upload_fileobj(f, settings.AWS_BUCKET, s3_key)

            # ✅ S3 URL 반환
            s3_url = f"https://{settings.AWS_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

            # ✅ 임시 디렉토리는 with 블록 끝나면 자동 삭제됨!
            return HttpResponse(f"S3 업로드 완료: {s3_url}")

    except Exception as e:
        return HttpResponse(f"예외 발생: {str(e)}", status=500)
