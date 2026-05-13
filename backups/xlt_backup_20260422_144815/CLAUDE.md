# CLAUDE.md

Claude Code가 이 저장소에서 작업할 때 참고하는 가이드라인입니다.

## 프로젝트 개요

**XLT System v3.0** - Figma URL이나 이미지에서 OCR로 텍스트를 추출하고 5개 언어로 번역하는 자동화 시스템

**핵심 워크플로우**: Figma URL/이미지 입력 → OCR 텍스트 추출 → 사용자 선택 → 치환자 처리 → 번역 미리보기 → Excel 다운로드

**v3.0 주요 기능**:
- Flask 기반 웹 인터페이스
- Google Translate 전용 (Claude AI 제거)
- 자동 치환자 감지 ({{0}}, {{1}} 등)
- 다운로드 전 번역 미리보기
- Excel 병합 기능

## Development Environment Setup

### Initial Setup
```bash
# Clone and install dependencies
pip install -r requirements.txt

# Configure Figma access (optional but recommended)
cp figma_config_example.json figma_config.json
# Add your Figma personal access token to figma_config.json
```

### Development Server
```bash
# Start development web server (automatically starts via SessionStart hook)
python3 stable_web_server.py

# Access web interface
http://localhost:5004

# Manual server management
pkill -f stable_web_server.py  # Stop server
lsof -i :5004                  # Check port conflicts
ps aux | grep stable_web_server.py | grep -v grep  # Check running server
```

### Environment Variables
```bash
export FIGMA_TOKEN="your_figma_personal_access_token"
```

## 아키텍처

### 웹 애플리케이션 (Flask)
- **메인 진입점**: `stable_web_server.py` (포트 5004)
- **세션 관리**: OCR 결과 및 번역 진행 상황을 메모리에 저장
- **2개 탭**: 텍스트 번역 + Excel 병합
- **번역 미리보기**: Excel 다운로드 전 결과 표시 (최신 버전 추가)

### 핵심 컴포넌트 (`xlt/` 패키지)
- **Pipeline** (`xlt/core/pipeline.py`): 메인 워크플로우 오케스트레이션
- **입력 처리** (`xlt/input/`): Figma URL, 로컬 이미지
- **OCR 엔진** (`xlt/ocr/engine.py`): EasyOCR 기반 텍스트 추출
- **번역** (`xlt/translation/translator.py`): Google Translate API
- **출력** (`xlt/output/excel.py`): Excel 파일 생성
- **치환자** (`xlt/utils/placeholder_detector.py`): 자동 패턴 감지

### 주요 워크플로우
1. **입력**: Figma URL 또는 이미지 업로드
2. **OCR**: 신뢰도 필터링으로 텍스트 추출
3. **선택**: 사용자가 체크박스로 텍스트 선택
4. **치환자**: 패턴 자동 감지 ({{0}}, {{1}}) 및 사용자 확인
5. **번역**: 개별 텍스트 처리 (5개 언어: ko_KR, en_US, ja_JP, zh_TW, th_TH)
6. **미리보기**: XLT 키와 함께 번역 결과 표시
7. **다운로드**: `sampleformat.xlsx` 구조로 Excel 생성

### 번역 미리보기 시스템 (최신 기능)
**중요한 워크플로우 변경**: 즉시 Excel 다운로드 대신 사용자가 미리보기를 먼저 확인

**구현 방식**:
- `static/js/ocr_results.js`의 `showTranslationPreview()` 함수
- XLT 키, 원본 텍스트, 처리된 텍스트(치환자 포함), 5개 언어 번역 결과 모두 표시
- 미리보기 확인 후 `/download-excel` 엔드포인트로 실제 파일 다운로드

### 치환자 시스템
**자동 감지 패턴**: 숫자, 금액(USDT, USD 등), 기간(일, 시간), 레벨, 퍼센트, 개수
**사용자 워크플로우**: 자동 감지 → 모달 확인 → 개별 텍스트 선택 → {{0}}, {{1}} 할당
**번역 보존**: 모든 언어에서 치환자 유지

