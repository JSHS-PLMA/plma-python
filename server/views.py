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
    video_id = request.GET.get("videoId", "")
    url = f'https://www.youtube.com/watch?v={video_id}'  # 예시 영상

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

        # return StreamingHttpResponse(generate(audio_url), content_type=content_type)
        if s3_client.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(Key="upload_file_path_name", Body=generate(audio_url), ContentType=content_type, ACL='public-read') is not None:
            return JsonResponse({"link": f"https://s3-{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/songs/{video_id}"}, status = 200)
    except Exception as e:
        return HttpResponseServerError(f"오류 발생: {str(e)}")
