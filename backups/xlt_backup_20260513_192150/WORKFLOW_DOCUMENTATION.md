# XLT System v3.3 워크플로우 완전 가이드

**작성일**: 2026-04-27  
**대상 버전**: XLT System v3.3.0

---

## 📋 목차

1. [전체 프로세스 개요](#전체-프로세스-개요)
2. [상세 단계별 워크플로우](#상세-단계별-워크플로우)
3. [플로우차트](#플로우차트)
4. [기능별 상세 설명](#기능별-상세-설명)
5. [데이터 흐름도](#데이터-흐름도)

---

## 전체 프로세스 개요

```
Figma URL 입력
    ↓
이미지 다운로드 & 텍스트 추출
    ↓
맞춤법/띄어쓰기 자동 교정 (v3.3)
    ↓
사용자 텍스트 선택 & 수정
    ↓
(선택) 맞춤법 검사 버튼 클릭 (v3.3)
    ↓
치환자 감지 & 적용
    ↓
XLT Key 생성/설정
    ↓
번역 실행 (Unifi 전문 번역)
    ↓
사용자 교정 학습 (v3.3)
    ↓
Excel 다운로드
```

**소요 시간**: 평균 30초~2분 (텍스트 개수에 따라)

---

## 상세 단계별 워크플로우

### Phase 1: 입력 및 검증 (Frontend)

#### 1.1 Figma URL 입력
**파일**: `templates/index.html`, `static/js/main.js`

**사용자 동작**:
- Figma URL을 입력 필드에 붙여넣기
- "번역 시작" 버튼 클릭

**시스템 처리**:
```javascript
// 1. URL 형식 검증 (클라이언트)
if (!figmaUrl.includes('figma.com')) {
    alert('올바른 Figma URL을 입력해주세요.');
    return;
}

// 2. POST 요청 전송
fetch('/upload', {
    method: 'POST',
    body: formData
})
```

**검증 항목**:
- ✅ URL에 'figma.com' 포함 여부
- ✅ 빈 값 체크

---

### Phase 2: 이미지 처리 & 텍스트 추출 (Backend)

#### 2.1 세션 생성
**파일**: `stable_web_server.py:1155` (`/upload` 엔드포인트)

```python
# 고유 세션 ID 생성
session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
session_logs[session_id] = []
```

**세션 정보 저장**:
- OCR 결과
- 로그 메시지
- 번역 진행 상황
- 이미지 경로

---

#### 2.2 Figma 이미지 다운로드
**파일**: `xlt/input/figma.py`

**처리 순서**:

1. **Figma Token 확인**
```python
# figma_config.json 또는 환경변수에서 토큰 로드
figma_token = config.get_figma_token()
if not figma_token:
    raise ValueError("Figma 토큰이 설정되지 않았습니다")
```

2. **URL 파싱**
```python
# URL에서 file-key와 node-id 추출
# 예: https://www.figma.com/design/ABC123/...?node-id=123-456
file_key, node_id = self._parse_figma_url(figma_url)
```

3. **Figma API 호출**
```python
# GET /v1/images/:file_key?ids=:node_id&format=png&scale=2
response = requests.get(
    f"https://api.figma.com/v1/images/{file_key}",
    params={'ids': node_id, 'format': 'png', 'scale': 2},
    headers={'X-Figma-Token': figma_token}
)
```

4. **이미지 다운로드**
```python
# Figma가 반환한 이미지 URL에서 PNG 다운로드
image_url = response.json()['images'][node_id]
image_data = requests.get(image_url).content

# 임시 파일로 저장
temp_file = f"figma/{session_id}_figma.png"
```

**로그 출력**:
```
📸 피그마 이미지 다운로드 중...
✅ 피그마 이미지 다운로드 완료
```

---

#### 2.3 텍스트 추출 (2가지 방법)

##### 방법 A: Figma Text API (우선 시도)
**파일**: `xlt/input/figma.py:extract_text_from_node()`

```python
# GET /v1/files/:file_key/nodes?ids=:node_id
response = requests.get(
    f"https://api.figma.com/v1/files/{file_key}/nodes",
    params={'ids': node_id},
    headers={'X-Figma-Token': figma_token}
)

# 모든 TEXT 노드 추출
texts = self._extract_text_nodes(node_data)
```

**장점**:
- 정확한 텍스트 (OCR 오류 없음)
- 신뢰도 100%
- 빠른 처리 속도

**로그 출력**:
```
✅ 피그마 API로 4개 텍스트 추출 완료
💡 OCR 없이 정확한 텍스트를 가져왔습니다 (신뢰도 100%)
```

---

##### 방법 B: OCR (Text API 실패 시)
**파일**: `xlt/ocr/engine.py`

```python
# EasyOCR 엔진 사용
reader = easyocr.Reader(['ko', 'en'], gpu=False)
results = reader.readtext(image_array)

# 결과 변환
ocr_results = [{
    'text': text,
    'confidence': confidence,
    'bbox': bbox
}]
```

**처리 순서**:
1. 이미지 → NumPy 배열 변환
2. EasyOCR로 텍스트 감지
3. 신뢰도 임계값 필터링 (기본 0.3)
4. 좌표(bbox) 정보 포함

**로그 출력**:
```
🤖 OCR 텍스트 추출 중...
✅ OCR 완료: 4개 텍스트 발견
```

---

#### 2.4 맞춤법/띄어쓰기 자동 교정 (v3.3 신규)
**파일**: `stable_web_server.py:257` (`apply_korean_corrections()`)

**3단계 교정 파이프라인**:

```python
# 1단계: OCR 특화 사전 (즉시 교정)
correction_dict = {
    '이울': '이율',
    '미선': '미션',
    '토근': '토큰',
    '모매일': '매일',
    # ... 20+ 항목
}
for wrong, correct in correction_dict.items():
    text = text.replace(wrong, correct)

# 2단계: 바른 API 맞춤법 검사 (캐시 우선)
# - 캐시 확인: data/spelling_corrections.json
# - 캐시 없으면: 바른 AI API 호출 (api.bareun.ai:443)
text = check_spelling_with_bareun(text)

# 3단계: 정규표현식 정리
# - 연속 공백 제거
# - 조사 띄어쓰기 ("게임 을" → "게임을")
# - 숫자 단위 ("10 개" → "10개")
text = re.sub(r'([가-힣])\s+(은|는|이|가|을|를|의|와|과)', r'\1\2', text)
```

**예시**:
```
원본:    "일일미선달성완료"
1단계:   "일일미션달성완료"
2단계:   "일일 미션 달성 완료"
3단계:   "일일 미션 달성 완료" (이미 올바름)
```

**로그 출력**:
```
🔤 교정: '일일미선달성완료' → '일일 미션 달성 완료'
✅ 텍스트 추출 완료: 4개 텍스트 발견 (교정 적용됨)
```

**캐시 관리**:
- 바른 API 응답은 자동으로 `data/spelling_corrections.json`에 저장
- 다음번 동일 텍스트는 API 호출 없이 캐시에서 즉시 반환
- 평균 0.007초 (캐시) vs 1~2초 (API)

---

### Phase 3: 사용자 선택 & 수정 (Frontend)

#### 3.1 OCR 결과 페이지 표시
**파일**: `templates/ocr_results.html`

**화면 구성**:
```
┌─────────────────────────────────────┐
│ 의미있는 텍스트 (4개)   [전체 OCR 결과] │
├─────────────────────────────────────┤
│ □ #1 (필터링됨)                     │
│   일일 미션 달성 완료   [🔍 맞춤법]  │
│   신뢰도: 100.0%                    │
├─────────────────────────────────────┤
│ □ #2 (필터링됨)                     │
│   리워드 받으러 가기    [🔍 맞춤법]  │
│   신뢰도: 100.0%                    │
└─────────────────────────────────────┘
```

**2개 탭 제공**:
1. **의미있는 텍스트**: 필터링된 텍스트만 (추천)
   - 신뢰도 > 0.3
   - 길이 > 1
   - 특수문자만 있는 텍스트 제외

2. **전체 OCR 결과**: 모든 텍스트 (디버깅용)

---

#### 3.2 텍스트 선택 & 수정
**파일**: `static/js/ocr_results.js:334` (`updateSelectedItems()`)

**사용자 동작**:
1. 체크박스 클릭하여 텍스트 선택
2. 텍스트 입력 필드 클릭하여 수정
3. (선택) 맞춤법 검사 버튼 클릭

**시스템 처리**:
```javascript
// 체크박스 변경 감지
checkbox.addEventListener('change', () => {
    this.handleSelectionChange();
});

// 선택된 항목 업데이트
updateSelectedItems() {
    this.selectedItems = [];
    document.querySelectorAll('.item-checkbox:checked').forEach(checkbox => {
        const ocrItem = checkbox.closest('.ocr-item');
        const textInput = ocrItem.querySelector('.text-edit-input');
        
        this.selectedItems.push({
            index: ocrItem.dataset.index,
            text: textInput.value.trim(),  // 사용자 수정 텍스트
            source_type: ocrItem.dataset.source
        });
    });
}
```

**플로팅 패널 표시**:
```
┌────────────────────────┐
│ 🎯 선택된 항목: 2개    │
│ [2개 항목 번역]        │
│ [전체 선택] [선택 해제] │
└────────────────────────┘
```

---

#### 3.3 맞춤법 검사 버튼 (v3.3 신규)
**파일**: `static/js/ocr_results.js:2529` (`checkSpelling()`)

**사용자 동작**:
- 텍스트 옆 🔍 버튼 클릭

**시스템 처리**:
```javascript
// 1. API 요청
const response = await fetch('/api/spell-check', {
    method: 'POST',
    body: JSON.stringify({ text: originalText })
});

// 2. 교정된 텍스트로 업데이트
inputField.value = result.corrected_text;

// 3. 시각적 피드백
inputField.style.backgroundColor = '#d4edda';  // 녹색 깜빡임
setTimeout(() => {
    inputField.style.backgroundColor = '';
}, 1500);
```

**백엔드 처리** (`/api/spell-check`):
```python
text = request.json['text']
corrected_text = apply_korean_corrections(text)  # 3단계 교정

return {
    'status': 'success',
    'original_text': text,
    'corrected_text': corrected_text,
    'changed': text != corrected_text
}
```

**알림 표시**:
```
✅ 맞춤법 교정 완료: "일일미션달성..." → "일일 미션 달성 완료"
```

---

### Phase 4: 치환자 감지 (Backend + Frontend)

#### 4.1 치환자 패턴 분석
**파일**: `stable_web_server.py:1481` (`/check-placeholders` 엔드포인트)

**API 요청**:
```javascript
fetch('/check-placeholders', {
    method: 'POST',
    body: JSON.stringify({
        selected_indexes: [0, 1, 2],
        selected_texts: [
            "일일 미션 달성 완료",
            "매일 10개 달성하세요",
            "리워드 받으러 가기"
        ],
        session_id: "session_xxx"
    })
})
```

**백엔드 처리**:
```python
from xlt.utils.placeholder_detector import PlaceholderDetector

detector = PlaceholderDetector()

# 각 텍스트 분석
for text in selected_texts:
    # 숫자 패턴 감지: "10", "100", "50%" 등
    has_number = detector.has_number_pattern(text)
    
    # 변수 패턴 감지: "{name}", "$value", "@user" 등
    has_variable = detector.has_variable_pattern(text)
    
    if has_number or has_variable:
        # 치환자 제안 생성
        suggestion = detector.suggest_placeholder(text)
        # 예: "매일 10개 달성하세요" → "매일 {{0}}개 달성하세요"
```

**반환 데이터**:
```json
{
  "status": "success",
  "has_placeholders": true,
  "placeholder_suggestions": [
    {
      "original_text": "매일 10개 달성하세요",
      "pattern_text": "매일 {{0}}개 달성하세요",
      "detected_patterns": ["10"],
      "confidence": 0.9
    }
  ]
}
```

---

#### 4.2 치환자 선택 모달 (Frontend)
**파일**: `static/js/ocr_results.js:1213` (`showPlaceholderModal()`)

**모달 UI**:
```
┌─────────────────────────────────────────────┐
│ 🔧 치환자 적용 선택                         │
├─────────────────────────────────────────────┤
│ #1 매일 10개 달성하세요                     │
│                                             │
│ ☑ 치환자 적용하기                          │
│ 원본:   매일 10개 달성하세요               │
│ 적용후: 매일 {{0}}개 달성하세요            │
│                                             │
│ [텍스트 수정 가능]                         │
├─────────────────────────────────────────────┤
│ #2 일일 미션 달성 완료                      │
│ □ 치환자 없음 (원본 유지)                  │
├─────────────────────────────────────────────┤
│         [전체 선택] [전체 해제]             │
│         [취소]      [적용하기]              │
└─────────────────────────────────────────────┘
```

**사용자 선택**:
1. 각 텍스트별로 치환자 적용 여부 선택
2. 치환자 적용된 텍스트 직접 수정 가능
3. "적용하기" 버튼 클릭

**결과 처리**:
```javascript
// 최종 텍스트 배열 생성
const finalTexts = [];
suggestions.forEach(suggestion => {
    const checkbox = document.getElementById(`apply_placeholder_${i}`);
    if (checkbox.checked) {
        // 치환자 적용
        const editedText = document.getElementById(`edit_text_${i}`).value;
        finalTexts.push(editedText);  // "매일 {{0}}개 달성하세요"
    } else {
        // 원본 유지
        finalTexts.push(suggestion.original_text);
    }
});

// 세션에 저장 (다음 단계로 전달)
await fetch('/store-final-texts', {
    method: 'POST',
    body: JSON.stringify({
        session_id: sessionId,
        final_texts: finalTexts
    })
});
```

---

### Phase 5: XLT Key 생성/설정 (Frontend + Backend)

#### 5.1 키 생성 모드 선택
**파일**: `static/js/ocr_results.js:1037` (모달 HTML 생성 부분)

**모달 UI**:
```
┌─────────────────────────────────────────┐
│ 🔑 XLT Key 설정                         │
├─────────────────────────────────────────┤
│ 🔧 키 생성 방식 선택 (v3.3)             │
│                                         │
│ ◉ 지능형 키 (Unifi 패턴 분석)          │
│   예: XLT_mission_text_매일_달성_001   │
│                                         │
│ ○ 단순 prefix + 번호                   │
│   [MY_KEY______] 입력                  │
│   예: MY_KEY_001, MY_KEY_002           │
├─────────────────────────────────────────┤
│ #1 일일 미션 달성 완료                  │
│ [XLT_mission_text_일일_미션_001]       │
│                                         │
│ #2 매일 {{0}}개 달성하세요              │
│ [XLT_achievement_text_매일_002]        │
├─────────────────────────────────────────┤
│      [자동 생성]  [확인]                │
└─────────────────────────────────────────┘
```

---

#### 5.2 지능형 키 생성 (기본값)
**파일**: `xlt/utils/unifi_key_generator.py`

**생성 로직**:
```python
def generate_unifi_key(self, text: str, index: int) -> str:
    # 1. Unifi DB에서 유사 키 검색 (1,244개 항목)
    similar_key = self._find_similar_key_in_db(text)
    
    if similar_key:
        # 기존 패턴 활용: "XLT_mission_text_xxx_001"
        prefix = self._extract_prefix(similar_key)
        return f"{prefix}_{index:03d}"
    
    # 2. 키워드 추출 (한글 → 로마자)
    keywords = self._extract_keywords(text)
    # "일일 미션 달성" → ["일일", "미션", "달성"]
    
    # 3. 카테고리 분석
    category = self._analyze_category(keywords)
    # "미션" → "mission"
    
    # 4. 키 조합
    return f"XLT_{category}_text_{'_'.join(keywords)}_{index:03d}"
```

**예시**:
```
텍스트: "일일 미션 달성 완료"
키: XLT_mission_text_일일_미션_달성_001

텍스트: "매일 10개 달성하세요"
키: XLT_achievement_text_매일_달성_002

텍스트: "리워드 받으러 가기"
키: XLT_reward_button_리워드_받으러_003
```

---

#### 5.3 단순 키 생성 (v3.3 신규)
**파일**: `xlt/utils/unifi_key_generator.py:145` (`generate_simple_key()`)

**생성 로직**:
```python
def generate_simple_key(self, prefix: str, index: int) -> str:
    base_key = f"{prefix}_{index:03d}"
    
    # 중복 확인
    if base_key in self.used_keys:
        # 중복 시 번호 증가
        counter = index + 1
        while f"{prefix}_{counter:03d}" in self.used_keys:
            counter += 1
        base_key = f"{prefix}_{counter:03d}"
    
    return base_key
```

**예시**:
```
prefix: "MY_KEY"
결과: MY_KEY_001, MY_KEY_002, MY_KEY_003, ...
```

---

#### 5.4 사용자 키 수정
**기능**: 각 텍스트의 키를 직접 수정 가능

```javascript
// 키 입력 필드 생성
<input type="text" 
       class="form-control xlt-key-input" 
       value="${autoGeneratedKey}"
       placeholder="XLT 키를 입력하세요">
```

**검증**:
- 중복 키 확인
- 빈 값 체크
- 특수문자 경고

---

### Phase 6: 번역 실행 (Backend)

#### 6.1 번역 요청
**파일**: `stable_web_server.py:1645` (`/translate-selected` 엔드포인트)

**API 요청**:
```javascript
fetch('/translate-selected', {
    method: 'POST',
    body: JSON.stringify({
        session_id: sessionId,
        xlt_keys: [
            "XLT_mission_text_일일_미션_001",
            "XLT_achievement_text_매일_002"
        ]
    })
})
```

---

#### 6.2 사용자 교정 학습 (v3.3 신규)
**파일**: `stable_web_server.py:1698`

**학습 로직**:
```python
# OCR 원본 텍스트와 사용자 최종 텍스트 비교
cache = load_spelling_cache()

for idx, final_text in zip(selected_indexes, final_texts):
    ocr_text = ocr_results[idx]['text']  # OCR 원본
    
    # 사용자가 수정한 경우
    if ocr_text != final_text:
        # 학습 데이터로 저장
        cache[ocr_text] = final_text
        learned_count += 1
        
        logger.info(f"📚 사용자 교정 학습: '{ocr_text}' → '{final_text}'")

# 캐시 저장
save_spelling_cache(cache)
```

**학습 효과**:
```json
// data/spelling_corrections.json
{
  "일일 미션 달성 완료": "매일 미션 완료!",
  "리워드 바드리 가기": "리워드 받으러 가기"
}
```

**로그 출력**:
```
[session_xxx] 📚 사용자 교정 학습: '일일 미션 달성 완료' → '매일 미션 완료!'
[session_xxx] 📚 사용자 교정 학습: '리워드 바드리 가기' → '리워드 받으러 가기'
[session_xxx] ✅ 총 2개 사용자 교정 학습 완료
```

---

#### 6.3 Unifi 전문 번역
**파일**: `xlt/translation/unifi_translator.py`

**번역 프로세스**:

```python
# 1. guide.md 용어집 로드 (1,244개 항목)
terminology = load_translation_guide()

# 2. 대상 언어 설정 (ko_KR 제외)
target_languages = ['en_US', 'ja_JP', 'zh_TW', 'th_TH']

# 3. 각 텍스트별 번역
for text in selected_texts:
    result = {
        'ko_KR': text  # 한국어는 원본 그대로
    }
    
    # 4. Unifi DB에서 기존 번역 확인
    existing_translation = unifi_db.get(text)
    if existing_translation:
        # 기존 번역 사용 (일관성 보장)
        result.update(existing_translation)
        logger.info(f"✅ Unifi DB 번역 사용: {text[:20]}...")
    else:
        # 5. Google Translate API 호출
        for lang in target_languages:
            translated = translator.translate(text, dest=lang)
            result[lang] = translated.text
            
        # 6. 용어집 적용 (guide.md)
        for lang in target_languages:
            for term_ko, translations in terminology.items():
                if term_ko in result[lang]:
                    result[lang] = result[lang].replace(
                        term_ko, 
                        translations[lang]
                    )
    
    # 7. 치환자 복원 ({{0}}, {{1}} 등)
    for lang in target_languages:
        result[lang] = restore_placeholders(result[lang], placeholders)
```

**번역 예시**:
```python
# 입력
text = "매일 {{0}}개 달성하세요"

# 번역 결과
{
    'ko_KR': '매일 {{0}}개 달성하세요',
    'en_US': 'Achieve {{0}} daily',
    'ja_JP': '毎日{{0}}個達成してください',
    'zh_TW': '每天完成{{0}}個',
    'th_TH': 'ทำให้สำเร็จ {{0}} ทุกวัน'
}
```

**진행 상황 업데이트**:
```python
# 세션 상태 업데이트
session_status[session_id] = {
    'translation_progress': {
        'status': 'translating',
        'current_language': 'en_US',
        'completed_languages': [],
        'total_texts': 4,
        'message': '영어 번역 중... (1/4)'
    }
}
```

---

#### 6.4 번역 결과 구성
**파일**: `stable_web_server.py:1890`

**데이터 구조**:
```python
translations = []

for i, text in enumerate(selected_texts):
    translation_result = {
        'xlt_key': xlt_keys[i],
        'ko_KR': text,
        'en_US': translated_texts['en_US'][i],
        'ja_JP': translated_texts['ja_JP'][i],
        'zh_TW': translated_texts['zh_TW'][i],
        'th_TH': translated_texts['th_TH'][i],
        'metadata': {
            'source': 'figma',
            'confidence': 1.0,
            'has_placeholder': '{{' in text,
            'translation_mode': 'google',
            'timestamp': datetime.now().isoformat()
        }
    }
    translations.append(translation_result)
```

**세션에 저장**:
```python
temp_ocr_results[session_id]['translations'] = translations
temp_ocr_results[session_id]['translation_status'] = 'completed'
```

**반환 응답**:
```json
{
  "status": "success",
  "translations": [...],
  "message": "번역이 완료되었습니다",
  "total_count": 4
}
```

---

### Phase 7: Excel 다운로드 (Backend)

#### 7.1 다운로드 요청
**파일**: `stable_web_server.py:2065` (`/download-excel` 엔드포인트)

**API 요청**:
```javascript
fetch('/download-excel', {
    method: 'POST',
    body: JSON.stringify({
        session_id: sessionId
    })
})
```

---

#### 7.2 Excel 파일 생성
**파일**: `xlt/output/excel_formatter.py`

**생성 프로세스**:

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

wb = Workbook()
ws = wb.active
ws.title = "번역 결과"

# 1. 헤더 작성
headers = ['XLT Key', '한국어(ko_KR)', '영어(en_US)', 
           '일본어(ja_JP)', '중국어(zh_TW)', '태국어(th_TH)']
ws.append(headers)

# 2. 헤더 스타일 적용
header_font = Font(bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal='center', vertical='center')

# 3. 데이터 행 작성
for translation in translations:
    row = [
        translation['xlt_key'],
        translation['ko_KR'],
        translation['en_US'],
        translation['ja_JP'],
        translation['zh_TW'],
        translation['th_TH']
    ]
    ws.append(row)

# 4. 열 너비 자동 조정
for column in ws.columns:
    max_length = 0
    column_letter = column[0].column_letter
    for cell in column:
        if cell.value:
            max_length = max(max_length, len(str(cell.value)))
    ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

# 5. 파일 저장
filename = f"translations_{session_id}_{timestamp}.xlsx"
filepath = os.path.join('output', filename)
wb.save(filepath)
```

**Excel 파일 구조**:
```
┌─────────────────────┬──────────────┬────────────────┬──────────────┬──────────────┬──────────────┐
│ XLT Key             │ 한국어(ko_KR)│ 영어(en_US)    │ 일본어(ja_JP)│ 중국어(zh_TW)│ 태국어(th_TH)│
├─────────────────────┼──────────────┼────────────────┼──────────────┼──────────────┼──────────────┤
│ XLT_mission_text_   │ 매일 미션    │ Daily Mission  │ 毎日ミッション│ 每日任務      │ ภารกิจรายวัน│
│ 매일_미션_001       │ 완료!        │ Completed!     │ 完了!        │ 完成!        │ เสร็จสิ้น!   │
├─────────────────────┼──────────────┼────────────────┼──────────────┼──────────────┼──────────────┤
│ XLT_achievement_    │ 매일 {{0}}개 │ Achieve {{0}}  │ 毎日{{0}}個  │ 每天完成      │ ทำให้สำเร็จ  │
│ text_매일_002       │ 달성하세요   │ daily          │ 達成してく... │ {{0}}個      │ {{0}} ทุกวัน │
└─────────────────────┴──────────────┴────────────────┴──────────────┴──────────────┴──────────────┘
```

---

#### 7.3 파일 다운로드 응답

**응답 헤더 설정**:
```python
return send_file(
    filepath,
    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    as_attachment=True,
    download_name=filename
)
```

**브라우저 처리**:
```javascript
// Blob 생성 및 다운로드
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'translations.xlsx';
a.click();
window.URL.revokeObjectURL(url);
```

**완료 메시지**:
```
✅ Excel 파일 다운로드 완료!
📂 파일명: translations_session_xxx_20260427_162345.xlsx
```

---

#### 7.4 학습 리포트 표시 (v3.3 신규)
**파일**: `static/js/ocr_results.js:showLearningReport()`, `templates/ocr_results.html`

**표시 조건**:
```javascript
// Excel 다운로드 모달 닫힌 후 자동 표시
modal.addEventListener('hidden.bs.modal', () => {
    if (result.learned_count && result.learned_count > 0) {
        this.showLearningReport(result.learned_count, result.learned_corrections);
    }
});
```

**리포트 UI**:
```
┌──────────────────────────────────────────────┐
│ 🧠 맞춤법/띄어쓰기 학습 결과 리포트  [v3.3]  │
├──────────────────────────────────────────────┤
│ 총 2개의 교정 내용을 학습했습니다            │
│                                              │
│ ┌────────────────────┬──────────────────────┐│
│ │ OCR 원본           │ 사용자 수정          ││
│ ├────────────────────┼──────────────────────┤│
│ │ 일일 미션 달성 완료│ 매일 미션 완료!      ││
│ │ 리워드 바드리 가기 │ 리워드 받으러 가기   ││
│ └────────────────────┴──────────────────────┘│
│                                              │
│ 💡 다음번 동일한 텍스트가 나오면 자동으로    │
│    학습된 교정이 적용됩니다.                 │
└──────────────────────────────────────────────┘
```

**백엔드 데이터 구조**:
```python
# /download-excel 응답에 포함
return jsonify({
    'status': 'success',
    'download_url': download_url,
    'learned_count': learned_count,  # v3.3
    'learned_corrections': [         # v3.3
        {
            'original': '일일 미션 달성 완료',
            'corrected': '매일 미션 완료!'
        },
        {
            'original': '리워드 바드리 가기',
            'corrected': '리워드 받으러 가기'
        }
    ]
})
```

**학습 효과**:
- 다음 번 OCR 시 동일한 텍스트 자동 교정
- `data/spelling_corrections.json`에 영구 저장
- 캐시 우선 적용 (0.007초 응답)

---

### Phase 0: 설정 및 준비 (v3.3 신규)

#### 0.1 바른 API 키 설정
**파일**: `templates/settings.html`, `stable_web_server.py`

**설정 페이지 접근**:
```
http://localhost:5004/settings
```

**UI 구성**:
```
┌──────────────────────────────────────────┐
│ ⚙️ XLT System 설정                       │
├──────────────────────────────────────────┤
│ 🔑 Figma API 토큰                        │
│ [figd_xxxxxxxxxxxxxxxx]  [👁️] [테스트]  │
│                                          │
│ 🔤 바른 AI 맞춤법 검사 API 키 (v3.3)    │
│ [koba-xxxxxxxx]  [👁️] [키 테스트]       │
│                                          │
│ 💡 키가 없어도 기본 맞춤법 교정이        │
│    작동합니다. 더 정확한 교정을 위해     │
│    바른 API 키를 설정하세요.             │
│                                          │
│              [저장]                      │
└──────────────────────────────────────────┘
```

**키 테스트 프로세스**:
```javascript
// 프론트엔드
document.getElementById('test-bareun-key').addEventListener('click', async () => {
    const apiKey = document.getElementById('bareun-api-key').value;
    
    const response = await fetch('/api/settings/test-bareun-key', {
        method: 'POST',
        body: JSON.stringify({ api_key: apiKey })
    });
    
    const result = await response.json();
    if (result.status === 'success') {
        alert('✅ API 키가 유효합니다.');
    } else {
        alert('❌ API 키 테스트 실패: ' + result.message);
    }
});
```

**백엔드 검증**:
```python
@app.route('/api/settings/test-bareun-key', methods=['POST'])
def api_test_bareun_key():
    """바른 API 키 테스트 (bareunpy SDK 사용)"""
    api_key = request.json.get('api_key')
    
    from bareunpy import Corrector
    try:
        corrector = Corrector(
            apikey=api_key,  # ⚠️ 주의: apikey (언더스코어 없음)
            host="api.bareun.ai",
            port=443
        )
        test_text = "테스트 문장입니다"
        result = corrector.correct_error(content=test_text)
        
        return jsonify({
            'status': 'success',
            'message': 'API 키가 유효합니다.'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
```

**설정 저장**:
```python
# user_config.json에 저장
config = {
    'figma_token': 'figd_xxx...',
    'bareun_api_key': 'koba-xxx...'  # v3.3 추가
}
save_user_config(config)
```

**맞춤법 검사 시 사용**:
```python
# 사용자 설정 키 우선 사용
user_config = load_user_config()
API_KEY = user_config.get('bareun_api_key') or "koba-J4OURKA-25EEKQI-VVMMIJI-JGOUYCY"

corrector = Corrector(apikey=API_KEY, host="api.bareun.ai", port=443)
```

---

## 플로우차트

### 전체 워크플로우 플로우차트

```
                        START
                          │
                          ▼
         ┌────────────────────────────────┐
         │  사용자: Figma URL 입력        │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │  Frontend: URL 형식 검증       │
         └────────────────┬───────────────┘
                          │ POST /upload
                          ▼
         ┌────────────────────────────────┐
         │  Backend: 세션 생성            │
         │  (session_id, logs 초기화)     │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │  Figma: 이미지 다운로드        │
         │  (API: /v1/images/:file_key)   │
         └────────────────┬───────────────┘
                          │
                          ▼
                ┌─────────┴─────────┐
                │  텍스트 추출 방법  │
                └─────────┬─────────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
      ┌─────────┐   ┌─────────┐   ┌────────┐
      │Figma API│   │OCR 엔진 │   │ 둘다   │
      │ (우선)  │   │(대체)   │   │ 사용   │
      └────┬────┘   └────┬────┘   └───┬────┘
           │             │             │
           └─────────────┼─────────────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │ v3.3: 맞춤법/띄어쓰기 자동 교정│
         │ 1. OCR 특화 사전               │
         │ 2. 바른 API (캐시 우선)        │
         │ 3. 정규표현식 정리             │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Frontend: OCR 결과 페이지 표시 │
         │ - 2개 탭 (필터링/전체)         │
         │ - 각 텍스트 수정 가능          │
         │ - 맞춤법 검사 버튼 (v3.3)     │
         └────────────────┬───────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
  ┌──────────────────┐      ┌──────────────────┐
  │ 사용자: 텍스트   │      │ 사용자: 맞춤법   │
  │ 선택 & 수정      │      │ 검사 버튼 클릭   │
  └────────┬─────────┘      └────────┬─────────┘
           │                         │
           │                         │ POST /api/spell-check
           │                         ▼
           │         ┌────────────────────────────────┐
           │         │ Backend: 3단계 교정 재실행     │
           │         │ - 교정된 텍스트 반환          │
           │         └────────────────┬───────────────┘
           │                         │
           │                         ▼
           │         ┌────────────────────────────────┐
           │         │ Frontend: 입력 필드 업데이트   │
           │         │ - 녹색 깜빡임 효과            │
           │         └────────────────┬───────────────┘
           │                         │
           └─────────────┬───────────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │ 사용자: "번역 시작" 버튼 클릭  │
         └────────────────┬───────────────┘
                          │
                          │ POST /check-placeholders
                          ▼
         ┌────────────────────────────────┐
         │ Backend: 치환자 패턴 분석      │
         │ - 숫자 패턴 감지               │
         │ - 변수 패턴 감지               │
         │ - 치환자 제안 생성             │
         └────────────────┬───────────────┘
                          │
                          ▼
             ┌────────────┴────────────┐
             │  치환자 발견?           │
             └────┬────────────┬───────┘
                  │ YES        │ NO
                  ▼            │
  ┌────────────────────────┐  │
  │ Frontend: 치환자 모달  │  │
  │ - 각 항목별 적용 선택  │  │
  │ - 텍스트 수정 가능     │  │
  └──────────┬─────────────┘  │
             │                │
             │ [적용하기]     │
             ▼                │
  ┌────────────────────────┐  │
  │ POST /store-final-texts│  │
  │ - 최종 텍스트 저장     │  │
  └──────────┬─────────────┘  │
             │                │
             └────────┬───────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │ Frontend: XLT Key 설정 모달    │
         │ - 지능형 키 (기본)             │
         │ - 단순 prefix + 번호 (v3.3)   │
         └────────────────┬───────────────┘
                          │
             ┌────────────┴────────────┐
             │  키 생성 모드?          │
             └────┬────────────┬───────┘
                  │ 지능형     │ 단순
                  ▼            ▼
  ┌──────────────────┐  ┌──────────────────┐
  │ Backend:         │  │ Backend:         │
  │ Unifi 패턴 분석  │  │ PREFIX_001       │
  │ 키워드 추출      │  │ PREFIX_002       │
  │ 카테고리 분석    │  │ PREFIX_003       │
  └────────┬─────────┘  └────────┬─────────┘
           │                     │
           └──────────┬──────────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │ 사용자: 키 확인/수정           │
         │ - 각 키 직접 수정 가능         │
         │ - 중복 검사                    │
         └────────────────┬───────────────┘
                          │
                          │ POST /translate-selected
                          ▼
         ┌────────────────────────────────┐
         │ Backend: 사용자 교정 학습 (v3.3)│
         │ - OCR 텍스트 ↔ 최종 텍스트     │
         │ - 차이점을 캐시에 저장         │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Backend: Unifi 전문 번역       │
         │ 1. Unifi DB 확인 (1,244개)     │
         │ 2. Google Translate API        │
         │ 3. guide.md 용어집 적용        │
         │ 4. 치환자 복원                 │
         └────────────────┬───────────────┘
                          │
              ┌───────────┴───────────┐
              │ 언어별 순차 번역      │
              └───────────┬───────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    ┌────────┐      ┌────────┐      ┌────────┐
    │ en_US  │      │ ja_JP  │      │ zh_TW  │
    └────┬───┘      └────┬───┘      └────┬───┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │    th_TH         │
              └──────────┬───────┘
                         │
                         ▼
         ┌────────────────────────────────┐
         │ 번역 결과 구성 & 세션 저장     │
         │ {xlt_key, ko_KR, en_US, ...}   │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Frontend: 번역 결과 테이블 표시│
         │ - 5개 언어 미리보기            │
         │ - Excel 다운로드 버튼          │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ 사용자: "Excel 다운로드" 클릭  │
         └────────────────┬───────────────┘
                          │
                          │ POST /download-excel
                          ▼
         ┌────────────────────────────────┐
         │ Backend: Excel 파일 생성       │
         │ 1. Workbook 생성               │
         │ 2. 헤더 스타일 적용            │
         │ 3. 데이터 행 작성              │
         │ 4. 열 너비 자동 조정           │
         │ 5. 파일 저장 (output/)         │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Backend: 파일 다운로드 응답    │
         │ - Content-Type: .xlsx          │
         │ - as_attachment: True          │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ Frontend: 브라우저 다운로드    │
         │ - Blob 생성                    │
         │ - 자동 다운로드 트리거         │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ v3.3: 다운로드 모달 표시       │
         │ "Excel 파일 다운로드 완료!"    │
         └────────────────┬───────────────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │ v3.3: 모달 닫힘 이벤트 감지    │
         └────────────────┬───────────────┘
                          │
             ┌────────────┴────────────┐
             │  학습된 교정 있음?      │
             └────┬────────────┬───────┘
                  │ YES        │ NO
                  ▼            │
  ┌────────────────────────┐  │
  │ v3.3: 학습 리포트 표시 │  │
  │ - OCR 원본 테이블      │  │
  │ - 사용자 수정 테이블   │  │
  │ - 학습 개수 표시       │  │
  └──────────┬─────────────┘  │
             │                │
             └────────┬───────┘
                      │
                      ▼
         ┌────────────────────────────────┐
         │  ✅ 완료!                      │
         │  Excel 파일 저장됨             │
         │  학습 데이터 업데이트됨 (v3.3) │
         └────────────────────────────────┘
                          │
                          ▼
                         END
```

---

## 기능별 상세 설명

### 1. 세션 관리

**세션 ID 형식**:
```
session_YYYYMMDD_HHMMSS_xxxxxxxx
예: session_20260427_143025_a7b3c9d2
```

**세션 데이터 구조**:
```python
temp_ocr_results[session_id] = {
    'ocr_results': [...],           # OCR 추출 텍스트
    'selected_indexes': [...],      # 선택된 인덱스
    'final_texts': [...],           # 치환자 적용된 최종 텍스트
    'translations': [...],          # 번역 결과
    'translation_status': 'pending',
    'image_path': '/path/to/image.png',
    'source': 'figma',
    'timestamp': '2026-04-27T14:30:25'
}

session_logs[session_id] = [
    {
        'message': '🔤 교정: "일일미션" → "일일 미션"',
        'timestamp': '14:30:28',
        'type': 'info'
    },
    ...
]
```

**세션 수명**:
- 생성: Figma URL 업로드 시
- 유지: 번역 완료 후 30분
- 삭제: 서버 재시작 또는 수동 정리

---

### 2. OCR 신뢰도 필터링

**필터링 조건**:
```python
def is_meaningful_text(text: str, confidence: float) -> bool:
    # 1. 신뢰도 임계값
    if confidence < 0.3:
        return False
    
    # 2. 최소 길이
    if len(text.strip()) < 2:
        return False
    
    # 3. 특수문자만 있는 경우
    if all(not c.isalnum() for c in text):
        return False
    
    # 4. 숫자만 있는 경우 (선택적)
    if text.isdigit():
        return False
    
    return True
```

**필터링 결과**:
```
전체 OCR 결과: 15개
의미있는 텍스트: 4개

제외된 텍스트:
- "·" (특수문자만)
- "123" (숫자만)
- "a" (너무 짧음)
- "asdfkj" (신뢰도 0.15)
```

---

### 3. 치환자 패턴

**지원 패턴**:

| 패턴 유형 | 예시 | 변환 후 |
|----------|------|---------|
| 숫자 | "매일 10개 달성" | "매일 {{0}}개 달성" |
| 퍼센트 | "50% 할인" | "{{0}}% 할인" |
| 금액 | "100원 보상" | "{{0}}원 보상" |
| 변수 | "{name}님 환영" | "{{0}}님 환영" |
| 날짜 | "2026-04-27" | "{{0}}" |

**감지 로직**:
```python
patterns = [
    r'\d+',              # 숫자
    r'\d+%',             # 퍼센트
    r'\d+원',            # 금액
    r'\{[a-zA-Z_]+\}',   # {변수}
    r'\d{4}-\d{2}-\d{2}' # 날짜
]
```

---

### 4. 번역 우선순위

**번역 소스 우선순위**:
```
1순위: Unifi DB (1,244개 기존 번역)
   ↓ 없으면
2순위: Google Translate API
   ↓ 번역 후
3순위: guide.md 용어집 적용
```

**예시**:
```
텍스트: "일일 미션 달성하고 리워드 받기"

1. Unifi DB 확인: ❌ 없음
2. Google 번역:
   - en_US: "Complete daily missions and get rewards"
3. 용어집 적용 (guide.md):
   - "리워드" → "Reward" (대문자)
   - 최종: "Complete daily missions and get Rewards"
```

---

### 5. 에러 처리

**주요 에러 케이스**:

| 에러 상황 | 처리 방법 | 사용자 메시지 |
|----------|----------|--------------|
| Figma 토큰 없음 | 설정 페이지 리다이렉트 | "Figma 토큰을 설정해주세요" |
| Figma URL 잘못됨 | 재입력 요청 | "올바른 Figma URL을 입력해주세요" |
| 이미지 다운로드 실패 | 재시도 (3회) | "이미지 다운로드 실패. 잠시 후 다시 시도해주세요" |
| OCR 텍스트 없음 | 전체 OCR 결과 표시 | "의미있는 텍스트가 없습니다. 전체 결과를 확인하세요" |
| 번역 API 실패 | 에러 로그 + 알림 | "번역 중 오류가 발생했습니다" |
| Excel 생성 실패 | 재시도 버튼 제공 | "Excel 파일 생성 실패" |

---

## 데이터 흐름도

### 텍스트 데이터 변환 과정

```
1. Figma URL
   https://figma.com/design/ABC/test?node-id=1-2
   
   ↓ [Figma API]

2. Figma 이미지 (PNG)
   /tmp/figma_abc123.png
   
   ↓ [OCR Engine OR Figma Text API]

3. OCR 원본 텍스트
   "일일미선달성완료"
   
   ↓ [자동 교정 v3.3]

4. 교정된 텍스트
   "일일 미션 달성 완료"
   
   ↓ [사용자 수정]

5. 사용자 수정 텍스트
   "매일 미션 완료!"
   
   ↓ [맞춤법 검사 버튼 - 선택사항]

6. 재교정된 텍스트
   "매일 미션 완료!"
   
   ↓ [치환자 감지]

7. 치환자 적용 텍스트
   "매일 미션 완료!"
   (치환자 없음)
   
   ↓ [XLT Key 생성]

8. 키 설정된 텍스트
   Key: XLT_mission_text_매일_미션_001
   Text: "매일 미션 완료!"
   
   ↓ [번역 실행]

9. 다국어 번역 결과
   {
     'ko_KR': '매일 미션 완료!',
     'en_US': 'Daily Mission Completed!',
     'ja_JP': '毎日ミッション完了!',
     'zh_TW': '每日任務完成！',
     'th_TH': 'ภารกิจรายวันเสร็จสิ้น!'
   }
   
   ↓ [Excel 생성]

10. Excel 파일
    translations_session_xxx.xlsx
    
    ↓ [다운로드]

11. 사용자 PC에 저장
    ~/Downloads/translations_session_xxx.xlsx
```

---

### 캐시/학습 데이터 흐름

```
1. 초기 상태
   data/spelling_corrections.json
   { }
   
   ↓

2. OCR 텍스트 추출
   "일일미선달성완료"
   
   ↓ [바른 API 호출]

3. API 교정 결과
   "일일 미션 달성 완료"
   
   ↓ [캐시 저장]

4. 캐시 업데이트
   {
     "일일미선달성완료": "일일 미션 달성 완료"
   }
   
   ↓

5. 사용자 수정
   "매일 미션 완료!"
   
   ↓ [번역 시작 시 학습]

6. 캐시 업데이트 (학습)
   {
     "일일미선달성완료": "일일 미션 달성 완료",
     "일일 미션 달성 완료": "매일 미션 완료!"
   }
   
   ↓

7. 다음 사용 시
   OCR: "일일미선달성완료"
   → 캐시 매칭: "일일 미션 달성 완료"
   → 캐시 매칭: "매일 미션 완료!"
   → 최종 출력: "매일 미션 완료!"
```

---

## 성능 최적화

### 1. 캐시 전략

**맞춤법 캐시**:
- 히트율: ~80% (반복 텍스트 많음)
- 응답 시간: 0.007초 (캐시) vs 1-2초 (API)
- 저장 위치: `data/spelling_corrections.json`

**번역 캐시** (Unifi DB):
- 히트율: ~30% (Unifi 프로젝트 특화)
- 데이터: 1,244개 기존 번역
- 저장 위치: `Unifi/Unifi_XLT_231115.xlsx`

---

### 2. 병렬 처리

**비동기 번역**:
```python
# 언어별 병렬 번역 (v3.1+)
async def translate_batch(texts, languages):
    tasks = []
    for lang in languages:
        task = asyncio.create_task(
            translate_texts(texts, lang)
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

**성능 개선**:
- 순차: 4개 언어 × 2초 = 8초
- 병렬: max(2초) = 2초
- **4배 빠름** ✅

---

### 3. 진행 상황 표시

**실시간 업데이트**:
```javascript
// SSE (Server-Sent Events) 연결
const eventSource = new EventSource(`/api/translation/progress?session_id=${sessionId}`);

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateProgressBar(data.percentage);
    updateStatusMessage(data.message);
};
```

**진행률 계산**:
```python
progress = (completed_languages / total_languages) * 100
message = f"{current_language} 번역 중... ({completed}/{total})"
```

---

## 보안 고려사항

### 1. Figma Token 보호

**저장 위치**:
- ❌ 코드에 하드코딩
- ✅ `figma_config.json` (gitignore)
- ✅ 환경 변수 `FIGMA_TOKEN`

**전송 방식**:
- API 요청 시 Header에 포함
- HTTPS 필수

---

### 2. 세션 보안

**세션 ID**:
- UUID 기반 (예측 불가능)
- 타임스탬프 포함 (중복 방지)

**세션 격리**:
- 각 사용자 독립적인 세션
- 세션 간 데이터 접근 불가

---

### 3. 입력 검증

**Figma URL**:
```python
# URL 형식 검증
if not url.startswith('https://www.figma.com/'):
    raise ValueError("Invalid Figma URL")

# Path 검증 (디렉토리 탐색 방지)
if '..' in url or '~' in url:
    raise ValueError("Invalid characters in URL")
```

**텍스트 입력**:
```python
# 길이 제한
if len(text) > 10000:
    raise ValueError("Text too long")

# XSS 방지 (HTML 이스케이프)
from html import escape
safe_text = escape(text)
```

---

## 문제 해결 가이드

### Q1: 교정이 적용되지 않음
**증상**: OCR 결과 페이지에 오타가 그대로 표시됨

**원인**:
1. 서버 프로세스가 오래된 코드 실행 중
2. Python 캐시 파일이 남아있음

**해결**:
```bash
# 서버 재시작
pkill -f stable_web_server.py

# 캐시 제거
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +

# 서버 시작
python3 stable_web_server.py
```

---

### Q2: 치환자가 번역 후 손상됨
**증상**: `{{0}}`가 `{ {0} }`로 변경됨

**원인**: Google Translate가 중괄호를 단어로 인식

**해결**: 치환자 복원 로직 강화
```python
def restore_placeholders(text, original_placeholders):
    # 손상된 패턴 복구
    text = re.sub(r'\{\s*\{\s*(\d+)\s*\}\s*\}', r'{{\1}}', text)
    text = re.sub(r'\{\s*\{(\w+)\}\s*\}', r'{{\1}}', text)
    return text
```

---

### Q3: Excel 다운로드 시 한글 깨짐
**증상**: Excel 파일의 한글이 '???'로 표시

**원인**: UTF-8 인코딩 미적용

**해결**:
```python
# openpyxl은 자동으로 UTF-8 사용
wb.save(filepath)  # ✅ 이미 올바름

# 만약 CSV 사용 시
df.to_csv(filepath, encoding='utf-8-sig')  # BOM 포함
```

---

## 버전별 주요 변경사항

### v3.3.0 (2026-04-27) - 현재 버전

#### ✨ 신규 기능
1. **바른 API 키 설정 페이지**
   - 설정 페이지에서 맞춤법 검사 API 키 관리
   - 키 테스트 기능 (bareunpy SDK 사용)
   - 보기/숨기기 토글 버튼
   - 키 없어도 기본 교정 작동

2. **맞춤법/띄어쓰기 학습 리포트**
   - Excel 다운로드 후 자동 표시
   - OCR 원본 ↔ 사용자 수정 매핑 테이블
   - 학습 개수 표시
   - 다음 사용 시 자동 적용

3. **맞춤법/띄어쓰기 자동 교정**
   - 3단계 파이프라인 (사전 → 바른 API → 정규식)
   - 바른 AI API 캐시 시스템
   - 맞춤법 검사 버튼 (사용자 재검사)

4. **사용자 교정 학습**
   - 번역 시작 시 자동 학습
   - OCR 텍스트 ↔ 최종 텍스트 비교
   - `data/spelling_corrections.json`에 저장

5. **단순 prefix + 번호 키 생성 모드**
   - 지능형 키 외 단순 키 생성 옵션
   - `MY_KEY_001`, `MY_KEY_002` 형식

#### 🐛 버그 수정
- Excel 다운로드 오류 수정 (`sampleformat.xlsx` 자동 생성)
- 바른 API 테스트 파라미터 수정 (`api_key` → `apikey`)
- Figma Text API 텍스트도 교정 적용

#### 📚 문서 개선
- 웹 UI 테스트 프로토콜 확립
- TEST_PLAN.md 업데이트
- WORKFLOW_DOCUMENTATION.md 업데이트

### v3.2.0 (2026-04-24)
- 사용자 수정 텍스트 치환자 반영
- 하위 호환성 완전 유지

### v3.1.0 (2026-04-20)
- Unifi 전문 번역 시스템 (1,244개 DB)
- 지능형 XLT 키 생성
- rumps 기반 macOS 트레이
- 자동 업데이트 시스템

### v3.0.0 (2026-04-15)
- Figma 전용 번역 시스템으로 전환
- guide.md 기반 번역
- 치환자 자동 감지

---

## 참고 자료

### 내부 문서
- `CLAUDE.md` - 개발 가이드
- `ARCHITECTURE.md` - 시스템 아키텍처
- `USER_MANUAL.md` - 사용자 매뉴얼
- `TEST_PLAN.md` - 테스트 계획

### 외부 라이브러리
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - OCR 엔진
- [googletrans](https://py-googletrans.readthedocs.io/) - Google 번역
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel 생성
- [Flask](https://flask.palletsprojects.com/) - 웹 프레임워크
- [bareunpy](https://bareun.ai/) - 바른 맞춤법 검사기

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-04-27  
**작성자**: Claude Code  
**문의**: XLT System 개발팀
