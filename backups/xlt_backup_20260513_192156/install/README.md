# XLT System v3.1 설치 가이드

**Figma → 다국어 번역 자동화 도구**

## 🚀 빠른 설치 (macOS)

### 설치
```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install.sh | bash
```

### 제거
```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
```

## 📋 요구사항

- **macOS** 10.15 이상
- **Python 3** (없으면 Homebrew로 설치 안내)
- **인터넷 연결** (설치 및 번역 시)

## 🎯 사용법

1. 설치 완료 후 데스크톱의 **"XLT System.command"** 더블클릭
2. 브라우저 자동 접속: `http://localhost:5004`
3. Figma URL 입력 → OCR → 텍스트 선택 → 번역 → Excel 다운로드

## 🛠️ 수동 설치 (문제 발생 시)

```bash
# Python 3 확인
python3 --version

# 직접 설치
mkdir -p ~/XLT-System && cd ~/XLT-System
curl -L https://github.com/hobong-ho6/xlt-system/archive/main.zip -o main.zip
unzip main.zip && mv xlt-system-main/* . && rm -rf xlt-system-main main.zip
pip3 install -r requirements.txt --user
python3 stable_web_server.py
```

## ❓ 문제 해결

### Python이 없는 경우
```bash
# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 설치
brew install python3
```

### 포트 충돌 (5004)
```bash
# 실행 중인 프로세스 확인
lsof -i :5004

# XLT 프로세스 종료
pkill -f stable_web_server
```

## 🔗 링크

- **프로젝트**: https://github.com/hobong-ho6/xlt-system
- **이슈 제보**: https://github.com/hobong-ho6/xlt-system/issues