# Claude CLI 연결 해제 테스트 가이드

## 📋 현재 완료 상황 (2026-04-30 17:45)

### ✅ 구현 완료된 기능들

1. **Claude 통합 번역 시스템**
   - 맞춤법 검사 + 번역 동시 처리
   - guide.md 78개 용어집 완전 활용
   - 바른 API 학습 패턴 반영

2. **Claude CLI 상태 모니터링**
   - `/api/health` 엔드포인트에 Claude 상태 추가
   - `subprocess.run(['claude', '--version'])` 설치 확인
   - `ClaudeTranslator.test_connection()` 연결 테스트

3. **동적 기능 제어**
   - Claude 불가시 번역 옵션 자동 비활성화
   - Google 번역으로 자동 전환
   - 사용자 알림 시스템

### 🎯 테스트 완료 상태
- **Claude CLI 정상 상태 확인**: ✅
- **웹 UI 상태 표시**: ✅  
- **기능 활성화**: ✅

---

## 🧪 Claude CLI 연결 해제 테스트 절차

### 1단계: 현재 상태 스크린샷 저장
```bash
# 웹 브라우저에서 localhost:5004 시스템 상태 섹션 스크린샷 저장
# 파일명: claude_normal_status.png
```

### 2단계: Claude CLI 연결 해제
다음 중 하나의 방법으로 Claude CLI를 사용 불가능하게 만들기:

**방법 A: Claude CLI 로그아웃**
```bash
claude logout
```

**방법 B: Claude CLI 프로세스 종료** (임시)
```bash
pkill -f claude
```

**방법 C: PATH에서 제거** (임시)
```bash
# ~/.zshrc 또는 ~/.bash_profile에서 Claude CLI 경로 주석 처리
```

### 3단계: 웹 인터페이스 상태 확인
1. **브라우저에서 localhost:5004 새로고침**
2. **시스템 상태 섹션 확인**:
   - [ ] Claude CLI 상태가 "error" 또는 "warning"으로 변경되었는가?
   - [ ] 상태 메시지가 적절한가?
   - [ ] 상태 아이콘/배지가 올바르게 표시되는가?

3. **번역 엔진 선택 섹션 확인**:
   - [ ] "Claude 통합 처리" 옵션이 비활성화되었는가?
   - [ ] "Claude 번역" 옵션이 비활성화되었는가?
   - [ ] 비활성화된 옵션들이 시각적으로 구분되는가? (흐려짐 등)

4. **자동 전환 확인**:
   - [ ] Claude 통합이 선택되어 있었다면 Google로 자동 전환되었는가?
   - [ ] 적절한 알림 메시지가 표시되었는가?

### 4단계: 기능 동작 테스트
1. **Figma URL 또는 이미지 업로드**
2. **OCR 결과 확인**:
   - [ ] OCR 텍스트 추출이 정상 작동하는가?
   - [ ] Claude 관련 버튼이 나타나지 않는가?
3. **Google 번역 실행**:
   - [ ] Google 번역이 정상 작동하는가?
   - [ ] Excel 다운로드가 정상 작동하는가?

### 5단계: 테스트 결과 기록

**스크린샷 저장**:
- `claude_disconnected_status.png`: Claude CLI 연결 해제 후 상태
- `claude_disconnected_ui.png`: 번역 엔진 선택 UI 비활성화 상태

**테스트 결과 메모**:
```
= Claude CLI 연결 해제 테스트 결과 =

[시스템 상태]
- Claude CLI 상태: [ 실제 표시된 상태 기록 ]
- 상태 메시지: "[ 실제 메시지 기록 ]"
- 시각적 표현: [ OK/WARNING/ERROR 배지 상태 ]

[UI 비활성화]
- Claude 통합 처리: [ 비활성화됨/활성화됨 ]
- Claude 번역: [ 비활성화됨/활성화됨 ]
- 시각적 구분: [ 흐려짐/정상 ]

[자동 전환]
- 이전 선택: [ Claude 통합/Claude/Google ]
- 전환 후: [ Google/기타 ]
- 알림 메시지: "[ 실제 표시된 메시지 ]"

[기능 동작]
- OCR: [ 정상/오류 ]
- Google 번역: [ 정상/오류 ]  
- Excel 다운로드: [ 정상/오류 ]

[개선 필요 사항]
1. [ 발견된 문제점들 ]
2. [ UI 개선 제안 ]
3. [ 메시지 개선 제안 ]
```

---

## 🔧 Claude CLI 재연결 후 작업 계획

### 다음에 Claude를 실행할 때 해야 할 작업들:

#### 1. 테스트 결과 분석
- 위에서 기록한 테스트 결과를 바탕으로 개선점 식별
- 사용자 경험 관점에서 부족한 부분 파악

#### 2. 개선 작업 우선순위
**High Priority** (즉시 수정 필요):
- [ ] 상태 감지 정확성 문제
- [ ] UI 비활성화 작동 문제  
- [ ] 기능 동작 오류

**Medium Priority** (사용자 경험 개선):
- [ ] 상태 메시지 사용자 친화성
- [ ] 알림 메시지 개선
- [ ] 시각적 피드백 향상

**Low Priority** (추가 기능):
- [ ] Claude 재연결 자동 감지
- [ ] 상태 변경 실시간 알림
- [ ] 상태 히스토리 기록

#### 3. 구체적 구현 계획
각 개선 사항에 대해:
1. **문제점**: 무엇이 문제였는지
2. **해결책**: 어떻게 수정할지
3. **구현 파일**: 어떤 파일을 수정할지
4. **테스트 방법**: 어떻게 확인할지

#### 4. 최종 검증
- Claude CLI 재연결 후 정상 상태 복구 확인
- 개선된 기능들 동작 테스트
- handoff.md 업데이트

---

## 📝 참고 정보

### 주요 파일 위치
- `stable_web_server.py`: Claude 상태 확인 로직 (line 3158~)
- `templates/index.html`: Claude 상태 UI (Claude CLI 상태 항목)  
- `static/js/app.js`: 동적 기능 제어 (`updateClaudeTranslationOptions` 함수)
- `xlt/translation/claude_translator.py`: Claude 연결 테스트 (`test_connection` 메서드)

### 현재 웹 서버 상태
- 포트: 5004
- 실행 중: ✅
- 접속 URL: http://localhost:5004

### Claude CLI 복구 방법
```bash
# 방법 A를 사용한 경우
claude login

# 방법 B를 사용한 경우  
# (자동으로 복구됨, 필요시 Claude 재시작)

# 방법 C를 사용한 경우
# ~/.zshrc 또는 ~/.bash_profile 주석 해제 후 source
```

---

**테스트 준비 완료**: 이제 Claude CLI를 연결 해제하고 위 절차에 따라 테스트를 진행하세요.