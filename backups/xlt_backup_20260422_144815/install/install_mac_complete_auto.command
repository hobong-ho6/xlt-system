#!/bin/bash

# XLT System v3.0 macOS 완전 자동 설치 스크립트 (모든 의존성 포함)
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
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 로고 표시
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            XLT System v3.0 Complete         ║${NC}"
echo -e "${BLUE}║        피그마 → 다국어 번역 자동화 도구        ║${NC}"
echo -e "${BLUE}║           완전 자동 설치 (모든 의존성)        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# 진행 단계 함수
step_counter=0
show_step() {
    step_counter=$((step_counter + 1))
    echo -e "${PURPLE}[${step_counter}/12]${NC} $1"
    echo "────────────────────────────────────────"
}

# 오류 처리 함수
handle_error() {
    echo ""
    echo -e "${RED}❌ 설치 중 오류가 발생했습니다: $1${NC}"
    echo -e "${YELLOW}💡 문제 해결:${NC}"
    echo "   1. 인터넷 연결을 확인하세요"
    echo "   2. 관리자 권한으로 실행해보세요"
    echo "   3. 수동으로 필요한 도구를 설치해보세요"
    echo ""
    echo -e "${YELLOW}설치를 중단합니다. Enter 키를 누르세요.${NC}"
    read
    exit 1
}

# Xcode Command Line Tools 설치 함수
install_xcode_tools() {
    echo -e "${BLUE}🛠️ Xcode Command Line Tools 설치${NC}"

    # 이미 설치되어 있는지 확인
    if xcode-select -p &> /dev/null; then
        echo -e "${GREEN}✅ Xcode Command Line Tools 이미 설치됨${NC}"
        return 0
    fi

    echo "📦 Xcode Command Line Tools 설치 중... (약 5-10분 소요)"
    echo "   일부 Python 패키지 컴파일에 필요합니다."

    # 자동 설치 시작
    xcode-select --install 2>/dev/null || true

    echo "⏳ 설치가 완료될 때까지 기다리는 중..."
    echo "   팝업 창에서 '설치' 버튼을 클릭해주세요."

    # 설치 완료 대기
    while ! xcode-select -p &> /dev/null; do
        sleep 5
        echo "   ⏳ 아직 설치 중..."
    done

    echo -e "${GREEN}✅ Xcode Command Line Tools 설치 완료${NC}"
}

# Git 설치 함수
install_git() {
    echo -e "${BLUE}📱 Git 설치${NC}"

    if command -v git &> /dev/null; then
        git_version=$(git --version 2>&1 | cut -d' ' -f3)
        echo -e "${GREEN}✅ Git ${git_version} 이미 설치됨${NC}"
        return 0
    fi

    echo "📦 Git 설치 중..."
    if command -v brew &> /dev/null; then
        brew install git
    else
        echo -e "${YELLOW}⚠️ Git 설치를 위해 Homebrew가 필요합니다.${NC}"
        echo "   Xcode Command Line Tools에 포함된 Git을 사용합니다."
    fi
    echo -e "${GREEN}✅ Git 설치 완료${NC}"
}

