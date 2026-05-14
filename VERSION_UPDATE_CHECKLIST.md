# 버전 업데이트 체크리스트

**목적**: 새 버전 개발 완료 및 배포 시 업데이트해야 할 모든 문서와 작업 목록

---

## 📋 버전 업데이트 프로세스

### Phase 1: 개발 완료 전 체크

- [ ] 모든 기능 개발 완료
- [ ] 로컬 테스트 완료 (TEST_PLAN.md 기준)
- [ ] 웹 UI 기능은 브라우저에서 실제 테스트 완료
- [ ] 코드 리뷰 완료
- [ ] 버그 수정 완료

---

### Phase 2: 문서 업데이트 (배포 전 필수)

#### 2.1 코어 문서 (필수)

**우선순위 1 - 반드시 업데이트**:

- [ ] **`CLAUDE.md`**
  - [ ] 프로젝트 개요의 버전 번호 업데이트
  - [ ] 핵심 워크플로우에 신규 기능 추가
  - [ ] 주요 기능 목록 업데이트
  - [ ] v3.x 신규 기능 섹션 추가
  - [ ] 버전별 주요 변경사항 추가
  - [ ] 마지막 "이 가이드는 vX.X 기준..." 버전 업데이트

- [ ] **`handoff.md`**
  - [ ] 최신 버전 정보 업데이트 (상단)
  - [ ] vX.X 주요 변경사항 섹션 추가
  - [ ] 개선 배경 및 구현 내용 작성
  - [ ] 기술적 구현 코드 예시 추가
  - [ ] 테스트 상태 체크리스트 업데이트
  - [ ] 배포 정보 (커밋 해시 등) 추가

- [ ] **`TEST_PLAN.md`**
  - [ ] 문서 정보의 기준 버전 업데이트
  - [ ] 신규 기능별 테스트 케이스 추가 (TC-FUNC-XXX)
  - [ ] 하위 호환성 테스트 케이스 추가 (TC-COMPAT-XXX)
  - [ ] 테스트 교훈 섹션 업데이트 (실패 사례 포함)
  - [ ] 회귀 테스트 체크리스트 업데이트

- [ ] **`WORKFLOW_DOCUMENTATION.md`**
  - [ ] 대상 버전 업데이트 (상단)
  - [ ] 전체 프로세스 개요에 신규 단계 추가
  - [ ] Phase별 상세 워크플로우 업데이트
  - [ ] 플로우차트에 신규 분기 추가
  - [ ] 기능별 상세 설명 추가
  - [ ] 버전별 주요 변경사항 업데이트

#### 2.2 설정 및 참조 문서 (중요)

**우선순위 2 - 변경사항 있을 경우**:

- [ ] **`README.md`**
  - [ ] 버전 번호 업데이트
  - [ ] 주요 기능 목록 업데이트
  - [ ] 스크린샷 업데이트 (UI 변경 시)
  - [ ] 설치 방법 업데이트 (변경 시)

- [ ] **`USER_MANUAL.md`**
  - [ ] 신규 기능 사용법 추가
  - [ ] 스크린샷/예시 이미지 업데이트
  - [ ] FAQ 섹션 업데이트
  - [ ] 문제 해결 가이드 업데이트

- [ ] **`CHANGELOG_v3.x.md`**
  - [ ] 신규 버전 섹션 추가
  - [ ] 변경사항 카테고리별 정리:
    - ✨ 신규 기능
    - 🐛 버그 수정
    - 🔧 개선사항
    - 📚 문서 업데이트
    - ⚠️ Breaking Changes (있는 경우)

#### 2.3 기술 문서 (선택)

**우선순위 3 - 아키텍처/API 변경 시**:

- [ ] **`ARCHITECTURE.md`**
  - [ ] 시스템 구조 다이어그램 업데이트
  - [ ] 신규 컴포넌트 추가
  - [ ] 데이터 흐름 업데이트

- [ ] **`API_DOCUMENTATION.md`** (있는 경우)
  - [ ] 신규 API 엔드포인트 추가
  - [ ] 요청/응답 스펙 업데이트
  - [ ] 에러 코드 추가

- [ ] **`DEVELOPMENT_PLAN.md`**
  - [ ] 완료된 기능 체크
  - [ ] 다음 버전 계획 업데이트

---

### Phase 3: 코드 업데이트

- [ ] **`version.json`**
  ```json
  {
    "version": "3.x.0",
    "release_date": "2026-XX-XX",
    "codename": "XXX"
  }
  ```

- [ ] **설정 페이지 버전 표시**
  - [ ] `templates/settings.html` - 페이지 타이틀 버전
  - [ ] `templates/settings.html` - 헤더 버전 배지
  - [ ] `templates/settings.html` - 푸터 버전 정보

- [ ] **메인 페이지 버전 표시** (있는 경우)
  - [ ] `templates/index.html` - 푸터 버전

---

### Phase 4: 배포 전 최종 테스트

#### 4.1 완전 삭제 → 재설치 테스트

```bash
# 1. 환경 초기화
rm -rf ~/XLT-System ~/Desktop/"XLT System (Tray).command"

# 2. 최신 설치 스크립트 실행
curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash

# 3. 트레이 앱 실행
~/Desktop/"XLT System (Tray).command"
```

