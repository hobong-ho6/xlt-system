#!/bin/bash

# XLT System Uninstaller v5.1.0
# 완전한 XLT System 제거 스크립트 (개선된 버전)

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 전역 변수
INSTALL_DIR="$HOME/XLT-System"
DEV_DIR="$HOME/xlt-dev"
DEV_TEMP_DIR="$HOME/xlt-dev-temp"
DOCUMENTS_DIR="$HOME/Documents/XLTTT"
DESKTOP_SHORTCUT="$HOME/Desktop/XLT System (Tray).command"
LOG_FILE="$HOME/.xlt_uninstall.log"

echo -e "${YELLOW}🗑️  XLT System Uninstaller v5.1.0${NC}"
echo -e "${YELLOW}============================================${NC}"
echo -e "${BLUE}완전한 XLT System 제거 (모든 파일 및 프로세스)${NC}"
echo ""

# 사용자 확인
echo -e "${YELLOW}⚠️  이 작업은 XLT System을 완전히 제거합니다:${NC}"
echo -e "${YELLOW}   ✅ 설치된 모든 파일 삭제${NC}"
echo -e "${YELLOW}   ✅ 실행 중인 모든 프로세스 종료${NC}"
echo -e "${YELLOW}   ✅ 바로가기 및 설정 파일 삭제${NC}"
echo -e "${YELLOW}   ✅ 개발용 디렉토리 정리${NC}"
echo -e "${YELLOW}   ✅ 로그 파일 정리${NC}"
echo ""
echo -e "${RED}정말로 제거하시겠습니까? (y/N): ${NC}"
read -r confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✅ 제거가 취소되었습니다.${NC}"
    exit 0
fi

echo -e "${YELLOW}🔄 XLT System 완전 제거를 시작합니다...${NC}"
echo ""

# 로그 시작
{
    echo "XLT System Complete Uninstall Log - $(date)"
    echo "=============================================="
} > "$LOG_FILE"

# 1. 실행 중인 프로세스 완전 종료
echo -e "${YELLOW}1️⃣  실행 중인 XLT 프로세스 완전 종료 중...${NC}"

# XLT 관련 프로세스 찾기 및 종료 (확장된 목록)
PROCESSES=(
    "python.*xlt_tray.py"
    "python.*stable_web_server.py"
    "python.*main.py"
    "python.*xlt"
    "XLT System"
    "xlt_tray"
    "stable_web_server"
)

for process in "${PROCESSES[@]}"; do
    if pgrep -f "$process" > /dev/null 2>&1; then
        echo "   🔄 $process 종료 중..."
        pkill -f "$process"
        sleep 1
        # 강제 종료도 시도
        pkill -9 -f "$process" 2>/dev/null
        echo "     ✅ 종료됨" | tee -a "$LOG_FILE"
    else
        echo "   ℹ️  $process: 실행 중이지 않음" | tee -a "$LOG_FILE"
    fi
done

# 포트 5004 완전 정리
if lsof -ti:5004 >/dev/null 2>&1; then
    echo "   🔄 포트 5004 프로세스 완전 종료 중..."
    lsof -ti:5004 | xargs kill -9 2>/dev/null
    sleep 1
    echo "     ✅ 포트 정리됨" | tee -a "$LOG_FILE"
fi

# 2. 모든 XLT 디렉토리 제거
echo -e "${YELLOW}2️⃣  모든 XLT 디렉토리 제거 중...${NC}"

DIRECTORIES=(
    "$INSTALL_DIR"
    "$DEV_DIR"
    "$DEV_TEMP_DIR"
    "$DOCUMENTS_DIR"
)

for dir in "${DIRECTORIES[@]}"; do
    if [ -d "$dir" ]; then
        echo "   🔄 $(basename "$dir") 삭제 중..."
        rm -rf "$dir"
        echo "     ✅ 디렉토리 삭제됨: $dir" | tee -a "$LOG_FILE"
    else
        echo "   ℹ️  $(basename "$dir"): 존재하지 않음" | tee -a "$LOG_FILE"
    fi
done

# 3. 바로가기 및 설정 파일 제거
echo -e "${YELLOW}3️⃣  바로가기 및 설정 파일 제거 중...${NC}"

# 바로가기 파일들
SHORTCUTS=(
    "$DESKTOP_SHORTCUT"
    "$HOME/Desktop/XLT System.command"
)

for shortcut in "${SHORTCUTS[@]}"; do
    if [ -f "$shortcut" ]; then
        echo "   🔄 $(basename "$shortcut") 삭제 중..."
        rm -f "$shortcut"
        echo "     ✅ 바로가기 삭제됨" | tee -a "$LOG_FILE"
    else
        echo "   ℹ️  $(basename "$shortcut"): 존재하지 않음" | tee -a "$LOG_FILE"
    fi
