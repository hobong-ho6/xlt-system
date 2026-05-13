#!/bin/bash

# XLT System v3.0 스마트 설치 스크립트 (버전 비교 + 자동 업데이트)
# GitHub에서 최신 버전 확인 후 필요시에만 다운로드

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 로고 표시
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        XLT System v3.0 스마트 설치           ║${NC}"
echo -e "${BLUE}║      버전 비교 + 자동 업데이트 지원          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# GitHub 저장소 정보
GITHUB_USER="hobong-ho6"                       # GitHub 사용자명
GITHUB_REPO="xlt-system"                       # 저장소명
GITHUB_BRANCH="main"                           # 브랜치명
LOCAL_INSTALL_DIR="$HOME/XLT-System"           # 로컬 설치 디렉토리

# API URLs (계정 불필요)
RELEASES_API="https://api.github.com/repos/${GITHUB_USER}/${GITHUB_REPO}/releases/latest"
DOWNLOAD_URL="https://github.com/${GITHUB_USER}/${GITHUB_REPO}/archive/refs/heads/${GITHUB_BRANCH}.zip"

# 오류 처리 함수
handle_error() {
    echo ""
    echo -e "${RED}❌ 오류 발생: $1${NC}"
    echo -e "${YELLOW}💡 문제 해결:${NC}"
    echo "   1. 인터넷 연결을 확인하세요"
    echo "   2. GitHub 저장소가 Public으로 설정되어 있는지 확인하세요"
    echo "   3. 방화벽 설정을 확인하세요"
    echo ""
    exit 1
}

