# 🗑️ XLT System v3.1 제거 가이드

**터미널 명령어로 간단하게 제거하기**

## 🚀 빠른 제거

```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
```

## 📂 제거되는 항목

- **설치 디렉토리**: `~/XLT-System`
- **바로가기**: `~/Desktop/XLT System.command`
- **백업 파일들** (선택적)
- **Python 패키지들** (선택적)

## 🛠️ 수동 제거

```bash
# 프로세스 종료
pkill -f stable_web_server

# 파일 제거
rm -rf ~/XLT-System
rm -f ~/Desktop/"XLT System.command"

# 백업 제거 (선택사항)
rm -rf ~/XLT-System.backup.*

# Python 패키지 제거 (선택사항)
pip3 uninstall easyocr googletrans openpyxl
```

## 🔄 재설치

```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install.sh | bash
```

끝! 🎉