#!/bin/bash

# XLT System v3.0 macOS 전용 원클릭 설치 스크립트
# 피그마 디자인 → 다국어 번역 자동화 도구

set -e  # 오류 발생 시 스크립트 중단

# install 폴더에서 실행되는 경우 상위 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(basename "$SCRIPT_DIR")" == "install" ]]; then
    cd "$SCRIPT_DIR/.."
    echo "📂 XLT System 프로젝트 디렉토리로 이동: $(pwd)"
fi

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
echo -e "${BLUE}║               XLT System v3.0                ║${NC}"
echo -e "${BLUE}║        피그마 → 다국어 번역 자동화 도구        ║${NC}"
echo -e "${BLUE}║               macOS 전용 설치               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# 진행 단계 함수
step_counter=0
show_step() {
    step_counter=$((step_counter + 1))
    echo -e "${PURPLE}[${step_counter}/8]${NC} $1"
    echo "────────────────────────────────────────"
}

# 오류 처리 함수
handle_error() {
    echo ""
    echo -e "${RED}❌ 설치 중 오류가 발생했습니다: $1${NC}"
    echo -e "${YELLOW}💡 문제 해결:${NC}"
    echo "   1. 인터넷 연결을 확인하세요"
    echo "   2. Python 3.8+ 설치를 확인하세요"
    echo "   3. 관리자 권한으로 실행해보세요: sudo ./install_mac.sh"
    echo ""
    exit 1
}

# 1단계: 시스템 환경 확인
show_step "시스템 환경 확인"

# macOS 확인
if [[ "$OSTYPE" != "darwin"* ]]; then
    handle_error "이 스크립트는 macOS 전용입니다."
fi

echo -e "${GREEN}✅ macOS 시스템 확인 완료${NC}"

# Python 설치 확인
if ! command -v python3 &> /dev/null; then
    handle_error "Python 3가 설치되지 않았습니다. brew install python3 또는 python.org에서 설치하세요."
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} 감지됨${NC}"

# Python 버전 체크 (3.8 이상)
python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" || handle_error "Python 3.8 이상이 필요합니다. (현재: $PYTHON_VERSION)"

# 2단계: pip 및 가상환경 준비
show_step "패키지 관리자 업그레이드"

echo "📦 pip 업그레이드 중..."
python3 -m pip install --upgrade pip --user --quiet || handle_error "pip 업그레이드 실패"
echo -e "${GREEN}✅ pip 업그레이드 완료${NC}"

# 3단계: 의존성 설치
show_step "XLT System 의존성 설치"

echo "📚 필수 패키지 설치 중... (약 2-3분 소요)"
echo "   - EasyOCR (OCR 엔진)"
echo "   - Google Translate (번역 API)"
echo "   - Flask (웹 서버)"
echo "   - OpenPyXL (Excel 처리)"
echo "   - Pillow (이미지 처리)"
echo "   - PysTray (시스템 트레이)"

# 설치 진행률 표시
pip3 install -r requirements.txt --user --quiet --progress-bar off || handle_error "패키지 설치 실패"

echo -e "${GREEN}✅ 모든 의존성 설치 완료${NC}"

# 4단계: 설정 파일 생성
show_step "기본 설정 생성"

# Figma 설정 파일 생성
if [ -f "figma_config_example.json" ] && [ ! -f "figma_config.json" ]; then
    cp figma_config_example.json figma_config.json
    echo -e "${GREEN}✅ Figma 설정 파일 생성됨${NC}"
fi

# 필요한 디렉토리 생성
mkdir -p output figma logs
echo -e "${GREEN}✅ 작업 디렉토리 생성 완료${NC}"

# 5단계: 시스템 검증
show_step "XLT System 초기화 검증"

# 현재 디렉토리를 Python path에 추가하여 xlt 패키지 검증
INSTALL_DIR=$(pwd)
PYTHONPATH="$INSTALL_DIR:$PYTHONPATH" python3 -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
try:
    from xlt import XLTConfig, XLTPipeline
    config = XLTConfig()
    pipeline = XLTPipeline(config)
    print('✅ XLT System 초기화 성공')
except Exception as e:
    print(f'❌ 초기화 실패: {e}')
    exit(1)
" || handle_error "XLT System 검증 실패"

# 6단계: 데스크톱 바로가기 생성
show_step "데스크톱 바로가기 생성"

INSTALL_DIR=$(pwd)
SHORTCUT_PATH="$HOME/Desktop/XLT System.command"

cat > "$SHORTCUT_PATH" << EOF
#!/bin/bash
# XLT System v3.0 시작 스크립트

