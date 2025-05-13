import os
import boto3
import tempfile
from yt_dlp import YoutubeDL
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.http import JsonResponse, HttpResponseServerError

# AWS 환경 변수
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')

# S3 클라이언트
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_S3_REGION_NAME)

def download_and_upload_to_s3(video_url):
    try:
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'cookiefile': '/home/ubuntu/Server/plma_python/server/cookies.txt'
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                file_path = os.path.join(tmpdir, f"{info['title']}.mp3")
                print(f"Downloaded temp file: {file_path}")

            # S3로 바로 업로드
            return upload_fileobj_to_s3(file_path, info['title'] + '.mp3')

    except Exception as e:
        print(f"YT-DLP Error: {str(e)}")
        return HttpResponseServerError(f"YT-DLP Error: {str(e)}")

def upload_fileobj_to_s3(file_path, s3_filename):
    try:
        with open(file_path, 'rb') as file_data:
            s3_key = f"songs/{s3_filename}"
            s3_client.upload_fileobj(file_data, AWS_STORAGE_BUCKET_NAME, s3_key, ExtraArgs={'ACL': 'public-read'})

        print(f"Uploaded to S3: {s3_key}")
        s3_link = f"https://s3-{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/{s3_key}"
        return JsonResponse({"link": s3_link}, status=200)

    except NoCredentialsError:
        return HttpResponseServerError("AWS credentials missing.")
    except PartialCredentialsError:
        return HttpResponseServerError("Incomplete AWS credentials.")
    except Exception as e:
        print(f"S3 Upload Error: {str(e)}")
        return HttpResponseServerError(f"S3 Upload Error: {str(e)}")

def youtube_audio(request):
    video_id = request.GET.get("videoId")
    if not video_id:
        return HttpResponseServerError("No video ID provided.")

    video_url = f'https://www.youtube.com/watch?v={video_id}'
    return download_and_upload_to_s3(video_url)