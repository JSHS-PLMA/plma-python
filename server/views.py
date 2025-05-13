from pytube import YouTube
import boto3
import os
import io
from django.http import JsonResponse, HttpResponseServerError

# AWS credentials from environment
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')

s3_client = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_S3_REGION_NAME
)

def youtube_audio(request, isMain = False):
    video_id = request if isMain else request.GET.get("videoId", "")
    print(video_id)
    if not video_id:
        return HttpResponseServerError("No video ID provided.")

    try:
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        audio_stream = yt.streams.filter(only_audio=True).first()

        # Download to memory
        buffer = io.BytesIO()
        audio_stream.stream_to_buffer(buffer)
        buffer.seek(0)

        # Create S3 file name
        s3_key = f"songs/{yt.title}.mp4"  # or .webm depending on stream

        # Upload to S3
        s3_client.upload_fileobj(
            buffer,
            Bucket=AWS_STORAGE_BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={"ACL": "public-read"}
        )

        s3_link = f"https://s3-{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}/{s3_key}"
        return JsonResponse({"link": s3_link})

    except Exception as e:
        print("Error:", str(e))
        return HttpResponseServerError(str(e))

def main():
    video_id = "APbt9_S003Y"

    youtube_audio(video_id, True)


if __name__ == "__main__":
    main()