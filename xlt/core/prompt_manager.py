"""
Claude AI 프롬프트 관리 시스템

사용자가 각 기능별 Claude 프롬프트를 편집하고 관리할 수 있는 시스템
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptManager:
    """Claude AI 프롬프트 관리자"""

    def __init__(self):
        """초기화"""
        self.config_dir = Path(__file__).parent.parent.parent
        self.prompts_file = self.config_dir / "claude_prompts_config.json"

        # 기본 프롬프트 정의
        self.default_prompts = self._get_default_prompts()

        # 설정 파일이 없으면 기본값으로 생성
        if not self.prompts_file.exists():
            self.save_prompts(self.default_prompts)
            logger.info(f"✅ 기본 프롬프트 설정 파일 생성: {self.prompts_file}")

        logger.info("✅ PromptManager 초기화 완료")

    def _get_default_prompts(self) -> Dict[str, Any]:
        """기본 프롬프트 정의"""
        return {
            "figma_translation": {
                "name": "피그마 번역 프롬프트",
                "description": "피그마에서 추출한 텍스트를 다국어로 번역할 때 사용되는 프롬프트",
                "prompt": """다음 텍스트를 {target_languages}로 정확하게 번역해주세요.

원문: {source_text}

요구사항:
1. UI/UX 컨텍스트에 맞는 자연스러운 번역을 해주세요
2. 버튼, 레이블, 메뉴 등의 인터페이스 요소임을 고려해주세요
3. 간결하고 명확한 표현을 사용해주세요
4. 각 언어의 일반적인 UI 표현을 따라주세요
5. 기술 용어는 해당 언어권의 표준 용어를 사용해주세요

다음 JSON 형식으로 응답해주세요:
```json
{{
    "translations": {{
        "en_US": "영어 번역",
        "ja_JP": "일본어 번역",
        "zh_TW": "중국어(번체) 번역",
        "th_TH": "태국어 번역"
    }}
}}
```""",
                "variables": ["source_text", "target_languages"],
                "last_modified": datetime.now().isoformat()
            },

            "excel_translation": {
                "name": "엑셀 번역 프롬프트",
                "description": "엑셀 파일의 텍스트를 일괄 번역할 때 사용되는 프롬프트",
                "prompt": """다음 텍스트들을 {target_languages}로 일괄 번역해주세요.

번역할 텍스트 목록:
{text_list}

요구사항:
1. 각 텍스트의 컨텍스트를 파악하여 적절한 번역을 해주세요
2. 일관성 있는 용어 사용을 유지해주세요
3. 문맥에 맞는 자연스러운 표현을 사용해주세요
4. 전문 용어는 해당 분야의 표준 용어를 사용해주세요

다음 JSON 형식으로 응답해주세요:
```json
{{
    "translations": [
        {{
            "original": "원본 텍스트 1",
            "translations": {{
                "en_US": "영어 번역",
                "ja_JP": "일본어 번역",
                "zh_TW": "중국어(번체) 번역",
                "th_TH": "태국어 번역"
            }}
        }}
    ]
}}
```""",
                "variables": ["text_list", "target_languages"],
                "last_modified": datetime.now().isoformat()
            },

            "excel_validation_spelling": {
                "name": "엑셀 검증 - 맞춤법 검증",
                "description": "한글 텍스트의 맞춤법과 띄어쓰기를 검증하는 프롬프트",
                "prompt": """다음 한글 텍스트들의 맞춤법과 띄어쓰기를 검증해주세요.

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

UI/UX 용어, 기술 용어, 금융 용어는 일반적인 표기를 따르되, 명백한 오타나 띄어쓰기 오류만 지적해주세요.""",
                "variables": ["text_list"],
                "last_modified": datetime.now().isoformat()
            },

            "excel_validation_terminology": {
                "name": "엑셀 검증 - 용어집 검증",
                "description": "한글 텍스트와 용어집을 비교하여 일관성을 검증하는 프롬프트",
                "prompt": """다음 한글 텍스트들을 제공된 용어집과 비교하여 용어 일관성을 검증해주세요.

검증할 텍스트:
{text_list}

참고 용어집:
{terminology_data}

각 텍스트에 대해 다음 형식으로 응답해주세요:

```json
{{
    "results": [
        {{
            "index": 1,
            "original_text": "원본 텍스트",
            "has_terminology_issue": true/false,
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

용어집에 있는 표준 용어와 다른 표현이 사용된 경우 지적해주세요.""",
                "variables": ["text_list", "terminology_data"],
                "last_modified": datetime.now().isoformat()
            },

            "excel_validation_language": {
                "name": "엑셀 검증 - 언어 일치성",
                "description": "각 열의 텍스트가 정의된 언어와 일치하는지 검증하는 프롬프트",
                "prompt": """다음 엑셀 열들의 텍스트가 해당 언어에 맞는지 검증해주세요.

열별 샘플 텍스트:
{texts_by_column}

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

언어 코드와 실제 텍스트 언어가 일치하지 않는 경우를 찾아주세요.""",
                "variables": ["texts_by_column"],
                "last_modified": datetime.now().isoformat()
            },

            "excel_validation_multilingual": {
                "name": "엑셀 검증 - 다국어 용어집",
                "description": "다국어 텍스트와 용어집을 비교하여 오역을 검증하는 프롬프트",
                "prompt": """다음 다국어 텍스트들을 용어집과 비교하여 용어 일관성을 검증해주세요.

검증할 텍스트 (언어별):
{texts_by_language}

참고 용어집:
{terminology_data}

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

각 언어에서 표준 용어집과 다른 용어가 사용되었거나 오역으로 보이는 경우를 찾아주세요.""",
                "variables": ["texts_by_language", "terminology_data"],
                "last_modified": datetime.now().isoformat()
            },

            "excel_validation_completeness": {
                "name": "엑셀 검증 - 데이터 완성도",
                "description": "엑셀 데이터의 빈 필드와 완성도를 검증하는 프롬프트",
                "prompt": """다음 엑셀 데이터의 완성도를 검증해주세요.

{sample_data}

총 {total_rows}개 행이 있습니다.

다음 형식으로 응답해주세요:

```json
{{
    "summary": {{
        "total_rows": {total_rows},
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
5. 전체적인 데이터 완성도""",
                "variables": ["sample_data", "total_rows"],
                "last_modified": datetime.now().isoformat()
            },

            "excel_auto_correction": {
                "name": "엑셀 자동 교정",
                "description": "Claude AI가 텍스트를 자동으로 교정하고 재번역하는 프롬프트",
                "prompt": """다음 한국어 텍스트를 {target_languages}로 정확하게 번역해주세요.

원문 (한국어): {korean_text}

{terminology_context}

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
```""",
                "variables": ["korean_text", "target_languages", "terminology_context"],
                "last_modified": datetime.now().isoformat()
            }
        }

    def load_prompts(self) -> Dict[str, Any]:
        """프롬프트 설정 로드"""
        try:
            if self.prompts_file.exists():
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)

                # 기본 프롬프트와 병합 (새로운 프롬프트가 추가된 경우)
                for key, default_prompt in self.default_prompts.items():
                    if key not in prompts:
                        prompts[key] = default_prompt
                        logger.info(f"📝 새로운 기본 프롬프트 추가: {key}")

                return prompts
            else:
                return self.default_prompts

        except Exception as e:
            logger.error(f"❌ 프롬프트 로드 오류: {e}")
            return self.default_prompts

    def save_prompts(self, prompts: Dict[str, Any]) -> bool:
        """프롬프트 설정 저장"""
        try:
            # 수정 시간 업데이트
            for prompt_data in prompts.values():
                if isinstance(prompt_data, dict):
                    prompt_data['last_modified'] = datetime.now().isoformat()

            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 프롬프트 설정 저장 완료: {self.prompts_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 프롬프트 저장 오류: {e}")
            return False

    def get_prompt(self, prompt_type: str) -> Optional[str]:
        """특정 프롬프트 조회"""
        try:
            prompts = self.load_prompts()
            prompt_data = prompts.get(prompt_type, {})
            return prompt_data.get('prompt', '')
        except Exception as e:
            logger.error(f"❌ 프롬프트 조회 오류 ({prompt_type}): {e}")
            return None

    def update_prompt(self, prompt_type: str, new_prompt: str,
                     name: str = None, description: str = None) -> bool:
        """특정 프롬프트 업데이트"""
        try:
            prompts = self.load_prompts()

            if prompt_type not in prompts:
                logger.error(f"❌ 존재하지 않는 프롬프트 타입: {prompt_type}")
                return False

            # 프롬프트 업데이트
            prompts[prompt_type]['prompt'] = new_prompt
            prompts[prompt_type]['last_modified'] = datetime.now().isoformat()

            if name:
                prompts[prompt_type]['name'] = name
            if description:
                prompts[prompt_type]['description'] = description

            return self.save_prompts(prompts)

        except Exception as e:
            logger.error(f"❌ 프롬프트 업데이트 오류 ({prompt_type}): {e}")
            return False

    def reset_to_default(self, prompt_type: str = None) -> bool:
        """기본 프롬프트로 리셋"""
        try:
            if prompt_type:
                # 특정 프롬프트만 리셋
                if prompt_type not in self.default_prompts:
                    logger.error(f"❌ 존재하지 않는 프롬프트 타입: {prompt_type}")
                    return False

                prompts = self.load_prompts()
                prompts[prompt_type] = self.default_prompts[prompt_type].copy()
                return self.save_prompts(prompts)
            else:
                # 모든 프롬프트 리셋
                return self.save_prompts(self.default_prompts.copy())

        except Exception as e:
            logger.error(f"❌ 프롬프트 리셋 오류: {e}")
            return False

    def get_prompt_info(self) -> Dict[str, Any]:
        """모든 프롬프트 정보 조회 (편집용)"""
        try:
            prompts = self.load_prompts()

            # 편집에 필요한 정보만 정리
            prompt_info = {}
            for key, data in prompts.items():
                prompt_info[key] = {
                    'name': data.get('name', ''),
                    'description': data.get('description', ''),
                    'prompt': data.get('prompt', ''),
                    'variables': data.get('variables', []),
                    'last_modified': data.get('last_modified', ''),
                    'char_count': len(data.get('prompt', ''))
                }

            return prompt_info

        except Exception as e:
            logger.error(f"❌ 프롬프트 정보 조회 오류: {e}")
            return {}

# 전역 프롬프트 매니저 인스턴스
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """프롬프트 매니저 싱글톤 인스턴스 반환"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager