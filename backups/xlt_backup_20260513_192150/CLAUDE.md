# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 개발 원칙

이 원칙들은 XLT System의 모든 개발을 안내하며, 코드 변경 시 반드시 참고해야 합니다.

### 🧠 1. 코딩하기 전에 생각하기 (Think Before Coding)
**섣불리 가정하지 마세요. 헷갈리는 것을 숨기지 마세요. 트레이드오프를 명확히 밝히세요.**

**구현 전 반드시 확인:**
- [ ] 가정을 명시적으로 밝히고, 불확실하면 질문하세요
- [ ] 여러 해석이 가능하다면 이를 모두 제시하세요 - 임의로 조용히 선택하지 마세요
- [ ] 더 간단한 방법이 있다면 그렇다고 말하세요. 필요하다면 이의를 제기하세요
- [ ] 무언가 명확하지 않다면 멈추세요. 무엇이 헷갈리는지 명시하고 질문하세요

### ⚡ 2. 단순함 우선 (Simplicity First)
**문제를 해결하는 최소한의 코드만 작성하세요. 추측성 코드는 작성하지 마세요.**

**개발 시 준수사항:**
- [ ] 요청받은 것 이상의 기능을 추가하지 마세요
- [ ] 일회용 코드를 위해 추상화를 하지 마세요
- [ ] 요청받지 않은 "유연성"이나 "구성 가능성"을 추가하지 마세요
- [ ] 일어날 수 없는 시나리오에 대한 에러 처리를 하지 마세요
- [ ] 50줄로 끝낼 수 있는 코드를 200줄로 작성했다면 다시 작성하세요

> ❕ **스스로에게 물어보세요:** "시니어 엔지니어가 이 코드를 보고 너무 복잡하다고 할까?"  
> 만약 그렇다면 단순화하세요.

### 🎯 3. 외과 수술처럼 정교한 변경 (Surgical Changes)
**반드시 필요한 부분만 건드리세요. 본인이 어질러놓은 것만 정리하세요.**

**기존 코드 수정 시:**
- [ ] 인접한 코드, 주석, 포맷팅을 굳이 "개선"하려 하지 마세요
- [ ] 망가지지 않은 것을 리팩토링하지 마세요
- [ ] 본인의 방식과 다르더라도 기존 코드 스타일을 따르세요
- [ ] 무관한 데드 코드를 발견하면 언급만 하고 삭제하지 마세요

**본인의 변경으로 인해 고립된 코드(orphans)가 발생한 경우:**
- [ ] 당신의 변경으로 인해 사용되지 않게 된 import/변수/함수를 제거하세요
- [ ] 요청받지 않는 한 기존에 있던 데드 코드를 지우지 마세요

> 🎯 **검증 기준:** 변경된 모든 줄은 사용자의 요청과 직접적으로 연결되어야 합니다.

### 🚀 4. 목표 중심 실행 (Goal-Driven Execution)
**성공 기준을 정의하세요. 검증될 때까지 반복하세요.**

**작업을 검증 가능한 목표로 변환하세요:**
- "유효성 검사 추가" → "잘못된 입력에 대한 테스트를 작성하고, 이를 통과하게 만들기"
- "버그 수정" → "버그를 재현하는 테스트를 작성하고, 이를 통과하게 만들기"  
- "X 리팩토링" → "수정 전과 후 모두 테스트를 통과하는지 확인하기"

**여러 단계로 이루어진 작업의 경우 간략한 계획을 명시하세요:**
```text
1. [단계] → 검증: [확인 사항]
2. [단계] → 검증: [확인 사항]  
3. [단계] → 검증: [확인 사항]
```

> 강력한 성공 기준이 있어야 독립적으로 반복(loop) 작업을 수행할 수 있습니다.  
> 약한 기준("그냥 되게 만들어")은 끊임없는 추가 설명을 요구하게 만듭니다.

---

## 프로젝트 개요

**XLT System v5.1.0** - Figma URL에서 텍스트를 직접 추출하고 5개 언어로 번역하는 완전 자동화 시스템

