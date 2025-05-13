from django.http import StreamingHttpResponse, HttpResponseServerError, JsonResponse
from yt_dlp import YoutubeDL
import requests
import os
from dotenv import load_dotenv

import boto3

load_dotenv(verbose=True)

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')

s3_client = boto3.client('s3',  aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_S3_REGION_NAME)

def youtube_audio(request):
    video_id = request.GET.get("videoId", "").strip()
    if not video_id:
        return JsonResponse({"error": "videoId 파라미터가 필요합니다."}, status=400)

    url = f'https://www.youtube.com/watch?v={video_id}'

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False,
        'outtmpl': '-',
        'cookiefile': '/home/ubuntu/Server/plma_python/server/cookies.txt',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        },
    }

    def generate(audio_url):
        with requests.get(audio_url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=4096):
                yield chunk

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            ext = info.get('ext', 'webm')
            content_type = f'audio/{ext}'

        key = f"songs/{video_id}.{ext}"
        s3_client.put_object(
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Body=generate(audio_url),
            ContentType=content_type,
            ACL='public-read'
        )

        return JsonResponse({
            "link": f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{key}"
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": e}, status=500)

