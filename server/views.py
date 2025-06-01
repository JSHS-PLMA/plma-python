import os
import tempfile
from django.http import HttpResponse
from django.conf import settings
from yt_dlp import YoutubeDL
import boto3

def youtube_audio(request):
    video_id = request.GET.get('videoId')
    key = request.GET.get('key')

    if not(key == settings.KEY):
        return HttpResponse("Invalid Key", status=403)

    if not video_id:
        return HttpResponse("videoId 파라미터가 필요합니다.", status=400)

    filename = f"{video_id}.mp3"
    s3_key = f"{settings.AWS_REPO}/{filename}"

    # ✅ S3 클라이언트
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    # ✅ S3 URL
    s3_url = f"https://{settings.AWS_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

    try:
        # ✅ S3에 파일이 이미 존재하는지 확인
        try:
            s3.head_object(Bucket=settings.AWS_BUCKET, Key=s3_key)
            # ✅ 이미 존재하면 URL 바로 반환
            return HttpResponse(f"이미 S3에 존재합니다: {s3_url}")
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                # 존재하지 않음, 아래에서 다운로드!
                pass
            else:
                # 다른 오류는 예외로 처리
                raise e

        # ✅ 존재하지 않으면 yt-dlp로 다운로드 & S3 업로드
        cookie_path = os.path.join(settings.BASE_DIR, 'server', 'cookies.txt')

        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': os.path.join(temp_dir, f'{video_id}.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'cookiefile': cookie_path,
                'postprocessor_args': ['-threads', '1'],
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])

            mp3_path = os.path.join(temp_dir, filename)
            with open(mp3_path, 'rb') as f:
                s3.upload_fileobj(f, settings.AWS_BUCKET, s3_key)

        return HttpResponse(f"S3 업로드 완료: {s3_url}")

    except Exception as e:
        return HttpResponse(f"예외 발생: {str(e)}", status=500)


