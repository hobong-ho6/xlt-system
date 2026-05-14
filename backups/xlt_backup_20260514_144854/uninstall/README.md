# XLT System 제거 방법

## 방법 1: 로컬 스크립트 사용 (권장)
```bash
cd ~/XLT-System/uninstall
./local_uninstall.sh
```

## 방법 2: 온라인 스크립트 사용
```bash
echo "y" | curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/uninstall.sh | bash
```

## 방법 3: 데스크톱 바로가기 사용
데스크톱의 "XLT System 제거.command" 파일을 더블클릭

## 방법 4: 수동 제거
```bash
# 프로세스 종료
pkill -f "python.*xlt"

# 디렉토리 삭제
rm -rf ~/XLT-System
rm -rf ~/Documents/XLTTT

# 바로가기 삭제
rm -f ~/Desktop/"XLT System"*.command
```

모든 방법으로 완전한 제거가 가능합니다.
