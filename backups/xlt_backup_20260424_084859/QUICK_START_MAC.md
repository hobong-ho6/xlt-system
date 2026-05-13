# ⚡ XLT System v3.0 macOS 빠른 시작

**3분 안에 설치하고 바로 사용하기!**

---

## 🏃‍♂️ 30초 설치 체크리스트

### ✅ 설치 전 확인사항
- [ ] **macOS 10.15+** (시스템 정보에서 확인)
- [ ] **Python 3.8+** (`python3 --version`)  
- [ ] **인터넷 연결** (Wi-Fi/유선)
- [ ] **2GB 여유공간** (저장공간 확인)

### 🚀 원클릭 설치

**1. 터미널 열기**
- `Cmd + Space` → "터미널" 입력 → Enter

**2. XLT System 다운로드**
```bash
cd ~/Downloads
# Git이 있으면:
git clone https://github.com/YOUR_REPO/XLT-System.git

# 또는 ZIP 파일 다운로드 후 압축 해제
```

**3. 설치 실행**
```bash
cd XLT-System
chmod +x install_mac.sh
./install_mac.sh
```

**4. 설치 완료!**
- 모든 질문에 `Y` 또는 Enter
- 약 2-3분 후 완료

---

## 🎯 즉시 사용하기

### 방법 1: 데스크톱 바로가기 (추천)
1. **데스크톱**에서 `XLT System.command` **더블클릭**
2. 웹 브라우저 자동 열림 (`http://localhost:5004`)
3. Figma URL 붙여넣기 → 번역 시작!

### 방법 2: 직접 실행
```bash
cd ~/Downloads/XLT-System
python3 stable_web_server.py
```

---

## 🧪 첫 번역 테스트

### 테스트용 Figma URL
```
https://www.figma.com/design/GOCHAYBS7hIrmWRGNuJOKV/Web3?node-id=42997-1033&t=PV0e598gBCKFl9CQ-1
```

### 번역 과정 (30초)
1. **Figma URL 입력** → "OCR 텍스트 추출" 버튼
2. **텍스트 선택** → 번역할 항목 체크박스 선택  
3. **XLT 키 입력** → 예: `test_key_001`
4. **번역 미리보기** → 5개 언어 결과 확인
5. **Excel 다운로드** → 완성된 번역 파일 다운로드

---

## ⚠️ 문제 발생 시

### 가장 흔한 문제들

**🔥 "Permission denied" 오류**
```bash
chmod +x install_mac.sh
```

**🔥 Python 없음**
- [python.org](https://python.org)에서 다운로드
- 또는: `brew install python3`

**🔥 포트 충돌**
```bash
pkill -f stable_web_server.py
```

**🔥 패키지 설치 실패**
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt --user
```

### 즉시 도움받기

**시스템 상태 확인**
```bash
curl -s http://localhost:5004/api/health
```

**로그 확인**
```bash
cd ~/Downloads/XLT-System
tail logs/*.log
```

---

## 🎉 성공!

XLT System이 정상 작동하면:

- ✅ 브라우저에 `http://localhost:5004` 페이지 표시
- ✅ "XLT System v3.0" 로고 확인  
- ✅ Figma URL 입력창 표시
- ✅ 시스템 상태 모든 항목 "OK"

**🌟 이제 피그마 디자인을 5개 언어로 번역할 수 있습니다!**

### 다음 단계
- **Figma 토큰 설정** → 더 빠른 처리 (선택사항)
- **자동 시작 설정** → 부팅 시 자동 실행 (선택사항)
- **시스템 트레이** → 메뉴바에서 편리한 관리 (선택사항)

**📖 자세한 사용법**: `README_INSTALL_MAC.md` 참조