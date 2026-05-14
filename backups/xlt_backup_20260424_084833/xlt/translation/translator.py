"""Google Translate based translator for XLT system"""

import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.exceptions import TranslationError
from .languages import (
    DEFAULT_LANGUAGES,
    get_google_translate_code,
    validate_language_codes,
    detect_primary_language
)
from ..utils.helpers import retry_on_failure, format_duration


class Translator:
    """Google Translate API 기반 번역기"""

    def __init__(self, config):
        self.config = config
        self.batch_size = config.translation_batch_size
        self.timeout = config.translation_timeout
        self._translator = None

    def _get_translator(self):
        """Google Translate 인스턴스 반환 (지연 초기화)"""
        if self._translator is None:
            try:
                from googletrans import Translator as GoogleTranslator
                self._translator = GoogleTranslator()
            except ImportError:
                raise TranslationError("", "", "googletrans 라이브러리가 설치되지 않았습니다. pip install googletrans==4.0.0rc1")
            except Exception as e:
                raise TranslationError("", "", f"번역기 초기화 실패: {str(e)}")

        return self._translator

    def translate_text(self, text: str, target_language: str, source_language: str = 'auto') -> str:
        """단일 텍스트 번역

        Args:
            text: 번역할 텍스트
            target_language: 대상 언어 코드 (XLT 형식)
            source_language: 소스 언어 코드 (기본값: 자동 감지)

        Returns:
            str: 번역된 텍스트

        Raises:
            TranslationError: 번역 실패 시
        """
        if not text.strip():
            return text

        try:
            translator = self._get_translator()

            # XLT 언어 코드를 Google Translate 코드로 변환
            target_code = get_google_translate_code(target_language)
            source_code = get_google_translate_code(source_language) if source_language != 'auto' else 'auto'

            # 소스와 타겟이 같으면 번역 건너뛰기
            if source_code != 'auto' and source_code == target_code:
                return text

            # 재시도 로직으로 번역 실행
            def translate_func():
                result = translator.translate(text, dest=target_code, src=source_code)
                return result.text

            translated = retry_on_failure(translate_func, max_retries=3, delay=1.0)

            # 번역 결과가 비어있으면 원본 반환
            return translated.strip() if translated and translated.strip() else text

        except Exception as e:
            # 번역 실패 시 원본 텍스트 반환하고 경고
            print(f"⚠️ 번역 실패 ({text[:20]}...): {str(e)}")
            return text

    def translate_batch(self, texts: List[str], target_languages: List[str]) -> List[Dict[str, str]]:
        """텍스트 배치를 여러 언어로 번역

        Args:
            texts: 번역할 텍스트 목록
            target_languages: 대상 언어 목록 (XLT 형식)

        Returns:
            List[Dict[str, str]]: 번역 결과 목록
        """
        if not texts:
            return []

        start_time = time.time()

        # 언어 코드 유효성 검사
        valid_languages = validate_language_codes(target_languages)
        if not valid_languages:
            raise TranslationError("", "", f"유효한 언어가 없습니다: {target_languages}")

        # 결과 초기화
        results = []
        for text in texts:
            result = {'original': text}
            for lang in valid_languages:
                result[lang] = text  # 기본값은 원본 텍스트
            results.append(result)

        # 소스 언어 자동 감지 (첫 번째 텍스트 기준)
        source_language = detect_primary_language(texts[0]) if texts else 'auto'
        print(f"🔍 소스 언어 자동 감지: {source_language}")
        print(f"   번역할 언어 목록: {valid_languages}")

        try:
            # 각 언어별로 번역 (병렬 처리)
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_lang = {}

                for lang in valid_languages:
                    # 소스 언어와 같으면 건너뛰기
                    if lang == source_language:
                        print(f"   ⏭️  {lang} 건너뛰기 (소스 언어와 동일)")
                        continue

                    print(f"   ✅ {lang} 번역 작업 추가")
                    future = executor.submit(self._translate_all_to_language, texts, lang, source_language)
                    future_to_lang[future] = lang

                # 결과 수집 (timeout을 넉넉하게 설정)
                timeout_per_language = max(self.timeout * 2, 120)  # 최소 120초
                print(f"   ⏱️  언어당 타임아웃: {timeout_per_language}초")

                for future in as_completed(future_to_lang, timeout=timeout_per_language):
                    lang = future_to_lang[future]
                    try:
                        translations = future.result()
                        print(f"   ✅ {lang} 번역 완료: {len(translations)}개 텍스트")
                        for i, translated_text in enumerate(translations):
                            if i < len(results):
                                results[i][lang] = translated_text
                    except Exception as e:
                        print(f"   ⚠️ {lang} 번역 실패: {str(e)}")

        except Exception as e:
            print(f"⚠️ 배치 번역 중 오류: {str(e)}")
            # 타임아웃된 언어들 확인
            for future, lang in future_to_lang.items():
                if not future.done():
                    print(f"   ❌ {lang} 번역 미완료 (타임아웃)")

        processing_time = time.time() - start_time

        # 로깅용 통계
        if hasattr(self, 'logger'):
            self.logger.log_translation_result(
                translation_count=len(texts),
                languages=valid_languages,
                processing_time=processing_time
            )

        return results

    def _translate_all_to_language(self, texts: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """모든 텍스트를 특정 언어로 번역"""
        translated_texts = []

        for text in texts:
            try:
                translated = self.translate_text(text, target_language, source_language)
                translated_texts.append(translated)
            except Exception:
                # 개별 번역 실패 시 원본 텍스트 사용
                translated_texts.append(text)

        return translated_texts

    def translate_with_substitution(self, text_with_placeholders: str, target_languages: List[str]) -> Dict[str, str]:
        """치환자가 포함된 텍스트 번역

        Args:
            text_with_placeholders: 치환자가 포함된 텍스트 (예: "{{0}} USDT 받기", "{{amount}} USDT 받기")
            target_languages: 대상 언어 목록

        Returns:
            Dict[str, str]: 언어별 번역 결과
        """
        import re

        # 치환자 패턴 찾기 (숫자 또는 텍스트 모두 지원)
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        placeholders = re.findall(placeholder_pattern, text_with_placeholders)

        if not placeholders:
            # 치환자가 없으면 일반 번역
            results = self.translate_batch([text_with_placeholders], target_languages)
            return results[0] if results else {}

        # 치환자를 임시 텍스트로 치환 (번역 시 혼동 방지)
        temp_text = text_with_placeholders
        temp_placeholders = {}

        for i, placeholder in enumerate(placeholders):
            # 고유한 임시 키 생성 (번역기가 건드리지 않을 형태)
            temp_key = f"XLTPLACEHOLDER{i:03d}X"
            temp_placeholders[temp_key] = placeholder
            temp_text = temp_text.replace(f"{{{{{placeholder}}}}}", temp_key)

        # 임시 텍스트 번역
        translation_results = self.translate_batch([temp_text], target_languages)

        if not translation_results:
            return {}

        # 치환자를 다시 원래 형태로 복원
        final_results = {}
        for lang, translated in translation_results[0].items():
            if lang == 'original':
                continue

            restored_text = translated
            # 임시 키를 원래 치환자로 복원
            for temp_key, original_placeholder in temp_placeholders.items():
                restored_text = restored_text.replace(temp_key, f"{{{{{original_placeholder}}}}}")

            final_results[lang] = restored_text

        return final_results

    def get_translation_statistics(self) -> Dict[str, Any]:
        """번역 통계 정보 반환 (필요시 구현)"""
        return {
            'batch_size': self.batch_size,
            'timeout': self.timeout,
            'supported_languages': len(DEFAULT_LANGUAGES)
        }

    def test_connection(self) -> bool:
        """번역 서비스 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            test_result = self.translate_text("test", "ko_KR", "en")
            return test_result is not None
        except Exception:
            return False