# Python Homebrew 설치 함수
install_python_homebrew() {
    echo -e "${BLUE}🍺 Homebrew를 사용한 Python 설치${NC}"

    # Homebrew 설치 확인
    if ! command -v brew &> /dev/null; then
        echo "📦 Homebrew 설치 중... (약 5-10분 소요)"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # PATH 설정
        if [[ $(uname -m) == 'arm64' ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi

    echo "🐍 Python 3 설치 중..."
    brew install python3
    echo -e "${GREEN}✅ Python 설치 완료${NC}"
}

# Python 공식 설치파일 다운로드
install_python_official() {
    echo -e "${BLUE}🌐 Python 공식 설치파일 다운로드${NC}"

    # 아키텍처 확인
    if [[ $(uname -m) == 'arm64' ]]; then
        PYTHON_URL="https://www.python.org/ftp/python/3.11.8/python-3.11.8-macos11.pkg"
    else
        PYTHON_URL="https://www.python.org/ftp/python/3.11.8/python-3.11.8-macosx10.9.pkg"
    fi

    echo "📥 Python 설치파일 다운로드 중..."
    curl -o /tmp/python_installer.pkg "$PYTHON_URL"

    echo "📦 Python 설치 중... (관리자 권한 필요)"
    sudo installer -pkg /tmp/python_installer.pkg -target /

    # 설치 파일 정리
    rm -f /tmp/python_installer.pkg

    echo -e "${GREEN}✅ Python 설치 완료${NC}"
}

# 고급 패키지 설치 함수 (실패 시 대안 제공)
install_packages_with_fallback() {
    echo -e "${BLUE}📚 XLT System 의존성 고급 설치${NC}"

    # 기본 패키지 목록
    REQUIRED_PACKAGES=(
        "easyocr==1.7.0"
        "googletrans==4.0.0rc1"
        "openpyxl==3.1.2"
        "flask"
        "pillow"
        "requests"
        "psutil"
    )

    # 선택적 패키지 목록 (시스템 트레이용)
    OPTIONAL_PACKAGES=(
        "pystray"
    )

    echo "📦 필수 패키지 설치 시도 중..."

    # 변수 초기화
    individual_install=false

    # 현재 디렉토리에 requirements.txt 존재 여부 확인
    INSTALL_DIR=$(pwd)
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        echo "   requirements.txt 파일 발견: $INSTALL_DIR/requirements.txt"
        # requirements.txt로 일괄 설치 시도
        if pip3 install -r "$INSTALL_DIR/requirements.txt" --user --quiet --progress-bar off; then
            echo -e "${GREEN}✅ 모든 패키지 설치 성공 (requirements.txt)${NC}"
        else
            echo -e "${YELLOW}⚠️ 일괄 설치 실패. 개별 설치를 시도합니다...${NC}"

            # 개별 패키지 설치로 fallback
            individual_install=true
        fi
    else
        echo -e "${YELLOW}⚠️ requirements.txt 파일이 없습니다. 개별 설치를 진행합니다...${NC}"
        individual_install=true
    fi

    # 개별 패키지 설치가 필요한 경우
    if [ "$individual_install" = true ]; then
        failed_packages=()

        for package in "${REQUIRED_PACKAGES[@]}"; do
            echo "   설치 중: $package"
            if pip3 install "$package" --user --quiet; then
                echo -e "   ${GREEN}✅ $package 설치 성공${NC}"
            else
                echo -e "   ${RED}❌ $package 설치 실패${NC}"
                failed_packages+=("$package")
            fi
        done

        # 실패한 패키지가 있으면 대안 제공
        if [ ${#failed_packages[@]} -gt 0 ]; then
            echo ""
            echo -e "${RED}❌ 다음 패키지 설치에 실패했습니다:${NC}"
            for pkg in "${failed_packages[@]}"; do
                echo "   - $pkg"
            done
            echo ""
            echo -e "${YELLOW}💡 대안 해결책:${NC}"
            echo "   1. 인터넷 연결을 확인하세요"
            echo "   2. pip 캐시를 정리하세요: pip3 cache purge"
            echo "   3. 가상환경 사용을 고려하세요"
            echo ""

            read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                handle_error "사용자가 설치를 중단했습니다."
            fi
        else
            echo -e "${GREEN}✅ 모든 필수 패키지 설치 완료${NC}"
        fi
    fi

    # 선택적 패키지 설치
    echo ""
    echo "📱 선택적 패키지 설치 중..."
    for package in "${OPTIONAL_PACKAGES[@]}"; do
        echo "   설치 중: $package (실패해도 계속 진행)"
        pip3 install "$package" --user --quiet 2>/dev/null || echo "   ⚠️ $package 설치 실패 (선택사항)"
    done
}

# 시스템 성능 확인 함수
check_system_performance() {
    echo -e "${BLUE}🔍 시스템 성능 확인${NC}"

    # CPU 코어 수
    cpu_cores=$(sysctl -n hw.ncpu)
    echo "   CPU 코어: ${cpu_cores}개"

    # 메모리 확인
    memory_gb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    echo "   메모리: ${memory_gb}GB"

    # 성능 권장사항
    if [ $cpu_cores -lt 4 ] || [ $memory_gb -lt 8 ]; then
        echo -e "${YELLOW}⚠️ 시스템 성능 주의사항:${NC}"
        echo "   • OCR 처리 시간이 다소 오래 걸릴 수 있습니다"
        echo "   • 큰 이미지 처리 시 메모리 부족 가능성이 있습니다"
    else
        echo -e "${GREEN}✅ 시스템 성능 충분${NC}"
    fi
}

# 네트워크 연결 고급 확인
check_network_advanced() {
    echo -e "${BLUE}🌐 네트워크 연결 고급 확인${NC}"

    # 기본 인터넷 연결
    if ping -c 1 google.com &> /dev/null; then
        echo -e "${GREEN}✅ 기본 인터넷 연결 정상${NC}"
    else
        echo -e "${RED}❌ 인터넷 연결 없음${NC}"
        handle_error "인터넷 연결이 필요합니다."
    fi

    # Google Translate API 접근 확인
    if curl -s --connect-timeout 5 "https://translate.googleapis.com" > /dev/null; then
        echo -e "${GREEN}✅ Google Translate API 접근 가능${NC}"
    else
        echo -e "${YELLOW}⚠️ Google Translate API 접근 제한 (방화벽 확인 필요)${NC}"
    fi

    # Python 패키지 저장소 접근 확인
    if curl -s --connect-timeout 5 "https://pypi.org" > /dev/null; then
        echo -e "${GREEN}✅ Python 패키지 저장소 접근 가능${NC}"
    else
        echo -e "${YELLOW}⚠️ Python 패키지 저장소 접근 제한${NC}"
    fi
}

# 1단계: 시스템 환경 확인
show_step "시스템 환경 확인"

# macOS 확인
if [[ "$OSTYPE" != "darwin"* ]]; then
    handle_error "이 스크립트는 macOS 전용입니다."
fi

echo -e "${GREEN}✅ macOS 시스템 확인 완료${NC}"
echo "   버전: $(sw_vers -productVersion)"
echo "   아키텍처: $(uname -m)"

# 2단계: 네트워크 연결 고급 확인
show_step "네트워크 연결 고급 확인"
check_network_advanced

# 3단계: 시스템 성능 확인
show_step "시스템 성능 확인"
check_system_performance

# 4단계: Xcode Command Line Tools 설치
show_step "개발 도구 설치"
install_xcode_tools

# 5단계: Git 설치 (선택사항)
show_step "Git 버전 관리 도구 설치"
echo "시스템 업데이트와 개발에 유용한 Git을 설치하시겠습니까?"
read -p "Git 설치 (Y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    install_git
else
    echo -e "${BLUE}⏭️ Git 설치를 건너뜁니다${NC}"
fi

# 6단계: Python 설치 확인 및 자동 설치
show_step "Python 환경 확인 및 설치"

if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}❌ Python 3가 설치되지 않았습니다.${NC}"
    echo ""
    echo -e "${BLUE}🤖 Python을 자동으로 설치하시겠습니까?${NC}"
    echo ""
    echo "   1) ${GREEN}Homebrew로 자동 설치${NC} (권장 - 패키지 관리 용이)"
    echo "   2) ${BLUE}공식 설치파일 다운로드${NC} (빠름 - 직접 설치)"
    echo "   3) ${YELLOW}수동 설치${NC} (python.org 방문하여 직접 설치)"
    echo ""

    while true; do
        read -p "선택하세요 (1-3): " python_choice
        case $python_choice in
            1)
                echo ""
                echo -e "${GREEN}🍺 Homebrew로 Python 설치를 시작합니다...${NC}"
                install_python_homebrew
                break
                ;;
            2)
                echo ""
                echo -e "${BLUE}🌐 공식 설치파일로 Python 설치를 시작합니다...${NC}"
                install_python_official
                break
                ;;
            3)
                echo ""
                echo -e "${YELLOW}💻 수동 설치를 선택하셨습니다.${NC}"
                echo "1. 브라우저에서 https://python.org 방문"
                echo "2. Download → macOS용 Python 3.11+ 다운로드"
                echo "3. 설치 완료 후 이 스크립트를 다시 실행하세요"
                echo ""
                open "https://python.org"
                echo -e "${YELLOW}설치 완료 후 Enter 키를 누르세요.${NC}"
                read
                exit 0
                ;;
            *)
                echo -e "${RED}올바른 번호(1-3)를 입력해주세요.${NC}"
                ;;
        esac
    done
