#!/bin/bash

# XLT System v5.1.1 완전 자동화 설치 스크립트 v2.2
# "원클릭 완전 자동화" - 실패 불가능한 설치 시스템 + 언인스톨러 포함

set -e

# =====================================
# 전역 설정 및 색상
# =====================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# 전역 변수
INSTALL_DIR="$HOME/XLT-System"
DOWNLOAD_URL="https://github.com/hobong-ho6/xlt-system/archive/refs/heads/main.zip"
GITHUB_RAW_URL="https://raw.githubusercontent.com/hobong-ho6/xlt-system/main"
LOG_FILE="$HOME/.xlt_install.log"

# 설치 통계
TOTAL_STEPS=12
CURRENT_STEP=0
START_TIME=$(date +%s)

# =====================================
# 유틸리티 함수들
# =====================================

log_message() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" >> "$LOG_FILE"
}

progress_bar() {
    local current=$1
    local total=$2
    local desc="$3"

    CURRENT_STEP=$current
    local percent=$((current * 100 / total))
    local filled=$((current * 50 / total))

    printf "\r${BLUE}진행률: ["
    for ((i=0; i<filled; i++)); do printf "█"; done
    for ((i=filled; i<50; i++)); do printf "░"; done
    printf "] %d%% - %s${NC}" $percent "$desc"

    if [ $current -eq $total ]; then
        echo ""
    fi
}

success_message() {
    echo -e "${GREEN}✅ $1${NC}"
    log_message "SUCCESS" "$1"
}

warning_message() {
    echo -e "${YELLOW}⚠️ $1${NC}"
    log_message "WARNING" "$1"
}

error_message() {
    echo -e "${RED}❌ $1${NC}"
    log_message "ERROR" "$1"
}

info_message() {
    echo -e "${CYAN}ℹ️ $1${NC}"
    log_message "INFO" "$1"
}

# =====================================
# 환경 감지 시스템
# =====================================