**핵심 워크플로우**: Figma URL 입력 → **직접 텍스트 노드 추출** → **Claude 품질 검증 번역** (95점 목표) → 사용자 선택 → 텍스트 수정 → 치환자 처리 → 번역 미리보기 → Excel 다운로드

**v5.1.0 핵심 기능**:
- 🔥 **Claude 품질 검증 시스템** - 85점 → 95점 목표, 2단계 Claude 워크플로우
- 🚀 **Figma 텍스트 추출 방식 혁신** - OCR → 직접 텍스트 노드 추출, 100% 정확도
- ✨ **100% Claude 기반 번역** - 외부 API 완전 제거, 순수 Claude AI 처리
- ⚡ **90점 기준 자동 품질 검증** - 번역 후 자동 검증 및 재번역 시스템
- 🎯 **전문가 수준 Claude 검증** - 용어 일관성, 맞춤법, 자연스러움 자동 체크
- 🚀 **완전 자동화 업데이트 시스템** (v5.0.0) - 백그라운드 자동 감지 + 트레이 알림
- 🔍 **GitHub 레이트 리밋 근본 해결** (v5.0.0) - Personal Access Token 지원 (60회→5,000회)

---

## 빠른 시작

### 자동 설치 (권장)
```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash
```

### 실행
```bash
# 웹 서버 시작
python3 stable_web_server.py

# 트레이 앱 시작 (macOS 네이티브)
python3 xlt_tray.py

# 웹 인터페이스 접속
open http://localhost:5004
```

### 의존성 설치 (수동 설치 시)
```bash
# 필수 패키지 (순서 중요)
pip install "numpy<2" pillow==9.5.0
pip install googletrans==4.0.0rc1 easyocr openpyxl flask requests torch pandas

# macOS 트레이 (rumps)
pip install 'pyobjc-core>=9.0,<10.0' 'pyobjc-framework-Cocoa>=9.0,<10.0' rumps psutil
```

**⚠️ 중요**: NumPy 2.x 비호환 - `numpy<2` 버전 고정 필수

---

## 핵심 아키텍처

### 메인 컴포넌트 (v5.1.0)
```
설치 (install_v2.sh)
    ↓
트레이 (xlt_tray.py) + 자동 업데이트 시스템
    ↓        ↘
웹 서버 (stable_web_server.py)    백그라운드 자동 업데이터 (auto_updater.py)
    ↓                                     ↓
├── 텍스트 추출 (Figma Files API)         ├── GitHub API 체크 (6시간마다)
├── 번역 (xlt/translation/claude_translator.py)  ├── Personal Access Token 지원
├── 치환자 (xlt/utils/placeholder_detector.py)  ├── 다중 소스 fallback 시스템
├── 키 생성 (xlt/utils/unifi_key_generator.py)  └── 자동 백업/복원 시스템
└── 설정 관리 (xlt/core/config.py)
```

### 핵심 파일
- **`stable_web_server.py`**: Flask 웹 서버 (메인 진입점)
- **`xlt_tray.py`**: macOS 트레이 앱 (rumps 기반) + 자동 업데이트 통합
- **`xlt/translation/claude_translator.py`**: Claude 품질 검증 번역 시스템 (v5.1.0)
- **`xlt/translation/unifi_translator.py`**: Unifi 전문 번역 (1,244개 DB)
- **`xlt/utils/auto_updater.py`**: 완전 자동화 업데이트 시스템 (v5.0.0)
- **`xlt/utils/unifi_key_generator.py`**: 지능형 XLT 키 생성
- **`xlt/core/config.py`**: 동적 설정 시스템

---

## 개발 가이드라인

### 번역 시스템 원칙

**Google Translate 오작동 방지 (CRITICAL)**:
```python
# ✅ 올바른 방식
target_languages = ['en_US', 'ja_JP', 'zh_TW', 'th_TH']  
result['ko_KR'] = original_text  # 한국어 원본 직접 사용

# ❌ 잘못된 방식 (모든 언어가 한국어로 반환됨)
target_languages = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
```

