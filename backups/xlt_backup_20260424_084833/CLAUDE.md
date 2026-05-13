# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**XLT System v3.1** - Figma URL이나 이미지에서 OCR로 텍스트를 추출하고 5개 언어로 번역하는 자동화 시스템

**핵심 워크플로우**: Figma URL/이미지 입력 → OCR 텍스트 추출 → 사용자 선택 → 치환자 처리 → 번역 미리보기 → Excel 다운로드

**v3.1 주요 기능**:
- Flask 기반 웹 인터페이스 (포트 5004)
- **Unifi 전문 번역 시스템** (guide.md 준수, 1,244개 용어 DB 활용)
- **지능형 XLT 키 생성** (Unifi 패턴 분석 기반)
- **자동 업데이트 시스템** (GitHub API 기반, 웹 UI 통합)
- **강화된 I/O 에러 방지 시스템** (원자적 파일 쓰기, 자동 복구, 종합 검증)
- **완전한 언인스톨러** (3가지 제거 옵션)
- 자동 치환자 감지 ({{0}}, {{1}} 등)
- 번역 미리보기 및 Excel 병합 기능

## 개발 환경 설정

### 빠른 시작
```bash
# 자동 설치 (권장 - v2.0 완전 자동화)
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash

# 수동 의존성 설치
pip install -r requirements.txt

# 웹 서버 시작 (SessionStart 훅으로 자동 시작)
python3 stable_web_server.py

# 트레이 앱 시작 (터미널 독립 실행)
python3 xlt_tray.py

# 웹 인터페이스 접속
http://localhost:5004
```

### 트레이 시스템 (v3.1 rumps 기반)
```bash
# 트레이 앱 터미널 독립 실행 (권장)
~/Desktop/"XLT System (Tray).command"

# 트레이 앱 직접 실행 (macOS 네이티브)
python3 xlt_tray.py

# 실행 중인 트레이 앱 확인
pgrep -f "python.*xlt_tray.py"

# rumps 라이브러리 설치
pip install 'pyobjc-core>=9.0,<10.0' 'pyobjc-framework-Cocoa>=9.0,<10.0' rumps
```

### 환경 설정
```bash
# Figma 토큰 설정 (선택 사항)
export FIGMA_TOKEN="your_figma_personal_access_token"

# 또는 설정 파일 생성
cp figma_config_example.json figma_config.json
# figma_config.json에 토큰 추가
```

## 핵심 아키텍처

### 메인 컴포넌트
- **`stable_web_server.py`**: Flask 웹 서버 (메인 진입점)
- **`xlt_tray.py`**: **시스템 트레이 앱** (v3.1 신규) - 터미널 독립 실행, 동적 메뉴
- **`xlt/core/pipeline.py`**: 워크플로우 오케스트레이션
- **`xlt/ocr/engine.py`**: EasyOCR 기반 텍스트 추출
- **`xlt/translation/`**:
  - `translator.py`: Google Translate 기본 번역
  - `unifi_translator.py`: **Unifi 전문 번역** (v3.1 신규)
- **`xlt/utils/`**:
  - `unifi_key_generator.py`: **지능형 키 생성** (v3.1 신규)
  - `updater.py`: **자동 업데이트** (v3.1 신규)
  - `placeholder_detector.py`: 치환자 자동 감지

### 설치 시스템 (v3.1 완전 개선)
- **`install/install_v2.sh`**: **완전 자동화 설치** - 4단계 fallback 전략, macOS 호환성
- **`install/uninstall.sh`**: **지능형 언인스톨러** - 3가지 제거 옵션
- **`install/debug_install.sh`**: 디버깅 모드 설치 (문제 진단용)

### 번역 워크플로우
1. **입력**: Figma URL 또는 이미지 업로드
2. **OCR**: EasyOCR로 텍스트 추출 + 한국어 교정
3. **선택**: 사용자 체크박스 선택
4. **치환자**: 자동 패턴 감지 (숫자, 금액, 레벨, 퍼센트 등)
5. **번역**: 개별 텍스트 처리 (ko_KR, en_US, ja_JP, zh_TW, th_TH)
6. **미리보기**: XLT 키와 함께 번역 결과 표시
7. **다운로드**: Excel 파일 생성

## 핵심 번역 가이드라인 (Unifi 서비스)

