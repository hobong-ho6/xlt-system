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


class GoogleSheetsError(XLTException):
    """구글 시트 관련 오류 (v5.1.1 추가)"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.error_code = error_code
        super().__init__(f"구글 시트 오류: {message}")


class GoogleSheetsAPIError(GoogleSheetsError):
    """구글 시트 API 관련 오류"""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        self.status_code = status_code
        super().__init__(message, error_code)


class TerminologyError(XLTException):
    """용어집 관련 오류"""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"용어집 오류 ({operation}): {message}")


class TerminologyCacheError(XLTException):
    """용어집 캐시 관련 오류"""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"용어집 캐시 오류 ({operation}): {message}")


class AuthenticationError(GoogleSheetsError):
    """인증 오류"""
    def __init__(self, message: str = "구글 시트 인증에 실패했습니다"):
        super().__init__(message, "AUTH_FAILED")