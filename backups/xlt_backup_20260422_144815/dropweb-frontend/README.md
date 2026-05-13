# XLT System - DropWeb 배포용 프론트엔드

이 폴더는 DropWeb 정적 호스팅 서비스에 업로드할 수 있는 XLT System 웹 인터페이스입니다.

## 📋 사용 방법

### 1. 사전 준비 (사용자 로컬)
```bash
# XLT 백엔드 서버 시작
cd /Users/user/Documents/XLTTT
python3 stable_web_server.py

# ✅ 서버가 http://localhost:5004 에서 실행 중인지 확인
curl http://localhost:5004/api/health
```

### 2. DropWeb 업로드
1. 이 폴더 전체를 ZIP으로 압축
2. DropWeb에서 ZIP 파일 업로드
3. 배포된 웹사이트 접속

### 3. 작업 플로우
```
사용자 브라우저 (DropWeb 호스팅)
         ↓ API 호출
사용자 로컬 서버 (localhost:5004)
         ↓ 처리 결과
사용자 브라우저 (결과 표시 + Excel 다운로드)
```

## 🏗️ 아키텍처

### 클라이언트-서버 분리
- **프론트엔드**: DropWeb 정적 호스팅 (이 폴더)
- **백엔드**: 사용자 로컬 XLT 시스템 (localhost:5004)

### 통신 방식
- JavaScript Fetch API로 로컬 서버와 통신
- CORS 헤더로 브라우저 정책 해결
- 실시간 상태 업데이트 및 진행 상황 표시

## 📁 파일 구조

```
dropweb-frontend/
├── index.html          # 메인 웹 페이지
├── script.js           # XLT 서버 통신 로직
├── style.css           # 추가 스타일
├── service-spec.md     # 서비스 기획서
└── README.md           # 이 파일
```

## ⚙️ 기술 스택

- **HTML5**: 시맨틱 마크업
- **CSS3**: 커스텀 스타일 + 애니메이션
- **JavaScript ES6+**: 비동기 통신, DOM 조작
- **Tailwind CSS**: UI 프레임워크 (CDN)

## 🔧 로컬 개발

### 파일 수정 후 테스트
1. 브라우저에서 `index.html` 직접 열기
2. 또는 간단한 HTTP 서버 실행:
   ```bash
   # Python 내장 서버
   python3 -m http.server 8000
   
   # Node.js serve (npx 사용)
   npx serve .
   ```

### 디버깅
- 브라우저 개발자 도구 (F12) Console 탭 확인
- Network 탭에서 API 호출 상태 확인
- XLT 로컬 서버 터미널 로그 확인

## 🚨 주의사항

### CORS 정책
- DropWeb (HTTPS) → 로컬 서버 (HTTP) 호출 시 Mixed Content 이슈 발생 가능
- 일부 브라우저에서 localhost 접근 제한 있을 수 있음

### 브라우저 호환성
- Chrome, Firefox: 완전 지원
- Safari: 로컬 서버 접근 정책 확인 필요
- Edge: Chrome과 동일

### 방화벽
- 로컬 방화벽에서 5004 포트 접근 허용 필요
- 회사 네트워크에서 localhost 접근 정책 확인

## 📊 성능 최적화

### 파일 크기
- 현재 총 크기: ~50KB (이미지 없음)
- Tailwind CDN 사용으로 번들 크기 최소화
- 압축 후 DropWeb 업로드 제한 150MB 대비 매우 여유

### 로딩 속도
- CDN 라이브러리로 빠른 초기 로딩
- 로컬 서버 통신으로 OCR/번역 처리 속도 최적화
- 번역 미리보기로 사용자 대기 시간 단축

## 🔄 업데이트 방법

1. **코드 수정**: 이 폴더의 파일들 수정
2. **테스트**: 로컬에서 동작 확인
3. **배포**: 수정된 폴더를 다시 ZIP으로 압축하여 DropWeb 업로드
4. **문서 업데이트**: `service-spec.md`에 변경사항 기록

## 📞 지원

### 문제 해결
1. **연결 실패**: XLT 로컬 서버 상태 확인
2. **CORS 오류**: 브라우저 콘솔에서 상세 오류 확인
3. **성능 이슈**: 네트워크 탭에서 API 응답 시간 확인

### 개발 문의
- XLT System 관련: `/Users/user/Documents/XLTTT/` 폴더 참조
- DropWeb 배포: 이 README와 `service-spec.md` 참조