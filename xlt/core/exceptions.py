"""XLT System Custom Exceptions"""

from typing import Optional


class XLTException(Exception):
    """XLT 시스템 기본 예외 클래스"""
    pass


class InputProcessingError(XLTException):
    """입력 처리 중 발생하는 오류"""
    def __init__(self, source: str, message: str):
        self.source = source
        super().__init__(f"입력 처리 오류 ({source}): {message}")


class OCRProcessingError(XLTException):
    """OCR 처리 중 발생하는 오류"""
    def __init__(self, message: str, confidence: Optional[float] = None):
        self.confidence = confidence
        super().__init__(f"OCR 처리 오류: {message}")


class TranslationError(XLTException):
    """번역 처리 중 발생하는 오류"""
    def __init__(self, source_lang: str, target_lang: str, message: str):
        self.source_lang = source_lang
        self.target_lang = target_lang
        super().__init__(f"번역 오류 ({source_lang} → {target_lang}): {message}")


class OutputProcessingError(XLTException):
    """출력 처리 중 발생하는 오류"""
    def __init__(self, output_type: str, message: str):
        self.output_type = output_type
        super().__init__(f"출력 처리 오류 ({output_type}): {message}")


class ConfigurationError(XLTException):
    """설정 관련 오류"""
    pass


class FigmaAPIError(InputProcessingError):
    """피그마 API 관련 오류"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__("Figma API", f"{message} (상태 코드: {status_code})" if status_code else message)