### 한국어 우선 로컬라이제이션
- 모든 사용자 인터페이스는 한국어
- OCR 오류 교정 패턴 내장: `{'이울': '이율', '미선': '미션', '토근': '토큰'}`
- 텍스트 항상 Y좌표 순서로 표시 (위에서 아래로)

### Excel 출력 구조
`Sample/sampleformat.xlsx` 템플릿과 정확히 일치:
- Key ID | en_US | ko_KR | ja_JP | zh_CN | zh_TW | vi_VN | tr_TR | ru_RU | de_DE | th_TH | fr_FR | ms_MY | id_ID | ar_AA | pt_BR | pt_PT | it_IT | es_419 | es_ES

## Critical Translation Guidelines (Unifi Service)

**MANDATORY**: When working with Unifi fintech service translations, strictly follow `guide.md`:

### Key Requirements
- **Reference Database**: Always check `Unifi/Unifi_WEB BROWSER_v*.xlsx` for existing translations (1,245+ entries)
- **Terminology Consistency**: Use established financial terms from the reference database
- **Search Pattern**: Look for similar Key patterns (e.g., `UF_asset_*`, `Common_login_*`)
- **Tone Guidelines**: 
  - Korean: Friendly formal (~해요 style) - "매일 이자를 드려요", "확인해 보세요"
  - English: Clear, concise financial language - "Log in with Apple", "Transaction Type"
  - Japanese: Polite (です・ます체) - "ログインしてください", "確認できます"
  - Chinese: Formal traditional Chinese - "請確認", "使用...登入"
  - Thai: Polite without คะ/ครับ - "เข้าสู่ระบบ", "กรุณาตรวจสอบ"

### Translation Process
1. Check existing translations in reference database first
2. Apply OCR corrections from config.py for Korean text
3. Preserve all placeholders ({{0}}, {{wallet}}, etc.)
4. Maintain HTML tags (<span />, <br />)
5. Follow fintech compliance requirements for legal terms

## Key Architecture Decisions

### Flask Web Server as Primary Interface
- **Why**: Replaces CLI-based main.py for better user experience
- **Port**: 5004 (configured in stable_web_server.py)
- **Auto-start**: SessionStart hook automatically starts server
- **Two Tabs**: Text Translation + Excel Merging functionality

### Translation System Design
- **Critical**: `target_languages` excludes 'ko_KR' to prevent Google Translate malfunction
- **Fallback**: Korean text is used directly as original (no translation needed)
- **Individual Processing**: Each text translated separately to avoid language detection errors
- **Batch Prevention**: Mixed language batches cause detection failures

### Removed Components (v3.0)
- **Clipboard functionality**: Removed for stability (was causing UI issues)
- **Claude AI integration**: Google Translate only (simplified architecture)
- **CLI main.py interface**: Web-first approach with stable_web_server.py as entry point
- **File uploads**: Figma URL processing only (no local file uploads)

### 번역 시스템 핵심 수정사항
**중요**: Google Translate 오작동 방지를 위해 번역 시스템에서 'ko_KR' 제외:
```python
# ✅ 올바른 방식
target_languages = ['en_US', 'ja_JP', 'zh_TW', 'th_TH']  
result['ko_KR'] = original_text  # 한국어 원본 텍스트 직접 사용

# ❌ 잘못된 방식 (모든 언어가 한국어로 반환됨)  
target_languages = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
```

### 텍스트 추출 정책
**엄격한 요구사항**: 번호가 매겨진 목록뿐만 아니라 의미있는 모든 텍스트 추출. 사용자 인터페이스에서 그룹화나 분류 없이 Y좌표 순서로 표시.

**다단계 필터링**:
1. UI 영역 제외 (Y좌표 임계값)
2. 배지/라벨 패턴 제거
3. 노이즈 텍스트 제거 (시간 패턴, 특수문자)
4. 한국어 텍스트 교정 및 정규화
5. 신뢰도 기반 필터링