**필수 사항**: Unifi 핀테크 서비스 번역 시 `guide.md` 엄격 준수

### 주요 요구사항
- **참조 DB**: `Unifi/Unifi_WEB BROWSER_v*.xlsx` (1,244개 항목)
- **톤앤매너**: 
  - 한국어: 친근한 격식체 (~해요) - "매일 이자를 드려요"
  - 영어: 명확한 금융 언어 - "Log in with Apple"
  - 일본어: 정중한 경어 (です・ます체)
  - 중국어: 정중한 번체 중국어
  - 태국어: คะ/ครับ 없이 정중하게

### 번역 프로세스
1. 참조 데이터베이스에서 기존 번역 확인
2. OCR 교정 적용 (`{'이울': '이율', '미선': '미션', '토근': '토큰'}`)
3. 치환자 보존 ({{0}}, {{wallet}} 등)
4. HTML 태그 유지

## 핵심 아키텍처 결정사항

### 번역 시스템 설계 (중요)
**Google Translate 오작동 방지**: 번역 시스템에서 'ko_KR' 제외
```python
# ✅ 올바른 방식
target_languages = ['en_US', 'ja_JP', 'zh_TW', 'th_TH']  
result['ko_KR'] = original_text  # 한국어 원본 직접 사용

# ❌ 잘못된 방식 (모든 언어가 한국어로 반환됨)
target_languages = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
```

### v3.1 신규 시스템

#### Unifi 전문 번역 시스템
```python
from xlt.translation.unifi_translator import UnifiTranslator

translator = UnifiTranslator(XLTConfig())
result = translator.translate_with_unifi_context(
    "지갑 연결하기", ['en_US', 'ja_JP']
)
# Returns: {'ko_KR': '지갑 연결하기', 'en_US': 'Connect Wallet', 'ja_JP': 'ウォレット接続'}
```

#### 지능형 XLT 키 생성
```python
from xlt.utils.unifi_key_generator import UnifiKeyGenerator

generator = UnifiKeyGenerator()
key = generator.generate_unifi_key("지갑 연결하기", 1)
# Returns: "XLT_asset_text_지갑_연결하기_001" (instead of "item_1_hash")
```

#### 자동 업데이트 시스템
```python
from xlt.utils.updater import XLTUpdater

updater = XLTUpdater()
latest_version = await updater.check_for_updates()
if latest_version:
    success = await updater.perform_update()
```

#### 강화된 I/O 에러 방지 시스템
```bash
# 설치 시 자동으로 생성되는 Tray 바로가기에 포함된 기능들:
# - 원자적 파일 쓰기 (임시 파일 + os.fsync + 원자적 이동)
# - 자동 GitHub 복구 (코드 누락 시 최신 파일 다운로드)
# - 종합 권한 테스트 (기본/JSON/원자적 쓰기 3단계 검증)
# - 실시간 API 테스트 (피그마 토큰 저장 API 실제 동작 확인)
# - 스마트 문제 해결 안내 (컴포넌트별 맞춤 해결방법)

# 사용자는 emergency_io_fix.sh 스크립트를 별도로 실행할 필요 없음
# XLT System (Tray).command 더블클릭만으로 모든 안정성 검증 수행
```

#### 트레이 시스템 아키텍처 (v3.1 rumps 기반)
```python
import rumps
from xlt_tray import XLTTrayApp

# rumps.App 클래스 상속
# - macOS 네이티브 PyObjC 기반
# - Tcl/Tk 의존성 없음 (pystray 크래시 문제 해결)
app = XLTTrayApp()  # rumps.App 초기화
app.run()           # macOS 트레이에 아이콘 표시

# 동적 메뉴 업데이트 (rumps.Timer로 5초마다 자동)
app.check_server_status()      # 포트 + 프로세스 이중 확인
app.update_menu_state()        # 메뉴 활성화/비활성화, 아이콘 변경 (🔴/🟢)

# 메뉴 구성 (rumps 방식 - v3.1 강화)
menu = [
    rumps.MenuItem('XLT System 열기', callback=app.open_browser),
    rumps.separator,
    rumps.MenuItem('서버 시작', callback=app.menu_start_server),
    rumps.MenuItem('서버 중지', callback=app.menu_stop_server),
    rumps.MenuItem('서버 재시작', callback=app.menu_restart_server),  # NEW
    rumps.separator,
    rumps.MenuItem('로그 보기', callback=app.view_logs),  # NEW - 터미널로 실시간 로그
    rumps.MenuItem('상태 확인', callback=app.show_status),
]

# 서버 재시작 기능
def menu_restart_server(self, sender):
    self.menu_stop_server(None)
    time.sleep(2)
    self.start_server_async()
    rumps.notification("XLT System", "서버 재시작", "서버가 재시작되었습니다.")

# 로그 보기 기능 (macOS 터미널)
def view_logs(self, sender):
    # AppleScript로 터미널 열기, tail -f로 실시간 로그
    script = f'tell application "Terminal" to do script "tail -f {log_file}"'
    subprocess.run(['osascript', '-e', script])

# 터미널 독립 실행 (nohup)
nohup python3 xlt_tray.py > xlt_tray.log 2>&1 &
```

