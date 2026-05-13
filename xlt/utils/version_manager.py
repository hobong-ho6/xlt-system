"""
XLT System 중앙화된 버전 관리 시스템
version.json 파일을 기반으로 모든 버전 정보를 중앙에서 관리
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class VersionManager:
    """버전 정보 중앙 관리자"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.version_file = self.project_root / "version.json"
        self._version_cache = None

    def get_version_info(self) -> Dict[str, any]:
        """버전 정보 조회 (캐싱 지원)"""
        if self._version_cache is None:
            self._load_version_info()
        return self._version_cache or self._get_fallback_version()

    def _load_version_info(self) -> None:
        """version.json 파일에서 버전 정보 로드"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    self._version_cache = json.load(f)
            else:
                print(f"⚠️ version.json 파일을 찾을 수 없습니다: {self.version_file}")
                self._version_cache = None
        except Exception as e:
            print(f"❌ version.json 로드 실패: {e}")
            self._version_cache = None

    def _get_fallback_version(self) -> Dict[str, any]:
        """폴백 버전 정보"""
        return {
            "name": "XLT System",
            "version": "5.0.6",
            "build": "2026-05-06",
            "installation_type": "unknown"
        }

    def get_version(self) -> str:
        """버전 번호만 반환 (v5.0.6)"""
        info = self.get_version_info()
        version = info.get('version', '5.0.6')
        return f"v{version}" if not version.startswith('v') else version

    def get_version_number(self) -> str:
        """순수 버전 번호만 반환 (5.0.6)"""
        info = self.get_version_info()
        version = info.get('version', '5.0.6')
        return version.replace('v', '') if version.startswith('v') else version

    def get_full_name(self) -> str:
        """전체 이름 반환 (XLT System v5.0.6)"""
        info = self.get_version_info()
        name = info.get('name', 'XLT System')
        version = self.get_version()
        return f"{name} {version}"

    def get_build_date(self) -> str:
        """빌드 날짜 반환"""
        info = self.get_version_info()
        return info.get('build', '2026-05-06')

    def refresh_cache(self) -> None:
        """버전 정보 캐시 새로고침"""
        self._version_cache = None
        self._load_version_info()


# 전역 싱글톤 인스턴스
_version_manager = None

def get_version_manager() -> VersionManager:
    """버전 매니저 싱글톤 인스턴스 반환"""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager

def get_version() -> str:
    """버전 번호 반환 (v5.0.6) - 편의 함수"""
    return get_version_manager().get_version()

def get_version_number() -> str:
    """순수 버전 번호 반환 (5.0.6) - 편의 함수"""
    return get_version_manager().get_version_number()

def get_full_name() -> str:
    """전체 이름 반환 (XLT System v5.0.6) - 편의 함수"""
    return get_version_manager().get_full_name()