### 사용자 선택 기반 번역
**핵심 원칙**: 추출된 모든 텍스트가 아닌 사용자가 선택한 텍스트만 번역. 사용자는 OCR 원본 결과와 필터링된 의미있는 텍스트 모두에서 선택 가능.

## 파일 구조

### Key Files and Structure
```
stable_web_server.py       # 🚀 Main entry point (Flask web server)
requirements.txt           # Python dependencies
figma_config.json         # Figma API credentials (create from example)

xlt/                      # Main XLT package
├── core/                 # Core pipeline system  
│   ├── pipeline.py       # Main workflow orchestration
│   ├── config.py         # Central configuration with OCR corrections
│   └── exceptions.py     # Custom exception hierarchy
├── input/               # Input processing modules
│   ├── figma.py         # Figma URL processor (primary input method)
│   └── image.py         # Local image processor  
├── ocr/                 # OCR processing system
│   ├── engine.py        # EasyOCR engine wrapper
│   ├── filters.py       # Text filtering (UI area removal, noise filtering)
│   └── extractors.py    # Meaningful text extraction logic
├── translation/         # Translation system
│   ├── translator.py    # Google Translate API wrapper  
│   └── languages.py     # Language configuration and mapping
├── output/              # Output processing
│   ├── excel.py         # Excel file generation/management
│   └── formatter.py     # Data formatting utilities
└── utils/               # Common utilities
    ├── placeholder_detector.py  # {{0}}, {{1}} pattern detection
    └── helpers.py       # Helper functions

templates/               # 🌐 Web interface templates
├── index.html          # Main page (Figma URL input + real-time logs)
└── ocr_results.html    # Text selection and translation interface

static/                  # 🎨 Web assets
├── js/
│   ├── app.js          # Main page JavaScript
│   └── ocr_results.js  # Translation interface logic
└── css/
    └── style.css       # Web styling

# 📋 Reference and configuration files
guide.md                # 🔥 Translation guidelines (MUST reference for Unifi)
Sample/sampleformat.xlsx # Excel output template structure
Unifi/Unifi_WEB BROWSER_v*.xlsx # Translation database (1,245+ entries)
handoff.md              # Development handoff documentation
.claude/settings.json   # Project-specific Claude Code settings
```

### Removed Files (v3.0)
- ❌ `main.py` - Replaced by web interface
- ❌ `xlt/input/clipboard.py` - Removed for stability
- ❌ Claude AI integration files - Simplified to Google Translate only

### Key API Endpoints

#### Main Workflow
- `POST /upload` - Process Figma URL or image file, returns OCR results
- `GET /select_texts` - Text selection interface with filtering options  
- `POST /check-placeholders` - Placeholder pattern detection and suggestions
- `POST /translate-selected` - Translation with preview data (JSON response)
- `POST /download-excel` - Excel file generation after preview confirmation

#### System & Health
- `GET /api/health` - System health check (translation, dependencies, memory)
- `GET /api/logs/<session_id>` - Real-time session logs for progress tracking
- `GET /api/translation-progress/<session_id>` - Translation progress polling

#### Excel Management  
- `GET /download/<filename>` - Direct Excel file download
- `POST /merge-excel` - Excel file merging functionality (separate tab)

#### Development & Testing
- `GET /test_web_flow.html` - Automated workflow testing page
- Static file serving for `/templates/` and `/static/` assets

## 일반적인 문제 및 해결책

### 번역 문제
**태국어 번역 타임아웃**: th_TH 컬럼에 태국어 대신 한국어가 표시되는 경우:
```bash
# xlt/core/config.py에서 타임아웃 설정 확인
translation_timeout: int = 120  # 120초 이상이어야 함

# 태국어 번역 직접 테스트
python3 -c "
from xlt.translation.translator import Translator
from xlt.core.config import XLTConfig
translator = Translator(XLTConfig())
result = translator.translate_batch(['테스트'], ['th_TH'])
print(result)
"
```

