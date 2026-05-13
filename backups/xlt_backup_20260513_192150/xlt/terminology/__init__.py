"""
XLT System v5.1.1 - Terminology Management Package
구글 시트 기반 용어집 관리 시스템

주요 클래스:
- GoogleSheetsTerminology: 구글 시트 용어집 관리
- TerminologyCache: 로컬 캐시 관리
- GoogleSheetsAPI: 구글 시트 API 래퍼
"""

from .google_sheets import GoogleSheetsTerminology
from .cache import TerminologyCache
from .sheets_api import GoogleSheetsAPI

__version__ = "5.1.1"
__all__ = [
    "GoogleSheetsTerminology",
    "TerminologyCache",
    "GoogleSheetsAPI"
]