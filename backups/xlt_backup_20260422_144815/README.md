# 🎨 XLT System v3.0

**Figma 디자인 → 다국어 번역 자동화 도구**

피그마 URL이나 이미지에서 OCR로 텍스트를 추출하고 5개 언어로 자동 번역하여 Excel 파일로 제공하는 웹 기반 번역 시스템입니다.

---

## ✨ **주요 기능**

- 🎨 **Figma URL 입력** → 자동 이미지 추출
- 🔍 **OCR 텍스트 인식** → EasyOCR 기반 고정밀 추출  
- 🌐 **5개 언어 번역** → ko_KR, en_US, ja_JP, zh_TW, th_TH
- 🔧 **치환자 자동 감지** → {{0}}, {{1}} 패턴 자동 처리
- 👁️ **번역 미리보기** → Excel 다운로드 전 결과 확인
- 📊 **Excel 출력** → 다국어 번역표 자동 생성
- 🌐 **웹 인터페이스** → 사용자 친화적 UI

---

## 📖 **사용자 메뉴얼**

**🎯 [USER_MANUAL.md](USER_MANUAL.md) - 완전한 사용법 가이드**
- 📸 실제 스크린샷과 함께하는 단계별 설명
- 🎨 텍스트 번역 완전 워크플로우
- 📊 엑셀 합치기 기능 사용법
- 🚨 문제 해결 및 고급 사용법
- 💡 최적화 팁과 주의사항

---

## 🚀 **빠른 설치** (macOS 전용)

### 🌟 **방법 1: 스마트 설치** (권장 - 버전 비교 자동)

**한 줄 설치**:
```bash
curl -O https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_smart_update.command && chmod +x install_smart_update.command && ./install_smart_update.command
```

**또는 파일 다운로드**:
1. **[install_smart_update.command](https://github.com/hobong-ho6/xlt-system/raw/main/install/install_smart_update.command)** 다운로드
2. 더블클릭 실행
3. 자동으로 최신 버전 확인 → 설치/업데이트

### ⚡ **방법 2: 완전 자동 설치**

**한 줄 설치**:
```bash
curl -O https://raw.githubusercontent.com/your-username/xlt-system/main/install/install_standalone.command && chmod +x install_standalone.command && ./install_standalone.command
```

**또는 파일 다운로드**:
1. **[install_standalone.command](https://github.com/hobong-ho6/xlt-system/raw/main/install/install_standalone.command)** 다운로드  
2. 더블클릭 실행
3. GitHub에서 자동 다운로드 → 설치

---

## 📋 **설치 과정**

### 🛠️ **자동 설치되는 컴포넌트**

- ✅ **Xcode Command Line Tools** (개발 도구)
- ✅ **Python 3.8+** (3가지 방법 중 선택)
- ✅ **Git** (버전 관리, 선택적)
- ✅ **모든 Python 패키지** (OCR, 번역, 웹서버)

### ⏱️ **설치 시간**
- **신규 설치**: 10-15분 (모든 의존성 포함)
- **업데이트**: 2-3분 (기존 설치 기반)

### 🔧 **시스템 요구사항**
- **macOS**: 10.15 이상
- **메모리**: 4GB 이상 권장
- **저장공간**: 2GB 이상
- **인터넷**: 설치 및 번역 시 필요

---

## 🎯 **사용 방법**

### 1️⃣ **설치 완료 후**
- 데스크톱의 **"XLT System.command"** 더블클릭
- 웹 브라우저 자동 접속: `http://localhost:5004`

### 2️⃣ **번역 과정**
1. **Figma URL 입력** (예: `https://figma.com/design/...`)
2. **OCR 텍스트 추출** 버튼 클릭
3. **번역할 텍스트 선택** (체크박스)
4. **치환자 확인** (자동 감지된 {{0}}, {{1}} 패턴)
5. **번역 미리보기** 확인
6. **Excel 파일 다운로드**

### 🎨 **테스트용 Figma URL**
```
https://www.figma.com/design/GOCHAYBS7hIrmWRGNuJOKV/Web3?node-id=42997-1033&t=PV0e598gBCKFl9CQ-1
```

---

## 🔄 **업데이트**

### 🌟 **자동 버전 확인** (스마트 설치 사용 시)
```bash
# 기존 install_smart_update.command 재실행
./install_smart_update.command
```

자동으로:
- ✅ 현재 설치된 버전 확인
- ✅ GitHub에서 최신 버전 확인  
- ✅ 업데이트 필요시 알림
- ✅ 선택적 업데이트 진행

### 📊 **버전 히스토리**
현재 버전은 **v3.0.0** (2024-04-22)

**주요 업데이트**:
- 완전 자동 설치 시스템
- GitHub 배포 및 자동 업데이트
- 번역 미리보기 기능
- 시스템 성능 분석

---

## 🛠️ **개발자 정보**

### 📁 **프로젝트 구조**
```
xlt-system/
├── install/                # 설치 스크립트들
├── xlt/                    # XLT System 소스 코드
├── stable_web_server.py    # Flask 웹 서버
├── requirements.txt        # Python 의존성
├── version.json           # 버전 정보
└── README.md              # 이 파일
```

### 🔧 **로컬 개발 설치**
```bash
git clone https://github.com/your-username/xlt-system.git
cd xlt-system
pip install -r requirements.txt
python3 stable_web_server.py
```

### 🌐 **웹 인터페이스**
- **메인 페이지**: `http://localhost:5004`
- **시스템 상태**: `http://localhost:5004/api/health`
- **로그 확인**: `http://localhost:5004/api/logs`

---

## ❓ **문제 해결**

### 🚫 **일반적인 문제**

**"개발자를 확인할 수 없음" 오류**:
- 파일 **우클릭** → **"열기"** 선택

**설치 중 오류**:
- 인터넷 연결 확인
- macOS 버전 확인 (10.15 이상)
- 저장공간 확인 (2GB 이상)

**포트 5004 충돌**:
```bash
lsof -i :5004           # 사용 중인 프로세스 확인
pkill -f stable_web_server.py  # 기존 서버 종료
```

### 🔍 **시스템 진단**
설치 전 호환성 체크:
```bash
curl -O https://raw.githubusercontent.com/your-username/xlt-system/main/install/check_system_mac.command
chmod +x check_system_mac.command
./check_system_mac.command
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