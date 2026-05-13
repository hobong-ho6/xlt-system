#!/bin/bash

# XLT System v3.1 터미널 독립 실행 스크립트
# 터미널 종료 후에도 백그라운드에서 계속 실행

INSTALL_DIR="/Users/ho6/XLT-System"

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
    nohup python3 xlt_tray.py > "$LOG_FILE" 2>&1 &
    TRAY_PID=$!
    disown $TRAY_PID  # 터미널에서 완전 분리
    sleep 5

    # 트레이 앱 실행 확인
    if kill -0 $TRAY_PID 2>/dev/null; then
        echo "✅ 트레이 앱이 시작되었습니다!"
        SERVER_PID=$TRAY_PID
        START_MODE="tray"
    else
        echo "⚠️ 트레이 앱 시작 실패 - 웹 서버 모드로 전환..."
        START_MODE="fallback"
    fi
else
    START_MODE="fallback"
fi

# Fallback: 웹 서버 직접 시작
if [ "$START_MODE" = "fallback" ]; then
    echo "🌐 웹 서버를 직접 시작합니다..."
    nohup python3 stable_web_server.py > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    disown $SERVER_PID  # 터미널에서 완전 분리
    sleep 3

    if kill -0 $SERVER_PID 2>/dev/null; then
        echo "✅ 웹 서버가 시작되었습니다!"
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
echo "⏰ 10초 후 터미널이 자동으로 닫힙니다..."
echo "   💡 또는 아무 키나 눌러서 수동으로 닫으세요."
echo "   (프로세스 완전 분리 대기 중...)"

# 브라우저도 자동으로 열기
sleep 2
open http://localhost:5004 2>/dev/null || true

# 백그라운드 프로세스 완전 분리 대기
echo "🔄 프로세스 안정화 중..."
sleep 3

# 프로세스 실행 재확인
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ 백그라운드 프로세스 안정적으로 실행 중"
else
    echo "⚠️ 백그라운드 프로세스 상태 불확실"
fi

# 사용자 입력 대기 (10초 타임아웃)
echo ""
if read -t 10 -n 1 -s -r; then
    echo "🚪 사용자 입력으로 터미널을 닫습니다..."
else
    echo "🚪 자동으로 터미널을 닫습니다..."
fi

# AppleScript로 터미널 창 닫기 시도 (더 안전하게)
osascript -e 'tell application "Terminal" to close front window' 2>/dev/null || true