done

# 4. 로그 및 설정 파일 완전 정리
echo -e "${YELLOW}4️⃣  로그 및 설정 파일 완전 정리 중...${NC}"

# 로그 및 설정 파일들
CONFIG_FILES=(
    "$HOME/.xlt_install.log"
    "$HOME/.xlt_update.log"
    "$HOME/.xlt/github_token"
    "$HOME/.xlt"
    "$HOME/.claude/projects/-Users-user-Documents-XLTTT"
)

for config_file in "${CONFIG_FILES[@]}"; do
    if [ -e "$config_file" ]; then
        echo "   🔄 $(basename "$config_file") 삭제 중..."
        rm -rf "$config_file"
        echo "     ✅ 설정 파일 삭제됨" | tee -a "$LOG_FILE"
    else
        echo "   ℹ️  $(basename "$config_file"): 존재하지 않음" | tee -a "$LOG_FILE"
    fi
done

# 5. 임시 파일 및 캐시 정리
echo -e "${YELLOW}5️⃣  임시 파일 및 캐시 정리 중...${NC}"

# 임시 파일 패턴
TEMP_PATTERNS=(
    "/tmp/*xlt*"
    "/tmp/*XLT*"
    "$HOME/.cache/*xlt*"
)

for pattern in "${TEMP_PATTERNS[@]}"; do
    if ls $pattern 1> /dev/null 2>&1; then
        echo "   🔄 임시 파일 삭제 중: $pattern"
        rm -rf $pattern 2>/dev/null
        echo "     ✅ 임시 파일 정리됨" | tee -a "$LOG_FILE"
    fi
done

# 6. 최종 확인 및 검증
echo -e "${YELLOW}6️⃣  제거 완료 검증 중...${NC}"

REMAINING_FILES=0
ISSUES=()

# 디렉토리 검증
for dir in "${DIRECTORIES[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ❌ 디렉토리가 여전히 존재함: $dir"
        ISSUES+=("디렉토리: $dir")
        ((REMAINING_FILES++))
    fi
done

# 바로가기 검증
for shortcut in "${SHORTCUTS[@]}"; do
    if [ -f "$shortcut" ]; then
        echo "   ❌ 바로가기가 여전히 존재함: $shortcut"
        ISSUES+=("바로가기: $shortcut")
        ((REMAINING_FILES++))
    fi
done

# 프로세스 검증
if pgrep -f "python.*xlt\|XLT System" > /dev/null 2>&1; then
    echo "   ❌ XLT 프로세스가 여전히 실행 중"
    ISSUES+=("실행 중인 프로세스")
    ((REMAINING_FILES++))
fi

# 포트 검증
if lsof -ti:5004 >/dev/null 2>&1; then
    echo "   ❌ 포트 5004가 여전히 사용 중"
    ISSUES+=("포트 5004")
    ((REMAINING_FILES++))
fi

# 결과 출력
echo ""
echo -e "${BLUE}============================================${NC}"
if [ $REMAINING_FILES -eq 0 ]; then
    echo -e "${GREEN}🎉 XLT System이 완전히 제거되었습니다!${NC}"
    echo -e "${GREEN}   ✅ 모든 파일과 프로세스가 정리되었습니다${NC}"
    echo -e "${GREEN}   ✅ 모든 디렉토리가 삭제되었습니다${NC}"
    echo -e "${GREEN}   ✅ 모든 설정과 로그가 정리되었습니다${NC}"

    # 언인스톨 로그도 삭제 (마지막에)
    echo -e "${BLUE}📋 언인스톨 로그 삭제 중...${NC}"
    sleep 2
    rm -f "$LOG_FILE"

else
    echo -e "${RED}⚠️  일부 항목이 완전히 제거되지 않았습니다 (${REMAINING_FILES}개):${NC}"
    for issue in "${ISSUES[@]}"; do
        echo -e "${YELLOW}   - $issue${NC}"
    done
    echo ""
    echo -e "${YELLOW}💡 수동 정리 명령어:${NC}"
    echo -e "${BLUE}   sudo rm -rf ~/XLT-System ~/xlt-dev ~/Documents/XLTTT${NC}"
    echo -e "${BLUE}   pkill -9 -f python.*xlt${NC}"
    echo -e "${BLUE}   sudo lsof -ti:5004 | xargs kill -9${NC}"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${YELLOW}🙏 XLT System을 사용해주셔서 감사합니다!${NC}"
echo -e "${BLUE}   재설치: curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash${NC}"
echo ""