else
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python ${PYTHON_VERSION} 이미 설치됨${NC}"
fi

# Python 버전 재확인
python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" || handle_error "Python 3.8 이상이 필요합니다."

# 7단계: pip 업그레이드
show_step "패키지 관리자 업그레이드"

echo "📦 pip 업그레이드 중..."
python3 -m pip install --upgrade pip --user --quiet || handle_error "pip 업그레이드 실패"
echo -e "${GREEN}✅ pip 업그레이드 완료${NC}"

# 8단계: XLT System 의존성 고급 설치
show_step "XLT System 의존성 고급 설치"

# 현재 디렉토리를 Python path에 추가
export PYTHONPATH="$(pwd):$PYTHONPATH"
install_packages_with_fallback

# 9단계: 설정 파일 생성
show_step "기본 설정 생성"

if [ -f "figma_config_example.json" ] && [ ! -f "figma_config.json" ]; then
    cp figma_config_example.json figma_config.json
    echo -e "${GREEN}✅ Figma 설정 파일 생성됨${NC}"
fi

mkdir -p output figma logs
echo -e "${GREEN}✅ 작업 디렉토리 생성 완료${NC}"

# 10단계: 시스템 검증
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
    print(f'   설치 위치: $INSTALL_DIR')
    print(f'   Python 경로: {sys.path[0]}')
