#!/bin/bash

# XLT System v3.0 자동 설치 스크립트
# 개인 PC용 원클릭 설치

echo "🚀 XLT System v3.0 설치를 시작합니다..."
echo "📍 피그마 디자인 → 다국어 번역 자동화 도구"
echo ""

# 시스템 정보 확인
OS=$(uname -s)
ARCH=$(uname -m)
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)

echo "🔍 시스템 정보:"
echo "  OS: $OS"
echo "  Architecture: $ARCH"
echo "  Python: $PYTHON_VERSION"
echo ""

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3가 설치되지 않았습니다."
    echo "💡 Python 3.8 이상을 설치한 후 다시 실행해주세요."
    echo "   - macOS: brew install python3"
    echo "   - Ubuntu: sudo apt install python3 python3-pip"
    echo "   - Windows: https://python.org 에서 다운로드"
    exit 1
fi

# Python 버전 체크 (3.8 이상 필요)
python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if [ $? -ne 0 ]; then
    echo "❌ Python 3.8 이상이 필요합니다. (현재: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python 환경이 준비되었습니다."
echo ""

# pip 업그레이드
echo "📦 pip 업그레이드 중..."
python3 -m pip install --upgrade pip --quiet

# 의존성 설치
echo "📚 필수 패키지 설치 중..."
echo "  - EasyOCR (OCR 엔진)"
echo "  - Google Translate (번역 엔진)"
echo "  - OpenPyXL (Excel 처리)"
echo "  - Flask (웹 서버)"
echo "  - Pillow (이미지 처리)"

pip3 install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo "✅ 모든 패키지가 성공적으로 설치되었습니다."
else
    echo "❌ 패키지 설치 중 오류가 발생했습니다."
    echo "💡 인터넷 연결을 확인하고 다시 시도해주세요."
    exit 1
fi

echo ""

# 설정 파일 생성
echo "⚙️  기본 설정 생성 중..."

# Figma 설정 파일 생성 (예제에서 복사)
if [ -f "figma_config_example.json" ] && [ ! -f "figma_config.json" ]; then
    cp figma_config_example.json figma_config.json
    echo "✅ Figma 설정 파일이 생성되었습니다."
    echo "   📝 figma_config.json 파일을 열어 Figma 토큰을 추가해주세요."
fi

# 출력 폴더 생성
mkdir -p output figma logs
echo "✅ 필요한 폴더들이 생성되었습니다."

echo ""

# 데스크톱 바로가기 생성 (macOS)
if [ "$OS" = "Darwin" ]; then
    echo "🖥️  데스크톱 바로가기 생성 중..."

    INSTALL_DIR=$(pwd)
    SHORTCUT_PATH="$HOME/Desktop/XLT System.command"

    cat > "$SHORTCUT_PATH" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
python3 stable_web_server.py
EOF

    chmod +x "$SHORTCUT_PATH"
    echo "✅ 데스크톱 바로가기가 생성되었습니다."
fi

# Linux 바로가기 생성
if [ "$OS" = "Linux" ]; then
    echo "🖥️  데스크톱 바로가기 생성 중..."

    INSTALL_DIR=$(pwd)
    DESKTOP_FILE="$HOME/Desktop/xlt-system.desktop"

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=XLT System
Comment=피그마 디자인 다국어 번역 도구
Exec=bash -c 'cd "$INSTALL_DIR" && python3 stable_web_server.py'
Icon=applications-internet
Terminal=true
Categories=Office;Development;
EOF

    chmod +x "$DESKTOP_FILE"
    echo "✅ 데스크톱 바로가기가 생성되었습니다."
fi

# 시스템 검증
echo "🔬 시스템 검증 중..."

python3 -c "
try:
    from xlt import XLTConfig, XLTPipeline
    config = XLTConfig()
    pipeline = XLTPipeline(config)
    print('✅ XLT 시스템 초기화 성공')
except Exception as e:
    print(f'❌ 초기화 실패: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 시스템 검증에 실패했습니다."
    exit 1
fi

echo ""
echo "🎉 XLT System v3.0 설치가 완료되었습니다!"
echo ""
echo "📋 사용 방법:"
echo "  1. 서버 시작:"
if [ "$OS" = "Darwin" ]; then
    echo "     - 데스크톱의 'XLT System.command' 더블클릭"
fi
echo "     - 또는 터미널에서: python3 stable_web_server.py"
echo ""
echo "  2. 웹 브라우저에서 접속:"
echo "     http://localhost:5004"
echo ""
echo "  3. 피그마 토큰 설정 (선택사항):"
echo "     figma_config.json 파일 편집"
echo ""
echo "💡 문제 해결:"
echo "  - 포트 충돌 시: lsof -i :5004"
echo "  - 서버 종료: pkill -f stable_web_server.py"
echo "  - 로그 확인: logs/ 폴더"
echo ""
echo "🌐 웹 브라우저를 열어 http://localhost:5004 에 접속하세요!"

# 자동으로 브라우저 열기 (선택사항)
read -p "🔗 지금 브라우저를 여시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v open &> /dev/null; then
        # macOS
        open http://localhost:5004 2>/dev/null &
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open http://localhost:5004 2>/dev/null &
    fi

    echo "🚀 서버를 시작합니다..."
    python3 stable_web_server.py
fi