## 주요 API 엔드포인트

### 메인 워크플로우
- `POST /upload` - Figma URL/이미지 처리, OCR 결과 반환
- `GET /select_texts` - 텍스트 선택 인터페이스
- `POST /check-placeholders` - 치환자 패턴 감지
- `POST /translate-selected` - 번역 미리보기 데이터
- `POST /download-excel` - Excel 파일 생성

### v3.1 신규 API
- `GET /api/update/check` - GitHub 최신 버전 확인
- `POST /api/update/perform` - 업데이트 실행
- `POST /api/translate/unifi` - Unifi 전용 번역
- `POST /api/keys/generate` - Unifi 패턴 키 생성
- `GET /api/system/info` - 시스템 정보

### 시스템 관리
- `GET /api/health` - 시스템 상태 체크
- `GET /api/logs/<session_id>` - 실시간 로그

## 일반적인 문제 해결

### I/O 에러 방지 시스템 (v3.1 강화)
```bash
# 권장: Tray 바로가기 사용 (자동 안정성 검증 포함)
# 데스크톱의 "XLT System (Tray).command" 더블클릭

# 수동 안정성 검증 (필요 시)
curl -s http://localhost:5004/api/health | python3 -m json.tool

# 긴급 복구 (Tray 바로가기 실행 시 자동으로 수행됨)
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/emergency_io_fix.sh | bash
```

### 트레이 시스템 문제 해결 (v3.1 rumps 기반)
```bash
# 트레이 앱 상태 확인
pgrep -f "python.*xlt_tray.py" || echo "트레이 앱 미실행"

# 트레이 앱 로그 확인
tail -f ~/XLT-System/xlt_tray.log

# 트레이 앱 강제 종료 후 재시작
pkill -f "python.*xlt_tray.py"
cd ~/XLT-System && python3 xlt_tray.py

# rumps 라이브러리 문제 시 (pyobjc 9.x 버전 사용)
pip install --user 'pyobjc-core>=9.0,<10.0' 'pyobjc-framework-Cocoa>=9.0,<10.0' rumps

# rumps import 테스트
python3 -c "import rumps; print('✅ rumps 정상')"

# 터미널 독립 실행이 안 될 때
nohup python3 xlt_tray.py > xlt_tray.log 2>&1 &
```

### 서버 관리
```bash
# 서버 재시작
pkill -f stable_web_server.py
python3 stable_web_server.py

# 포트 충돌 확인
lsof -i :5004

# 시스템 상태 확인
curl -s http://localhost:5004/api/health
```

### 패키지 호환성 문제
```bash
# NumPy 2.x 호환성 오류 해결
pip install "numpy<2" pillow==9.5.0

# OCR 엔진 오류 해결 
pip install easyocr torch torchvision

# 의존성 패키지 전체 재설치
pip install -r requirements.txt --force-reinstall
```

### 번역 문제
```bash
# 태국어 번역 타임아웃 확인
# xlt/core/config.py에서 translation_timeout: 120 이상 설정

# 개별 번역 테스트
python3 -c "
from xlt.translation.translator import Translator
from xlt.core.config import XLTConfig
translator = Translator(XLTConfig())
result = translator.translate_batch(['테스트'], ['th_TH'])
print(result)
"
```

### 잘못된 업데이트 알림 문제
```bash
# ZIP 설치 환경에서 업데이트 버튼 지속 노출 시
# 서버 재시작으로 버전 체크 로직 갱신
pkill -f stable_web_server.py
cd ~/XLT-System && python3 stable_web_server.py
```

