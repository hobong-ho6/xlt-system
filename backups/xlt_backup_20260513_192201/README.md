# 🎨 XLT System v5.0.0

**Figma 디자인 → Unifi 전문 다국어 번역 자동화 시스템**

피그마 URL이나 이미지에서 OCR로 텍스트를 추출하고 **맞춤법/띄어쓰기를 자동 교정**한 후 **Unifi 전문 용어 데이터베이스**를 활용하여 5개 언어로 자동 번역하는 **macOS 네이티브 트레이** 기반 번역 시스템입니다.

---

## ✨ **v4.3.0 주요 기능**

### 🆕 **v5.0.0 신규 기능 (2026-05-06) - 완전 자동화 시스템**
- 🚀 **완전 자동화 업데이트 시스템** → 백그라운드 자동 감지 + 트레이 알림 + 원클릭 업데이트
- 🔍 **GitHub 레이트 리밋 근본 해결** → Personal Access Token 지원 (60회→5,000회) + Raw URL fallback
- 📱 **macOS 트레이 자동 알림** → 중요 업데이트 시 시스템 레벨 알림
- ⚡ **지능형 업데이트 분류** → 긴급/중요/일반/패치별 다른 처리 방식
- 🔄 **백그라운드 자동 감지** → 6시간마다 자동 체크, 사용자 개입 없음
- 🛡️ **안전한 자동 업데이트** → 자동 백업 + 복원 시스템으로 안전 보장

### 🎯 **v4.0-4.1 기능 (계속 지원)**
- ✨ **Claude CLI 통합 번역** → 맞춤법 + 번역 동시 처리 (AI 기반)
- ✨ **엑셀 파일 번역** → 업로드한 엑셀 파일을 XLT 형식으로 번역
- ✨ **Claude CLI 상태 모니터링** → 1초 이내 정확한 상태 감지

### 🎯 **v3.1-3.3 기능 (계속 지원)**

### 🎯 **완전한 워크플로우**
- 🎨 **Figma URL/이미지 입력** → EasyOCR 고정밀 텍스트 추출
- 🌐 **5개 언어 번역** → ko_KR, en_US, ja_JP, zh_TW, th_TH
- 🔧 **치환자 자동 처리** → {{0}}, {{wallet}} 등 패턴 완벽 보존
- 👁️ **실시간 번역 미리보기** → Excel 다운로드 전 결과 확인
- 📊 **Excel 출력** → 다국어 번역표 자동 생성

### 🏆 **Unifi 전문 번역 시스템**
- 📚 **1,244개 용어 데이터베이스** → guide.md 기준 금융 전문 번역
- 🎯 **지능형 XLT 키 생성** → `item_1_hash` → `XLT_asset_text_지갑_연결하기_001`
- 🔥 **68개 핵심 용어 사전** → 일관된 금융 용어 번역 보장

### 🖥️ **macOS 네이티브 트레이 시스템**
- 🎯 **시스템 트레이 아이콘** → rumps 기반 PyObjC 네이티브 API
- 🔄 **동적 메뉴** → 서버 상태 실시간 반영 (🔴 중지, 🟢 실행)
- ⚡ **서버 제어** → 시작/중지/재시작 원클릭
- 📋 **실시간 로그** → 터미널 자동 실행, tail -f 로그 스트리밍
- 🚀 **터미널 독립 실행** → 터미널 종료 후에도 계속 작동

### 🔄 **자동 업데이트 시스템**
- 🔍 **GitHub API 버전 체크** → 시작 시 최신 버전 확인
- 🌐 **웹 UI 업데이트** → 헤더 알림 + 인터랙티브 모달
- 🛡️ **안전한 업데이트** → 자동 백업, 롤백 기능

### 📊 **실시간 로깅 시스템**
- 📝 **Python logging 통합** → RotatingFileHandler (10MB, 3개 백업)
- 🏷️ **세션 ID 추적** → 모든 작업 개별 추적
- 🎨 **컬러 로그** → 에러/성공 시각화

