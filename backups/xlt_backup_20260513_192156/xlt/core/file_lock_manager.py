"""
파일 잠금 시스템

XLT System v5.1.0 호환 파일 잠금 관리자
- POSIX flock() 기반 Advisory Locking
- 중요도별 잠금 우선순위
- 강제 해제 메커니즘
"""

import fcntl
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from contextlib import contextmanager

from .config import XLTConfig


class FileLockManager:
    """파일 잠금 관리자"""

    def __init__(self, config: Optional[XLTConfig] = None):
        """
        Args:
            config: XLTConfig 인스턴스 (None이면 기본 설정)
        """
        self.config = config or XLTConfig()

        # 협업 디렉토리 경로 설정
        self.claude_dir = Path.home() / ".claude" / "projects" / "-Users-user-Documents-XLTTT"
        self.collab_dir = self.claude_dir / "collaboration"
        self.sessions_dir = self.collab_dir / "sessions"

        # JSON 파일 경로
        self.session_locks_file = self.sessions_dir / "session_locks.json"

        # 잠금 우선순위 매트릭스 (높을수록 우선)
        self.lock_priorities = {
            'version.json': 10,
            'auto_update_config.json': 10,
            'stable_web_server.py': 8,
            'xlt/translation/claude_translator.py': 6,
            'xlt/core/config.py': 6,
            'templates/index.html': 4,
            'xlt/input/figma.py': 3,
            'xlt/ocr/engine.py': 3,
            # 기본값
            '_default': 1
        }

        # 잠금 타임아웃 (기본 5분)
        self.lock_timeout = timedelta(seconds=getattr(config, 'zone_lock_timeout_seconds', 300))

        # 활성 잠금 파일 핸들들 (메모리에서 관리)
        self._active_locks: Dict[str, object] = {}

        # 디렉토리 존재 확인
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리가 존재하는지 확인하고 생성"""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # 기본 JSON 파일이 없으면 생성
        if not self.session_locks_file.exists():
            self._create_default_session_locks()

    def _create_default_session_locks(self) -> None:
        """기본 세션 잠금 파일 생성"""
        default_data = {
            "locked_files": {},
            "lock_history": [],
            "last_updated": datetime.now().isoformat()
        }

        with open(self.session_locks_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

    def acquire_lock(self, file_path: str, session_id: str, timeout_seconds: int = 30) -> Tuple[bool, str]:
        """
        파일 잠금 획득

        Args:
            file_path: 잠글 파일 경로
            session_id: 요청한 세션 ID
            timeout_seconds: 대기 타임아웃 (초)

        Returns:
            Tuple[success, message]: (성공 여부, 메시지)
        """
        try:
            # 파일 경로 정규화
            normalized_path = self._normalize_path(file_path)

            # 현재 잠금 상태 확인
            current_locks = self._load_session_locks()

            # 이미 잠겨 있는지 확인
            if normalized_path in current_locks['locked_files']:
                existing_lock = current_locks['locked_files'][normalized_path]

                # 같은 세션이면 성공
                if existing_lock['session_id'] == session_id:
                    return True, f"파일이 이미 현재 세션에 의해 잠겨 있습니다"

                # 잠금 만료 확인
                lock_time = datetime.fromisoformat(existing_lock['locked_at'])
                if datetime.now() - lock_time > self.lock_timeout:
                    # 만료된 잠금 강제 해제
                    self._force_release_lock(normalized_path, "잠금 타임아웃")
                else:
                    return False, f"파일이 다른 세션({existing_lock['session_id']})에 의해 잠겨 있습니다"

            # 실제 파일 시스템 레벨 잠금 시도
            lock_acquired = self._acquire_file_system_lock(normalized_path, timeout_seconds)

            if not lock_acquired:
                return False, f"파일 시스템 레벨 잠금 실패 (타임아웃: {timeout_seconds}초)"

            # 잠금 정보 등록
            lock_info = {
                "session_id": session_id,
                "locked_at": datetime.now().isoformat(),
                "priority": self._get_file_priority(normalized_path),
                "lock_type": "exclusive"
            }

            current_locks['locked_files'][normalized_path] = lock_info
            current_locks['last_updated'] = datetime.now().isoformat()

            # 잠금 히스토리에 추가
            history_entry = {
                "action": "acquire",
                "file_path": normalized_path,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "priority": lock_info['priority']
            }
            current_locks['lock_history'].append(history_entry)

            # 히스토리 크기 제한 (최근 100개만 유지)
            if len(current_locks['lock_history']) > 100:
                current_locks['lock_history'] = current_locks['lock_history'][-100:]

            # 업데이트된 잠금 정보 저장
            self._save_session_locks(current_locks)

            return True, f"파일 잠금 성공 (우선순위: {lock_info['priority']})"

        except Exception as e:
            return False, f"잠금 획득 중 오류 발생: {e}"

    def release_lock(self, file_path: str, session_id: str) -> Tuple[bool, str]:
        """
        파일 잠금 해제

        Args:
            file_path: 해제할 파일 경로
            session_id: 요청한 세션 ID

        Returns:
            Tuple[success, message]: (성공 여부, 메시지)
        """
        try:
            # 파일 경로 정규화
            normalized_path = self._normalize_path(file_path)

            # 현재 잠금 상태 확인
            current_locks = self._load_session_locks()

            # 잠금이 존재하는지 확인
            if normalized_path not in current_locks['locked_files']:
                return True, "파일이 잠겨 있지 않습니다"

            existing_lock = current_locks['locked_files'][normalized_path]

            # 세션 권한 확인
            if existing_lock['session_id'] != session_id:
                return False, f"다른 세션({existing_lock['session_id']})의 잠금입니다"

            # 파일 시스템 레벨 잠금 해제
            self._release_file_system_lock(normalized_path)

            # 잠금 정보 제거
            del current_locks['locked_files'][normalized_path]
            current_locks['last_updated'] = datetime.now().isoformat()

            # 잠금 히스토리에 추가
            history_entry = {
                "action": "release",
                "file_path": normalized_path,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "duration": self._calculate_lock_duration(existing_lock['locked_at'])
            }
            current_locks['lock_history'].append(history_entry)

            # 업데이트된 잠금 정보 저장
            self._save_session_locks(current_locks)

            return True, "파일 잠금 해제 성공"

        except Exception as e:
            return False, f"잠금 해제 중 오류 발생: {e}"

    def release_session_locks(self, session_id: str) -> int:
        """
        세션의 모든 잠금 해제

        Args:
            session_id: 해제할 세션 ID

        Returns:
            int: 해제된 잠금 수
        """
        try:
            current_locks = self._load_session_locks()
            released_count = 0

            # 해당 세션의 잠금 찾기
            files_to_release = []
            for file_path, lock_info in current_locks['locked_files'].items():
                if lock_info['session_id'] == session_id:
                    files_to_release.append(file_path)

            # 잠금 해제
            for file_path in files_to_release:
                success, _ = self.release_lock(file_path, session_id)
                if success:
                    released_count += 1

            return released_count

        except Exception as e:
            print(f"⚠️ 세션 잠금 해제 실패: {e}")
            return 0

    def check_file_lock_status(self, file_path: str) -> Dict:
        """
        파일 잠금 상태 확인

        Args:
            file_path: 확인할 파일 경로

        Returns:
            Dict: 잠금 상태 정보
        """
        try:
            normalized_path = self._normalize_path(file_path)
            current_locks = self._load_session_locks()

            if normalized_path in current_locks['locked_files']:
                lock_info = current_locks['locked_files'][normalized_path]
                lock_time = datetime.fromisoformat(lock_info['locked_at'])
                duration = datetime.now() - lock_time

                return {
                    "is_locked": True,
                    "session_id": lock_info['session_id'],
                    "locked_at": lock_info['locked_at'],
                    "duration_seconds": int(duration.total_seconds()),
                    "priority": lock_info['priority'],
                    "is_expired": duration > self.lock_timeout
                }
            else:
                return {
                    "is_locked": False,
                    "session_id": None,
                    "locked_at": None,
                    "duration_seconds": 0,
                    "priority": self._get_file_priority(normalized_path),
                    "is_expired": False
                }

        except Exception as e:
            return {
                "is_locked": False,
                "error": str(e)
            }

    def get_locked_files_by_session(self, session_id: str) -> List[str]:
        """세션별 잠긴 파일 목록 조회"""
        try:
            current_locks = self._load_session_locks()
            locked_files = []

            for file_path, lock_info in current_locks['locked_files'].items():
                if lock_info['session_id'] == session_id:
                    locked_files.append(file_path)

            return locked_files

        except Exception:
            return []

    def cleanup_expired_locks(self) -> int:
        """만료된 잠금 정리"""
        try:
            current_locks = self._load_session_locks()
            cleanup_count = 0

            files_to_cleanup = []
            for file_path, lock_info in current_locks['locked_files'].items():
                lock_time = datetime.fromisoformat(lock_info['locked_at'])
                if datetime.now() - lock_time > self.lock_timeout:
                    files_to_cleanup.append(file_path)

            # 만료된 잠금 해제
            for file_path in files_to_cleanup:
                self._force_release_lock(file_path, "잠금 만료")
                cleanup_count += 1

            return cleanup_count

        except Exception as e:
            print(f"⚠️ 만료 잠금 정리 실패: {e}")
            return 0

    @contextmanager
    def file_lock(self, file_path: str, session_id: str, timeout_seconds: int = 30):
        """
        컨텍스트 매니저를 사용한 파일 잠금

        Usage:
            with lock_manager.file_lock('stable_web_server.py', session_id) as acquired:
                if acquired:
                    # 파일 작업 수행
                    pass
        """
        success, message = self.acquire_lock(file_path, session_id, timeout_seconds)

        try:
            yield success
        finally:
            if success:
                self.release_lock(file_path, session_id)

    def _acquire_file_system_lock(self, file_path: str, timeout_seconds: int) -> bool:
        """파일 시스템 레벨 잠금 획득"""
        try:
            # 프로젝트 루트 기준 절대 경로 생성
            if not os.path.isabs(file_path):
                abs_file_path = os.path.join(self.config.config_path, file_path)
            else:
                abs_file_path = file_path

            # 파일이 존재하지 않으면 건너뛰기 (선택적 잠금)
            if not os.path.exists(abs_file_path):
                return True

            # 잠금 파일 경로 (.lock 확장자)
            lock_file_path = f"{abs_file_path}.lock"

            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                try:
                    # 잠금 파일 생성 및 잠금 시도
                    lock_fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)

                    # Non-blocking 잠금 시도
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

                    # 성공 시 파일 핸들 저장
                    self._active_locks[file_path] = lock_fd

                    return True

                except (OSError, IOError):
                    # 잠금 실패, 잠시 대기 후 재시도
                    time.sleep(0.1)

            return False

        except Exception:
            return False

    def _release_file_system_lock(self, file_path: str) -> None:
        """파일 시스템 레벨 잠금 해제"""
        try:
            if file_path in self._active_locks:
                lock_fd = self._active_locks[file_path]

                # 잠금 해제
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)

                # 잠금 파일 삭제
                if not os.path.isabs(file_path):
                    abs_file_path = os.path.join(self.config.config_path, file_path)
                else:
                    abs_file_path = file_path

                lock_file_path = f"{abs_file_path}.lock"
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)

                # 메모리에서 제거
                del self._active_locks[file_path]

        except Exception as e:
            print(f"⚠️ 파일 시스템 잠금 해제 실패: {e}")

    def _force_release_lock(self, file_path: str, reason: str) -> None:
        """강제 잠금 해제"""
        try:
            current_locks = self._load_session_locks()

            if file_path in current_locks['locked_files']:
                lock_info = current_locks['locked_files'][file_path]

                # 파일 시스템 레벨 잠금 해제
                self._release_file_system_lock(file_path)

                # 잠금 정보 제거
                del current_locks['locked_files'][file_path]
                current_locks['last_updated'] = datetime.now().isoformat()

                # 강제 해제 히스토리 추가
                history_entry = {
                    "action": "force_release",
                    "file_path": file_path,
                    "session_id": lock_info['session_id'],
                    "timestamp": datetime.now().isoformat(),
                    "reason": reason
                }
                current_locks['lock_history'].append(history_entry)

                # 업데이트된 정보 저장
                self._save_session_locks(current_locks)

        except Exception as e:
            print(f"⚠️ 강제 잠금 해제 실패: {e}")

    def _normalize_path(self, file_path: str) -> str:
        """파일 경로 정규화"""
        # 절대 경로를 상대 경로로 변환
        if file_path.startswith(self.config.config_path):
            return os.path.relpath(file_path, self.config.config_path)

        # 이미 상대 경로면 그대로 반환
        return file_path.replace(os.path.sep, '/')

    def _get_file_priority(self, file_path: str) -> int:
        """파일 우선순위 조회"""
        # 정확한 파일명 매치
        if file_path in self.lock_priorities:
            return self.lock_priorities[file_path]

        # 패턴 매치
        for pattern, priority in self.lock_priorities.items():
            if pattern != '_default' and pattern in file_path:
                return priority

        # 기본값
        return self.lock_priorities['_default']

    def _calculate_lock_duration(self, locked_at: str) -> str:
        """잠금 지속 시간 계산 (초)"""
        try:
            lock_time = datetime.fromisoformat(locked_at)
            duration = datetime.now() - lock_time
            return f"{int(duration.total_seconds())}초"
        except Exception:
            return "알 수 없음"

    def _load_session_locks(self) -> Dict:
        """세션 잠금 데이터 로드"""
        try:
            with open(self.session_locks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "locked_files": {},
                "lock_history": [],
                "last_updated": datetime.now().isoformat()
            }

    def _save_session_locks(self, data: Dict) -> None:
        """세션 잠금 데이터 저장"""
        with open(self.session_locks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)