**Unifi 톤앤매너**:
- **한국어**: 친근한 격식체 (~해요) - "매일 이자를 드려요"
- **영어**: 명확한 금융 언어 - "Log in with Apple"
- **일본어**: 정중한 경어 (です・ます体)
- **중국어**: 정중한 번체 중국어
- **태국어**: คะ/ครับ 없이 정중하게

**번역 프로세스**:
1. Unifi DB (1,244개)에서 기존 번역 확인
2. Claude 품질 검증 (v5.1.0) - 90점 이상 자동 재번역
3. 치환자 보존 ({{0}}, {{wallet}} 등)
4. HTML 태그 유지

### 코드베이스 작업 가이드라인

**기능 추가 시**:
- 모든 사용자 인터페이스는 한국어
- Unifi 관련 번역은 반드시 `guide.md` 참조
- **하위 호환성 유지** (기존 기능 보호)

**웹 서버 개발**:
- 메인 진입점: `stable_web_server.py` (main.py 아님)
- 세션 관리: 메모리 기반 OCR 결과 및 번역 진행 상황
- 모든 API는 JSON 응답, 한국어 오류 메시지

### 테스트 & 배포 가이드라인

**핵심 원칙**:
1. **개발자 우선 테스트**: 사용자 테스트 전 개발자가 먼저 검증
2. **완전 삭제 → 재설치**: 신규 사용자 관점 테스트
3. **근본적 해결**: 임시 해결책 금지, 설치 스크립트 자체 개선
4. **하위 호환성**: 모든 버전 업데이트 시 기존 기능 보호

**배포 전 필수 테스트**:
```bash
# 1. 완전한 환경 초기화
rm -rf ~/XLT-System ~/Desktop/"XLT System (Tray).command"

# 2. 최신 설치 스크립트 실행
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash

# 3. 전체 워크플로우 테스트
~/Desktop/"XLT System (Tray).command"
# → 트레이 아이콘 표시, 웹 브라우저 실행, 번역 워크플로우 확인
```

> 📋 **상세 테스트 계획**: `TEST_PLAN.md` 참조 (50+ 테스트 케이스)  
> 📝 **배포 체크리스트**: `VERSION_UPDATE_CHECKLIST.md` 참조

---

## API 레퍼런스

### 워크플로우 엔드포인트
- `POST /upload` - Figma URL/이미지 처리, 텍스트 추출 결과 반환
- `GET /select_texts` - 텍스트 선택 인터페이스
- `POST /check-placeholders` - 치환자 패턴 감지
- `POST /translate-selected` - 번역 미리보기 데이터
- `POST /download-excel` - Excel 파일 생성

### 시스템 관리
- `GET /api/health` - 시스템 상태 체크 (Claude CLI 상태 포함)
- `GET /api/update/check` - GitHub 최신 버전 확인
- `POST /api/translate/unifi` - Unifi 전용 번역

### 엑셀 번역
- `POST /api/excel-translate` - 엑셀 파일 업로드 및 번역 시작
- `GET /api/excel-progress/<session_id>` - 엑셀 번역 진행 상태 확인
- `GET /api/download-excel/<filename>` - 번역된 엑셀 파일 다운로드

---

## 코드 예제

### Claude 품질 검증 번역 (v5.1.0)
```python
from xlt.translation.claude_translator import ClaudeTranslator

translator = ClaudeTranslator(config)
result = translator.translate_with_quality_verification(
    "지갑 연결하기", 
    target_languages=['en_US', 'ja_JP'],
    quality_threshold=90
)
# Returns: {'ko_KR': '지갑 연결하기', 'en_US': 'Connect Wallet', 'ja_JP': 'ウォレット接続', 'quality_score': 95}
```

### Unifi 전문 번역 시스템
```python
from xlt.translation.unifi_translator import UnifiTranslator

translator = UnifiTranslator(XLTConfig())
result = translator.translate_with_unifi_context(
    "지갑 연결하기", ['en_US', 'ja_JP']
)
# Returns: {'ko_KR': '지갑 연결하기', 'en_US': 'Connect Wallet', 'ja_JP': 'ウォレット接続'}
```

