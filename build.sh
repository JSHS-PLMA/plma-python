#!/bin/bash

# 1. 환경 변수 설정 (가상환경 활성화 등)
source /home/ubuntu/venv/bin/activate  # 가상환경 경로

# 2. 코드 pull
git pull
echo "✅ Git pull 완료"

# 3. 패키지 설치
pip install -r requirements.txt
echo "✅ requirements.txt 설치 완료"

# 4. 마이그레이션
python manage.py migrate
echo "✅ DB 마이그레이션 완료"

# 5. 정적 파일 수집
python manage.py collectstatic --noinput
echo "✅ static 파일 수집 완료"

# 6. 서버 재시작 (예: gunicorn, daphne, etc.)
# pm2 사용 시:
pm2 restart plma_python
echo "✅ PM2 재시작 완료"
