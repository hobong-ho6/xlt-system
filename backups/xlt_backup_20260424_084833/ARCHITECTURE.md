# XLT 시스템 v2.0 아키텍처

## 🎯 설계 목표
- **단순성**: 복잡한 구조를 피하고 직관적인 모듈 분리
- **확장성**: 새로운 입력 방식, OCR 엔진, 번역 서비스 쉽게 추가 가능
- **유지보수성**: 명확한 책임 분리와 테스트 가능한 구조
- **사용성**: 간단한 CLI 인터페이스와 대화형 모드

## 📁 디렉토리 구조

```
xlt/                     # 메인 패키지
├── __init__.py
├── core/               # 핵심 파이프라인
│   ├── __init__.py
│   ├── pipeline.py     # 메인 워크플로우 오케스트레이션
│   ├── config.py       # 설정 관리 (언어, 필터 등)
│   └── exceptions.py   # 커스텀 예외 클래스
├── input/              # 입력 처리 모듈
│   ├── __init__.py
│   ├── base.py         # 입력 처리 추상 기본 클래스
│   ├── clipboard.py    # 클립보드 이미지 처리
│   ├── figma.py        # 피그마 URL 처리
│   └── image.py        # 로컬 이미지 파일 처리
├── ocr/                # OCR 처리 모듈
│   ├── __init__.py
│   ├── engine.py       # EasyOCR 엔진 래퍼
│   ├── filters.py      # 텍스트 필터링 (UI 제거, 노이즈 등)
│   └── extractors.py   # 의미있는 텍스트 추출 로직
├── translation/        # 번역 처리 모듈
│   ├── __init__.py
│   ├── translator.py   # Google Translate API 래퍼
│   └── languages.py    # 지원 언어 설정
├── output/             # 출력 처리 모듈
│   ├── __init__.py
│   ├── excel.py        # Excel 파일 생성/업데이트
│   └── formatter.py    # 데이터 포맷팅 유틸리티
├── ui/                 # 사용자 인터페이스
│   ├── __init__.py
│   ├── interactive.py  # 대화형 선택 인터페이스
│   └── display.py      # 결과 표시 유틸리티
└── utils/              # 공통 유틸리티
    ├── __init__.py
    ├── logger.py       # 세션 기반 로깅
    └── helpers.py      # 공통 헬퍼 함수
```

## 🔄 데이터 플로우

```
입력 → OCR → 필터링 → 사용자 선택 → 번역 → Excel 출력
  ↓      ↓        ↓          ↓          ↓         ↓
Image  Text   Filtered   Selected   Translated  Excel
Source  Raw    Text       Text       Text       File
```

## 🎛️ 메인 엔트리 포인트

`main.py` - 단일 엔트리 포인트로 모든 기능 통합
- CLI 인수 파싱
- 입력 방식 자동 감지
- 파이프라인 실행
- 에러 처리

## 🔌 플러그인 아키텍처

각 모듈은 추상 기본 클래스를 상속받아 새로운 구현체 추가 가능:
- `InputProcessor` - 새로운 입력 소스 (웹 URL, API 등)
- `OCREngine` - 새로운 OCR 서비스 (AWS Textract, Azure 등)
- `TranslationService` - 새로운 번역 서비스 (DeepL, OpenAI 등)
- `OutputHandler` - 새로운 출력 형식 (CSV, JSON 등)

## 📊 설정 관리

`config.py`에서 중앙 집중식 설정 관리:
```python
DEFAULT_LANGUAGES = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
OCR_CONFIDENCE_THRESHOLD = 0.5
UI_FILTER_ZONES = {...}
TRANSLATION_BATCH_SIZE = 10
```

## 🚀 사용 방식

### 기본 사용법
```bash
python main.py image.png              # 학습 모드 (기본)
python main.py --auto image.png       # 자동 모드
python main.py --interactive          # 대화형 모드
```

### 고급 사용법
```bash
python main.py clipboard --languages ko,en,ja
python main.py figma-url --output custom.xlsx
python main.py --config custom_config.json
```

## 🎯 핵심 개선사항

1. **명확한 모듈 분리**: 각 모듈이 단일 책임
2. **타입 힌트**: 모든 함수와 클래스에 타입 어노테이션
3. **에러 처리**: 각 단계별 명확한 예외 처리
4. **테스트 가능**: 각 모듈을 독립적으로 테스트 가능
5. **로깅**: 구조화된 로깅으로 디버깅 지원
6. **설정 관리**: 중앙 집중식 설정으로 유연성 확보