### 지능형 XLT 키 생성
```python
from xlt.utils.unifi_key_generator import UnifiKeyGenerator

generator = UnifiKeyGenerator()
key = generator.generate_unifi_key("지갑 연결하기", 1)
# Returns: "XLT_asset_text_지갑_연결하기_001"
```

---

## 문제 해결 가이드

### 트레이 시스템
```bash
# 트레이 앱 상태 확인
pgrep -f "python.*xlt_tray.py"

# rumps 설치 문제
pip install 'pyobjc-core>=9.0,<10.0' 'pyobjc-framework-Cocoa>=9.0,<10.0' rumps

# rumps import 테스트
python3 -c "import rumps; print('✅ rumps 정상')"
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

### 패키지 호환성
```bash
# NumPy 2.x 호환성 오류 해결
pip install "numpy<2" pillow==9.5.0

# 의존성 패키지 전체 재설치
pip install -r requirements.txt --force-reinstall
```

---

## 버전 히스토리

### v5.1.0 (2026-05-07) - 현재
- 🔥 **Claude 품질 검증 시스템** - 85점 → 95점 목표, 2단계 Claude 워크플로우 구축
- 🚀 **Figma 텍스트 추출 방식 혁신** - OCR → 직접 텍스트 노드 추출, 100% 정확도 달성
- ✨ **100% Claude 기반 번역** - 외부 API(바른, 구글) 완전 제거, 순수 Claude AI 처리
- 🎯 **전문가 수준 Claude 검증** - 용어 일관성, 맞춤법, 자연스러움 4가지 기준 자동 체크

### v5.0.0 (2026-05-06)
- 🚀 **완전 자동화 업데이트 시스템** - 백그라운드 자동 감지 (6시간) + 트레이 알림
- 🔍 **GitHub 레이트 리밋 근본 해결** - Personal Access Token 지원 (60회→5,000회)
- 📱 **macOS 트레이 자동 알림** - 중요 업데이트 시 시스템 레벨 알림 자동 표시
- 🛡️ **안전한 자동 업데이트** - 자동 백업 + 복원 시스템으로 안전 보장

### v4.3.0 (2026-05-06)
- 🚀 **Claude CLI 타임아웃 근본 해결** - 청크 처리 성공률 0% → 100% 완전 해결
- 🔧 **XLTConfig 동적 설정 시스템** - claude_timeout: 120초, claude_chunk_size: 3개
- ✅ **35개 텍스트 엑셀 번역 성공** - 140개 번역 결과 9분 20초 완료, 성공률 100%

> **전체 변경 이력**: `handoff.md` 및 `CHANGELOG_v*.md` 파일 참조

---

## 지원 환경

### 지원 언어
- ko_KR (원본), en_US, ja_JP, zh_TW, th_TH

### 지원 플랫폼
- macOS 10.15+ (트레이 기능)
- Python 3.7+
- Anaconda/Miniconda 완벽 호환

---

## 📚 관련 문서

### 개발 참조
- **CLAUDE.md** (이 문서) - 개발 원칙, 아키텍처, 빠른 참조
- **handoff.md** - 기술적 구현 세부사항, 버전별 변경 이력
- **DEVELOPMENT_PLAN.md** - 향후 개발 계획 및 로드맵

### 프로세스 & 품질
- **TEST_PLAN.md** - 포괄적인 테스트 전략 (50+ 테스트 케이스)
- **VERSION_UPDATE_CHECKLIST.md** - 배포 프로세스 완전 체크리스트
- **WORKFLOW_DOCUMENTATION.md** - 사용자 워크플로우 상세 가이드

### 사용자 문서
- **README.md** - 프로젝트 소개 및 설치 가이드
- **USER_MANUAL.md** - 상세 사용법 및 스크린샷

### 외부 참고
- [EasyOCR](https://github.com/JaidedAI/EasyOCR)
- [rumps](https://github.com/jaredks/rumps)
- [Flask](https://flask.palletsprojects.com/)

---

**이 가이드는 v5.1.0 기준으로 작성되었으며, 향후 버전 개발 시 업데이트됩니다.**