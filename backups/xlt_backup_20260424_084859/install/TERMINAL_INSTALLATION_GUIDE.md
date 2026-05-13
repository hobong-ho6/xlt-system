# 💻 XLT System v3.1 터미널 설치 가이드

**터미널에서 간단한 명령어로 설치하기**

## 🎯 v3.1 주요 기능
- **완전 자동화 설치**: 4단계 fallback 전략으로 macOS 완벽 호환
- **트레이 시스템**: 터미널 독립 실행, 동적 메뉴, 백그라운드 모드
- **강화된 안정성**: I/O 에러 방지, 자동 복구, 종합 검증
- **자동 업데이트**: GitHub 기반 버전 관리

## 📋 설치 방법

### 1️⃣ 터미널 열기
- **macOS**: `Cmd + Space` → "터미널" 검색 → Enter

### 2️⃣ 설치 명령어 복사 붙여넣기
```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash
```

### 3️⃣ 사용하기
**두 가지 실행 방법**:

#### 방법 1: 트레이 앱 (권장) ⭐
- 데스크톱의 **"XLT System (Tray).command"** 더블클릭
- 시스템 트레이에서 서버 시작/중지 제어
- 터미널 자동 닫힘, 백그라운드 실행
- 실시간 서버 상태 모니터링

#### 방법 2: 웹 서버 직접 실행
- 데스크톱의 **"XLT System.command"** 더블클릭
- 또는 브라우저에서 `http://localhost:5004`

## 🗑️ 제거 방법

**3가지 제거 옵션 제공**:
```bash
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
```

- **완전 제거**: 프로그램 + 백업 + 설정 모두 삭제
- **기본 제거**: 프로그램만 삭제 (백업 보존)
- **프로세스 종료**: 실행 중인 서버만 중지

## ❗ Python 없는 경우

**install_v2.sh가 자동으로 설치 시도하지만, 수동 설치 방법**:
```bash
# 1. Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Python 설치
brew install python3

# 3. XLT System 재설치
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash
```

## 🔧 문제 해결

### 설치 관련 문제

#### macOS 호환성 문제 (timeout 명령어)
```bash
# install_v2.sh가 자동으로 해결 (4단계 fallback 전략)
# 수동 디버깅이 필요한 경우:
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/debug_install.sh | bash
```

#### I/O 에러 문제
```bash
# Tray 바로가기 사용 시 자동 검증 및 복구
# 수동 긴급 복구:
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/emergency_io_fix.sh | bash
```

### 서버 실행 문제

#### 포트 충돌
```bash
# 서버 완전 종료
pkill -f stable_web_server
pkill -f xlt_tray

# 포트 사용 확인
lsof -i :5004
```

#### 트레이 앱이 안 보일 때
```bash
# 트레이 앱 상태 확인
pgrep -f "python.*xlt_tray.py" || echo "트레이 앱 미실행"

# 로그 확인
tail -f ~/XLT-System/xlt_tray.log

# 수동 재시작
cd ~/XLT-System
nohup python3 xlt_tray.py > xlt_tray.log 2>&1 &
```

#### 권한 오류
```bash
# 바로가기 실행 권한 부여
chmod +x ~/Desktop/"XLT System.command"
chmod +x ~/Desktop/"XLT System (Tray).command"
```

### 완전 수동 설치 (긴급 상황용)
```bash
mkdir -p ~/XLT-System && cd ~/XLT-System
curl -L https://github.com/hobong-ho6/xlt-system/archive/main.zip -o main.zip
unzip main.zip && mv xlt-system-main/* . && rm -rf xlt-system-main main.zip
pip3 install "numpy<2" pillow==9.5.0
pip3 install googletrans==4.0.0rc1 easyocr openpyxl flask pillow requests pystray psutil --user
python3 stable_web_server.py
```

## 📊 시스템 상태 확인

```bash
# 서버 상태
curl -s http://localhost:5004/api/health | python3 -m json.tool

# 트레이 앱 상태
pgrep -f "python.*xlt_tray.py"

# 설치된 구성요소
ls -la ~/XLT-System
ls -la ~/Desktop/"XLT System"*
```

---

**🎉 XLT System v3.1 - 완전 자동화 설치 + 트레이 시스템 + 강화된 안정성**

끝! 더 자세한 정보는 [GitHub](https://github.com/hobong-ho6/xlt-system) 참조