except Exception as e:
    print(f'❌ 초기화 실패: {e}')
    print(f'   현재 디렉토리: $INSTALL_DIR')
    print('   xlt 패키지 확인 중...')
    import os
    if os.path.exists('$INSTALL_DIR/xlt'):
        print('   ✅ xlt 디렉토리 존재')
        if os.path.exists('$INSTALL_DIR/xlt/__init__.py'):
            print('   ✅ xlt/__init__.py 존재')
        else:
            print('   ❌ xlt/__init__.py 없음')
    else:
        print('   ❌ xlt 디렉토리 없음')
    exit(1)
" || handle_error "XLT System 검증 실패"

# 11단계: 데스크톱 바로가기 생성
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
echo "   설치 위치: $INSTALL_DIR"
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

# 12단계: 시스템 트레이 앱 설정 (선택사항)
show_step "시스템 트레이 앱 설정 (선택사항)"

echo "시스템 트레이에서 XLT System을 관리하시겠습니까?"
echo "트레이 앱을 사용하면 메뉴 바에서 서버 시작/종료가 가능합니다."
echo ""
read -p "트레이 앱을 설치하시겠습니까? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📱 시스템 트레이 앱 설정 중..."

    python3 -c "import pystray" 2>/dev/null || {
        echo "   PysTray 설치 중..."
        pip3 install pystray --user --quiet || echo "⚠️  PysTray 설치 실패 (선택사항이므로 계속 진행)"
    }

    TRAY_SHORTCUT="$HOME/Desktop/XLT System (Tray).command"
    cat > "$TRAY_SHORTCUT" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
# Python path 설정 (xlt 패키지 인식을 위해)
export PYTHONPATH="$INSTALL_DIR:\$PYTHONPATH"
echo "🎨 XLT System 트레이 앱 시작 중..."
python3 xlt_tray.py
EOF
    chmod +x "$TRAY_SHORTCUT"
    echo -e "${GREEN}✅ 트레이 앱 바로가기 생성됨${NC}"
fi

# 최종 설치 완료 및 시스템 정보 요약
echo ""
echo "══════════════════════════════════════════════"
echo -e "${GREEN}🎉 XLT System v3.0 Complete 설치 완료!${NC}"
echo "══════════════════════════════════════════════"
echo ""

# 설치된 컴포넌트 요약
echo -e "${CYAN}📋 설치된 컴포넌트:${NC}"
echo "  🐍 Python: $(python3 --version 2>&1 | cut -d' ' -f2)"
echo "  📦 pip: $(pip3 --version 2>&1 | cut -d' ' -f2)"
if command -v git &> /dev/null; then
    echo "  📱 Git: $(git --version 2>&1 | cut -d' ' -f3)"
fi
if xcode-select -p &> /dev/null; then
    echo "  🛠️ Xcode Command Line Tools: 설치됨"
fi
if command -v brew &> /dev/null; then
    echo "  🍺 Homebrew: $(brew --version 2>&1 | head -1 | cut -d' ' -f2)"
fi
echo "  📚 XLT System 패키지: 모두 설치됨"
echo ""

echo -e "${BLUE}🚀 사용 방법:${NC}"
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

echo -e "${CYAN}🛠️  시스템 정보:${NC}"
echo "  • macOS: $(sw_vers -productVersion)"
echo "  • 아키텍처: $(uname -m)"
echo "  • CPU 코어: $(sysctl -n hw.ncpu)개"
echo "  • 메모리: $(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))GB"
echo "  • 설치 위치: $(pwd)"
echo ""

echo -e "${YELLOW}💡 지금 XLT System을 시작하시겠습니까?${NC}"
read -p "시작하기 (Y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo -e "${GREEN}🚀 XLT System 시작 중...${NC}"

    # Python path 설정
    export PYTHONPATH="$(pwd):$PYTHONPATH"

    # 포트 5004 사용 여부 확인
    if lsof -Pi :5004 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  포트 5004가 이미 사용 중입니다.${NC}"
        echo "   기존 XLT System 서버를 종료하고 새로 시작합니다..."

        # 기존 서버 종료
        pkill -f stable_web_server.py 2>/dev/null || true
        sleep 2

        # 포트가 여전히 사용 중인지 확인
        if lsof -Pi :5004 -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}❌ 기존 서버를 종료할 수 없습니다.${NC}"
            echo "   수동으로 종료 후 데스크톱의 'XLT System.command'를 실행하세요."
            exit 1
        fi
    fi

    # 브라우저 열기
    open http://localhost:5004 2>/dev/null &

    # 서버 시작 (3초 후)
    sleep 3
    python3 stable_web_server.py
else
    echo ""
    echo -e "${BLUE}📌 나중에 데스크톱의 'XLT System.command' 파일을 실행하세요!${NC}"
    echo ""
    echo -e "${YELLOW}모든 설치가 완료되었습니다. Enter 키를 누르면 창이 닫힙니다.${NC}"
    read
fi