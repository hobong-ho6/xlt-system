"""
XLT System 상세 디버그 로거
모든 번역 과정을 상세하게 로그로 기록하여 문제점 분석
"""

import os
import logging
import traceback
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class XLTDebugLogger:
    """XLT 시스템 전용 디버그 로거"""

    def __init__(self):
        self.setup_logging()
        self._session_data = {}
        self._lock = threading.Lock()

    def setup_logging(self):
        """로그 시스템 초기화"""
        # log 디렉토리 생성
        self.log_dir = Path(__file__).parent.parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # 날짜별 로그 파일명
        today = datetime.now().strftime("%Y%m%d")

        # 메인 로거 설정
        self.logger = logging.getLogger('xlt_debug')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # 기존 핸들러 제거

        # 파일 핸들러 - 상세 디버그
        debug_file = self.log_dir / f"debug_{today}.log"
        debug_handler = logging.FileHandler(debug_file, encoding='utf-8')
        debug_handler.setLevel(logging.DEBUG)

        # 에러 전용 핸들러
        error_file = self.log_dir / f"errors_{today}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)

        # 번역 과정 전용 핸들러
        translation_file = self.log_dir / f"translation_{today}.log"
        translation_handler = logging.FileHandler(translation_file, encoding='utf-8')
        translation_handler.setLevel(logging.INFO)

        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        debug_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        translation_handler.setFormatter(formatter)

        self.logger.addHandler(debug_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(translation_handler)

        # 콘솔 핸들러 (선택적)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.info("=== XLT Debug Logger 초기화 완료 ===")
        self.logger.info(f"로그 디렉토리: {self.log_dir}")

    def log_session_start(self, session_id: str, request_data: Dict[str, Any]):
        """세션 시작 로그"""
        with self._lock:
            self._session_data[session_id] = {
                'start_time': datetime.now(),
                'request_data': request_data,
                'steps': []
            }

        self.logger.info(f"=== 세션 시작: {session_id} ===")
        self.logger.info(f"요청 데이터: {json.dumps(request_data, ensure_ascii=False, indent=2)}")

    def log_step(self, session_id: str, step: str, data: Any = None, level: str = 'INFO'):
        """단계별 진행 로그"""
        timestamp = datetime.now()
        step_info = {
            'timestamp': timestamp.isoformat(),
            'step': step,
            'data': data
        }

        with self._lock:
            if session_id in self._session_data:
                self._session_data[session_id]['steps'].append(step_info)

        log_method = getattr(self.logger, level.lower(), self.logger.info)
        if data:
            log_method(f"[{session_id}] {step}: {json.dumps(data, ensure_ascii=False, default=str)}")
        else:
            log_method(f"[{session_id}] {step}")

    def log_error(self, session_id: str, error: Exception, context: str = ""):
        """에러 상세 로그"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }

        with self._lock:
            if session_id in self._session_data:
                self._session_data[session_id]['error'] = error_info

        self.logger.error(f"[{session_id}] {context} 에러 발생:")
        self.logger.error(f"[{session_id}] 에러 타입: {type(error).__name__}")
        self.logger.error(f"[{session_id}] 에러 메시지: {str(error)}")
        self.logger.error(f"[{session_id}] 스택 트레이스:")
        self.logger.error(traceback.format_exc())

    def log_translation_attempt(self, session_id: str, translator_info: Dict[str, Any]):
        """번역 시도 상세 로그"""
        self.logger.info(f"[{session_id}] === 번역 시도 상세 정보 ===")
        self.logger.info(f"[{session_id}] 번역기 타입: {translator_info.get('type', 'Unknown')}")
        self.logger.info(f"[{session_id}] 번역 모드: {translator_info.get('mode', 'Unknown')}")
        self.logger.info(f"[{session_id}] 연결 테스트 결과: {translator_info.get('connection_test', 'Unknown')}")
        self.logger.info(f"[{session_id}] 텍스트 수량: {translator_info.get('text_count', 0)}")
        self.logger.info(f"[{session_id}] 대상 언어: {translator_info.get('target_languages', [])}")

    def log_connection_test_detail(self, session_id: str, test_info: Dict[str, Any]):
        """연결 테스트 상세 로그"""
        self.logger.debug(f"[{session_id}] === 연결 테스트 상세 ===")
        self.logger.debug(f"[{session_id}] 테스트 방법: {test_info.get('method', 'Unknown')}")
        self.logger.debug(f"[{session_id}] 테스트 시작: {test_info.get('start_time', 'Unknown')}")
        self.logger.debug(f"[{session_id}] 테스트 결과: {test_info.get('result', 'Unknown')}")
        self.logger.debug(f"[{session_id}] 소요 시간: {test_info.get('duration', 'Unknown')}초")

        if 'error' in test_info:
            self.logger.error(f"[{session_id}] 연결 테스트 에러: {test_info['error']}")

    def save_session_summary(self, session_id: str):
        """세션 종료 시 전체 요약 저장"""
        if session_id not in self._session_data:
            return

        session_data = self._session_data[session_id]
        summary_file = self.log_dir / f"session_{session_id}.json"

        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)

            self.logger.info(f"[{session_id}] 세션 요약 저장 완료: {summary_file}")

        except Exception as e:
            self.logger.error(f"[{session_id}] 세션 요약 저장 실패: {e}")

    def cleanup_session(self, session_id: str):
        """세션 데이터 정리"""
        with self._lock:
            if session_id in self._session_data:
                del self._session_data[session_id]


# 전역 싱글톤 인스턴스
_debug_logger = None

def get_debug_logger() -> XLTDebugLogger:
    """디버그 로거 싱글톤 인스턴스 반환"""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = XLTDebugLogger()
    return _debug_logger

# 편의 함수들
def log_session_start(session_id: str, request_data: Dict[str, Any]):
    get_debug_logger().log_session_start(session_id, request_data)

def log_step(session_id: str, step: str, data: Any = None, level: str = 'INFO'):
    get_debug_logger().log_step(session_id, step, data, level)

def log_error(session_id: str, error: Exception, context: str = ""):
    get_debug_logger().log_error(session_id, error, context)

def log_translation_attempt(session_id: str, translator_info: Dict[str, Any]):
    get_debug_logger().log_translation_attempt(session_id, translator_info)

def log_connection_test_detail(session_id: str, test_info: Dict[str, Any]):
    get_debug_logger().log_connection_test_detail(session_id, test_info)

def save_session_summary(session_id: str):
    get_debug_logger().save_session_summary(session_id)

def cleanup_session(session_id: str):
    get_debug_logger().cleanup_session(session_id)