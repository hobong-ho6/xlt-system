"""
Claude AI 검증용 전문 프롬프트 시스템

엑셀 검증의 모든 과정을 Claude AI로 처리하기 위한 프롬프트 템플릿 관리
"""

class ClaudePrompts:
    """Claude AI 엑셀 검증용 프롬프트 관리자"""

    def __init__(self):
        """초기화"""
        self._prompt_manager = None

    def _get_prompt_manager(self):
        """프롬프트 매니저 싱글톤 인스턴스 반환"""
        if self._prompt_manager is None:
            try:
                from ..core.prompt_manager import get_prompt_manager
                self._prompt_manager = get_prompt_manager()
            except Exception as e:
                print(f"⚠️ 프롬프트 매니저 로드 실패: {e}")
                self._prompt_manager = None
        return self._prompt_manager

    def _get_custom_prompt(self, prompt_type: str, fallback_prompt: str = "") -> str:
        """사용자 정의 프롬프트 조회 (실패 시 fallback 사용)"""
        try:
            prompt_manager = self._get_prompt_manager()
            if prompt_manager:
                custom_prompt = prompt_manager.get_prompt(prompt_type)
                if custom_prompt:
                    return custom_prompt
        except Exception as e:
            print(f"⚠️ 사용자 정의 프롬프트 로드 실패 ({prompt_type}): {e}")

        return fallback_prompt

    def get_spelling_validation_prompt(self, korean_texts: list, key_ids: list = None) -> str:
        """한글 맞춤법/띄어쓰기 검증 프롬프트"""
        text_list = ""
        for i, text in enumerate(korean_texts):
            key_id = key_ids[i] if key_ids and i < len(key_ids) else f"item_{i+1}"
            text_list += f"{i+1}. [{key_id}] {text}\n"

        # 사용자 정의 프롬프트 조회
        custom_template = self._get_custom_prompt('excel_validation_spelling', '')

        if custom_template:
            try:
                return custom_template.format(text_list=text_list)
            except Exception as e:
                print(f"❌ 맞춤법 검증 프롬프트 포맷팅 오류: {e}")

        # Fallback: 기본 프롬프트
        return f"""다음 한글 텍스트들의 맞춤법과 띄어쓰기를 검증해주세요.

텍스트 목록:
{text_list}

각 텍스트에 대해 다음 형식으로 응답해주세요:

```json
{{
    "results": [
        {{
            "index": 1,
            "original_text": "원본 텍스트",
            "is_correct": true/false,
            "errors": [
                {{
                    "type": "맞춤법" 또는 "띄어쓰기",
                    "error": "오류 내용",
                    "suggestion": "수정 제안"
                }}
            ]
        }}
    ]
}}
```

UI/UX 용어, 기술 용어, 금융 용어는 일반적인 표기를 따르되, 명백한 오타나 띄어쓰기 오류만 지적해주세요."""

    def get_terminology_validation_prompt(self, korean_texts: list, terminology_data: dict, key_ids: list = None) -> str:
        """한글 용어집 비교 검증 프롬프트"""
        text_list = ""
        for i, text in enumerate(korean_texts):
            key_id = key_ids[i] if key_ids and i < len(key_ids) else f"item_{i+1}"
            text_list += f"{i+1}. [{key_id}] {text}\n"

        # 용어집 데이터를 문자열로 변환
        terms_str = ""
        if terminology_data:
            for term_id, term_data in terminology_data.items():
                korean_term = term_data.get('ko_KR', '')
                if korean_term:
                    terms_str += f"- {korean_term}\n"

        # 사용자 정의 프롬프트 조회
        custom_template = self._get_custom_prompt('excel_validation_terminology', '')

        if custom_template:
            try:
                return custom_template.format(
                    text_list=text_list,
                    terminology_data=terms_str
                )
            except Exception as e:
                print(f"❌ 용어집 검증 프롬프트 포맷팅 오류: {e}")

        # Fallback: 기본 프롬프트
        return f"""다음 한글 텍스트들을 제공된 용어집과 비교하여 용어 일관성을 검증해주세요.

검증할 텍스트:
{text_list}

참고 용어집:
{terms_str}

각 텍스트에 대해 다음 형식으로 응답해주세요:

```json
{{
    "results": [
        {{
            "index": 1,
            "original_text": "원본 텍스트",
            "has_terminology_issue": true/false,
            "is_exception": false,
            "exception_reason": "exceptional 항목인 경우 사유",
            "issues": [
                {{
                    "wrong_term": "잘못 사용된 용어",
                    "suggested_term": "올바른 용어 (용어집 기준)",
                    "reason": "문제 설명"
                }}
            ]
        }}
    ]
}}
```

용어집에 있는 표준 용어와 다른 표현이 사용된 경우 지적해주세요. 만약 exceptional 항목으로 검증을 통과시키는 경우 is_exception을 true로 설정하고 사유를 명시하세요."""

    @staticmethod
    def get_language_detection_prompt(texts_by_column: dict) -> str:
        """언어 감지 및 일치성 검증 프롬프트"""
        columns_info = ""
        for col_name, texts in texts_by_column.items():
            sample_texts = texts[:3]  # 처음 3개만 샘플로 보여줌
            columns_info += f"\n{col_name} 열:\n"
            for i, text in enumerate(sample_texts, 1):
                columns_info += f"  {i}. {text}\n"

        return f"""다음 엑셀 열들의 텍스트가 해당 언어에 맞는지 검증해주세요.

열별 샘플 텍스트:
{columns_info}

각 열에 대해 다음 형식으로 응답해주세요:

```json
{{
    "results": [
        {{
            "column": "en_US",
            "expected_language": "영어",
            "detected_issues": [
                {{
                    "text": "문제가 있는 텍스트",
                    "detected_language": "감지된 언어",
                    "issue": "문제 설명",
                    "row_hint": "몇 번째 샘플인지"
                }}
            ]
        }}
    ]
}}
```

언어 코드와 실제 텍스트 언어가 일치하지 않는 경우를 찾아주세요:
- en_US: 영어
- ko_KR: 한국어
- ja_JP: 일본어
- zh_TW: 중국어(번체)
- th_TH: 태국어"""

    @staticmethod
    def get_multilingual_terminology_prompt(texts_by_language: dict, terminology_data: dict) -> str:
        """다국어 용어집 비교 검증 프롬프트"""
        languages_info = ""
        for lang, texts in texts_by_language.items():
            sample_texts = texts[:3]
            languages_info += f"\n{lang}:\n"
            for i, text in enumerate(sample_texts, 1):
                languages_info += f"  {i}. {text}\n"

        # 용어집에서 다국어 용어 추출
        terms_by_lang = {}
        if terminology_data:
            for term_id, term_data in terminology_data.items():
                for lang in ['en_US', 'ko_KR', 'ja_JP', 'zh_TW', 'th_TH']:
                    if lang in term_data and term_data[lang]:
                        if lang not in terms_by_lang:
                            terms_by_lang[lang] = []
                        terms_by_lang[lang].append(term_data[lang])

        terms_info = ""
        for lang, terms in terms_by_lang.items():
            terms_info += f"\n{lang} 표준 용어:\n"
            for term in terms[:10]:  # 처음 10개만
                terms_info += f"  - {term}\n"

        return f"""다음 다국어 텍스트들을 용어집과 비교하여 용어 일관성을 검증해주세요.

검증할 텍스트 (언어별 샘플):
{languages_info}

참고 용어집:
{terms_info}

각 언어별로 다음 형식으로 응답해주세요:

```json
{{
    "results": [
        {{
            "language": "en_US",
            "issues": [
                {{
                    "text": "문제가 있는 텍스트",
                    "wrong_term": "잘못된 용어",
                    "suggested_term": "표준 용어",
                    "issue_type": "오역" 또는 "용어 불일치"
                }}
            ]
        }}
    ]
}}
```

각 언어에서 표준 용어집과 다른 용어가 사용되었거나 오역으로 보이는 경우를 찾아주세요."""

    @staticmethod
    def get_completeness_validation_prompt(completeness_data: list) -> str:
        """빈 행 및 데이터 완성도 검증 프롬프트"""
        # 데이터 샘플 생성 (처음 5행)
        sample_data = "행별 데이터 샘플:\n"
        for i, (key_id, row_data) in enumerate(excel_data.items()):
            if i >= 5:  # 처음 5개만
                break
            sample_data += f"행 {i+1} (Key: {key_id}):\n"
            for lang, text in row_data.items():
                empty_status = "비어있음" if not text or str(text).strip() == "" else "있음"
                sample_data += f"  {lang}: {empty_status} - {text if text else 'N/A'}\n"
            sample_data += "\n"

        return f"""다음 엑셀 데이터의 완성도를 검증해주세요.

{sample_data}

총 {len(excel_data)}개 행이 있습니다.

다음 형식으로 응답해주세요:

```json
{{
    "summary": {{
        "total_rows": {len(excel_data)},
        "missing_key_ids": 0,
        "missing_korean": 0,
        "missing_translations": 0,
        "duplicate_keys": 0
    }},
    "issues": [
        {{
            "row_number": 1,
            "key_id": "XLT_key_001",
            "issue_type": "빈 필드" 또는 "중복 키" 또는 "필수 필드 누락",
            "missing_languages": ["en_US", "ja_JP"],
            "description": "문제 설명"
        }}
    ]
}}
```

다음 사항들을 검증해주세요:
1. Key ID가 비어있는 행
2. ko_KR (한국어)가 비어있는 행 - 필수 필드
3. 번역이 누락된 언어들
4. 중복된 Key ID
5. 전체적인 데이터 완성도"""

    def get_auto_correction_prompt(self, korean_text: str, terminology_data: dict, target_languages: list) -> str:
        """Claude AI 자동 교정 프롬프트"""
        # 용어집 참고 데이터 생성
        terms_context = ""
        if terminology_data:
            terms_context = "참고 용어집:\n"
            for term_id, term_data in terminology_data.items():
                korean_term = term_data.get('ko_KR', '')
                if korean_term:
                    terms_context += f"- 한국어: {korean_term}\n"
                    for lang in target_languages:
                        if lang in term_data and term_data[lang]:
                            terms_context += f"  {lang}: {term_data[lang]}\n"
                    terms_context += "\n"

        target_langs_str = ", ".join(target_languages)

        # 사용자 정의 프롬프트 조회
        custom_template = self._get_custom_prompt('excel_auto_correction', '')

        if custom_template:
            try:
                return custom_template.format(
                    korean_text=korean_text,
                    target_languages=target_langs_str,
                    terminology_context=terms_context
                )
            except Exception as e:
                print(f"❌ 자동 교정 프롬프트 포맷팅 오류: {e}")

        # Fallback: 기본 프롬프트
        return f"""다음 한국어 텍스트를 {target_langs_str}로 정확하게 번역해주세요.

원문 (한국어): {korean_text}

{terms_context}

요구사항:
1. 용어집의 표준 용어를 우선적으로 사용하세요
2. 각 언어의 자연스러운 표현을 사용하세요
3. UI/UX, 금융, 기술 용어는 해당 분야의 표준 용어를 사용하세요
4. 일관된 톤앤매너를 유지하세요

다음 형식으로 응답해주세요:

```json
{{
    "original": "{korean_text}",
    "translations": {{
        "en_US": "영어 번역",
        "ja_JP": "일본어 번역",
        "zh_TW": "중국어(번체) 번역",
        "th_TH": "태국어 번역"
    }},
    "used_terminology": [
        {{
            "korean_term": "사용된 한국어 용어",
            "translations": {{
                "en_US": "영어 용어",
                "ja_JP": "일본어 용어"
            }}
        }}
    ]
}}
```"""

    @staticmethod
    def get_correction_validation_prompt(original_data: dict, corrected_data: dict) -> str:
        """교정 결과 검증 프롬프트"""
        comparison = "교정 전후 비교:\n\n"

        for key_id, original_row in original_data.items():
            if key_id in corrected_data:
                corrected_row = corrected_data[key_id]
                comparison += f"Key: {key_id}\n"

                for lang in ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']:
                    original_text = original_row.get(lang, '')
                    corrected_text = corrected_row.get(lang, '')

                    if original_text != corrected_text:
                        comparison += f"  {lang}:\n"
                        comparison += f"    교정 전: {original_text}\n"
                        comparison += f"    교정 후: {corrected_text}\n"
                comparison += "\n"

        return f"""교정된 번역 결과를 검증해주세요.

{comparison}

다음 형식으로 응답해주세요:

```json
{{
    "validation_result": {{
        "overall_quality": "우수" 또는 "양호" 또는 "개선 필요",
        "improvements_made": 5,
        "remaining_issues": 1
    }},
    "detailed_feedback": [
        {{
            "key_id": "XLT_key_001",
            "language": "en_US",
            "feedback": "교정 결과에 대한 평가",
            "quality_score": 95,
            "still_has_issues": false
        }}
    ]
}}
```

교정의 품질, 용어 일관성, 자연스러움을 종합적으로 평가해주세요."""