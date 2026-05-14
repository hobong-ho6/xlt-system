"""XLT System Logging Utilities - DISABLED"""

from datetime import datetime
from typing import Dict, Any
import time


class XLTLogger:
    """XLT 시스템 전용 로거 - 모든 기능 비활성화"""

    def __init__(self, config):
        # 최소한의 초기화만 수행, 파일/디렉토리 생성 없음
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()

    def info(self, message: str, **kwargs):
        """정보 로그 - 비활성화"""
        pass

    def warning(self, message: str, **kwargs):
        """경고 로그 - 비활성화"""
        pass

    def error(self, message: str, **kwargs):
        """오류 로그 - 비활성화"""
        pass

    def debug(self, message: str, **kwargs):
        """디버그 로그 - 비활성화"""
        pass

    def log_ocr_result(self, text_count: int, confidence_avg: float, processing_time: float):
        """OCR 결과 로깅 - 비활성화"""
        pass

    def log_translation_result(self, translation_count: int, languages: list, processing_time: float):
        """번역 결과 로깅 - 비활성화"""
        pass

    def log_user_selection(self, selected_count: int, total_count: int, mode: str):
        """사용자 선택 결과 로깅 - 비활성화"""
        pass

    def save_session_log(self):
        """세션 로그를 JSON 파일로 저장 - 비활성화"""
        pass

    def generate_analysis_report(self) -> Dict[str, Any]:
        """세션 분석 보고서 생성 - 비활성화"""
        return {
            'session_id': self.session_id,
            'duration': time.time() - self.start_time,
            'event_counts': {},
            'ocr_metrics': {},
            'translation_metrics': {},
            'total_events': 0
        }

    def __del__(self):
        """소멸자 - 비활성화"""
        pass