---

## 📖 **사용자 메뉴얼**

**🎯 [USER_MANUAL.md](USER_MANUAL.md) - 완전한 사용법 가이드**
- 📸 실제 스크린샷과 함께하는 단계별 설명
- 🎨 Unifi 전문 번역 완전 워크플로우
- 🖥️ 트레이 시스템 사용법
- 📊 엑셀 합치기 기능 사용법
- 🚨 문제 해결 및 고급 사용법

---

## 🚀 **원클릭 설치** (macOS)

### ⚡ **완전 자동화 설치**
```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash
```

### 🗑️ **완전한 언인스톨러**
```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
```

## 📋 **시스템 요구사항**
- **macOS** 10.15 이상 (네이티브 트레이 지원)
- **Python 3.7+** (Anaconda/Miniconda 완벽 호환)
- **저장공간** 2GB 이상
- **인터넷 연결** (설치 및 번역 API 사용)

---

## 🎯 **사용 방법**

### 1️⃣ **설치 완료 후**
- 데스크톱의 **"XLT System (Tray).command"** 더블클릭
- 🎯 **시스템 트레이**에서 XLT 아이콘 확인 (터미널 자동 닫힘)
- 웹 브라우저 자동 접속: `http://localhost:5004`

### 2️⃣ **트레이 시스템 사용법**
- **XLT System 열기** → 웹 인터페이스 접속
- **서버 시작/중지/재시작** → 원클릭 서버 제어
- **로그 보기** → 터미널 자동 실행, 실시간 작업 로그
- **상태 확인** → 시스템 정보 및 포트 상태

### 3️⃣ **번역 워크플로우** (v5.0.0 완전 자동화)
1. **Figma URL 입력** (또는 이미지 업로드)
2. **OCR 텍스트 추출** → EasyOCR 고정밀 인식
3. **✨ 맞춤법/띄어쓰기 자동 교정** → 3단계 파이프라인 즉시 적용
4. **텍스트 수정** → OCR 오류 수정 또는 원하는 문구로 변경
5. **🔍 맞춤법 재검사** → 각 텍스트 옆 검사 버튼 클릭 (선택사항)
6. **번역할 텍스트 선택** → 체크박스 개별 선택
7. **치환자 자동 감지** → {{0}}, {{wallet}} 등 패턴 확인
8. **XLT Key 생성** → 지능형 또는 단순 prefix 모드 선택
9. **📚 사용자 교정 학습** → 수정 내역 자동 저장
10. **🚀 Claude CLI 청크 번역** → 10개씩 분할 처리, 2-3분 완료 (자동 최적화)
11. **실시간 미리보기** → XLT 키와 함께 결과 확인
12. **Excel 다운로드** → 완성된 다국어 번역표

### 🎨 **테스트용 Figma URL**
```
https://www.figma.com/design/GOCHAYBS7hIrmWRGNuJOKV/Web3?node-id=42997-1033&t=PV0e598gBCKFl9CQ-1
```

---

## 🔄 **자동 업데이트**

**v5.0.0 완전 자동화 시스템 내장!**
- 🔍 백그라운드 자동 업데이트 감지 (6시간마다)
- 📱 macOS 트레이 시스템 알림 자동 표시
- ⚡ 중요 업데이트 자동 설치 (백업/복원 자동)
- 🌐 GitHub 계정 불필요 (레이트 리밋 완전 해결)
- 🛡️ 안전한 자동화 (백업 + 복원 시스템)

---

## 🛠️ **개발자 정보**

