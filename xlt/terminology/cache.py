"""
용어집 로컬 캐시 관리 시스템
TTL 기반으로 구글 시트 데이터를 로컬에 캐싱하여 성능을 최적화
"""

import os
import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..core.exceptions import XLTException


class TerminologyCacheError(XLTException):
    """용어집 캐시 관련 오류"""

    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"용어집 캐시 오류 ({operation}): {message}")


class TerminologyCache:
    """용어집 로컬 캐시 관리 클래스"""

    def __init__(self, config):
        """
        용어집 캐시 초기화

        Args:
            config: XLTConfig 인스턴스
        """
        self.config = config

        # 캐시 디렉토리 설정
        base_dir = getattr(config, 'config_path', os.getcwd())
        self.cache_dir = Path(base_dir) / 'cache' / 'terminology'

        # 캐시 파일 경로
        self.terminology_cache_file = self.cache_dir / 'terminology_cache.json'
        self.exceptions_cache_file = self.cache_dir / 'exceptions_cache.json'
        self.metadata_cache_file = self.cache_dir / 'metadata_cache.json'
        self.sync_log_file = self.cache_dir / 'sync_log.json'

        # 캐시 설정 (기존 claude_translator와 동일한 패턴)
        self.cache_ttl = getattr(config, 'terminology_cache_ttl', 7200)  # 2시간
        self.max_cache_size_mb = 50  # 최대 50MB
        self.enable_compression = False  # 향후 확장용

        # 스레드 안전성을 위한 락
        self._cache_lock = threading.Lock()

        # 메모리 캐시 (자주 사용되는 데이터)
        self._memory_cache = {}
        self._memory_cache_timestamp = 0

        # 캐시 디렉토리 생성
        self._ensure_cache_directory()

    def _ensure_cache_directory(self) -> None:
        """캐시 디렉토리 생성 (기존 XLT 패턴)"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 용어집 캐시 디렉토리 준비: {self.cache_dir}")
        except Exception as e:
            raise TerminologyCacheError("directory_creation", f"캐시 디렉토리 생성 실패: {str(e)}")

    def _get_cache_metadata(self, cache_file: Path) -> Dict[str, Any]:
        """캐시 파일의 메타데이터 조회"""
        try:
            if not cache_file.exists():
                return {}

            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return data.get('metadata', {})

        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️ 캐시 메타데이터 조회 실패: {cache_file.name} - {str(e)}")
            return {}

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """캐시 파일 유효성 검사 (TTL 기반)"""
        try:
            metadata = self._get_cache_metadata(cache_file)
            if not metadata:
                return False

            cached_at = metadata.get('cached_at')
            if not cached_at:
                return False

            # ISO 8601 형식으로 저장된 시각을 파싱
            cached_time = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
            current_time = datetime.now().astimezone()

            # TTL 체크
            elapsed = (current_time - cached_time).total_seconds()
            return elapsed < self.cache_ttl

        except Exception as e:
            print(f"⚠️ 캐시 유효성 체크 실패: {cache_file.name} - {str(e)}")
            return False

    def _calculate_data_hash(self, data: Any) -> str:
        """데이터 해시 계산 (변경 감지용)"""
        try:
            # 데이터를 JSON 문자열로 직렬화한 후 해시 계산
            json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(json_str.encode('utf-8')).hexdigest()
        except Exception:
            # 해시 계산 실패 시 타임스탬프 기반 해시 반환
            return hashlib.md5(str(time.time()).encode()).hexdigest()

    def get_cached_terminology(self) -> Optional[Dict[str, Dict[str, str]]]:
        """
        캐시된 용어집 데이터 조회

        Returns:
            Optional[Dict]: 캐시된 용어집 데이터 또는 None
        """
        with self._cache_lock:
            try:
                # 캐시 유효성 체크
                if not self._is_cache_valid(self.terminology_cache_file):
                    print("📝 용어집 캐시가 만료되었거나 없습니다")
                    return None

                # 메모리 캐시 우선 조회
                if (self._memory_cache.get('terminology') and
                        time.time() - self._memory_cache_timestamp < 300):  # 5분 메모리 캐시
                    print("🚀 용어집 메모리 캐시 히트")
                    return self._memory_cache['terminology']

                # 파일 캐시 조회
                with open(self.terminology_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                terminology_data = cache_data.get('data', {})

                # 메모리 캐시에 저장
                self._memory_cache['terminology'] = terminology_data
                self._memory_cache_timestamp = time.time()

                print(f"💾 용어집 파일 캐시 히트: {len(terminology_data)}개 용어")
                return terminology_data

            except Exception as e:
                print(f"⚠️ 용어집 캐시 조회 실패: {str(e)}")
                return None

    def store_terminology(self, data: Dict[str, Dict[str, str]],
                         source_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        용어집 데이터를 캐시에 저장

        Args:
            data: 용어집 데이터 {'한국어': {'en_US': 'English', ...}, ...}
            source_metadata: 소스 메타데이터 (시트 버전 등)
        """
        with self._cache_lock:
            try:
                current_time = datetime.now().astimezone()
                data_hash = self._calculate_data_hash(data)

                cache_data = {
                    'data': data,
                    'metadata': {
                        'cached_at': current_time.isoformat(),
                        'expires_at': (current_time + timedelta(seconds=self.cache_ttl)).isoformat(),
                        'data_hash': data_hash,
                        'total_terms': len(data),
                        'source_metadata': source_metadata or {},
                        'cache_version': '1.0'
                    }
                }

                # 파일 캐시에 저장
                with open(self.terminology_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

                # 메모리 캐시 업데이트
                self._memory_cache['terminology'] = data
                self._memory_cache_timestamp = time.time()

                print(f"💾 용어집 캐시 저장 완료: {len(data)}개 용어 (해시: {data_hash[:8]})")

                # 동기화 로그 업데이트
                self._update_sync_log('terminology', 'cached', len(data))

            except Exception as e:
                raise TerminologyCacheError("store_terminology", f"용어집 저장 실패: {str(e)}")

    def get_cached_exceptions(self) -> Optional[List[Dict[str, Any]]]:
        """
        캐시된 예외 항목 조회

        Returns:
            Optional[List[Dict]]: 캐시된 예외 항목 또는 None
        """
        with self._cache_lock:
            try:
                # 캐시 유효성 체크
                if not self._is_cache_valid(self.exceptions_cache_file):
                    print("📝 예외 항목 캐시가 만료되었거나 없습니다")
                    return None

                # 파일 캐시 조회
                with open(self.exceptions_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                exceptions_data = cache_data.get('data', [])
                print(f"💾 예외 항목 캐시 히트: {len(exceptions_data)}개 항목")
                return exceptions_data

            except Exception as e:
                print(f"⚠️ 예외 항목 캐시 조회 실패: {str(e)}")
                return None

    def store_exceptions(self, data: List[Dict[str, Any]],
                        source_metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        예외 항목 데이터를 캐시에 저장

        Args:
            data: 예외 항목 데이터
            source_metadata: 소스 메타데이터
        """
        with self._cache_lock:
            try:
                current_time = datetime.now().astimezone()
                data_hash = self._calculate_data_hash(data)

                cache_data = {
                    'data': data,
                    'metadata': {
                        'cached_at': current_time.isoformat(),
                        'expires_at': (current_time + timedelta(seconds=self.cache_ttl)).isoformat(),
                        'data_hash': data_hash,
                        'total_exceptions': len(data),
                        'source_metadata': source_metadata or {},
                        'cache_version': '1.0'
                    }
                }

                # 파일 캐시에 저장
                with open(self.exceptions_cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

                print(f"💾 예외 항목 캐시 저장 완료: {len(data)}개 항목 (해시: {data_hash[:8]})")

                # 동기화 로그 업데이트
                self._update_sync_log('exceptions', 'cached', len(data))

            except Exception as e:
                raise TerminologyCacheError("store_exceptions", f"예외 항목 저장 실패: {str(e)}")

    def invalidate_cache(self) -> None:
        """모든 캐시 무효화"""
        with self._cache_lock:
            try:
                # 파일 캐시 삭제
                for cache_file in [self.terminology_cache_file, self.exceptions_cache_file, self.metadata_cache_file]:
                    if cache_file.exists():
                        cache_file.unlink()
                        print(f"🗑️  캐시 파일 삭제: {cache_file.name}")

                # 메모리 캐시 정리
                self._memory_cache.clear()
                self._memory_cache_timestamp = 0

                # 무효화 로그
                self._update_sync_log('all', 'invalidated', 0)

                print("🧹 모든 용어집 캐시 무효화 완료")

            except Exception as e:
                print(f"⚠️ 캐시 무효화 중 오류: {str(e)}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        with self._cache_lock:
            stats = {
                'cache_directory': str(self.cache_dir),
                'cache_ttl_seconds': self.cache_ttl,
                'terminology_cache_exists': self.terminology_cache_file.exists(),
                'exceptions_cache_exists': self.exceptions_cache_file.exists(),
                'terminology_cache_valid': self._is_cache_valid(self.terminology_cache_file),
                'exceptions_cache_valid': self._is_cache_valid(self.exceptions_cache_file),
                'memory_cache_items': len(self._memory_cache),
                'cache_files': []
            }

            # 각 캐시 파일 정보
            for cache_file in [self.terminology_cache_file, self.exceptions_cache_file]:
                if cache_file.exists():
                    try:
                        file_stat = cache_file.stat()
                        metadata = self._get_cache_metadata(cache_file)

                        stats['cache_files'].append({
                            'name': cache_file.name,
                            'size_bytes': file_stat.st_size,
                            'modified_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'is_valid': self._is_cache_valid(cache_file),
                            'data_hash': metadata.get('data_hash', 'N/A'),
                            'total_items': metadata.get('total_terms', metadata.get('total_exceptions', 0))
                        })
                    except Exception:
                        pass

            return stats

    def _update_sync_log(self, data_type: str, action: str, item_count: int) -> None:
        """동기화 로그 업데이트"""
        try:
            current_time = datetime.now().astimezone()

            # 기존 로그 읽기
            sync_log = []
            if self.sync_log_file.exists():
                try:
                    with open(self.sync_log_file, 'r', encoding='utf-8') as f:
                        sync_log = json.load(f)
                except (json.JSONDecodeError, OSError):
                    sync_log = []

            # 새 로그 엔트리 추가
            sync_log.append({
                'timestamp': current_time.isoformat(),
                'data_type': data_type,
                'action': action,
                'item_count': item_count,
                'ttl_seconds': self.cache_ttl
            })

            # 로그는 최근 50개만 유지
            if len(sync_log) > 50:
                sync_log = sync_log[-50:]

            # 로그 파일 저장
            with open(self.sync_log_file, 'w', encoding='utf-8') as f:
                json.dump(sync_log, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ 동기화 로그 업데이트 실패: {str(e)}")

    def cleanup_expired_cache(self) -> None:
        """만료된 캐시 파일 정리"""
        with self._cache_lock:
            cleaned_files = []

            for cache_file in [self.terminology_cache_file, self.exceptions_cache_file]:
                if cache_file.exists() and not self._is_cache_valid(cache_file):
                    try:
                        cache_file.unlink()
                        cleaned_files.append(cache_file.name)
                    except Exception as e:
                        print(f"⚠️ 만료 캐시 삭제 실패: {cache_file.name} - {str(e)}")

            if cleaned_files:
                print(f"🧹 만료된 캐시 파일 정리 완료: {', '.join(cleaned_files)}")
                self._update_sync_log('cleanup', 'expired_removed', len(cleaned_files))