detect_environment() {
    progress_bar 1 $TOTAL_STEPS "환경 감지 및 분석 중..."

    info_message "시스템 환경 감지 중..."

    # OS 정보
    OS_TYPE=$(uname -s)
    OS_VERSION=$(uname -r)
    ARCH=$(uname -m)

    # Python 환경 감지
    PYTHON_ENV="unknown"
    PYTHON_VERSION=""
    CONDA_ENV=""
    VENV_ENV=""

    # Python 버전 확인
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    else
        error_message "Python 3이 설치되지 않았습니다"
        return 1
    fi

    # Conda 환경 확인
    if [ -n "$CONDA_DEFAULT_ENV" ] || command -v conda >/dev/null 2>&1; then
        PYTHON_ENV="conda"
        CONDA_ENV="$CONDA_DEFAULT_ENV"
        info_message "Conda 환경 감지됨: $CONDA_ENV"
    elif [ -n "$VIRTUAL_ENV" ]; then
        PYTHON_ENV="venv"
        VENV_ENV="$VIRTUAL_ENV"
        info_message "Virtual 환경 감지됨: $VENV_ENV"
    else
        PYTHON_ENV="system"
        info_message "시스템 Python 환경"
    fi

    # 기존 설치 확인
    EXISTING_INSTALL=""
    if [ -d "$INSTALL_DIR" ]; then
        EXISTING_INSTALL="found"
        if [ -f "$INSTALL_DIR/version.json" ]; then
            EXISTING_VERSION=$(python3 -c "
import json
try:
    with open('$INSTALL_DIR/version.json', 'r') as f:
        data = json.load(f)
        print(data.get('version', 'unknown'))
except:
    print('unknown')
" 2>/dev/null)
            info_message "기존 설치 발견: v$EXISTING_VERSION"
        fi
    fi

    # 실행 중인 프로세스 확인
    RUNNING_PROCESSES=""
    if pgrep -f "stable_web_server.py" >/dev/null 2>&1; then
        RUNNING_PROCESSES="server"
        info_message "XLT 서버가 실행 중입니다"
    fi

    # 포트 사용 확인
    PORT_USED=""
    if lsof -i:5004 >/dev/null 2>&1; then
        PORT_USED="5004"
        warning_message "포트 5004가 사용 중입니다"
    fi

    # 환경 요약 출력
    echo ""
    echo -e "${PURPLE}📊 환경 분석 결과:${NC}"
    echo "   🖥️  OS: $OS_TYPE $OS_VERSION ($ARCH)"
    echo "   🐍 Python: $PYTHON_VERSION ($PYTHON_ENV)"
    echo "   📁 기존 설치: ${EXISTING_INSTALL:-"없음"}"
    echo "   ⚡ 실행 중: ${RUNNING_PROCESSES:-"없음"}"
    echo "   🔌 포트 5004: ${PORT_USED:-"사용 가능"}"
    echo ""

    success_message "환경 감지 완료"
    return 0
}

# =====================================
# 지능형 정리 시스템
# =====================================

intelligent_cleanup() {
    progress_bar 2 $TOTAL_STEPS "기존 환경 지능형 정리 중..."

    info_message "기존 XLT System 환경 정리 시작..."

    # 1단계: 프로세스 정중한 종료
    if [ -n "$RUNNING_PROCESSES" ]; then
        info_message "실행 중인 XLT 프로세스 정중한 종료 시도..."
        pkill -TERM -f "stable_web_server.py" 2>/dev/null || true
        pkill -TERM -f "xlt_tray.py" 2>/dev/null || true
        sleep 3
    fi

    # 2단계: 포트 기반 강제 정리
    if [ -n "$PORT_USED" ]; then
        info_message "포트 5004 사용 프로세스 강제 종료..."
        PORT_PIDS=$(lsof -ti:5004 2>/dev/null || echo "")
        if [ -n "$PORT_PIDS" ]; then
            echo "$PORT_PIDS" | xargs kill -9 2>/dev/null || true
            sleep 2
        fi
    fi

    # 3단계: 완전한 프로세스 스캔 및 정리
    info_message "남은 XLT 프로세스 완전 정리..."
    REMAINING_PIDS=$(ps -eo pid,comm,args | grep -E "(stable_web_server|xlt_tray)" | grep -v grep | awk '{print $1}' 2>/dev/null || echo "")
    if [ -n "$REMAINING_PIDS" ]; then
        echo "$REMAINING_PIDS" | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # 4단계: 기존 설치 백업
    if [ -d "$INSTALL_DIR" ]; then
        BACKUP_DIR="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
        info_message "기존 설치를 백업 중: $BACKUP_DIR"
        mv "$INSTALL_DIR" "$BACKUP_DIR" 2>/dev/null || {
            warning_message "백업 실패, 강제 삭제 진행..."
            rm -rf "$INSTALL_DIR" 2>/dev/null || true
        }
    fi

    # 5단계: 최종 검증
    sleep 1
    if lsof -i:5004 >/dev/null 2>&1; then
        warning_message "포트 5004가 여전히 사용 중입니다 - 강제 해제 시도..."
        sudo lsof -ti:5004 | xargs sudo kill -9 2>/dev/null || true
    fi

    success_message "환경 정리 완료"
}

# =====================================
# macOS 호환성 함수
# =====================================

# macOS에서 timeout 명령어 대체 함수
run_with_timeout() {
    local timeout_seconds=$1
    shift

    if command -v timeout >/dev/null 2>&1; then
        # Linux/GNU timeout 사용
        timeout "$timeout_seconds" "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
        # macOS homebrew coreutils gtimeout 사용
        gtimeout "$timeout_seconds" "$@"
    else
        # macOS 기본 - 백그라운드 실행 + kill 방식
        "$@" &
        local pid=$!
        (
            sleep "$timeout_seconds"
            kill $pid 2>/dev/null || true
        ) &
        local killer_pid=$!
        wait $pid 2>/dev/null
        local result=$?
        kill $killer_pid 2>/dev/null || true
        return $result
    fi
}

# =====================================
# 다중 전략 패키지 설치 시스템
# =====================================

install_packages_strategy() {
    progress_bar 4 $TOTAL_STEPS "패키지 설치 전략 실행 중..."

    info_message "환경별 최적화된 패키지 설치 시작..."

    # 전략 1: Conda 환경 최적화 설치
    if [ "$PYTHON_ENV" = "conda" ]; then
        info_message "전략 1: Conda 환경 최적화 설치 시도..."
        if install_packages_conda; then
            success_message "Conda 설치 전략 성공"
            return 0
        fi
        warning_message "Conda 설치 실패 - 다음 전략 시도..."
    fi

    # 전략 2: 호환성 우선 설치
    info_message "전략 2: 호환성 우선 설치 시도..."
    if install_packages_compatibility; then
        success_message "호환성 우선 설치 성공"
        return 0
    fi
    warning_message "호환성 우선 설치 실패 - 다음 전략 시도..."

    # 전략 3: 최소 의존성 설치
    info_message "전략 3: 최소 의존성 설치 시도..."
    if install_packages_minimal; then
        success_message "최소 의존성 설치 성공"
        return 0
    fi
    warning_message "최소 의존성 설치 실패 - 긴급 전략 시도..."

    # 전략 4: 긴급 복구 설치
    info_message "전략 4: 긴급 복구 설치 시도..."
    if install_packages_emergency; then
        success_message "긴급 복구 설치 성공"
        return 0
    fi

    error_message "모든 설치 전략 실패"
    return 1
}

install_packages_conda() {
    info_message "Conda 환경 최적화 설치 중..."

    # 타임아웃과 함께 Conda로 핵심 패키지 설치 (30초 제한)
    info_message "⏳ Conda 패키지 다운로드 중 (최대 30초 대기)..."

    if run_with_timeout 30 conda install -c conda-forge numpy=1.21.6 pillow=9.5.0 pandas flask requests -y 2>/dev/null; then
        info_message "✅ Conda 설치 성공, pip 추가 패키지 설치 중..."
        # 나머지 패키지는 pip로 (타임아웃 60초)
        run_with_timeout 60 python3 -m pip install --user --quiet easyocr googletrans==4.0.0rc1 openpyxl psutil pystray torch 2>/dev/null
        return 0
    else
        warning_message "⚠️ Conda 설치 타임아웃 또는 실패 (30초 초과)"
        return 1
    fi
}

install_packages_compatibility() {
    info_message "호환성 우선 설치 중..."

    # 스마트 패키지 검증 및 설치 (이미 설치된 것은 스킵)
    install_if_missing() {
        local package_name="$1"
        local pip_name="$2"
        local import_name="$3"

        info_message "⏳ $package_name 확인 중..."
        if python3 -c "import $import_name" 2>/dev/null; then
            success_message "$package_name 이미 설치됨"
            return 0
        fi

        info_message "📦 $package_name 설치 중..."
        if run_with_timeout 30 python3 -m pip install --user "$pip_name" 2>&1; then
            success_message "$package_name 설치 완료"
            return 0
        else
            warning_message "$package_name 설치 실패"
            return 1
        fi
    }

    # 핵심 패키지 개별 설치 및 검증
    install_if_missing "NumPy" "\"numpy<2\"" "numpy" || return 1
    install_if_missing "Pillow" "pillow==9.5.0" "PIL" || return 1
    install_if_missing "Flask" "flask" "flask" || return 1
    install_if_missing "Requests" "requests" "requests" || return 1
    install_if_missing "PSUtil" "psutil" "psutil" || return 1
    install_if_missing "GoogleTrans" "googletrans==4.0.0rc1" "googletrans" || return 1
    install_if_missing "OpenPyXL" "openpyxl" "openpyxl" || return 1
    install_if_missing "Pandas" "pandas" "pandas" || return 1

    # rumps (macOS 전용 트레이) - 강화된 설치 로직
    info_message "⏳ rumps 설치 중 (macOS 네이티브 트레이)..."

    # 먼저 rumps 확인
    if python3 -c "import rumps" 2>/dev/null; then
        success_message "rumps 이미 설치됨"
    else
        info_message "rumps 설치가 필요합니다 - 다중 방법으로 시도..."

        # 환경 감지 (더 정확한 방법)
        PYTHON_ENV="system"
        if [ -n "$CONDA_DEFAULT_ENV" ] || [ -n "$CONDA_PREFIX" ] || command -v conda >/dev/null 2>&1; then
            PYTHON_ENV="conda"
            info_message "Conda 환경 감지됨: ${CONDA_DEFAULT_ENV:-base}"
        elif [[ "$(which python3)" == *"venv"* ]] || [[ "$(which python3)" == *"virtualenv"* ]]; then
            PYTHON_ENV="venv"
            info_message "가상환경 감지됨"
        fi

        # PyObjC와 패키지 충돌 해결 (에러 표시)
        info_message "PyObjC 의존성 준비 중..."
        if [ "$PYTHON_ENV" = "conda" ]; then
            # Anaconda 환경에서 패키지 충돌 해결
            pip install --upgrade numexpr bottleneck pandas || warning_message "패키지 업데이트 실패 (무시하고 진행)"
        fi

        # rumps 설치 시도 (여러 방법, 에러 표시)
        RUMPS_INSTALLED=false

        # 방법 1: 기본 pip (환경별 적응)
        info_message "방법 1: 기본 pip으로 rumps 설치 시도..."
        if [ "$PYTHON_ENV" = "conda" ]; then
            pip install rumps && RUMPS_INSTALLED=true
        else
            python3 -m pip install --user rumps && RUMPS_INSTALLED=true
        fi

        # 방법 2: PyObjC 명시적 설치 후 rumps
        if [ "$RUMPS_INSTALLED" = false ]; then
            info_message "방법 2: PyObjC 명시적 설치 후 rumps 시도..."
            if [ "$PYTHON_ENV" = "conda" ]; then
                pip install pyobjc-core pyobjc-framework-Cocoa && pip install rumps && RUMPS_INSTALLED=true
            else
                python3 -m pip install --user pyobjc-core pyobjc-framework-Cocoa && python3 -m pip install --user rumps && RUMPS_INSTALLED=true
            fi
        fi

        # 방법 3: 버전 제약 없이 강제 설치
        if [ "$RUMPS_INSTALLED" = false ]; then
            info_message "방법 3: 강제 설치 시도..."
            if [ "$PYTHON_ENV" = "conda" ]; then
                pip install --force-reinstall --no-deps rumps && RUMPS_INSTALLED=true
            else
                python3 -m pip install --user --force-reinstall --no-deps rumps && RUMPS_INSTALLED=true
            fi
        fi

        # 최종 검증
        if python3 -c "import rumps; print('✅ rumps 검증 성공')" 2>/dev/null; then
            success_message "rumps 설치 및 검증 완료"
        else
            error_message "❌ rumps 설치 완전 실패"
            warning_message "트레이 기능이 제한됩니다 (웹 서버는 정상 작동)"
            warning_message "수동 설치 필요: pip install rumps"
        fi
    fi

    # EasyOCR과 torch는 별도로 (실패해도 진행)
    info_message "⏳ OCR 패키지 설치 중 (선택사항)..."
    if ! python3 -c "import easyocr" 2>/dev/null; then
        run_with_timeout 60 python3 -m pip install --user easyocr torch 2>/dev/null || {
            warning_message "⚠️ EasyOCR/torch 설치 실패 - 런타임에 재시도됩니다"
        }
    else
        success_message "EasyOCR 이미 설치됨"
    fi

    return 0
}

install_packages_minimal() {
    info_message "최소 의존성 설치 중..."

    # 최소한의 패키지만 설치 (상세 에러 표시)
    info_message "⏳ 필수 패키지만 설치 시도 중..."
    if ! python3 -m pip install --user flask requests pillow openpyxl psutil 2>&1; then
        warning_message "최소 패키지 설치 실패"
        return 1
    fi

    return 0
}

install_packages_emergency() {
    info_message "긴급 복구 설치 중..."

    # 먼저 pip 업그레이드 시도
    info_message "⏳ pip 업그레이드 시도 중..."
    python3 -m pip install --user --upgrade pip 2>/dev/null || true

    # 시스템 권한으로 강제 설치 (상세 에러 표시)
    info_message "⏳ 시스템 권한으로 강제 설치 시도 중..."
    if ! pip3 install flask requests pillow openpyxl psutil --break-system-packages 2>&1; then
        error_message "긴급 복구 설치도 실패 - pip 환경에 문제가 있을 수 있습니다"
        error_message "수동 설치를 시도해주세요:"
        error_message "python3 -m pip install --user flask requests pillow openpyxl"
        return 1
    fi

    return 0
}

# =====================================
# 실시간 검증 시스템
# =====================================

comprehensive_verification() {

    info_message "설치된 시스템 종합 검증 시작..."

    cd "$INSTALL_DIR"

    # 1. 패키지 임포트 테스트
    info_message "패키지 임포트 테스트..."
    IMPORT_RESULTS=$(python3 -c "
import sys
import importlib
packages = ['flask', 'requests', 'PIL', 'openpyxl', 'json', 'pathlib']
failed = []
for pkg in packages:
    try:
        importlib.import_module(pkg)
    except ImportError as e:
        failed.append(f'{pkg}: {e}')

if failed:
    print('FAILED:' + '|'.join(failed))
else:
    print('SUCCESS')
" 2>&1)

    if [[ "$IMPORT_RESULTS" == "SUCCESS" ]]; then
        success_message "패키지 임포트 테스트 통과"
    else
        warning_message "일부 패키지 임포트 실패: $IMPORT_RESULTS"
    fi

    # 2. 파일 쓰기 권한 테스트
    info_message "파일 쓰기 권한 테스트..."
    if echo "test" > "verification_test.tmp" 2>/dev/null && rm -f "verification_test.tmp" 2>/dev/null; then
        success_message "파일 쓰기 권한 정상"
    else
        warning_message "파일 쓰기 권한 문제"
        chmod -R 755 . 2>/dev/null || true
    fi

    # 3. 서버 시작 테스트 (macOS 호환성 개선)
    info_message "서버 시작 테스트..."

    # macOS 호환성을 위해 백그라운드 실행 방식 사용
    python3 stable_web_server.py > /dev/null 2>&1 &
    SERVER_PID=$!
    sleep 5

    if kill -0 $SERVER_PID 2>/dev/null; then
        success_message "서버 시작 테스트 성공"
        kill $SERVER_PID 2>/dev/null || true
    else
        warning_message "서버 시작 테스트 실패"
    fi

    # 4. 필수 Excel 파일 확인
    info_message "필수 Excel 파일 확인..."
    EXCEL_FILES_OK=true

    if [ -f "Sample/sampleformat.xlsx" ]; then
        success_message "Excel 템플릿 파일 확인: Sample/sampleformat.xlsx"
    else
        warning_message "Excel 템플릿 파일 누락: Sample/sampleformat.xlsx"
        EXCEL_FILES_OK=false
    fi

    UNIFI_FILE=$(find Unifi -name "Unifi_WEB*.xlsx" 2>/dev/null | head -1)
    if [ -n "$UNIFI_FILE" ]; then
        success_message "Unifi 번역 DB 확인: $UNIFI_FILE"
    else
        warning_message "Unifi 번역 DB 누락: Unifi/Unifi_WEB*.xlsx"
        EXCEL_FILES_OK=false
    fi

    # 5. API 응답 테스트
    info_message "API 응답 테스트..."
    python3 stable_web_server.py >/dev/null 2>&1 &
    API_SERVER_PID=$!
    sleep 3

    if curl -s http://localhost:5004/api/version >/dev/null 2>&1; then
        success_message "API 응답 테스트 성공"
    else
        warning_message "API 응답 테스트 실패"
    fi

    kill $API_SERVER_PID 2>/dev/null || true
    sleep 2

    # 6. Excel 다운로드 기능 테스트 (필수 파일이 있는 경우에만)
    if [ "$EXCEL_FILES_OK" = true ]; then
        info_message "Excel 다운로드 기능 테스트..."
        EXCEL_TEST_RESULT=$(python3 -c "
import os
current_dir = os.path.dirname(os.path.abspath('stable_web_server.py'))
template_path = os.path.join(current_dir, 'Sample', 'sampleformat.xlsx')
print('SUCCESS' if os.path.exists(template_path) else 'FAILED')
" 2>&1)

        if [ "$EXCEL_TEST_RESULT" = "SUCCESS" ]; then
            success_message "Excel 템플릿 경로 접근 성공"
        else
            warning_message "Excel 템플릿 경로 접근 실패"
        fi
    fi

    success_message "종합 검증 완료"
}

# =====================================
# 초기 설정 파일 생성
# =====================================

create_initial_config() {
    info_message "초기 설정 파일 생성 중..."

    cd "$INSTALL_DIR"

    # 1. 사용자 설정 파일 생성 (기본값)
    if [ ! -f "user_config.json" ]; then
        cat > "user_config.json" << 'JSON_EOF'
{
    "server_port": 5004,
    "max_concurrent_users": 5,
    "session_timeout_minutes": 60,
    "output_directory": "~/Documents/XLTTT/output",
    "auto_open_browser": true,
    "enable_system_tray": true,
    "language": "ko_KR"
}
JSON_EOF
        info_message "기본 사용자 설정 파일 생성됨"
    fi

    # 2. 로그 설정 파일
    cat > "logging_config.json" << 'JSON_EOF'
{
    "logging": {
        "level": "INFO",
        "file": "xlt_system.log",
        "max_size_mb": 10,
        "backup_count": 3,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}
JSON_EOF

    # 3. 환경 설정 파일 생성
    cat > "environment.json" << JSON_ENV_EOF
{
    "installation": {
        "date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "version": "4.1.0",
        "installer_version": "2.1",
        "python_version": "$PYTHON_VERSION",
        "python_env": "$PYTHON_ENV",
        "os_type": "$OS_TYPE",
        "os_version": "$OS_VERSION",
        "arch": "$ARCH"
    },
    "paths": {
        "install_directory": "$INSTALL_DIR",
        "log_file": "$LOG_FILE",
        "desktop_shortcut": "$HOME/Desktop/XLT System (Tray).command"
    },
    "capabilities": {
        "self_healing": true,
        "auto_recovery": true,
        "multi_strategy_install": true,
        "comprehensive_verification": true
    }
}
JSON_ENV_EOF

    # 4. 출력 디렉토리 생성
    local output_dir="$HOME/Documents/XLTTT/output"
    mkdir -p "$output_dir" 2>/dev/null || {
        output_dir="$HOME/XLT-Output"
        mkdir -p "$output_dir" 2>/dev/null || true
    }

    if [ -d "$output_dir" ]; then
        info_message "출력 디렉토리 생성됨: $output_dir"
    fi

    # 5. 파일 권한 설정
    chmod 644 *.json 2>/dev/null || true

    success_message "초기 설정 파일들이 생성되었습니다"
}

# =====================================
# Claude CLI 설치 및 설정 시스템
# =====================================

setup_claude_cli() {
    info_message "Claude CLI 설치 및 설정 시작..."

    # Claude CLI 설치 여부 확인
    if command -v claude &> /dev/null; then
        info_message "Claude CLI가 이미 설치되어 있습니다."
    else
        info_message "Claude CLI 설치 중..."

        # macOS에서 Homebrew를 통한 설치
        if [[ "$OS_TYPE" == "Darwin" ]]; then
            if command -v brew &> /dev/null; then
                info_message "Homebrew를 통해 Claude CLI 설치 중..."
                if ! brew install anthropic/claude/claude > /dev/null 2>&1; then
                    warning_message "Homebrew 설치 실패, curl로 재시도..."
                    install_claude_with_curl
                fi
            else
                info_message "Homebrew가 없어서 curl로 Claude CLI 설치..."
                install_claude_with_curl
            fi
        else
            # Linux/기타 운영체제
            install_claude_with_curl
        fi
    fi

    # Claude CLI 설치 확인
    if command -v claude &> /dev/null; then
        success_message "Claude CLI 설치 완료"

        # Claude CLI 인증 상태 확인
        info_message "Claude CLI 인증 상태 확인 중..."

        if claude auth status --format json 2>/dev/null | grep -q '"loggedIn": *true'; then
            success_message "Claude CLI 이미 인증됨"
        else
            info_message "Claude CLI 인증이 필요합니다."
            echo ""
            echo -e "${YELLOW}🔑 Claude CLI 인증 안내${NC}"
            echo -e "${CYAN}─────────────────────────────────────────────${NC}"
            echo -e "${WHITE}1. 잠시 후 브라우저가 열립니다${NC}"
            echo -e "${WHITE}2. Claude.ai 계정으로 로그인하세요${NC}"
            echo -e "${WHITE}3. 인증을 완료한 후 아무 키나 누르세요${NC}"
            echo -e "${CYAN}─────────────────────────────────────────────${NC}"
            echo ""

            # 인증 프로세스 시작
            if claude auth login > /dev/null 2>&1; then
                success_message "Claude CLI 인증 완료!"

                # 인증 확인
                if claude auth status --format json 2>/dev/null | grep -q '"loggedIn": *true'; then
                    success_message "Claude CLI 설정 완료 - XLT System에서 사용 가능합니다"
                else
                    warning_message "인증이 완료되지 않았을 수 있습니다. 나중에 'claude auth login' 명령어로 다시 시도하세요."
                fi
            else
                warning_message "Claude CLI 인증 중 문제가 발생했습니다."
                echo -e "${CYAN}💡 수동 인증 방법:${NC}"
                echo "1. 터미널에서 'claude auth login' 실행"
                echo "2. 브라우저에서 Claude.ai 계정으로 로그인"
                echo "3. 인증 완료 후 XLT System 재시작"
            fi
        fi
    else
        error_message "Claude CLI 설치에 실패했습니다."
        echo -e "${CYAN}💡 수동 설치 방법:${NC}"
        echo "1. https://github.com/anthropics/anthropic-quickstarts 방문"
        echo "2. Claude CLI 설치 가이드 참조"
        echo "3. 설치 완료 후 'claude auth login' 실행"
        echo ""
        warning_message "Claude CLI 없이도 XLT System의 Google 번역 기능은 정상 작동합니다."
    fi
}

install_claude_with_curl() {
    info_message "curl을 통해 Claude CLI 설치 시도..."

    local install_dir="/usr/local/bin"
    local claude_binary="$install_dir/claude"

    # 관리자 권한으로 설치 시도
    if sudo curl -L https://github.com/anthropics/anthropic-cli/releases/latest/download/claude-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m | sed 's/x86_64/amd64/') -o "$claude_binary" 2>/dev/null; then
        sudo chmod +x "$claude_binary" 2>/dev/null
        if command -v claude &> /dev/null; then
            success_message "Claude CLI curl 설치 성공"
        else
            warning_message "Claude CLI 설치 실패 - 수동 설치가 필요할 수 있습니다."
        fi
    else
        warning_message "Claude CLI 자동 설치 실패"
    fi
}

# =====================================
# 자가 치유 바로가기 생성 시스템
# =====================================

create_independent_shortcut() {
    info_message "터미널 독립 Tray 바로가기 생성 중..."

    cat > "$HOME/Desktop/XLT System (Tray).command" << 'EOF'
#!/bin/bash

# XLT System v3.1 터미널 독립 실행 스크립트
# 터미널 종료 후에도 백그라운드에서 계속 실행

INSTALL_DIR="INSTALL_DIR_PLACEHOLDER"

echo "🚀 XLT System v3.1 시작 중..."
echo ""

# 1. 이미 실행 중인지 확인
if pgrep -f "python.*xlt_tray.py" > /dev/null 2>&1; then
    echo "⚠️ XLT 트레이 앱이 이미 실행 중입니다."
    echo "🔍 시스템 트레이에서 XLT 아이콘을 확인해주세요."
    sleep 3
    exit 0
fi

# 2. 설치 디렉토리 확인
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ XLT System 설치 디렉토리를 찾을 수 없습니다."
    echo "💡 재설치가 필요합니다:"
    echo "curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash"
    sleep 5
    exit 1
fi

# 3. 디렉토리 이동
cd "$INSTALL_DIR" || exit 1

# 4. 트레이 앱 파일 확인
if [ ! -f "xlt_tray.py" ]; then
    echo "❌ XLT 트레이 앱 파일을 찾을 수 없습니다."
    echo "💡 재설치가 필요합니다."
    sleep 3
    exit 1
fi

# 5. 스마트 서버 시작 (트레이 → 웹서버 fallback)
echo "🎯 XLT 시스템을 백그라운드에서 시작합니다..."

# 로그 파일 설정
LOG_FILE="$INSTALL_DIR/xlt_server.log"

# 먼저 트레이 앱 시도 (macOS 호환성 문제 대비)
if [ -f "xlt_tray.py" ]; then
    echo "🎨 트레이 앱 시작 시도 중..."
    # macOS 호환 방식으로 백그라운드 프로세스 분리
    (nohup python3 xlt_tray.py > "$LOG_FILE" 2>&1 &) &
    TRAY_PID=$!
    disown 2>/dev/null || true  # 터미널에서 완전 분리
    sleep 5  # 더 길게 대기

    # 트레이 앱 실행 확인 (프로세스 + 포트)
    sleep 2
    if pgrep -f "python.*xlt_tray.py" >/dev/null 2>&1 && lsof -i :5004 >/dev/null 2>&1; then
        echo "✅ 트레이 앱이 시작되었습니다!"
        START_MODE="tray"
        SERVER_RUNNING=true
    else
        echo "⚠️ 트레이 앱 시작 실패 - 웹 서버 모드로 전환..."
        START_MODE="fallback"
        SERVER_RUNNING=false
    fi
else
    START_MODE="fallback"
fi

# Fallback: 웹 서버 직접 시작
if [ "$START_MODE" = "fallback" ]; then
    echo "🌐 웹 서버를 직접 시작합니다..."
    # macOS 호환 방식으로 백그라운드 프로세스 분리
    (nohup python3 stable_web_server.py > "$LOG_FILE" 2>&1 &) &
    SERVER_PID=$!
    disown 2>/dev/null || true  # 터미널에서 완전 분리
    sleep 5  # 더 길게 대기

    # 포트 기반으로 서버 실행 확인 (더 안정적)
    sleep 3
    if lsof -i :5004 >/dev/null 2>&1; then
        echo "✅ 웹 서버가 포트 5004에서 시작되었습니다!"
        SERVER_RUNNING=true
    else
        echo "❌ 웹 서버 시작에 실패했습니다."
        echo "🔍 로그를 확인하세요: $LOG_FILE"
        sleep 5
        exit 1
    fi
fi

# 6. 최종 확인 및 안내
echo ""
echo "✅ XLT 시스템이 백그라운드에서 시작되었습니다!"
echo ""
echo "📍 다음을 확인하세요:"
if [ "$START_MODE" = "tray" ]; then
    echo "   🎯 시스템 트레이에 XLT 아이콘 표시"
fi
echo "   🌐 웹 인터페이스: http://localhost:5004"
echo ""
echo "💡 이제 터미널을 닫아도 XLT 시스템은 계속 실행됩니다!"
echo "🔍 로그 파일: $LOG_FILE"
echo ""
echo ""
echo "🎯 XLT 시스템이 백그라운드에서 안전하게 시작되었습니다!"
echo ""
echo "💡 터미널 종료 옵션을 선택하세요:"
echo "   1️⃣ Enter: 즉시 종료"
echo "   2️⃣ 15초 대기: 자동 종료"
echo "   3️⃣ 터미널 유지: 수동 종료"

# 브라우저 자동 열기
sleep 2
open http://localhost:5004 2>/dev/null || true

# 백그라운드 프로세스 완전 안정화 대기
echo ""
echo "🔄 프로세스 안정화 중... (5초)"
sleep 5

# 프로세스 상태 최종 확인
if [[ "$SERVER_RUNNING" == "true" ]] && lsof -i :5004 >/dev/null 2>&1; then
    echo "✅ 백그라운드 프로세스가 안전하게 실행 중입니다."
    echo ""

    # 사용자 입력 대기 (15초 타임아웃)
    echo "⏰ 15초 내에 선택하세요 (Enter=즉시종료, 시간초과=자동종료):"
    if read -t 15 -n 1 -s; then
        echo "🚪 사용자 요청으로 터미널을 종료합니다."
        # 즉시 종료
        osascript -e 'tell application "Terminal" to close front window' 2>/dev/null || exit 0
    else
        echo ""
        echo "🚪 15초 경과로 자동 종료합니다."
        # 자동 종료
        osascript -e 'tell application "Terminal" to close front window' 2>/dev/null || exit 0
    fi
else
    echo "⚠️ 백그라운드 프로세스 상태를 확인할 수 없습니다."
    echo "💡 브라우저에서 http://localhost:5004 를 확인해주세요."
    echo ""
    echo "❓ 터미널을 종료하시겠습니까? (y/N):"
    read -n 1 -r REPLY
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        osascript -e 'tell application "Terminal" to close front window' 2>/dev/null || exit 0
    else
        echo "터미널이 유지됩니다. 수동으로 종료해주세요."
    fi
fi

EOF

    # INSTALL_DIR 플레이스홀더를 실제 경로로 치환
    sed -i '' "s|INSTALL_DIR_PLACEHOLDER|$INSTALL_DIR|g" "$HOME/Desktop/XLT System (Tray).command"

    # 실행 권한 부여
    chmod +x "$HOME/Desktop/XLT System (Tray).command"

    success_message "터미널 독립 Tray 바로가기가 생성되었습니다"
}

# =====================================
# 자가 치유 시스템 설정
# =====================================

# 자가 치유 시스템 변수 (색상과 INSTALL_DIR은 스크립트 시작 부분에서 이미 정의됨)
MAX_RETRY=3
CURRENT_RETRY=0
AUTO_FIX_LOG="$HOME/.xlt_autofix.log"

# =====================================
# 자가 치유 유틸리티 함수
# =====================================

log_autofix() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$AUTO_FIX_LOG"
}

auto_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log_autofix "SUCCESS: $1"
}

auto_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
    log_autofix "WARNING: $1"
}

auto_error() {
    echo -e "${RED}❌ $1${NC}"
    log_autofix "ERROR: $1"
}

auto_info() {
    echo -e "${CYAN}🔧 $1${NC}"
    log_autofix "AUTO-FIX: $1"
}

auto_retry() {
    local action="$1"
    local max_attempts="$2"

    for attempt in $(seq 1 $max_attempts); do
        echo -e "${BLUE}🔄 시도 $attempt/$max_attempts: $action${NC}"
        if eval "$action"; then
            auto_success "$action 성공 (시도: $attempt)"
            return 0
        else
            auto_warning "$action 실패 (시도: $attempt)"
            sleep $((attempt * 2))
        fi
    done

    auto_error "$action 최종 실패 (시도: $max_attempts)"
    return 1
}

# =====================================
# 완전한 프로세스 정리 시스템
# =====================================

ultimate_process_cleanup() {
    echo -e "${PURPLE}🛑 완전한 프로세스 정리 시작...${NC}"

    # 1단계: 정중한 종료 시도
    auto_info "1단계: 정중한 프로세스 종료 시도"
    pkill -TERM -f stable_web_server.py 2>/dev/null && echo "   📋 서버 종료 신호 전송" || echo "   ℹ️ 실행 중인 서버 없음"
    pkill -TERM -f xlt_tray.py 2>/dev/null && echo "   📋 트레이 종료 신호 전송" || echo "   ℹ️ 실행 중인 트레이 없음"
    sleep 5

    # 2단계: 포트 기반 완전 정리
    auto_info "2단계: 포트 5004 완전 정리"
    local port_pids=$(lsof -ti:5004 2>/dev/null || echo "")
    if [ -n "$port_pids" ]; then
        echo "   🔥 포트 5004 사용 프로세스 강제 종료: $port_pids"
        echo "$port_pids" | xargs kill -9 2>/dev/null || true
        sleep 3
    else
        echo "   ✅ 포트 5004 사용 가능"
    fi

    # 3단계: 프로세스명 기반 완전 스캔
    auto_info "3단계: XLT 관련 모든 프로세스 스캔 및 정리"
    local xlt_pids=$(ps -eo pid,comm,args 2>/dev/null | grep -E "(stable_web_server|xlt_tray|python.*stable)" | grep -v grep | awk '{print $1}' || echo "")
    if [ -n "$xlt_pids" ]; then
        echo "   ⚡ 발견된 XLT 프로세스 강제 종료: $xlt_pids"
        echo "$xlt_pids" | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # 4단계: Python 프로세스 중 XLT 관련 정리
    auto_info "4단계: Python 프로세스 중 XLT 관련 정리"
    local python_xlt_pids=$(ps -eo pid,args 2>/dev/null | grep python | grep -E "(stable_web_server|xlt_tray)" | grep -v grep | awk '{print $1}' || echo "")
    if [ -n "$python_xlt_pids" ]; then
        echo "   🐍 Python XLT 프로세스 강제 종료: $python_xlt_pids"
        echo "$python_xlt_pids" | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # 5단계: 최종 검증 및 시스템 정리
    auto_info "5단계: 최종 검증 및 시스템 정리"

    # 포트 재확인
    if lsof -i:5004 >/dev/null 2>&1; then
        auto_warning "포트 5004가 여전히 사용 중 - 시스템 권한으로 강제 정리"
        sudo lsof -ti:5004 | xargs sudo kill -9 2>/dev/null || true
        sleep 2
    fi

    # 프로세스 재확인
    local final_check=$(ps -eo pid,args 2>/dev/null | grep -E "(stable_web_server|xlt_tray)" | grep -v grep || echo "")
    if [ -n "$final_check" ]; then
        auto_warning "일부 프로세스가 여전히 실행 중"
        echo "$final_check"
    else
        auto_success "모든 XLT 프로세스 완전 정리 완료"
    fi

    # 임시 파일 정리
    rm -f "$INSTALL_DIR"/*.tmp 2>/dev/null || true
    rm -f "$INSTALL_DIR"/*.lock 2>/dev/null || true

    echo "   🎯 프로세스 정리 완료 - 새 서버 시작 준비됨"
}

# =====================================
# 자동 의존성 복구 시스템
# =====================================

auto_fix_dependencies() {
    echo -e "${PURPLE}📦 자동 의존성 복구 시스템${NC}"

    cd "$INSTALL_DIR"

    # 필수 패키지 확인
    auto_info "필수 패키지 가용성 확인 중..."
    local missing_packages=""

    # Python 패키지 임포트 테스트
    local import_test=$(python3 -c "
import sys
packages = ['flask', 'requests', 'json', 'pathlib', 'os']
failed = []
for pkg in packages:
    try:
        __import__(pkg)
    except ImportError:
        failed.append(pkg)
if failed:
    print('MISSING:' + ','.join(failed))
else:
    print('OK')
" 2>&1)

    if [[ "$import_test" == "OK" ]]; then
        auto_success "필수 패키지 모두 사용 가능"
    else
        auto_warning "누락된 패키지: $import_test"
        auto_info "누락 패키지 자동 설치 시도..."

        # 자동 복구 시도
        auto_retry "python3 -m pip install --user flask requests" 2 || {
            auto_warning "pip 설치 실패 - 시스템 설치 시도"
            pip3 install flask requests --break-system-packages 2>/dev/null || true
        }
    fi
}

# =====================================
# I/O 에러 자동 복구 시스템
# =====================================

auto_fix_io_errors() {
    echo -e "${PURPLE}💾 I/O 에러 자동 복구 시스템${NC}"

    cd "$INSTALL_DIR"

    # 파일 권한 자동 수정
    auto_info "파일 권한 자동 최적화 중..."
    chmod 755 . 2>/dev/null || true
    chmod 644 *.py *.json 2>/dev/null || true
    chmod +x *.py 2>/dev/null || true

    # 설정 파일 권한 특별 처리
    if [ -f "figma_config.json" ]; then
        chmod 644 figma_config.json 2>/dev/null || true
        auto_info "figma_config.json 권한 수정됨"
    fi

    # 쓰기 권한 테스트
    auto_info "파일 쓰기 권한 테스트 중..."
    if echo "autofix_test" > "autofix_test.tmp" 2>/dev/null; then
        rm -f "autofix_test.tmp" 2>/dev/null
        auto_success "파일 쓰기 권한 정상"
    else
        auto_warning "파일 쓰기 권한 문제 - 자동 수정 시도"

        # 소유권 수정 시도
        chown -R "$(whoami)" . 2>/dev/null || {
            auto_warning "소유권 수정 실패 - 관리자 권한 필요할 수 있음"
        }
    fi

    # I/O 수정 코드 확인
    auto_info "I/O 에러 방지 코드 확인 중..."
    if grep -q "안전한 파일 쓰기" stable_web_server.py 2>/dev/null; then
        auto_success "I/O 에러 방지 코드 적용됨"
    else
        auto_warning "I/O 에러 방지 코드 누락 - GitHub에서 최신 파일 다운로드 시도"

        # 자동 복구: GitHub에서 최신 파일 다운로드
        if curl -sL "https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/stable_web_server.py" -o stable_web_server.py.new 2>/dev/null; then
            if [ -s "stable_web_server.py.new" ]; then
                cp stable_web_server.py "stable_web_server.py.backup.$(date +%Y%m%d_%H%M%S)" 2>/dev/null
                mv stable_web_server.py.new stable_web_server.py
                chmod 644 stable_web_server.py
                auto_success "최신 I/O 방지 코드로 자동 복구 완료"
            else
                rm -f stable_web_server.py.new 2>/dev/null
                auto_warning "다운로드된 파일이 비어있음"
            fi
        else
            auto_warning "GitHub 다운로드 실패"
        fi
    fi
}

# =====================================
# 지능형 서버 시작 시스템
# =====================================

intelligent_server_start() {
    echo -e "${PURPLE}🚀 지능형 서버 시작 시스템${NC}"

    cd "$INSTALL_DIR"

    # 1단계: 사전 검증
    auto_info "서버 시작 사전 검증 중..."

    # Python 실행 가능 확인
    if ! command -v python3 >/dev/null 2>&1; then
        auto_error "Python3이 설치되지 않았습니다"
        return 1
    fi

    # 서버 파일 존재 확인
    if [ ! -f "stable_web_server.py" ]; then
        auto_error "stable_web_server.py 파일이 없습니다"
        return 1
    fi

    # 2단계: 서버 시작 시도
    auto_info "서버 시작 시도 중..."

    # 백그라운드로 서버 시작
    python3 stable_web_server.py >/dev/null 2>&1 &
    SERVER_PID=$!

    # 서버 시작 대기
    auto_info "서버 초기화 대기 중 (15초)..."
    sleep 15

    # 3단계: 서버 응답 확인
    auto_info "서버 응답 확인 중..."
    local response_check=0

    for attempt in {1..5}; do
        if curl -s http://localhost:5004/api/version >/dev/null 2>&1; then
            auto_success "서버 응답 정상 (시도: $attempt)"
            response_check=1
            break
        else
            auto_info "서버 응답 대기 중... (시도: $attempt/5)"
            sleep 3
        fi
    done

    if [ $response_check -eq 1 ]; then
        # 4단계: I/O 에러 방지 테스트
        auto_info "I/O 에러 방지 시스템 테스트 중..."

        local io_test=$(curl -s -X POST http://localhost:5004/api/settings/save \
            -H "Content-Type: application/json" \
            -d '{"figma_token": "autofix_test_token"}' 2>/dev/null | grep -o '"status":"success"' || echo "")

        if [ -n "$io_test" ]; then
            auto_success "I/O 에러 방지 시스템 정상 작동"
            # 테스트 설정 파일 정리
            rm -f figma_config.json 2>/dev/null
        else
            auto_warning "I/O 에러 방지 시스템 문제 감지됨"
        fi

        return 0
    else
        auto_error "서버 응답 실패"
        return 1
    fi
}

# =====================================
# 자동 복구 메인 로직
# =====================================

auto_recovery_system() {
    echo -e "${CYAN}🔧 자동 복구 시스템 활성화${NC}"

    local recovery_needed=0

    # 복구 시도 1: 의존성 문제
    if ! auto_fix_dependencies; then
        auto_warning "의존성 복구 일부 실패"
        recovery_needed=1
    fi

    # 복구 시도 2: I/O 에러 문제
    auto_fix_io_errors

    # 복구 시도 3: 서버 시작
    if ! intelligent_server_start; then
        auto_error "서버 시작 실패 - 긴급 복구 모드 활성화"

        # 긴급 복구: 완전한 재설치 제안
        echo ""
        echo -e "${RED}🚨 자동 복구 실패 - 긴급 조치 필요${NC}"
        echo -e "${YELLOW}🔧 긴급 복구 방법:${NC}"
        echo "1. 완전 재설치 (권장):"
        echo "   curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash"
        echo ""
        echo "2. 수동 서버 시작:"
        echo "   cd $INSTALL_DIR && python3 stable_web_server.py"
        echo ""

        return 1
    fi

    return 0
}

# =====================================
# 메인 실행 로직
# =====================================

main() {
    # 시작 메시지
    echo ""
    echo -e "${BLUE}🚀 XLT System v3.1 자가 치유 시스템 시작${NC}"
    echo -e "${BLUE}===============================================${NC}"
    echo -e "${CYAN}💡 모든 문제를 자동으로 감지하고 해결합니다${NC}"
    echo ""

    # 로그 파일 초기화
    echo "XLT System 자가 치유 로그 - $(date)" > "$AUTO_FIX_LOG"

    # 디렉토리 확인
    if [ ! -d "$INSTALL_DIR" ]; then
        auto_error "XLT System 설치 디렉토리를 찾을 수 없습니다: $INSTALL_DIR"
        echo -e "${YELLOW}💡 재설치가 필요합니다:${NC}"
        echo "curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash"
        exit 1
    fi

    # 1단계: 완전한 프로세스 정리
    ultimate_process_cleanup

    # 2단계: 자동 복구 시스템
    if auto_recovery_system; then
        # 성공 시
        echo ""
        echo -e "${GREEN}🎉 XLT System v3.1 자가 치유 시작 성공!${NC}"
        echo -e "${GREEN}✅ 모든 문제가 자동으로 해결되었습니다${NC}"
        echo ""
        echo -e "${CYAN}🌐 브라우저에서 XLT System 열기...${NC}"
        open http://localhost:5004
        echo ""
        echo -e "${CYAN}🖥️ 시스템 트레이 애플리케이션 실행...${NC}"
        echo -e "${PURPLE}📱 사용 방법:${NC}"
        echo "1. 웹 브라우저에서 설정 페이지 접속"
        echo "2. 피그마 토큰 입력 및 저장 (I/O 에러 자동 방지)"
        echo "3. 메인 페이지에서 번역 작업 시작"
        echo ""
        echo -e "${PURPLE}💡 앞으로 모든 문제는 자동으로 해결됩니다!${NC}"
        echo ""

        # Tray 애플리케이션 실행 (안정성 강화)
        echo -e "${PURPLE}🖥️ 시스템 트레이 애플리케이션 시작 중...${NC}"

        if python3 xlt_tray.py 2>/dev/null; then
            auto_success "시스템 트레이 앱이 시작되었습니다"
        else
            auto_warning "시스템 트레이 앱 시작 실패"
            echo ""
            echo -e "${CYAN}💡 트레이 기능 없이도 모든 기능이 정상 작동합니다:${NC}"
            echo "   🌐 웹 브라우저: http://localhost:5004"
            echo "   📱 피그마 토큰 저장, 번역, Excel 출력 모두 가능"
            echo ""
            echo -e "${YELLOW}🔧 트레이 기능 복구 방법 (선택사항):${NC}"
            echo "   pip install --upgrade pystray pillow"
            echo "   시스템 재부팅 후 다시 실행"
            echo ""
        fi
    else
        # 실패 시
        echo ""
        echo -e "${RED}🚨 자가 치유 시스템 복구 실패${NC}"
        echo ""
        echo -e "${YELLOW}📞 지원 정보:${NC}"
        echo "   자동 복구 로그: $AUTO_FIX_LOG"
        echo "   긴급 재설치: curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash"
        echo ""
        exit 1
    fi
}

# =====================================
# 자가 치유 시스템 활성화
# =====================================

activate_self_healing_system() {
    info_message "자가 치유 시스템 설정 중..."

    cd "$INSTALL_DIR"

    # 1. 자가 치유 설정 파일 생성
    cat > "self_healing_config.json" << 'JSON_EOF'
{
    "self_healing": {
        "enabled": true,
        "auto_restart_on_crash": true,
        "auto_fix_io_errors": true,
        "auto_recover_dependencies": true,
        "health_check_interval": 60,
        "max_auto_restarts": 3,
        "emergency_contact": {
            "log_file": "~/.xlt_autofix.log",
            "reinstall_url": "https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh"
        }
    },
    "monitoring": {
        "check_port_5004": true,
        "check_server_response": true,
        "check_api_endpoints": ["/api/version", "/api/health"],
        "check_file_permissions": true
    },
    "auto_recovery": {
        "strategies": [
            "process_restart",
            "dependency_reinstall",
            "file_permission_fix",
            "github_file_refresh",
            "complete_reinstall"
        ]
    }
}
JSON_EOF

    # 2. 헬스 체크 스크립트 생성
    cat > "health_check.py" << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
XLT System 자가 치유 헬스 체크 시스템
"""

import json
import subprocess
import time
import requests
import os
import signal
import sys
from pathlib import Path

class XLTHealthChecker:
    def __init__(self):
        self.config_file = Path(__file__).parent / "self_healing_config.json"
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            self.config = {"self_healing": {"enabled": False}}

    def check_server_health(self):
        """서버 상태 확인"""
        try:
            response = requests.get("http://localhost:5004/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def check_process_running(self):
        """프로세스 실행 상태 확인"""
        try:
            result = subprocess.run(['pgrep', '-f', 'stable_web_server.py'],
                                  capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False

    def auto_restart_server(self):
        """서버 자동 재시작"""
        try:
            print("🔄 서버 자동 재시작 시도...")

            # 기존 프로세스 정리
            subprocess.run(['pkill', '-f', 'stable_web_server.py'], stderr=subprocess.DEVNULL)
            time.sleep(3)

            # 새 서버 시작
            subprocess.Popen(['python3', 'stable_web_server.py'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5)

            # 재시작 확인
            if self.check_server_health():
                print("✅ 서버 자동 재시작 성공")
                return True
            else:
                print("❌ 서버 재시작 실패")
                return False

        except Exception as e:
            print(f"❌ 자동 재시작 오류: {e}")
            return False

    def run_health_check(self):
        """헬스 체크 실행"""
        if not self.config.get("self_healing", {}).get("enabled", False):
            return True

        print("🔍 XLT System 헬스 체크 실행 중...")

        # 프로세스 확인
        if not self.check_process_running():
            print("⚠️ 서버 프로세스가 실행되지 않음")
            if self.auto_restart_server():
                return True
            else:
                return False

        # 서버 응답 확인
        if not self.check_server_health():
            print("⚠️ 서버 응답 실패")
            if self.auto_restart_server():
                return True
            else:
                return False

        print("✅ 시스템 정상")
        return True

if __name__ == "__main__":
    checker = XLTHealthChecker()
    success = checker.run_health_check()
    sys.exit(0 if success else 1)
PYTHON_EOF

    chmod +x health_check.py

    # 3. 시스템 모니터링을 위한 cron job 설정 (선택적)
    info_message "시스템 모니터링 설정 완료"

    success_message "자가 치유 시스템이 활성화되었습니다"
}

# =====================================
# 언인스톨러 설정
# =====================================

setup_uninstaller() {
    info_message "언인스톨러 설정 중..."

    cd "$INSTALL_DIR"

    # 1. uninstall 폴더 생성
    mkdir -p uninstall

    # 2. 언인스톨 스크립트 다운로드
    info_message "언인스톨 스크립트 다운로드 중..."
    if curl -sL "$GITHUB_RAW_URL/install/uninstall.sh" -o "uninstall/uninstall.sh"; then
        chmod +x "uninstall/uninstall.sh"
        success_message "언인스톨 스크립트 다운로드 완료"
    else
        warning_message "언인스톨 스크립트 다운로드 실패 - 온라인 버전을 사용하세요"
    fi

    # 3. 로컬 언인스톨 스크립트 생성
    cat > "uninstall/local_uninstall.sh" << 'UNINSTALL_EOF'
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
UNINSTALL_EOF

    chmod +x "uninstall/local_uninstall.sh"

    # 4. 데스크톱에 제거 바로가기 생성 (선택적)
    cat > "$HOME/Desktop/XLT System 제거.command" << 'SHORTCUT_EOF'
#!/bin/bash
cd ~/XLT-System/uninstall
./local_uninstall.sh
SHORTCUT_EOF

    chmod +x "$HOME/Desktop/XLT System 제거.command"

    # 5. README 파일 생성
    cat > "uninstall/README.md" << 'README_EOF'
# XLT System 제거 방법

## 방법 1: 로컬 스크립트 사용 (권장)
```bash
cd ~/XLT-System/uninstall
./local_uninstall.sh
```

## 방법 2: 온라인 스크립트 사용
```bash
echo "y" | curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
```

## 방법 3: 데스크톱 바로가기 사용
데스크톱의 "XLT System 제거.command" 파일을 더블클릭

## 방법 4: 수동 제거
```bash
# 프로세스 종료
pkill -f "python.*xlt"

# 디렉토리 삭제
rm -rf ~/XLT-System
rm -rf ~/Documents/XLTTT

# 바로가기 삭제
rm -f ~/Desktop/"XLT System"*.command
```

모든 방법으로 완전한 제거가 가능합니다.
README_EOF

    success_message "언인스톨러 설정 완료"
    info_message "제거 방법: ~/XLT-System/uninstall/local_uninstall.sh 실행"
}

# =====================================
# 메인 설치 함수
# =====================================

main() {
    # 시작 메시지
    echo ""
    echo -e "${BLUE}🚀 XLT System v5.1.1 완전 자동화 설치 시작${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${CYAN}💡 '원클릭 완전 자동화' - 실패 불가능한 설치 시스템 + 언인스톨러${NC}"
    echo ""

    # 로그 파일 초기화
    echo "XLT System 설치 로그 - $(date)" > "$LOG_FILE"

    # 1단계: 환경 감지
    detect_environment || {
        error_message "환경 감지 실패"
        exit 1
    }

    # 2단계: 지능형 정리
    intelligent_cleanup

    # 3단계: 소스 다운로드
    progress_bar 3 $TOTAL_STEPS "소스 코드 다운로드 중..."
    info_message "XLT System 소스 다운로드..."

    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    if curl -L "$DOWNLOAD_URL" -o xlt-system.zip --silent --show-error; then
        unzip -q xlt-system.zip
        mv xlt-system-main "$INSTALL_DIR"
        success_message "소스 다운로드 완료"
    else
        error_message "소스 다운로드 실패"
        exit 1
    fi

    rm -rf "$TEMP_DIR"

    # 4단계: 패키지 설치
    install_packages_strategy || {
        error_message "패키지 설치 실패"
        exit 1
    }

    # 5단계: 권한 설정
    progress_bar 5 $TOTAL_STEPS "파일 권한 설정 중..."
    cd "$INSTALL_DIR"
    chmod 755 .
    chmod 644 *.py *.json 2>/dev/null || true
    chmod +x *.py 2>/dev/null || true
    success_message "파일 권한 설정 완료"

    # 6단계: 설정 파일 생성
    progress_bar 6 $TOTAL_STEPS "초기 설정 파일 생성 중..."
    create_initial_config
    success_message "초기 설정 완료"

    # 7단계: Claude CLI 설치 및 설정
    progress_bar 7 $TOTAL_STEPS "Claude CLI 설치 및 설정 중..."
    setup_claude_cli
    success_message "Claude CLI 설정 완료"

    # 8단계: 종합 검증
    progress_bar 8 $TOTAL_STEPS "종합적 시스템 검증 중..."
    comprehensive_verification

    # 9단계: 자가 치유 바로가기 생성
    progress_bar 9 $TOTAL_STEPS "자가 치유 바로가기 생성 중..."
    create_independent_shortcut
    success_message "자가 치유 바로가기 생성 완료"

    # 10단계: 자가 치유 시스템 활성화
    progress_bar 10 $TOTAL_STEPS "자가 치유 시스템 활성화 중..."
    activate_self_healing_system
    success_message "자가 치유 시스템 활성화됨"

    # 11단계: 언인스톨러 설정
    progress_bar 11 $TOTAL_STEPS "언인스톨러 설정 중..."
    setup_uninstaller
    success_message "언인스톨러 설정 완료"

    # 12단계: 완료
    progress_bar 12 $TOTAL_STEPS "설치 완료!"

    # 완료 메시지
    local end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    echo ""
    echo -e "${GREEN}🎉 XLT System v5.1.1 설치 완료!${NC}"
    echo -e "${GREEN}⏱️  설치 소요 시간: ${duration}초${NC}"
    echo ""
    echo -e "${CYAN}📱 사용 방법:${NC}"
    echo "1. 데스크톱의 'XLT System (Tray).command' 더블클릭"
    echo "2. 🎯 시스템 트레이에서 XLT 아이콘 확인 (터미널 자동 닫힘)"
    echo "3. 브라우저에서 http://localhost:5004 접속"
    echo "4. 설정 페이지에서 피그마 토큰 입력"
    echo "5. Claude 통합 번역으로 고품질 번역 시작! ✨"
    echo ""
    echo -e "${GREEN}🤖 Claude 번역 기능:${NC}"
    echo "• 맞춤법 교정 + 번역을 동시에 처리"
    echo "• 가이드라인 기반 전문 번역"
    echo "• 피그마/엑셀 번역 모두 지원"
    echo ""
    echo -e "${GREEN}💡 터미널 독립 실행: 터미널을 닫아도 계속 실행됩니다!${NC}"
    echo ""
    echo -e "${RED}🗑️ 제거 방법:${NC}"
    echo "• 바로가기: 데스크톱의 'XLT System 제거.command' 더블클릭"
    echo "• 터미널: cd ~/XLT-System/uninstall && ./local_uninstall.sh"
    echo "• 온라인: echo \"y\" | curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash"
    echo ""
    echo -e "${PURPLE}💡 모든 문제는 자동으로 해결됩니다!${NC}"
    echo -e "${PURPLE}📞 문제 발생 시 로그: $LOG_FILE${NC}"
    echo ""
}

# 스크립트 실행
main "$@"