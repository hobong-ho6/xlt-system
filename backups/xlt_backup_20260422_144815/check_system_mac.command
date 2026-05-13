#!/bin/bash

# XLT System v3.0 macOS 설치 전 시스템 체크
# 설치 가능 여부를 미리 확인하는 스크립트

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}🔍 XLT System v3.0 macOS 호환성 체크${NC}"
echo "=============================================="
echo ""

# 체크 결과 저장
checks_passed=0
total_checks=6

# 1. macOS 버전 체크
echo -e "${BLUE}[1/6] macOS 버전 확인${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    macos_version=$(sw_vers -productVersion)
    echo "   감지된 버전: macOS $macos_version"

    # macOS 10.15+ 체크 (간단한 버전 비교)
    if [[ "$macos_version" == 1[1-9].* ]] || [[ "$macos_version" == [2-9]*.* ]]; then
        echo -e "   ${GREEN}✅ macOS 호환 (10.15+ 필요)${NC}"
        checks_passed=$((checks_passed + 1))
    else
        echo -e "   ${RED}❌ macOS 버전이 너무 낮습니다. 10.15+ 필요${NC}"
    fi
else
    echo -e "   ${RED}❌ macOS가 아닙니다${NC}"
fi

echo ""

# 2. Python 설치 체크
echo -e "${BLUE}[2/6] Python 설치 확인${NC}"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "   감지된 버전: Python $python_version"

    # Python 3.8+ 체크
    python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "   ${GREEN}✅ Python 호환 (3.8+ 필요)${NC}"
        checks_passed=$((checks_passed + 1))
    else
        echo -e "   ${RED}❌ Python 버전이 너무 낮습니다. 3.8+ 필요${NC}"
        echo -e "   ${YELLOW}💡 해결방법: brew install python3 또는 python.org에서 다운로드${NC}"
    fi
else
    echo -e "   ${RED}❌ Python 3가 설치되지 않았습니다${NC}"
    echo -e "   ${YELLOW}💡 해결방법: brew install python3 또는 python.org에서 다운로드${NC}"
fi

echo ""

# 3. pip 설치 체크
echo -e "${BLUE}[3/6] pip 패키지 관리자 확인${NC}"
if command -v pip3 &> /dev/null; then
    pip_version=$(pip3 --version 2>&1 | cut -d' ' -f2)
    echo "   감지된 버전: pip $pip_version"
    echo -e "   ${GREEN}✅ pip 사용 가능${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "   ${RED}❌ pip3가 설치되지 않았습니다${NC}"
    echo -e "   ${YELLOW}💡 해결방법: python3 -m ensurepip --upgrade${NC}"
fi

echo ""

# 4. 인터넷 연결 체크
echo -e "${BLUE}[4/6] 인터넷 연결 확인${NC}"
if ping -c 1 google.com &> /dev/null; then
    echo -e "   ${GREEN}✅ 인터넷 연결 정상${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "   ${RED}❌ 인터넷 연결 없음${NC}"
    echo -e "   ${YELLOW}💡 Wi-Fi 또는 유선 연결을 확인하세요${NC}"
fi

echo ""

# 5. 저장공간 체크
echo -e "${BLUE}[5/6] 저장공간 확인${NC}"
available_space=$(df -h . | tail -1 | awk '{print $4}' | sed 's/G.*//')
if [[ "$available_space" =~ ^[0-9]+$ ]] && [ "$available_space" -gt 2 ]; then
    echo "   사용 가능한 공간: ${available_space}GB"
    echo -e "   ${GREEN}✅ 충분한 저장공간 (2GB+ 필요)${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo "   사용 가능한 공간: ${available_space}"
    echo -e "   ${RED}❌ 저장공간 부족 (2GB+ 필요)${NC}"
    echo -e "   ${YELLOW}💡 불필요한 파일을 삭제하거나 정리하세요${NC}"
fi

echo ""

# 6. 필요 라이브러리 기본 확인
echo -e "${BLUE}[6/6] 기본 라이브러리 확인${NC}"
missing_libs=()

# 필수 Python 모듈들 체크
python3 -c "import ssl" 2>/dev/null || missing_libs+=("ssl")
python3 -c "import sqlite3" 2>/dev/null || missing_libs+=("sqlite3")
python3 -c "import json" 2>/dev/null || missing_libs+=("json")

if [ ${#missing_libs[@]} -eq 0 ]; then
    echo -e "   ${GREEN}✅ 기본 Python 라이브러리 정상${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "   ${RED}❌ 누락된 라이브러리: ${missing_libs[*]}${NC}"
    echo -e "   ${YELLOW}💡 Python을 다시 설치하세요${NC}"
fi

echo ""
echo "=============================================="
echo ""

# 최종 결과 출력
if [ $checks_passed -eq $total_checks ]; then
    echo -e "${GREEN}🎉 모든 체크 통과! ($checks_passed/$total_checks)${NC}"
    echo -e "${GREEN}✅ XLT System 설치가 가능합니다${NC}"
    echo ""
    echo -e "${BLUE}📋 다음 단계:${NC}"
    echo "   1. ./install_mac.sh 실행"
    echo "   2. 설치 완료까지 약 2-3분 대기"
    echo "   3. 데스크톱 바로가기로 실행"
    echo ""
else
    echo -e "${RED}❌ 일부 체크 실패 ($checks_passed/$total_checks)${NC}"
    echo -e "${YELLOW}⚠️  위에서 표시된 문제들을 해결 후 다시 시도하세요${NC}"
    echo ""
    echo -e "${BLUE}📋 일반적인 해결방법:${NC}"
    echo "   • Python: brew install python3"
    echo "   • 저장공간: 불필요한 파일 삭제"
    echo "   • 인터넷: Wi-Fi 연결 확인"
    echo ""
fi

# 시스템 정보 요약
echo -e "${BLUE}📊 시스템 정보 요약${NC}"
echo "   macOS: $(sw_vers -productVersion)"
if command -v python3 &> /dev/null; then
    echo "   Python: $(python3 --version 2>&1 | cut -d' ' -f2)"
else
    echo "   Python: 설치되지 않음"
fi
if command -v pip3 &> /dev/null; then
    echo "   pip: $(pip3 --version 2>&1 | cut -d' ' -f2)"
else
    echo "   pip: 설치되지 않음"
fi
echo "   저장공간: $(df -h . | tail -1 | awk '{print $4}') 사용 가능"
echo ""

echo ""
echo -e "${BLUE}Press Enter to close this window...${NC}"
read

if [ $checks_passed -eq $total_checks ]; then
    exit 0
else
    exit 1
fi