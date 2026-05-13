# GitHub Personal Access Token 설정 가이드

## 🎯 **중요: GitHub 계정 없어도 완전히 정상 작동!**

**XLT System은 GitHub 계정이 없는 사용자도 완전한 자동 업데이트를 제공합니다.**
- ✅ **계정 없음**: Raw GitHub URL 사용 → 완전 자동화 작동
- 🚀 **계정 있음**: Personal Access Token 추가 → 더 나은 경험

이 가이드는 **선택사항**입니다. 더 나은 경험을 원하는 사용자를 위한 고급 설정입니다.

## 🎯 효과

### **설정 전 (현재 문제)**
- ❌ **시간당 60회** API 호출 제한
- ❌ 여러 사용자 공유 시 더 빨리 소진
- ❌ "업데이트 버튼이 안 나타남" 문제

### **설정 후 (개선 효과)**
- ✅ **시간당 5,000회** API 호출 가능
- ✅ 개인 계정별 독립적 제한
- ✅ **완전 자동화 업데이트** 시스템 활성화
- ✅ **백그라운드 자동 감지** + **트레이 알림**

---

## 🔧 설정 방법

### **1단계: GitHub Personal Access Token 생성**

1. **GitHub 접속**: [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. **"Generate new token"** → **"Generate new token (classic)"** 선택
3. **설정 정보**:
   - **Note**: `XLT System Auto Update`
   - **Expiration**: `No expiration` (또는 1년)
   - **Scopes**: `public_repo` 체크 (읽기 전용)
4. **"Generate token"** 클릭
5. **토큰 복사** (한 번만 표시됨!)

### **2단계: XLT System에 토큰 설정**

#### **방법 A: 환경 변수 (추천)**
```bash
# macOS/Linux
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# 영구 설정 (~/.bash_profile 또는 ~/.zshrc에 추가)
echo 'export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx' >> ~/.zshrc
source ~/.zshrc
```

#### **방법 B: 설정 파일**
```bash
# XLT System 디렉토리에서
cd ~/XLT-System
echo '{"github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"}' > github_config.json
```

#### **방법 C: Git 설정**
```bash
git config --global github.token ghp_xxxxxxxxxxxxxxxxxxxx
```

---

## ✅ 설정 확인

### **토큰 설정 테스트**
```bash
cd ~/XLT-System
python3 -c "
from xlt.utils.auto_updater import get_auto_updater
auto_updater = get_auto_updater()
result = auto_updater.check_for_updates_async()
print('테스트 결과:', result)
"
```

### **예상 결과**
```
🔍 업데이트 확인 중... (19:30:15)
✅ GitHub API 인증 성공 (5000/5000 남음)
🎉 자동 업데이트 시스템 활성화됨
```

---

## 🚀 완전 자동화 기능

### **백그라운드 자동 감지**
- ⏰ **6시간마다** 자동으로 업데이트 확인
- 📱 **트레이 알림** 자동 표시 (macOS)
- 🔄 **중요 업데이트** 자동 설치

### **업데이트 우선도 분류**
- 🚨 **긴급**: 보안 수정 → 자동 설치 + 즉시 알림
- 🎉 **중요**: v4.3.0 타임아웃 해결 → 자동 설치 + 알림
- 📦 **일반**: 기능 개선 → 알림만 (사용자 선택)
- 🔧 **패치**: 작은 수정 → 자동 설치

### **트레이 알림 예시**
```
🎉 중요 업데이트 가능
XLT System
v4.3.0 주요 개선사항이 포함된 업데이트입니다.
```

---

## 🔐 보안 고려사항

### **토큰 권한**
- ✅ `public_repo` (읽기 전용) - **안전함**
- ❌ `repo` (쓰기 권한) - **불필요함**

### **토큰 보호**
- 🔒 토큰을 공개 저장소에 업로드하지 마세요
- 🔑 정기적으로 토큰 갱신 권장
- 📱 의심스러운 활동 시 즉시 토큰 삭제

---

## ❓ 문제 해결

### **"토큰을 찾을 수 없습니다"**
```bash
# 환경 변수 확인
echo $GITHUB_TOKEN

# 설정 파일 확인  
cat ~/XLT-System/github_config.json

# Git 설정 확인
git config --global github.token
```

### **"API 호출 실패"**
- 토큰이 만료되었는지 확인
- 인터넷 연결 상태 확인
- 토큰 권한(`public_repo`) 확인

### **"자동 업데이트가 작동하지 않음"**
```bash
# 트레이 앱 재시작
~/Desktop/"XLT System (Tray).command"

# 또는 웹 서버 재시작
cd ~/XLT-System
python3 stable_web_server.py
```

---

## 📊 레이트 리밋 모니터링

GitHub API 사용량은 다음 URL에서 확인할 수 있습니다:
- [https://api.github.com/rate_limit](https://api.github.com/rate_limit)

**토큰 설정 후 예상 응답**:
```json
{
  "rate": {
    "limit": 5000,
    "remaining": 4999,
    "reset": 1620000000
  }
}
```

---

**🎉 토큰 설정 완료 후, XLT System이 완전 자동화됩니다!**