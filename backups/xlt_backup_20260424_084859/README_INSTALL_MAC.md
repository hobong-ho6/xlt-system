# 🍎 XLT System v3.0 macOS 설치 가이드

**피그마 디자인 → 다국어 번역 자동화 도구**

---

## 📋 시스템 요구사항

### ✅ 필수 요구사항
- **macOS 10.15** (Catalina) 이상
- **Python 3.8** 이상
- **인터넷 연결** (패키지 다운로드 및 번역 API 사용)
- **여유 저장공간** 2GB 이상

### 🔍 시스템 확인 방법

**1. macOS 버전 확인**
```bash
sw_vers
```

**2. Python 설치 확인**
```bash
python3 --version
```
- Python이 없다면: [python.org](https://python.org)에서 다운로드
- 또는 Homebrew: `brew install python3`

---

## 🚀 원클릭 설치 (권장)

### 1단계: XLT System 다운로드

**방법 A: Git 클론 (권장)**
```bash
cd ~/Downloads
git clone [XLT_REPOSITORY_URL] XLT-System
cd XLT-System
```

**방법 B: ZIP 파일 다운로드**
1. XLT System ZIP 파일 다운로드
2. 압축 해제 후 터미널에서 폴더로 이동

### 2단계: 설치 스크립트 실행

```bash
chmod +x install_mac.sh
./install_mac.sh
```

### 3단계: 설치 과정 진행

설치 스크립트가 자동으로 다음을 수행합니다:

```
[1/8] 시스템 환경 확인
   ✅ macOS 시스템 확인 완료
   ✅ Python 3.9.6 감지됨

[2/8] 패키지 관리자 업그레이드
   ✅ pip 업그레이드 완료

[3/8] XLT System 의존성 설치 (2-3분 소요)
   ✅ 모든 의존성 설치 완료

[4/8] 기본 설정 생성
   ✅ Figma 설정 파일 생성됨
   ✅ 작업 디렉토리 생성 완료

[5/8] XLT System 초기화 검증
   ✅ XLT System 초기화 성공

[6/8] 데스크톱 바로가기 생성
   ✅ 'XLT System.command' 바로가기 생성됨

[7/8] 시스템 트레이 앱 설정 (선택사항)
   트레이 앱을 설치하시겠습니까? (y/N): y
   ✅ 트레이 앱 바로가기 생성됨

[8/8] 설치 완료
   🎉 XLT System v3.0 macOS 설치가 완료되었습니다!
```

---

## 🎯 설치 완료 후 사용법

### 방법 1: 데스크톱 바로가기 (가장 간편)

1. **데스크톱**에서 `XLT System.command` 파일 **더블클릭**
2. 터미널이 열리고 서버가 시작됨
3. **웹 브라우저**가 자동으로 `http://localhost:5004`에 접속
4. Figma URL을 입력하여 번역 시작!

### 방법 2: 시스템 트레이 앱 (백그라운드 실행)

1. **데스크톱**에서 `XLT System (Tray).command` 더블클릭
2. **메뉴 바**에 XLT 아이콘 표시
3. 아이콘 클릭으로 서버 시작/중지 가능

### 방법 3: 터미널에서 직접 실행

```bash
cd ~/Downloads/XLT-System  # 설치 폴더로 이동
python3 stable_web_server.py
```

---

## 🔧 추가 설정 (선택사항)

### 1. Figma 개인 액세스 토큰 설정

**더 빠른 처리를 위해 권장합니다.**

1. **Figma 계정 설정**
   - [Figma](https://figma.com) → Settings → Personal Access Tokens
   - **"Generate new token"** 클릭
   - 토큰 복사

2. **설정 파일 편집**
   ```bash
   cd ~/Downloads/XLT-System
   open figma_config.json
   ```

3. **토큰 입력**
   ```json
   {
     "figma_token": "여기에_복사한_토큰_붙여넣기"
   }
   ```

### 2. 부팅 시 자동 시작 설정

```bash
cd ~/Downloads/XLT-System
python3 setup_autostart.py
```

선택 메뉴:
- `1`: 자동 시작 설정
- `2`: 자동 시작 해제
- `3`: 현재 상태 확인

---

## 🌐 XLT System 사용법

### 1. 웹 인터페이스 접속
- URL: `http://localhost:5004`
- 자동으로 브라우저가 열림

### 2. 번역 워크플로우

**Step 1: Figma URL 입력**
```
https://www.figma.com/design/[파일ID]/[파일명]?node-id=[노드ID]
```

**Step 2: 텍스트 선택**
- OCR로 추출된 텍스트에서 번역할 항목 체크
- 치환자({{0}}, {{1}}) 자동 감지 및 적용

**Step 3: XLT 키 입력**
- 번역 결과의 고유 식별자 입력

**Step 4: 번역 미리보기**
- 한국어(교정됨), 영어, 일본어, 중국어, 태국어 결과 확인

**Step 5: Excel 다운로드**
- `sampleformat.xlsx` 구조로 파일 생성

### 3. 지원 언어

| 언어 | 코드 | 비고 |
|------|------|------|
| 한국어 | ko_KR | 맞춤법 자동 교정 |
| 영어 | en_US | |
| 일본어 | ja_JP | |
| 중국어(번체) | zh_TW | |
| 태국어 | th_TH | |

---

## 🛠️ 문제 해결

### 자주 발생하는 문제들

**1. "Permission denied" 오류**
```bash
chmod +x install_mac.sh
```

**2. Python 모듈 없음 오류**
```bash
pip3 install -r requirements.txt --user
```

**3. 포트 5004 사용 중**
```bash
# 기존 프로세스 확인
lsof -i :5004

# 프로세스 종료
pkill -f stable_web_server.py
```

**4. 서버가 시작되지 않음**
```bash
# 로그 확인
cd ~/Downloads/XLT-System
tail -f logs/*.log
```

**5. Figma URL 처리 안됨**
- Figma 토큰이 설정되었는지 확인
- URL 형식이 올바른지 확인
- 인터넷 연결 상태 확인

### 시스템 상태 확인

**서버 상태 체크**
```bash
curl -s http://localhost:5004/api/health
```

**XLT System 재시작**
```bash
cd ~/Downloads/XLT-System
pkill -f stable_web_server.py
python3 stable_web_server.py
```

### 완전 재설치

```bash
cd ~/Downloads
rm -rf XLT-System
# 처음부터 다시 설치
```

---

## 📞 지원 및 문의

### 로그 파일 위치
- **서버 로그**: `logs/server.log`
- **번역 로그**: `logs/translation.log`
- **오류 로그**: `logs/error.log`

### 시스템 정보 수집
문제 발생 시 다음 정보를 함께 제공해주세요:

```bash
# 시스템 정보
sw_vers
python3 --version
pip3 --version

# XLT System 상태
curl -s http://localhost:5004/api/health

# 설치된 패키지
pip3 list | grep -E "(easyocr|googletrans|flask|openpyxl)"
```

### 성능 최적화 팁

**1. 메모리 사용량 최적화**
- 대용량 이미지는 리사이징 후 처리
- 브라우저 캐시 정기적 삭제

**2. 번역 속도 향상**
- Figma 토큰 설정 (필수)
- 안정적인 인터넷 연결
- 텍스트 개수 50개 이하로 제한

**3. 시스템 안정성**
- macOS 업데이트 유지
- Python 가상환경 사용 (고급 사용자)

---

## 🎉 설치 완료!

XLT System v3.0이 성공적으로 설치되었습니다!

**🚀 지금 바로 시작하기:**
1. 데스크톱의 **"XLT System.command"** 더블클릭
2. 웹 브라우저에서 **http://localhost:5004** 접속
3. Figma URL 입력하여 첫 번역 시작!

**📚 더 자세한 사용법:**
- `guide.md` - Unifi 핀테크 번역 가이드라인
- `CLAUDE.md` - 개발자용 기술 문서
- `handoff.md` - 최신 개발 현황

**🌟 즐거운 번역 작업 되세요!**