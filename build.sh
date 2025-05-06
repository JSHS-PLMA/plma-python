#!/bin/bash

# 2. 코드 pull
git remote set-url origin https://github.com/JSHS-PLMA/plma-python.git
git pull origin main
echo "✅ Git pull 완료"

# 3. 패키지 설치
source venv/bin/activate
pip install -r requirements.txt
echo "✅ requirements.txt 설치 완료"