# 버전 비교 함수
version_compare() {
    if [[ $1 == $2 ]]; then
        echo "0"  # 같음
    elif [[ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" == "$1" ]]; then
        echo "1"  # $1이 더 낮음 (업데이트 필요)
    else
        echo "-1" # $1이 더 높음
    fi
}

# 로컬 버전 확인 함수
get_local_version() {
    if [ -f "$LOCAL_INSTALL_DIR/version.json" ]; then
        if command -v python3 &> /dev/null; then
            python3 -c "
import json
try:
    with open('$LOCAL_INSTALL_DIR/version.json', 'r') as f:
        data = json.load(f)
    print(data.get('version', '0.0.0'))
except:
    print('0.0.0')
" 2>/dev/null || echo "0.0.0"
        else
            # Python이 없는 경우 간단한 파싱
            grep '"version"' "$LOCAL_INSTALL_DIR/version.json" | sed 's/.*"version".*"\([^"]*\)".*/\1/' 2>/dev/null || echo "0.0.0"
        fi
    else
        echo "0.0.0"  # 설치되지 않음
    fi
}

# GitHub에서 최신 버전 확인 함수
get_remote_version() {
    echo -e "${BLUE}🌐 GitHub에서 최신 버전 확인 중...${NC}"

    if command -v curl &> /dev/null; then
        # GitHub API로 최신 릴리스 확인 (계정 불필요)
        RELEASE_INFO=$(curl -s "$RELEASES_API" 2>/dev/null || echo "")

        if [ -n "$RELEASE_INFO" ] && echo "$RELEASE_INFO" | grep -q "tag_name"; then
            # 릴리스가 있는 경우 tag_name에서 버전 추출
            echo "$RELEASE_INFO" | grep '"tag_name"' | sed 's/.*"tag_name".*"\([^"]*\)".*/\1/' | sed 's/^v//'
        else
            # 릴리스가 없는 경우 version.json에서 버전 확인
            VERSION_JSON=$(curl -s "https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}/version.json" 2>/dev/null || echo "")

            if [ -n "$VERSION_JSON" ] && echo "$VERSION_JSON" | grep -q "version"; then
                echo "$VERSION_JSON" | grep '"version"' | sed 's/.*"version".*"\([^"]*\)".*/\1/'
            else
                echo "unknown"
            fi
        fi
    else
        echo "unknown"
    fi
}

# 설치 진행 함수
perform_installation() {
    local install_type="$1"  # "install" 또는 "update"

    echo -e "${BLUE}📥 XLT System 다운로드 중...${NC}"

    # 임시 디렉토리 생성
    TEMP_DIR=$(mktemp -d)
    ZIP_FILE="$TEMP_DIR/xlt-system.zip"

    # ZIP 파일 다운로드
    echo "   📦 GitHub에서 소스코드 다운로드..."
    if command -v curl &> /dev/null; then
        curl -L "$DOWNLOAD_URL" -o "$ZIP_FILE" --progress-bar || handle_error "다운로드 실패"
    elif command -v wget &> /dev/null; then
        wget "$DOWNLOAD_URL" -O "$ZIP_FILE" --progress=bar || handle_error "다운로드 실패"
    else
        handle_error "curl 또는 wget이 필요합니다"
    fi

    # 기존 설치 백업 (업데이트인 경우)
    if [ "$install_type" == "update" ] && [ -d "$LOCAL_INSTALL_DIR" ]; then
        BACKUP_DIR="${LOCAL_INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "   💾 기존 설치 백업: $(basename "$BACKUP_DIR")"
        cp -r "$LOCAL_INSTALL_DIR" "$BACKUP_DIR"
    fi

    # 압축 해제
    echo "   📂 압축 해제 중..."
    cd "$TEMP_DIR"
    unzip -q "$ZIP_FILE" || handle_error "압축 해제 실패"

    # 압축 해제된 디렉토리 찾기
    EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "${GITHUB_REPO}-*" | head -1)
    if [ -z "$EXTRACTED_DIR" ]; then
        handle_error "압축 해제된 디렉토리를 찾을 수 없습니다"
    fi

    # 최종 설치 위치로 이동
    if [ -d "$LOCAL_INSTALL_DIR" ]; then
        rm -rf "$LOCAL_INSTALL_DIR"
    fi

    mkdir -p "$(dirname "$LOCAL_INSTALL_DIR")"
    mv "$EXTRACTED_DIR" "$LOCAL_INSTALL_DIR" || handle_error "설치 실패"

    # 임시 파일 정리
    rm -rf "$TEMP_DIR"

    echo -e "${GREEN}✅ 다운로드 완료${NC}"

    # 설치 스크립트 실행
    echo -e "${BLUE}🚀 XLT System 설치 시작...${NC}"
    cd "$LOCAL_INSTALL_DIR"

    # 설치 스크립트 찾기 및 실행
    INSTALL_SCRIPT=""
    if [ -f "install/install_mac_complete_auto.command" ]; then
        INSTALL_SCRIPT="install/install_mac_complete_auto.command"
    elif [ -f "install_mac_complete_auto.command" ]; then
        INSTALL_SCRIPT="install_mac_complete_auto.command"
    else
        handle_error "설치 스크립트를 찾을 수 없습니다"
    fi

    echo "   🎯 설치 스크립트: $INSTALL_SCRIPT"
    chmod +x "$INSTALL_SCRIPT"
    ./"$INSTALL_SCRIPT" || handle_error "설치 스크립트 실행 실패"
}

# 메인 실행 로직
echo -e "${BLUE}🔍 버전 확인 중...${NC}"

# 로컬 버전 확인
LOCAL_VERSION=$(get_local_version)
echo "   📱 로컬 버전: ${LOCAL_VERSION}"

if [ "$LOCAL_VERSION" != "0.0.0" ]; then
    echo -e "${GREEN}✅ XLT System이 이미 설치되어 있습니다${NC}"
    echo "   📂 설치 위치: $LOCAL_INSTALL_DIR"
fi

# 원격 버전 확인
REMOTE_VERSION=$(get_remote_version)

if [ "$REMOTE_VERSION" == "unknown" ]; then
    echo -e "${YELLOW}⚠️ 원격 버전을 확인할 수 없습니다${NC}"
    echo "   인터넷 연결 또는 저장소 접근에 문제가 있을 수 있습니다."
    echo ""

    if [ "$LOCAL_VERSION" == "0.0.0" ]; then
        read -p "그래도 설치를 진행하시겠습니까? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            perform_installation "install"
        else
            echo "설치를 취소합니다."
            exit 0
        fi
    else
        echo "기존 설치된 버전을 계속 사용하세요."
        exit 0
    fi
else
    echo "   🌐 최신 버전: ${REMOTE_VERSION}"

    # 버전 비교
    if [ "$LOCAL_VERSION" == "0.0.0" ]; then
        # 새로 설치
        echo ""
        echo -e "${GREEN}🆕 새로운 XLT System 설치${NC}"
        echo "   버전: v${REMOTE_VERSION}"
        echo ""
        read -p "설치를 진행하시겠습니까? (Y/n): " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            perform_installation "install"
        else
            echo "설치를 취소합니다."
            exit 0
        fi

    else
        # 버전 비교
        COMPARISON=$(version_compare "$LOCAL_VERSION" "$REMOTE_VERSION")

        if [ "$COMPARISON" == "0" ]; then
            # 동일한 버전
            echo ""
            echo -e "${GREEN}✅ 최신 버전이 이미 설치되어 있습니다!${NC}"
            echo "   현재 버전: v${LOCAL_VERSION}"
            echo ""
            echo -e "${YELLOW}💡 바탕화면의 'XLT System.command' 파일을 더블클릭하여 시작하세요!${NC}"

        elif [ "$COMPARISON" == "1" ]; then
            # 업데이트 가능
            echo ""
            echo -e "${YELLOW}🔄 업데이트가 사용 가능합니다!${NC}"
            echo "   현재 버전: v${LOCAL_VERSION}"
            echo "   최신 버전: v${REMOTE_VERSION}"
            echo ""

            read -p "업데이트하시겠습니까? (Y/n): " -n 1 -r
            echo ""

            if [[ ! $REPLY =~ ^[Nn]$ ]]; then
                perform_installation "update"
                echo ""
                echo -e "${GREEN}🎉 v${LOCAL_VERSION} → v${REMOTE_VERSION} 업데이트 완료!${NC}"
            else
                echo "업데이트를 취소합니다. 기존 버전을 계속 사용하세요."
            fi

        else
            # 로컬 버전이 더 높음 (개발 버전?)
            echo ""
            echo -e "${CYAN}🚀 개발 버전이 설치되어 있습니다${NC}"
            echo "   현재 버전: v${LOCAL_VERSION} (공식: v${REMOTE_VERSION})"
            echo "   개발 버전을 계속 사용하세요."
        fi
    fi
fi

echo ""
echo -e "${BLUE}📊 설치 정보:${NC}"
echo "   📂 설치 위치: $LOCAL_INSTALL_DIR"
echo "   🌐 GitHub: https://github.com/${GITHUB_USER}/${GITHUB_REPO}"
echo "   📱 바로가기: 데스크톱의 'XLT System.command'"
echo ""
echo -e "${GREEN}🎉 XLT System 준비 완료!${NC}"