### 📁 **v3.1 프로젝트 구조**
```
xlt-system/
├── install/                    # 완전 자동화 설치 시스템
│   ├── install_v2.sh          # 메인 설치 스크립트 (4단계 fallback)
│   └── uninstall.sh           # 완전한 언인스톨러 (3가지 옵션)
├── xlt/                       # XLT System 핵심 패키지
│   ├── core/                  # 파이프라인 오케스트레이션
│   ├── input/                 # Figma URL/이미지 입력 처리
│   ├── ocr/                   # EasyOCR 텍스트 추출
│   ├── translation/           # 번역 시스템
│   │   ├── translator.py      # 기본 Google Translate API
│   │   └── unifi_translator.py # Unifi 전문 번역기
│   ├── output/                # Excel 파일 생성
│   └── utils/                 # 유틸리티
│       ├── placeholder_detector.py # 치환자 감지
│       ├── unifi_key_generator.py  # 지능형 키 생성
│       └── updater.py             # 자동 업데이트
├── stable_web_server.py       # Flask 웹 서버 (메인)
├── xlt_tray.py               # macOS 네이티브 트레이 앱
├── templates/                # HTML 템플릿
├── static/                   # JavaScript, CSS
├── requirements.txt          # Python 의존성
├── guide.md                  # Unifi 번역 가이드라인
├── Unifi/                    # 1,244개 용어 데이터베이스
└── CLAUDE.md                 # 개발자 가이드라인
```

### 🔧 **로컬 개발 설치**
```bash
git clone https://github.com/hobong-ho6/xlt-system.git
cd xlt-system
pip install -r requirements.txt

# 웹 서버 시작
python3 stable_web_server.py

# 트레이 앱 시작 (별도 터미널)
python3 xlt_tray.py
```

### 🌐 **API 엔드포인트**
- **메인 페이지**: `http://localhost:5004`
- **시스템 상태**: `http://localhost:5004/api/health`
- **업데이트 확인**: `http://localhost:5004/api/update/check`
- **실시간 로그**: `http://localhost:5004/api/logs/<session_id>`

---

## ❓ **문제 해결**

### 🚫 **일반적인 문제**

**"개발자를 확인할 수 없음" 오류**:
- 파일 **우클릭** → **"열기"** 선택
- 시스템 환경설정 → 보안 및 개인정보보호 → "확인 없이 열기"

**트레이 아이콘이 보이지 않음**:
```bash
# rumps 라이브러리 확인
python3 -c "import rumps; print('✅ rumps 정상')"

# 수동 설치 (Anaconda 환경)
pip install rumps
```

**설치 중 오류**:
- 인터넷 연결 확인
- macOS 버전 확인 (10.15 이상)
- 저장공간 확인 (2GB 이상)
- Anaconda/Python 환경 충돌 → install_v2.sh가 자동 해결

**포트 5004 충돌**:
```bash
lsof -i :5004                      # 사용 중인 프로세스 확인
pkill -f "python.*stable_web_server.py"  # 기존 서버 종료

# 또는 트레이에서 "서버 중지" 클릭
```

**업데이트 실패**:
```bash
# Git 설정 문제 해결
git config --global user.email "xlt@system.local"
git config --global user.name "XLT System"

# 또는 완전 재설치
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash
```

### 🔍 **시스템 진단**
```bash
# 설치된 시스템 상태 확인
curl -s http://localhost:5004/api/health | python3 -m json.tool

# 트레이 앱 상태 확인
pgrep -f "python.*xlt_tray.py" && echo "✅ 트레이 실행 중" || echo "❌ 트레이 중지됨"

# 패키지 상태 확인
python3 -c "
import sys
print('Python:', sys.version)
try:
    import flask, rumps, easyocr, openpyxl
    print('✅ 모든 패키지 정상')
except ImportError as e:
    print('❌ 패키지 문제:', e)
"
```

---

## 📞 **지원**

- 🐛 **버그 제보**: [Issues](https://github.com/hobong-ho6/xlt-system/issues)
- 💡 **기능 제안**: [Issues](https://github.com/hobong-ho6/xlt-system/issues)  
- 📧 **문의**: GitHub Issues 사용

---

## 📄 **라이센스**

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

---

## 🌟 **기여**

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)  
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**🎨 Figma 디자인을 5개 언어로 자동 번역하는 새로운 경험을 시작하세요!**