#!/bin/bash

# XLT System 로컬 언인스톨러 (설치된 버전)
# 인터넷 연결 없이도 사용 가능

echo "🗑️ XLT System 제거 중..."

# 현재 디렉토리에서 온라인 언인스톨러 실행 시도
if [ -f "./uninstall.sh" ]; then
    echo "로컬 언인스톨 스크립트 실행 중..."
    ./uninstall.sh
else
    echo "온라인 언인스톨러 실행 중..."
    echo "y" | curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
fi