- [ ] ✅ 트레이 아이콘 표시 확인
- [ ] ✅ 웹 브라우저 자동 실행 (http://localhost:5004)
- [ ] ✅ 전체 워크플로우 테스트
- [ ] ✅ 신규 기능 테스트
- [ ] ✅ 회귀 테스트 (기존 기능)

#### 4.2 웹 UI 테스트 (신규 기능)

**각 신규 웹 UI 기능마다**:

```bash
# 1. 서버 시작
python3 stable_web_server.py

# 2. 브라우저 접속
open http://localhost:5004/[해당페이지]

# 3. 실제 상호작용
# - 버튼 클릭
# - 폼 입력
# - 모달 열기/닫기

# 4. 개발자 도구 확인
# - Console 에러 없음
# - Network 200 OK
```

- [ ] ✅ 신규 UI 기능 1: [기능명]
- [ ] ✅ 신규 UI 기능 2: [기능명]
- [ ] ✅ 신규 UI 기능 3: [기능명]

#### 4.3 하위 호환성 테스트

- [ ] v(X-1).X 클라이언트 → vX.X 서버 테스트
- [ ] 기존 설정 파일 호환성 확인
- [ ] 기존 캐시 파일 호환성 확인

---

### Phase 5: Git 커밋 및 배포

#### 5.1 문서 커밋

```bash
git add CLAUDE.md handoff.md TEST_PLAN.md WORKFLOW_DOCUMENTATION.md \
        README.md USER_MANUAL.md CHANGELOG_v3.x.md version.json

git commit -m "📚 vX.X 문서 전체 업데이트

## 업데이트된 문서
- CLAUDE.md: 버전 vX.X 반영
- handoff.md: vX.X 개발 완료 보고
- TEST_PLAN.md: 신규 테스트 케이스 추가
- WORKFLOW_DOCUMENTATION.md: 신규 워크플로우 반영
- README.md, USER_MANUAL.md, CHANGELOG_v3.x.md 업데이트

## 주요 변경사항
[신규 기능 요약]

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
"
```

#### 5.2 GitHub Push

```bash
git push origin main
```

- [ ] ✅ GitHub 푸시 완료
- [ ] ✅ Actions CI/CD 통과 (있는 경우)

#### 5.3 릴리즈 노트 작성

- [ ] GitHub Releases 페이지에서 새 릴리즈 생성
- [ ] 버전 태그: `v3.x.0`
- [ ] 릴리즈 제목: `XLT System v3.x - [코드네임]`
- [ ] 변경사항 작성 (CHANGELOG 기반)

---

### Phase 6: 사용자 알림

- [ ] 사용자에게 새 버전 배포 알림
- [ ] 주요 변경사항 요약 전달
- [ ] 업데이트 방법 안내:
  ```bash
  cd ~/XLT-System
  git pull origin main
  pkill -f stable_web_server.py
  python3 stable_web_server.py
  ```

---

## 📝 버전별 체크리스트 템플릿

### v3.X 업데이트 체크리스트

**개발 일자**: 2026-XX-XX  
**배포 일자**: 2026-XX-XX  
**담당자**: [이름]

#### 신규 기능
1. [기능 1 이름]
   - [ ] 기능 개발 완료
   - [ ] 테스트 완료
   - [ ] 문서 업데이트 완료

2. [기능 2 이름]
   - [ ] 기능 개발 완료
   - [ ] 테스트 완료
   - [ ] 문서 업데이트 완료

#### 문서 업데이트
- [ ] CLAUDE.md ✅
- [ ] handoff.md ✅
- [ ] TEST_PLAN.md ✅
- [ ] WORKFLOW_DOCUMENTATION.md ✅
- [ ] README.md ✅
- [ ] USER_MANUAL.md ✅
- [ ] CHANGELOG_v3.x.md ✅

#### 테스트
- [ ] 완전 삭제 → 재설치 테스트 ✅
- [ ] 웹 UI 테스트 ✅
- [ ] 회귀 테스트 ✅
- [ ] 하위 호환성 테스트 ✅

#### 배포
- [ ] Git 커밋 ✅
- [ ] GitHub Push ✅
- [ ] 릴리즈 노트 작성 ✅
- [ ] 사용자 알림 ✅

---

## 🚨 주의사항

### 절대 잊지 말 것

1. **웹 UI 테스트 필수**
   - 코드만 보고 "작동할 것" 추측 금지
   - 반드시 브라우저에서 실제 클릭/입력 테스트
   - 개발자 도구 Console/Network 확인

2. **완전 삭제 → 재설치 테스트**
   - 신규 사용자 관점 테스트
   - 파일 누락 여부 확인
   - 설치 스크립트 정상 작동 확인

3. **하위 호환성 유지**
   - 기존 기능 보호
   - API 변경 시 fallback 제공
   - 설정 파일 마이그레이션

4. **문서 버전 일관성**
   - 모든 문서의 버전 번호 동일
   - 날짜 정보 일관성 유지
   - 변경사항 상세 기록

---

## 📚 참고 문서

- `CLAUDE.md` - 개발 가이드
- `TEST_PLAN.md` - 테스트 계획
- `handoff.md` - 개발 현황 보고
- `WORKFLOW_DOCUMENTATION.md` - 워크플로우 가이드

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-04-27  
**작성자**: Claude Code
