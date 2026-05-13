"""XLT System Main Pipeline"""

from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import os

from .config import XLTConfig
from .exceptions import *
from ..input.base import InputProcessor
from ..utils.logger import XLTLogger


class XLTPipeline:
    """XLT 시스템 메인 파이프라인 클래스"""

    def __init__(self, config: Optional[XLTConfig] = None):
        self.config = config or XLTConfig()
        self.logger = XLTLogger(self.config)
        self.input_processors: Dict[str, InputProcessor] = {}
        self.ocr_engine = None
        self.translator = None
        self.excel_handler = None
        self.interactive_ui = None

        # 컴포넌트 초기화는 지연 로딩
        self._initialized = False

    def initialize(self):
        """파이프라인 컴포넌트 초기화 (지연 로딩)"""
        if self._initialized:
            return

        try:
            # 입력 처리기 등록
            self._register_input_processors()

            # OCR 엔진 초기화
            from ..ocr.engine import OCREngine
            self.ocr_engine = OCREngine(self.config)

            # 번역기 초기화 (XLT System v3.0 - Unifi 가이드 준수)
            try:
                from ..translation.unifi_translator import UnifiTranslator
                self.translator = UnifiTranslator(self.config)
                print("✅ Unifi 전용 번역기 활성화 (guide.md 기준 준수)")
            except Exception as e:
                print(f"⚠️ Unifi 번역기 초기화 실패, 기본 번역기 사용: {str(e)}")
                from ..translation.translator import Translator
                self.translator = Translator(self.config)

            # Excel 핸들러 초기화
            from ..output.excel import ExcelHandler
            self.excel_handler = ExcelHandler(self.config)

            # 대화형 UI 초기화
            from ..ui.interactive import InteractiveUI
            self.interactive_ui = InteractiveUI(self.config)

            self._initialized = True
            self.logger.info("XLT 파이프라인 초기화 완료")

        except Exception as e:
            raise ConfigurationError(f"파이프라인 초기화 실패: {str(e)}")

    def _register_input_processors(self):
        """입력 처리기 등록"""
        from ..input.image import ImageProcessor
        from ..input.figma import FigmaProcessor

        self.input_processors = {
            'file': ImageProcessor(self.config),
            'figma': FigmaProcessor(self.config)
        }

    def process(self, source: str, auto_mode: bool = False,
                languages: Optional[List[str]] = None) -> Dict[str, Any]:
        """메인 처리 워크플로우

        Args:
            source: 입력 소스 (파일 경로, 피그마 URL)
            auto_mode: 자동 모드 (모든 텍스트 자동 번역)
            languages: 번역할 언어 목록 (기본값: config의 default_languages)

        Returns:
            Dict[str, Any]: 처리 결과
        """
        if not self._initialized:
            self.initialize()

        self.logger.info(f"XLT 파이프라인 시작: {source}")

        try:
            # 1. 입력 처리
            image, source_description = self._process_input(source)
            self.logger.info(f"입력 처리 완료: {source_description}")

            # 2. OCR 처리
            ocr_results = self._process_ocr(image)
            self.logger.info(f"OCR 처리 완료: {len(ocr_results)} 개 텍스트 추출")

            # 3. 사용자 선택 (학습 모드) 또는 자동 선택
            if auto_mode:
                selected_texts = self._auto_select_texts(ocr_results)
                self.logger.info(f"자동 선택 완료: {len(selected_texts)} 개 텍스트")
            else:
                selected_texts = self._interactive_select_texts(ocr_results)
                self.logger.info(f"사용자 선택 완료: {len(selected_texts)} 개 텍스트")

            if not selected_texts:
                self.logger.warning("선택된 텍스트가 없음")
                return {
                    'status': 'no_selection',
                    'message': '번역할 텍스트가 선택되지 않았습니다.'
                }

            # 4. 번역 처리
            target_languages = languages or self.config.default_languages
            translations = self._process_translation(selected_texts, target_languages)
            self.logger.info(f"번역 처리 완료: {len(translations)} 개 항목")

            # 5. Excel 출력
            output_file = self._process_output(translations, source_description)
            self.logger.info(f"Excel 출력 완료: {output_file}")

            return {
                'status': 'success',
                'output_file': output_file,
                'processed_count': len(translations),
                'source': source_description
            }

        except Exception as e:
            self.logger.error(f"파이프라인 처리 실패: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'source': source
            }

    def _process_input(self, source: str) -> Tuple[Image.Image, str]:
        """입력 처리 단계"""
        input_type = InputProcessor.detect_input_type(source)

        if input_type not in self.input_processors:
            raise InputProcessingError(input_type, f"지원하지 않는 입력 타입: {input_type}")

        processor = self.input_processors[input_type]

        if not processor.can_process(source):
            raise InputProcessingError(input_type, f"처리할 수 없는 소스: {source}")

        return processor.process(source)

    def _process_ocr(self, image: Image.Image) -> List[Dict[str, Any]]:
        """OCR 처리 단계"""
        if not self.ocr_engine:
            raise OCRProcessingError("OCR 엔진이 초기화되지 않았습니다")

        return self.ocr_engine.extract_text(image)

    def _auto_select_texts(self, ocr_results: List[Dict[str, Any]]) -> List[str]:
        """자동 모드에서 텍스트 선택"""
        from ..ocr.extractors import TextExtractor

        extractor = TextExtractor(self.config)
        return extractor.extract_meaningful_texts(ocr_results)

    def _interactive_select_texts(self, ocr_results: List[Dict[str, Any]]) -> List[str]:
        """대화형 모드에서 사용자 텍스트 선택"""
        if not self.interactive_ui:
            raise XLTException("대화형 UI가 초기화되지 않았습니다")

        return self.interactive_ui.select_texts(ocr_results)

    def _process_translation(self, texts: List[str], target_languages: List[str]) -> List[Dict[str, str]]:
        """번역 처리 단계"""
        if not self.translator:
            raise TranslationError("", "", "번역기가 초기화되지 않았습니다")

        return self.translator.translate_batch(texts, target_languages)

    def _process_output(self, translations: List[Dict[str, str]], source_description: str) -> str:
        """Excel 출력 처리 단계"""
        if not self.excel_handler:
            raise OutputProcessingError("Excel", "Excel 핸들러가 초기화되지 않았습니다")

        return self.excel_handler.create_excel_file(translations, source_description)

    def cleanup(self):
        """리소스 정리"""
        for processor in self.input_processors.values():
            processor.cleanup()

        self.logger.info("XLT 파이프라인 정리 완료")