echo "🚀 XLT System v3.0 시작 중..."
echo "📍 피그마 디자인 → 다국어 번역 자동화 도구"
echo ""

cd "$INSTALL_DIR"

# Python path 설정 (xlt 패키지 인식을 위해)
export PYTHONPATH="$INSTALL_DIR:\$PYTHONPATH"

# 서버 상태 확인
if lsof -i :5004 >/dev/null 2>&1; then
    echo "⚠️  포트 5004가 이미 사용 중입니다."
    echo "   기존 서버를 종료하고 새로 시작합니다..."
    pkill -f stable_web_server.py 2>/dev/null || true
    sleep 2
fi

echo "🌐 웹 서버 시작 중... (http://localhost:5004)"
echo "   웹 브라우저가 자동으로 열립니다."
echo ""
echo "⚡ 종료하려면 Ctrl+C를 누르세요."
echo ""

# 브라우저 자동 열기 (3초 후)
(sleep 3 && open http://localhost:5004) &

# XLT 웹 서버 시작
python3 stable_web_server.py
EOF

chmod +x "$SHORTCUT_PATH"
echo -e "${GREEN}✅ '$(basename "$SHORTCUT_PATH")' 바로가기 생성됨${NC}"

# 7단계: 시스템 트레이 앱 설정 (선택사항)
show_step "시스템 트레이 앱 설정 (선택사항)"

echo "시스템 트레이에서 XLT System을 관리하시겠습니까?"
echo "트레이 앱을 사용하면 메뉴 바에서 서버 시작/종료가 가능합니다."
echo ""
read -p "트레이 앱을 설치하시겠습니까? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📱 시스템 트레이 앱 설정 중..."

    # PysTray 설치 확인
    python3 -c "import pystray" 2>/dev/null || {
        echo "   PysTray 설치 중..."
        pip3 install pystray --user --quiet || echo "⚠️  PysTray 설치 실패 (선택사항이므로 계속 진행)"
    }

    # 트레이 앱 바로가기 생성
    TRAY_SHORTCUT="$HOME/Desktop/XLT System (Tray).command"
    cat > "$TRAY_SHORTCUT" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
echo "🎨 XLT System 트레이 앱 시작 중..."
python3 xlt_tray.py
EOF
    chmod +x "$TRAY_SHORTCUT"
    echo -e "${GREEN}✅ 트레이 앱 바로가기 생성됨${NC}"
fi

# 8단계: 설치 완료 및 안내
show_step "설치 완료"

echo ""
echo -e "${GREEN}🎉 XLT System v3.0 macOS 설치가 완료되었습니다!${NC}"
echo ""
echo -e "${BLUE}📋 사용 방법:${NC}"
echo "  1️⃣  데스크톱의 '${YELLOW}XLT System.command${NC}' 더블클릭"
echo "  2️⃣  웹 브라우저에서 ${BLUE}http://localhost:5004${NC} 자동 접속"
echo "  3️⃣  Figma URL을 입력하여 번역 시작!"
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${PURPLE}🎨 트레이 앱:${NC}"
    echo "     '${YELLOW}XLT System (Tray).command${NC}' - 메뉴 바에서 관리"
    echo ""
fi

echo -e "${BLUE}⚙️  추가 설정 (선택사항):${NC}"
echo "  • Figma 토큰: ${YELLOW}figma_config.json${NC} 파일 편집"
echo "  • 자동 시작: ${YELLOW}python3 setup_autostart.py${NC} 실행"
echo ""

echo -e "${BLUE}🛠️  문제 해결:${NC}"
echo "  • 포트 충돌: ${YELLOW}lsof -i :5004${NC}"
echo "  • 서버 재시작: 터미널에서 Ctrl+C 후 다시 시작"
echo "  • 로그 확인: ${YELLOW}logs/${NC} 폴더"
echo ""

echo -e "${YELLOW}💡 지금 XLT System을 시작하시겠습니까?${NC}"
read -p "시작하기 (Y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${GREEN}🚀 XLT System 시작 중...${NC}"

    # Python path 설정
    export PYTHONPATH="$(pwd):$PYTHONPATH"

    # 브라우저 열기
    open http://localhost:5004 2>/dev/null &

    # 서버 시작 (3초 후)
    sleep 3
    python3 stable_web_server.py
else
    echo ""
    echo -e "${BLUE}📌 나중에 데스크톱의 'XLT System.command' 파일을 실행하세요!${NC}"
    echo ""
    echo -e "${YELLOW}설치가 완료되었습니다. Enter 키를 누르면 창이 닫힙니다.${NC}"
    read
fi