### 서버 문제
```bash
# 서버 시작 안됨
pkill -f stable_web_server.py
lsof -i :5004  # 포트 충돌 확인
python3 stable_web_server.py

# Excel 다운로드 안됨
# 브라우저 강제 새로고침: Cmd+Shift+R (Mac) / Ctrl+Shift+R (Windows)
# 브라우저 콘솔에서 테스트: window.ocrManager?.testDownload()
```

### 의존성
```bash
# 패키지 누락
pip install googletrans==4.0.0rc1 easyocr openpyxl pillow requests flask

# OCR 문제
pip show easyocr  # 설치 확인
```

## Configuration Management

### XLTConfig Class (xlt/core/config.py)
Central configuration with Korean OCR corrections built-in:

```python
# OCR error corrections for Korean text
ocr_corrections = {
    '이울': '이율',
    '미선': '미션', 
    '토근': '토큰',
    '받앉어요': '받았어요',
    '다사': '다시',
    '빈상': '빈상금'
}

# UI filtering zones for game interfaces
ui_filter_zones = {
    'top_gnb_threshold': 100,           # Top GNB area Y coordinate
    'bottom_tab_threshold': 0.8,        # Bottom tab area ratio
    'badge_patterns': [                 # Patterns to filter out
        r'\d+[a-zA-Z]\s*\)\s*\d+[가-힣]*',  # "6f ) 3일" pattern
        r'\d+[a-zA-Z]\s+\d+[!]*'            # "7a 39!" pattern
    ]
}

# Translation settings
translation_batch_size = 10
translation_timeout = 120  # Minimum 120 seconds for Thai translation
```

### Loading Custom Configuration
```python
from xlt.core.config import XLTConfig

# Load from file
config = XLTConfig.from_file('custom_config.json')

# Save current config
config.to_file('my_settings.json')
```

## Common Development Workflows

### Adding New Input Processor
```python
# Example: xlt/input/new_source.py
from xlt.input.base import InputProcessor
from PIL import Image
from typing import Tuple

class NewSourceProcessor(InputProcessor):
    def can_process(self, source: str) -> bool:
        return source.startswith('newsource://')
    
    def process(self, source: str) -> Tuple[Image.Image, str]:
        # Extract image from new source
        # Return (PIL Image, description)
        pass

# Register in xlt/core/pipeline.py
def initialize(self):
    self.input_processors['newsource'] = NewSourceProcessor(self.config)
```

### Adding New Translation Service
```python
# Example: xlt/translation/deepl_translator.py
from xlt.translation.translator import Translator

class DeepLTranslator(Translator):
    def translate_text(self, text: str, target_language: str) -> str:
        # DeepL API integration
        pass
```

### Debugging Translation Issues
1. **Check server logs**: Browser console (F12) shows real-time processing
2. **Test individual components**:
   ```bash
   # Test OCR only
   python3 -c "
   from xlt.ocr.engine import OCREngine
   from xlt.core.config import XLTConfig
   ocr = OCREngine(XLTConfig())
   # Process test image
   "
   
   # Test translation only
   curl -X POST http://localhost:5004/api/test-translation \
     -H "Content-Type: application/json" \
     -d '{"text": "테스트", "target": "en_US"}'
   ```

3. **Common Issues**:
   - **Thai translation timeout**: Increase `translation_timeout` to 120+ seconds
   - **Mixed language detection**: Process texts individually, not in batches
   - **Figma access**: Verify token in `figma_config.json` or `FIGMA_TOKEN` env var

### Web Interface Development
```bash
# Frontend assets location
static/js/app.js          # Main page JavaScript
static/js/ocr_results.js  # Translation interface logic
static/css/style.css      # Styling
templates/index.html      # Main page template
templates/ocr_results.html # Translation results page

# Key JavaScript functions
showTranslationPreview()  # Translation preview modal
translateSelected()       # Process selected texts
downloadResult()         # Excel file download
```

## 코드베이스 작업 시 주의사항

### 번역 로직 수정 시
**중요**: Google Translate 오작동 방지를 위해 번역 시스템에서 'ko_KR'을 target_languages에서 제외. 한국어 텍스트는 원본을 직접 사용.

