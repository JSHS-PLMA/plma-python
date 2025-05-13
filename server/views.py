import subprocess
import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.http import JsonResponse, HttpResponseServerError
from yt_dlp import YoutubeDL

# 환경 변수에서 AWS 자격 증명 로드
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')

# S3 클라이언트 생성
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_S3_REGION_NAME)

def download_audio(video_url):
    try:
        # yt-dlp 명령어 실행
        command = [
            'yt-dlp', 
            '--cookies', '/home/ubuntu/Server/plma_python/server/cookies.txt',
            '-x', '--audio-format', 'mp3',
            video_url
        ]
        # subprocess를 사용해 yt-dlp 실행
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)  # yt-dlp 출력 결과

        # 다운로드된 mp3 파일 경로
        output_filename = result.stdout.strip().split('\n')[-1]  # yt-dlp 출력에서 파일명 추출
        print(f"Downloaded audio file: {output_filename}")

        # S3에 업로드
        return upload_to_s3(output_filename)

    except subprocess.CalledProcessError as e:
        print(f"Error running yt-dlp: {e.stderr}")
        return HttpResponseServerError(f"YT-DLP Error: {e.stderr}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return HttpResponseServerError(f"Error: {str(e)}")

def upload_to_s3(file_name):
    try:
        # 로컬 파일 열기
        with open(file_name, 'rb') as file_data:
            # 파일을 S3 버킷에 업로드
            s3_client.put_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=f"songs/{file_name}", Body=file_data, ACL='public-read')
        
        print(f"File uploaded to S3 successfully: songs/{file_name}")

        # S3 링크 반환
        s3_link = f"https://s3-{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/songs/{file_name}"
        return JsonResponse({"link": s3_link}, status=200)

    except NoCredentialsError:
        return HttpResponseServerError("AWS credentials are missing or incorrect.")
    except PartialCredentialsError:
        return HttpResponseServerError("Incomplete AWS credentials.")
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")
        return HttpResponseServerError(f"Error uploading to S3: {str(e)}")

# Django view에서 사용
def youtube_audio(request):
    video_id = request.GET.get("videoId", " ")
    if not video_id:
        return HttpResponseServerError("No video ID provided.")

    video_url = f'https://www.youtube.com/watch?v={video_id}'
    return download_audio(video_url)
