#!/bin/bash

# XLT System 피그마 토큰 I/O 에러 긴급 해결 스크립트
# 설치 후에도 I/O 에러 지속 시 실행

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}🚨 XLT System 피그마 토큰 I/O 에러 긴급 해결${NC}"
echo "=================================================="

# XLT-System 디렉토리 확인
INSTALL_DIR="$HOME/XLT-System"
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}❌ XLT-System 디렉토리를 찾을 수 없습니다: $INSTALL_DIR${NC}"
    exit 1
fi

cd "$INSTALL_DIR"

echo -e "${BLUE}🔍 현재 상태 진단 중...${NC}"

# 1. 현재 버전 확인
if [ -f "version.json" ]; then
    CURRENT_VERSION=$(python3 -c "
import json
try:
    with open('version.json', 'r') as f:
        data = json.load(f)
        print(data.get('version', 'unknown'))
except:
    print('unknown')
" 2>/dev/null)
    echo "📦 현재 버전: $CURRENT_VERSION"
else
    echo -e "${YELLOW}⚠️ version.json 파일이 없습니다${NC}"
fi

# 2. I/O 수정 코드 확인
echo -e "${BLUE}🔍 I/O 수정 코드 상태 확인...${NC}"
if [ -f "stable_web_server.py" ]; then
    HAS_ATOMIC_FIX=$(grep -c "# 안전한 파일 쓰기 (임시 파일 사용)" stable_web_server.py 2>/dev/null || echo "0")
    HAS_TEMP_PATH=$(grep -c "temp_path = figma_config_path.with_suffix" stable_web_server.py 2>/dev/null || echo "0")
    HAS_OS_FSYNC=$(grep -c "os.fsync(f.fileno())" stable_web_server.py 2>/dev/null || echo "0")

    if [ "$HAS_ATOMIC_FIX" -gt "0" ] && [ "$HAS_TEMP_PATH" -gt "0" ] && [ "$HAS_OS_FSYNC" -gt "0" ]; then
        echo "✅ I/O 에러 수정 코드가 포함되어 있습니다"
        CODE_STATUS="ok"
    else
        echo -e "${RED}❌ I/O 에러 수정 코드가 누락되었습니다${NC}"
        echo "   원자적 수정 주석: $HAS_ATOMIC_FIX"
        echo "   임시 파일 생성: $HAS_TEMP_PATH"
        echo "   디스크 동기화: $HAS_OS_FSYNC"
        CODE_STATUS="missing"
    fi
else
    echo -e "${RED}❌ stable_web_server.py 파일이 없습니다${NC}"
    CODE_STATUS="missing"
fi

# 3. 모든 프로세스 완전 종료
echo -e "${BLUE}🛑 모든 XLT 프로세스 완전 종료...${NC}"
pkill -f stable_web_server.py 2>/dev/null || echo "   (stable_web_server 프로세스 없음)"
pkill -f xlt_tray.py 2>/dev/null || echo "   (xlt_tray 프로세스 없음)"
pkill -f python.*stable_web_server 2>/dev/null || echo "   (python stable_web_server 프로세스 없음)"
sleep 3

# 4. 강제로 최신 파일 다운로드
echo -e "${BLUE}📥 GitHub에서 최신 수정 파일 강제 다운로드...${NC}"
GITHUB_RAW_URL="https://raw.githubusercontent.com/hobong-ho6/xlt-system/main"

# 백업 생성
if [ -f "stable_web_server.py" ]; then
    cp stable_web_server.py "stable_web_server.py.emergency_backup.$(date +%Y%m%d_%H%M%S)"
    echo "   💾 기존 파일 백업 완료"
fi

# 최신 파일 다운로드
echo "   📄 stable_web_server.py 다운로드 중..."
if curl -sL "$GITHUB_RAW_URL/stable_web_server.py" -o stable_web_server.py.new; then
    if [ -s "stable_web_server.py.new" ]; then
        mv stable_web_server.py.new stable_web_server.py
        echo "   ✅ stable_web_server.py 업데이트 완료"
    else
        echo -e "${RED}   ❌ 다운로드된 파일이 비어있습니다${NC}"
        rm -f stable_web_server.py.new
    fi
else
    echo -e "${RED}   ❌ stable_web_server.py 다운로드 실패${NC}"
fi

echo "   📄 version.json 다운로드 중..."
if curl -sL "$GITHUB_RAW_URL/version.json" -o version.json.new; then
    if [ -s "version.json.new" ]; then
        mv version.json.new version.json
        echo "   ✅ version.json 업데이트 완료"
    else
        echo -e "${RED}   ❌ 다운로드된 version.json이 비어있습니다${NC}"
        rm -f version.json.new
    fi
else
    echo -e "${RED}   ❌ version.json 다운로드 실패${NC}"
fi

# 5. I/O 수정 코드 재확인
echo -e "${BLUE}🔍 업데이트 후 I/O 수정 코드 재확인...${NC}"
if [ -f "stable_web_server.py" ]; then
    HAS_ATOMIC_FIX=$(grep -c "# 안전한 파일 쓰기 (임시 파일 사용)" stable_web_server.py 2>/dev/null || echo "0")
    HAS_TEMP_PATH=$(grep -c "temp_path = figma_config_path.with_suffix" stable_web_server.py 2>/dev/null || echo "0")
    HAS_OS_FSYNC=$(grep -c "os.fsync(f.fileno())" stable_web_server.py 2>/dev/null || echo "0")

    if [ "$HAS_ATOMIC_FIX" -gt "0" ] && [ "$HAS_TEMP_PATH" -gt "0" ] && [ "$HAS_OS_FSYNC" -gt "0" ]; then
        echo "✅ I/O 에러 수정 코드가 정상적으로 적용되었습니다"
    else
        echo -e "${RED}❌ 여전히 I/O 에러 수정 코드가 누락되었습니다${NC}"
        echo -e "${YELLOW}💡 GitHub 동기화 문제일 수 있습니다. 잠시 후 다시 시도해주세요.${NC}"
    fi
fi

# 6. 파일 권한 강제 수정
echo -e "${BLUE}🔒 파일 권한 강제 수정...${NC}"
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR"/*.py "$INSTALL_DIR"/*.json 2>/dev/null || true
chmod +x "$INSTALL_DIR"/*.py 2>/dev/null || true

# 기존 설정 파일들 권한 수정
if [ -f "figma_config.json" ]; then
    chmod 644 figma_config.json
    echo "   🔑 figma_config.json 권한 수정"
fi

if [ -f "user_config.json" ]; then
    chmod 644 user_config.json
    echo "   ⚙️ user_config.json 권한 수정"
fi

# 7. 디스크 동기화
echo -e "${BLUE}💾 디스크 동기화...${NC}"
sync

# 8. 쓰기 권한 테스트
echo -e "${BLUE}📝 파일 쓰기 권한 테스트...${NC}"
TEST_FILE="$INSTALL_DIR/emergency_test_write.tmp"

if echo "emergency test" > "$TEST_FILE" 2>/dev/null; then
    rm -f "$TEST_FILE"
    echo "✅ 기본 파일 쓰기 권한 정상"
    WRITE_OK=true
else
    echo -e "${RED}❌ 기본 파일 쓰기 권한 문제${NC}"
    WRITE_OK=false
fi

# JSON 쓰기 테스트
TEST_JSON="$INSTALL_DIR/emergency_test.json"
if echo '{"test": "emergency"}' > "$TEST_JSON" 2>/dev/null; then
    rm -f "$TEST_JSON"
    echo "✅ JSON 파일 쓰기 권한 정상"
else
    echo -e "${RED}❌ JSON 파일 쓰기 권한 문제${NC}"
    WRITE_OK=false
fi

# 9. 원자적 쓰기 테스트 (실제 방식과 동일)
echo -e "${BLUE}🧪 원자적 파일 쓰기 테스트...${NC}"
ATOMIC_TEST="$INSTALL_DIR/emergency_atomic_test.json"
ATOMIC_OK=false

if python3 -c "
import os
import json
from pathlib import Path

try:
    figma_config = {'access_token': 'emergency_test_token_123456'}
    figma_config_path = Path('$ATOMIC_TEST')
    temp_path = figma_config_path.with_suffix('.tmp')

    # 임시 파일에 쓰기
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(figma_config, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())

    # 원자적 이동
    if figma_config_path.exists():
        figma_config_path.unlink()
    os.rename(temp_path, figma_config_path)

    # 검증
    with open(figma_config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data['access_token'] == 'emergency_test_token_123456'

    figma_config_path.unlink()
    print('SUCCESS')

except Exception as e:
    print(f'ERROR: {e}')
    # 정리
    if Path('$ATOMIC_TEST.tmp').exists():
        Path('$ATOMIC_TEST.tmp').unlink()
    if Path('$ATOMIC_TEST').exists():
        Path('$ATOMIC_TEST').unlink()
" 2>/dev/null; then
    ATOMIC_RESULT=$(python3 -c "
import os
import json
from pathlib import Path

try:
    figma_config = {'access_token': 'emergency_test_token_123456'}
    figma_config_path = Path('$ATOMIC_TEST')
    temp_path = figma_config_path.with_suffix('.tmp')

    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(figma_config, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())

    if figma_config_path.exists():
        figma_config_path.unlink()
    os.rename(temp_path, figma_config_path)

    with open(figma_config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert data['access_token'] == 'emergency_test_token_123456'

    figma_config_path.unlink()
    print('SUCCESS')

except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

    if [ "$ATOMIC_RESULT" = "SUCCESS" ]; then
        echo "✅ 원자적 파일 쓰기 테스트 성공"
        ATOMIC_OK=true
    else
        echo -e "${RED}❌ 원자적 파일 쓰기 테스트 실패: $ATOMIC_RESULT${NC}"
    fi
else
    echo -e "${RED}❌ 원자적 파일 쓰기 Python 실행 실패${NC}"
fi

# 10. 서버 시작 및 실제 API 테스트
echo -e "${BLUE}🚀 서버 시작 및 실제 API 테스트...${NC}"
python3 stable_web_server.py &
SERVER_PID=$!

# 서버 시작 대기
sleep 5

# 서버 응답 확인
if curl -s http://localhost:5004/api/version >/dev/null 2>&1; then
    echo "✅ 서버 응답 정상"

    # 실제 피그마 토큰 저장 API 테스트
    echo "🧪 실제 피그마 토큰 저장 API 테스트..."

    API_RESULT=$(curl -s -X POST http://localhost:5004/api/settings/save \
        -H "Content-Type: application/json" \
        -d '{"figma_token": "emergency_test_token_987654321"}' \
        2>/dev/null)

    if echo "$API_RESULT" | grep -q '"status":"success"'; then
        echo -e "${GREEN}✅ 피그마 토큰 저장 API 테스트 성공!${NC}"
        echo -e "${GREEN}🎉 I/O 에러가 해결되었습니다!${NC}"

        # 테스트 토큰 파일 정리
        rm -f figma_config.json 2>/dev/null

        API_OK=true
    else
        echo -e "${RED}❌ 피그마 토큰 저장 API 테스트 실패${NC}"
        echo "   API 응답: $API_RESULT"
        API_OK=false
    fi
else
    echo -e "${RED}❌ 서버 시작 실패${NC}"
    API_OK=false
fi

# 11. 최종 진단 결과
echo ""
echo -e "${BLUE}📋 최종 진단 결과${NC}"
echo "=================================="

if [ "$WRITE_OK" = true ]; then
    echo "✅ 파일 쓰기 권한: 정상"
else
    echo "❌ 파일 쓰기 권한: 문제"
fi

if [ "$ATOMIC_OK" = true ]; then
    echo "✅ 원자적 파일 쓰기: 정상"
else
    echo "❌ 원자적 파일 쓰기: 문제"
fi

if [ "$API_OK" = true ]; then
    echo "✅ 피그마 토큰 저장 API: 정상"
else
    echo "❌ 피그마 토큰 저장 API: 문제"
fi

# 12. 해결책 제안
echo ""
echo -e "${BLUE}💡 해결책${NC}"
echo "=================================="

if [ "$API_OK" = true ]; then
    echo -e "${GREEN}🎉 모든 문제가 해결되었습니다!${NC}"
    echo ""
    echo "📱 사용 방법:"
    echo "1. 브라우저에서 http://localhost:5004 접속"
    echo "2. 설정 페이지에서 실제 피그마 토큰 입력"
    echo "3. '설정 저장 및 적용' 버튼 클릭"
    echo "4. 성공 메시지 확인"

else
    echo -e "${RED}🚨 I/O 에러가 지속되고 있습니다${NC}"
    echo ""
    echo "🔧 추가 해결 방법:"

    if [ "$WRITE_OK" = false ]; then
        echo "1. 권한 문제 해결:"
        echo "   sudo chown -R \$(whoami) $INSTALL_DIR"
        echo "   chmod -R 755 $INSTALL_DIR"
    fi

    echo "2. 완전 재설치:"
    echo "   curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash"
    echo "   curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install.sh | bash"

    echo "3. 수동 디렉토리 생성 후 재설치:"
    echo "   rm -rf ~/XLT-System"
    echo "   mkdir -p ~/XLT-System"
    echo "   chmod 755 ~/XLT-System"
    echo "   curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install.sh | bash"
fi

echo ""
echo -e "${YELLOW}💡 서버는 백그라운드에서 실행 중입니다 (PID: $SERVER_PID)${NC}"
echo ""