### 기능 추가 시
- 모든 사용자 인터페이스 텍스트는 한국어
- 작업 세션 완료 시 `handoff.md` 업데이트: 완료된 작업, 남은 TODO, 중요 사항
- Unifi 관련 번역은 `guide.md` 참조

### Web Server Development
- **Entry Point**: `stable_web_server.py` (not main.py)
- **Session Management**: In-memory storage for OCR results and translation progress
- **API Endpoints**: All return JSON responses for frontend consumption
- **Error Handling**: Comprehensive exception handling with user-friendly Korean messages

### 번역 시스템 테스트
```bash
# 개별 언어 번역 테스트
python3 -c "
from xlt.translation.translator import Translator
from xlt.core.config import XLTConfig
translator = Translator(XLTConfig())
result = translator.translate_batch(['테스트 텍스트'], ['en_US'])
print(result)
"

# 서버 상태 확인
curl -s http://localhost:5004/api/health
```

## 빠른 참조

### 의존성 (requirements.txt)
- `easyocr==1.7.0` - OCR 엔진
- `googletrans==4.0.0rc1` - 번역 서비스
- `openpyxl==3.1.2` - Excel 파일 처리
- `flask` - 웹 프레임워크
- `pillow`, `requests`, `psutil` - 지원 라이브러리

### Current Status (v3.0)
- **Main Interface**: Flask web application (port 5004) with SessionStart auto-startup
- **Translation Preview**: Complete implementation (shows results before Excel download)
- **Supported Languages**: ko_KR (original), en_US, ja_JP, zh_TW, th_TH
- **Placeholder System**: Automatic detection of numbers, amounts, levels, percentages, counts
- **Excel Output**: Compatible with `Sample/sampleformat.xlsx` structure
- **Figma Integration**: Requires personal access token in `figma_config.json`
- **Web-First Architecture**: No CLI interface, all operations via web UI
- **Translation Quality**: Unifi fintech terminology consistency via `guide.md` compliance

### Production Readiness
- ✅ **Complete Workflow**: Figma URL → OCR → Selection → Placeholders → Translation Preview → Excel
- ✅ **Error Handling**: Comprehensive exception handling with Korean user messages  
- ✅ **Auto-Startup**: SessionStart hook automatically starts web server
- ✅ **Translation System**: Individual text processing prevents language detection errors
- ✅ **Korean OCR Corrections**: Built-in corrections for common OCR errors in Korean text

이 시스템은 Figma 디자인을 다국어 Excel 파일로 처리하는 번역 미리보기 기능을 갖춘 프로덕션 준비 완료 상태입니다.

## Testing and Validation

### System Health Check
```bash
# Check server status and all components
curl -s http://localhost:5004/api/health | python3 -m json.tool

# Verify XLT package import
python3 -c "from xlt import XLTPipeline, XLTConfig; print('✅ XLT system OK')"

# Test OCR system initialization
python3 -c "
from xlt import XLTConfig
from xlt.ocr.engine import OCREngine
config = XLTConfig()
ocr = OCREngine(config)
print('✅ OCR engine ready')
"
```

### Translation System Test
```bash
# Test individual language translation
python3 -c "
from xlt.translation.translator import Translator
from xlt.core.config import XLTConfig
translator = Translator(XLTConfig())
result = translator.translate_batch(['테스트 텍스트'], ['en_US'])
print('Translation result:', result)
"

# Test all supported languages
python3 -c "
from xlt.translation.translator import Translator
from xlt.core.config import XLTConfig
translator = Translator(XLTConfig())
languages = ['en_US', 'ja_JP', 'zh_TW', 'th_TH']
for lang in languages:
    result = translator.translate_batch(['안녕하세요'], [lang])
    print(f'{lang}: {result}')
"
```

### Figma Integration Test
```bash
# Test Figma token configuration
python3 -c "
from xlt.core.config import XLTConfig
config = XLTConfig()
token = config.get_figma_token()
print('✅ Figma token configured' if token else '⚠️ Figma token missing')
"
```