### 설치/제거 시스템 (v2.0)
```bash
# 완전 자동화 설치 (권장) - 2026-04-23 버그 수정됨
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash

# 완전 제거 (3가지 옵션)
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash

# 설치 문제 디버깅
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/debug_install.sh | bash

# macOS 호환성 문제 시 (timeout 명령어 없음)
# → install_v2.sh가 자동으로 run_with_timeout() 함수 사용하여 해결

# 2026-04-23 수정사항:
# - create_independent_shortcut() 함수 종료 누락 수정
# - 중복 코드 블록 (1118-1130번 줄) 제거
# - run_independent 미정의 함수 호출 제거
# → 설치 80% 멈춤 문제 완전 해결
```

## 코드베이스 작업 시 주의사항

### 번역 로직 수정 시
- **중요**: 'ko_KR'을 target_languages에서 제외하여 Google Translate 오작동 방지
- 한국어 텍스트는 원본을 직접 사용

### 기능 추가 시
- 모든 사용자 인터페이스는 한국어
- Unifi 관련 번역은 반드시 `guide.md` 참조
- 작업 완료 시 `handoff.md` 업데이트

### 웹 서버 개발
- 메인 진입점: `stable_web_server.py` (main.py 아님)
- 세션 관리: 메모리 기반 OCR 결과 및 번역 진행 상황
- 모든 API는 JSON 응답, 한국어 오류 메시지

## 현재 상태 (v3.1)

### 완료된 기능 ✅
- **완전한 워크플로우**: Figma → OCR → 선택 → 치환자 → 미리보기 → Excel
- **Unifi 전문 번역**: guide.md 준수, 1,244개 용어 DB
- **지능형 키 생성**: 의미있는 구조적 XLT 키 자동 생성
- **자동 업데이트**: GitHub API, 웹 UI, 안전한 백업/롤백
- **강화된 I/O 에러 방지**: 원자적 파일 쓰기, 자동 복구, 완전한 안정성 검증
- **완전한 언인스톨러**: 3가지 옵션, 지능형 감지
- **크로스 플랫폼**: 한글 파일명 문제 해결
- **동적 트레이 시스템**: 실시간 서버 상태 반영, 올바른 메뉴 활성화/비활성화
- **터미널 독립 실행**: nohup 백그라운드 실행, 터미널 종료 후에도 계속 작동
- **v2.0 설치 시스템**: 4단계 fallback 전략, macOS 호환성, 타임아웃 해결

### 지원 언어
- ko_KR (원본), en_US, ja_JP, zh_TW, th_TH

### 의존성 (호환성 최적화)
```bash
# 권장 설치 방법 v2.0 (완전 자동화, macOS 호환성 개선)
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash

# 디버깅 모드 설치 (문제 진단용)
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/debug_install.sh | bash

# 수동 설치 시 (순서 중요)
pip install "numpy<2" pillow==9.5.0
pip install googletrans==4.0.0rc1 easyocr openpyxl flask requests torch pandas rumps psutil
```

**중요**: NumPy 2.x와의 호환성 문제로 인해 numpy<2 버전 고정 필수

## 빠른 테스트

### 시스템 검증
```bash
# 전체 시스템 상태
curl -s http://localhost:5004/api/health | python3 -m json.tool

# XLT 패키지 임포트 확인
python3 -c "from xlt import XLTConfig; print('✅ XLT 시스템 OK')"
```

### v3.1 신규 기능 테스트
```bash
# Unifi 번역 시스템
python3 -c "
from xlt.translation.unifi_translator import UnifiTranslator
from xlt.core.config import XLTConfig
translator = UnifiTranslator(XLTConfig())
result = translator.translate_with_unifi_context('지갑 연결하기', ['en_US'])
print('Unifi 번역:', result)
"

# Unifi 키 생성
python3 -c "
from xlt.utils.unifi_key_generator import UnifiKeyGenerator
generator = UnifiKeyGenerator()
key = generator.generate_unifi_key('지갑 연결하기', 1)
print('생성된 키:', key)
"

# 업데이트 시스템
curl -s http://localhost:5004/api/update/check
```

이 시스템은 Figma 디자인을 다국어 Excel 파일로 처리하는 완전한 프로덕션 시스템입니다.