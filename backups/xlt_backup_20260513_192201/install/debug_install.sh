#!/bin/bash

# XLT System v3.1 디버깅 설치 스크립트
# 실제 에러 메시지를 표시하여 문제를 진단합니다

set -e  # 에러 발생 시 즉시 중단

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🔧 XLT System v3.1 디버깅 설치${NC}"
echo "실제 에러 메시지를 표시하여 문제를 진단합니다"
echo

# 1. 환경 정보 출력
echo -e "${BLUE}📊 시스템 환경 정보:${NC}"
echo "OS: $(uname -s) $(uname -r) $(uname -m)"
echo "Python: $(python3 --version 2>&1 || echo 'Python3 없음')"
echo "Pip: $(python3 -m pip --version 2>&1 || echo 'pip 없음')"

if command -v conda >/dev/null 2>&1; then
    echo "Conda: $(conda --version 2>&1 || echo 'conda 버전 확인 실패')"
    echo "Conda 환경: $(conda info --envs | grep '*' | awk '{print $1}' 2>/dev/null || echo '알 수 없음')"
fi

echo

# 2. 네트워크 테스트
echo -e "${BLUE}🌐 네트워크 연결 테스트:${NC}"
if curl -s --connect-timeout 5 https://pypi.org >/dev/null; then
    echo -e "${GREEN}✅ PyPI 접속 성공${NC}"
else
    echo -e "${RED}❌ PyPI 접속 실패 - 네트워크 문제일 수 있습니다${NC}"
fi

echo

# 3. pip 기본 테스트
echo -e "${BLUE}🧪 pip 기본 기능 테스트:${NC}"
echo "명령: python3 -m pip install --dry-run --user requests"

if python3 -m pip install --dry-run --user requests 2>&1; then
    echo -e "${GREEN}✅ pip 기본 기능 정상${NC}"
else
    echo -e "${RED}❌ pip 기본 기능에 문제가 있습니다${NC}"
    echo
    echo -e "${YELLOW}💡 해결방법 시도:${NC}"
    echo "1. pip 업그레이드: python3 -m pip install --user --upgrade pip"
    echo "2. 캐시 정리: python3 -m pip cache purge"
    echo "3. 권한 확인: ls -la ~/.local/lib/python*/site-packages/"
    exit 1
fi

echo

# 4. 실제 패키지 설치 테스트 (상세 에러 표시)
echo -e "${BLUE}📦 핵심 패키지 설치 테스트:${NC}"

packages=("flask" "requests" "pillow" "openpyxl")

for package in "${packages[@]}"; do
    echo -e "${YELLOW}설치 중: $package${NC}"
    echo "명령: python3 -m pip install --user --no-deps $package"

    if python3 -m pip install --user --no-deps "$package" 2>&1; then
        echo -e "${GREEN}✅ $package 설치 성공${NC}"
    else
        echo -e "${RED}❌ $package 설치 실패${NC}"
        echo "위의 에러 메시지를 확인해주세요."

        # 대안 제시
        echo -e "${YELLOW}대안 시도:${NC}"
        echo "시스템 권한으로 설치: sudo pip3 install $package"
        echo "Conda로 설치: conda install -c conda-forge $package"

        exit 1
    fi
    echo
done

echo -e "${GREEN}🎉 모든 핵심 패키지 설치 성공!${NC}"
echo

# 5. 소스 다운로드 및 설치 완료
echo -e "${BLUE}📥 XLT System 소스 다운로드...${NC}"
cd ~

if [ -d "XLT-System" ]; then
    echo "기존 설치 발견 - 백업 생성 중..."
    mv XLT-System "XLT-System.backup.$(date +%Y%m%d_%H%M%S)"
fi

if curl -L https://github.com/hobong-ho6/xlt-system/archive/main.zip -o xlt-main.zip; then
    echo -e "${GREEN}✅ 다운로드 성공${NC}"
else
    echo -e "${RED}❌ 다운로드 실패${NC}"
    exit 1
fi

unzip -q xlt-main.zip
mv xlt-system-main XLT-System
rm xlt-main.zip

echo -e "${GREEN}✅ XLT System 설치 완료!${NC}"
echo
echo -e "${BLUE}🚀 서버 시작:${NC}"
echo "cd ~/XLT-System && python3 stable_web_server.py"
echo
echo -e "${BLUE}🌐 웹 인터페이스:${NC}"
echo "http://localhost:5004"