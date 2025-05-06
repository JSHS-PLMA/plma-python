#!/bin/bash

# 1. 환경 변수 설정 (가상환경 활성화 등)
source /home/ubuntu/venv/bin/activate  # 가상환경 경로

# 2. 코드 pull
git pull
echo "✅ Git pull 완료"

# 3. 패키지 설치
pip install -r requirements.txt
echo "✅ requirements.txt 설치 완료"
