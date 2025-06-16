import os
import json
import base64
import tempfile
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func
import boto3

@csrf_exempt
def youtube_audio(request):
    if request.method != 'POST':
        return HttpResponse("POST method required", status=405)

    try:
        b64_payload = request.POST.get('data')

        if not b64_payload:
            return JsonResponse({"status": False, "error": "data 파라미터가 필요합니다."}, status=400)

        if isinstance(b64_payload, bytes):
            b64_payload = b64_payload.decode('ascii').strip()

        json_str = base64.b64decode(b64_payload).decode('utf-8')
        data = json.loads(json_str)

        required_keys = ['videoId', 'start', 'end']
        for key in required_keys:
            if key not in data:
                return JsonResponse({"status": False, "error": f"'{key}' 값이 필요합니다."}, status=400)

        video_id = data['videoId']
        start = data['start']
        end = data['end']

        if data.get('key') != settings.KEY:
            return JsonResponse({"status": False, "error": "Invalid Key"}, status=403)

        filename = f"{video_id}.mp3"
        s3_key = f"{settings.AWS_REPO}/{filename}"
        s3_url = f"https://{settings.AWS_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

        try:
            s3.head_object(Bucket=settings.AWS_BUCKET, Key=s3_key)
            return JsonResponse({
                "status": True,
                "message": "이미 S3에 존재합니다.",
                "url": s3_url
            })
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] != '404':
                raise e

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
                'download_ranges': download_range_func(None, [(start, end)]),
                'force_keyframes_at_cuts': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])

            mp3_path = os.path.join(temp_dir, filename)
            with open(mp3_path, 'rb') as f:
                s3.upload_fileobj(f, settings.AWS_BUCKET, s3_key)

        return JsonResponse({
            "status": True,
            "message": "S3 업로드 완료",
            "url": s3_url
        })

    except Exception as e:
        return JsonResponse({"status": False, "error": str(e)}, status=500)
