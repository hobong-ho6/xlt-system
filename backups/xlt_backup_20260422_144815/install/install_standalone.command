#!/bin/bash

# XLT System v3.0 독립형 설치 스크립트
# GitHub에서 전체 프로젝트를 자동 다운로드하여 설치 (계정 불필요)

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 로고 표시
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          XLT System v3.0 독립형 설치         ║${NC}"
echo -e "${BLUE}║    GitHub 자동 다운로드 (계정 불필요)         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# GitHub 저장소 정보 (Public 저장소 - 계정 불필요)
GITHUB_USER="hobong-ho6"             # GitHub 사용자명
GITHUB_REPO="xlt-system"             # 저장소명
GITHUB_BRANCH="main"                 # 브랜치명 (main 또는 master)
INSTALL_DIR="$HOME/XLT-System"

# 다운로드 URL (ZIP 파일 - 계정 불필요)
DOWNLOAD_URL="https://github.com/${GITHUB_USER}/${GITHUB_REPO}/archive/refs/heads/${GITHUB_BRANCH}.zip"

# 오류 처리 함수
handle_error() {
    echo ""
    echo -e "${RED}❌ 설치 중 오류가 발생했습니다: $1${NC}"
    echo -e "${YELLOW}💡 문제 해결:${NC}"
    echo "   1. 인터넷 연결을 확인하세요"
    echo "   2. GitHub 저장소가 Public으로 설정되어 있는지 확인하세요"
    echo "   3. 방화벽 설정을 확인하세요"
    echo ""
    exit 1
}

echo -e "${BLUE}🌐 GitHub에서 XLT System 다운로드 중...${NC}"
echo "   📦 저장소: https://github.com/${GITHUB_USER}/${GITHUB_REPO}"
echo "   🔓 Public 저장소 - GitHub 계정 불필요"
echo "   📥 다운로드 방식: ZIP 파일 직접 다운로드"
echo ""

# 기존 설치 디렉토리 확인
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}⚠️ 기존 설치가 발견되었습니다: $INSTALL_DIR${NC}"
    read -p "기존 설치를 제거하고 새로 설치하시겠습니까? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   🗑️ 기존 설치 제거 중..."
        rm -rf "$INSTALL_DIR"
    else
        echo "   ⏭️ 설치를 중단합니다."
        exit 0
    fi
fi

# 임시 디렉토리 생성
TEMP_DIR=$(mktemp -d)
ZIP_FILE="$TEMP_DIR/xlt-system.zip"

echo "   📁 임시 디렉토리: $TEMP_DIR"

# ZIP 파일 다운로드 (curl 사용, 계정 불필요)
echo "   📥 ZIP 파일 다운로드 중..."
if command -v curl &> /dev/null; then
    curl -L "$DOWNLOAD_URL" -o "$ZIP_FILE" --progress-bar || handle_error "curl 다운로드 실패"
elif command -v wget &> /dev/null; then
    wget "$DOWNLOAD_URL" -O "$ZIP_FILE" --progress=bar || handle_error "wget 다운로드 실패"
else
    handle_error "curl 또는 wget이 설치되지 않았습니다"
fi

# ZIP 파일 압축 해제
echo "   📦 압축 해제 중..."
cd "$TEMP_DIR"

if command -v unzip &> /dev/null; then
    unzip -q "$ZIP_FILE" || handle_error "압축 해제 실패"
else
    handle_error "unzip 명령어를 찾을 수 없습니다"
fi

# 압축 해제된 디렉토리 찾기
EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "${GITHUB_REPO}-*" | head -1)
if [ -z "$EXTRACTED_DIR" ]; then
    handle_error "압축 해제된 디렉토리를 찾을 수 없습니다"
fi

echo "   📂 압축 해제 완료: $EXTRACTED_DIR"

# 최종 설치 디렉토리로 이동
echo "   📁 설치 위치로 이동: $INSTALL_DIR"
mkdir -p "$(dirname "$INSTALL_DIR")"
mv "$EXTRACTED_DIR" "$INSTALL_DIR" || handle_error "설치 디렉토리 이동 실패"

# 임시 파일 정리
echo "   🧹 임시 파일 정리 중..."
rm -rf "$TEMP_DIR"

echo -e "${GREEN}✅ GitHub 다운로드 완료${NC}"
echo ""

# 다운로드된 프로젝트에서 설치 스크립트 실행
echo -e "${BLUE}🚀 XLT System 설치 시작...${NC}"
cd "$INSTALL_DIR"

# 설치 스크립트 확인 및 실행
INSTALL_SCRIPT=""
if [ -f "install/install_mac_complete_auto.command" ]; then
    INSTALL_SCRIPT="install/install_mac_complete_auto.command"
elif [ -f "install_mac_complete_auto.command" ]; then
    INSTALL_SCRIPT="install_mac_complete_auto.command"
else
    echo -e "${RED}❌ 설치 스크립트를 찾을 수 없습니다.${NC}"
    echo "   다음 위치를 확인했습니다:"
    echo "   - install/install_mac_complete_auto.command"
    echo "   - install_mac_complete_auto.command"
    echo ""
    echo "   📁 다운로드된 파일들:"
    ls -la
    handle_error "설치 스크립트 없음"
fi

echo "   🎯 설치 스크립트 발견: $INSTALL_SCRIPT"
echo "   ⚡ 완전 자동 설치 실행 중..."
echo ""

# 설치 스크립트 실행
chmod +x "$INSTALL_SCRIPT"
./"$INSTALL_SCRIPT" || handle_error "설치 스크립트 실행 실패"

echo ""
echo -e "${GREEN}🎉 XLT System 독립형 설치가 완료되었습니다!${NC}"
echo ""
echo -e "${BLUE}📊 설치 요약:${NC}"
echo "   📂 설치 위치: $INSTALL_DIR"
echo "   🌐 소스: https://github.com/${GITHUB_USER}/${GITHUB_REPO}"
echo "   🔓 GitHub 계정: 불필요 (Public 저장소)"
echo "   📱 바로가기: 데스크톱의 'XLT System.command'"
echo ""
echo -e "${YELLOW}💡 바탕화면의 'XLT System.command' 파일을 더블클릭하여 시작하세요!${NC}"

# 브라우저로 확인 페이지 열기 (선택사항)
read -p "설치 확인을 위해 웹 브라우저를 열까요? (Y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "🌐 웹 브라우저에서 http://localhost:5004 열기..."
    open http://localhost:5004 2>/dev/null || echo "   수동으로 http://localhost:5004에 접속해주세요."
fi