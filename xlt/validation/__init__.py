"""
XLT System Excel Validation Module

🚀 다른 Claude 수준의 정교한 검증 시스템:
- 유니코드 범위 기반 정확한 언어 감지
- 전체 데이터 배치 처리 (더 이상 샘플링 없음)
- 7가지 Placeholder 패턴 매칭
- /n 오타, 번역 누락, 언어 혼재 등 구체적 문제 감지
- 정상 케이스 필터링 (언어 라벨, 통화 코드)
"""

from .excel_validator import ExcelValidator
from .excel_corrector import ExcelCorrector
from .claude_prompts import ClaudePrompts
from .language_detector import LanguageDetector

__all__ = ['ExcelValidator', 'ExcelCorrector', 'ClaudePrompts', 'LanguageDetector']