#!/bin/bash

# XLT System v3.1 간단 제거 스크립트
# 터미널에서 실행: curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}🗑️ XLT System v3.1 제거${NC}"

# 설치 경로들
INSTALL_DIR="$HOME/XLT-System"
DESKTOP_SHORTCUT="$HOME/Desktop/XLT System (Tray).command"

# 현재 설치 상태 확인
echo "🔍 설치 상태 확인 중..."
FOUND_ITEMS=()

if [ -d "$INSTALL_DIR" ]; then
    SIZE=$(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1)
    FOUND_ITEMS+=("설치 디렉토리: $INSTALL_DIR ($SIZE)")
fi

if [ -f "$DESKTOP_SHORTCUT" ]; then
    FOUND_ITEMS+=("바로가기: $DESKTOP_SHORTCUT")
fi

# 백업 파일들 확인
BACKUPS=$(ls -d "$HOME"/XLT-System.backup.* 2>/dev/null || true)
if [ -n "$BACKUPS" ]; then
    for backup in $BACKUPS; do
        SIZE=$(du -sh "$backup" 2>/dev/null | cut -f1)
        FOUND_ITEMS+=("백업: $backup ($SIZE)")
    done
fi

# 실행 중인 프로세스 확인
RUNNING=$(ps aux | grep -E "(stable_web_server|XLT)" | grep -v grep | wc -l)

if [ ${#FOUND_ITEMS[@]} -eq 0 ] && [ $RUNNING -eq 0 ]; then
    echo -e "${GREEN}✅ XLT System이 설치되어 있지 않습니다.${NC}"
    exit 0
fi

# 발견된 항목 표시
echo ""
echo -e "${YELLOW}📦 발견된 XLT System 구성요소:${NC}"
for item in "${FOUND_ITEMS[@]}"; do
    echo "   • $item"
done

if [ $RUNNING -gt 0 ]; then
    echo -e "${YELLOW}⚠️ 실행 중인 프로세스: ${RUNNING}개${NC}"
fi

# 제거 확인 (파이프 실행 시에는 자동 진행)
echo ""
if [ -t 0 ]; then
    echo -e "${RED}정말로 XLT System을 제거하시겠습니까? (y/N)${NC}"
    read -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "제거를 취소합니다."
        exit 0
    fi
else
    echo -e "${YELLOW}⚠️ 파이프 실행: 자동으로 제거를 진행합니다...${NC}"
fi

echo ""
echo -e "${BLUE}🚀 XLT System 제거 시작...${NC}"

# 1. 실행 중인 프로세스 종료
if [ $RUNNING -gt 0 ]; then
    echo "1️⃣ 실행 중인 프로세스 종료..."
    pkill -f stable_web_server 2>/dev/null || true
    pkill -f "XLT System" 2>/dev/null || true
    echo "   ✅ 프로세스 종료 완료"
fi

# 2. 설치 디렉토리 제거
if [ -d "$INSTALL_DIR" ]; then
    echo "2️⃣ 설치 디렉토리 제거..."
    rm -rf "$INSTALL_DIR"
    echo "   ✅ $INSTALL_DIR 제거 완료"
fi

# 3. 바로가기 제거
if [ -f "$DESKTOP_SHORTCUT" ]; then
    echo "3️⃣ 바로가기 제거..."
    rm -f "$DESKTOP_SHORTCUT"
    echo "   ✅ 바로가기 제거 완료"
fi

# 4. 백업 제거 (선택사항)
if [ -n "$BACKUPS" ]; then
    echo ""
    if [ -t 0 ]; then
        echo -e "${YELLOW}백업 파일들도 제거하시겠습니까? (y/N)${NC}"
        read -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "4️⃣ 백업 파일 제거..."
            for backup in $BACKUPS; do
                rm -rf "$backup"
                echo "   🗑️ $(basename "$backup") 제거"
            done
            echo "   ✅ 백업 제거 완료"
        else
            echo "   ℹ️ 백업 파일은 유지됩니다"
        fi
    else
        echo "   ℹ️ 파이프 실행: 백업 파일은 유지됩니다"
    fi
fi

# 5. Python 패키지 제거 (선택사항)
echo ""
if [ -t 0 ]; then
    echo -e "${YELLOW}XLT 관련 Python 패키지도 제거하시겠습니까? (y/N)${NC}"
    echo -e "${RED}⚠️ 다른 프로그램에서 사용할 수 있으니 주의하세요${NC}"
    read -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "5️⃣ Python 패키지 제거..."
        packages=("easyocr" "googletrans" "openpyxl")
        for package in "${packages[@]}"; do
            echo "   🗑️ $package 제거 시도..."
            python3 -m pip uninstall -y "$package" 2>/dev/null || echo "     (없거나 제거 실패)"
        done
        echo "   ✅ Python 패키지 정리 완료"
    fi
else
    echo "   ℹ️ 파이프 실행: Python 패키지는 유지됩니다 (다른 프로그램에서 사용할 수 있음)"
fi

# 완료
echo ""
echo -e "${GREEN}✅ XLT System 제거 완료!${NC}"
echo ""
echo -e "${BLUE}재설치하려면 (v2.0 완전 자동화 설치):${NC}"
echo "curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash"
echo ""