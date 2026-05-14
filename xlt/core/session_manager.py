"""
Claude 세션 생명주기 관리 시스템

XLT System v5.1.0 호환 세션 관리자
- 세션 ID 생성 및 추적
- 세션 상태 업데이트 (활성/비활성/완료)
- 30분 비활성 세션 자동 정리
"""

import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .config import XLTConfig


class SessionManager:
    """클로드 세션 관리자"""

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
        self.active_sessions_file = self.sessions_dir / "active_sessions.json"
        self.session_locks_file = self.sessions_dir / "session_locks.json"

        # 세션 타임아웃 설정 (기본 30분)
        self.session_timeout = timedelta(minutes=getattr(config, 'session_timeout_minutes', 30))

        # 현재 세션 ID
        self.current_session_id = None

        # 디렉토리 존재 확인
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리가 존재하는지 확인하고 생성"""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        # 기본 JSON 파일들이 없으면 생성
        if not self.active_sessions_file.exists():
            self._create_default_active_sessions()

        if not self.session_locks_file.exists():
            self._create_default_session_locks()

    def _create_default_active_sessions(self) -> None:
        """기본 활성 세션 파일 생성"""
        default_data = {
            "sessions": [],
            "last_updated": datetime.now().isoformat(),
            "session_count": 0,
            "max_sessions": getattr(self.config, 'max_concurrent_sessions', 10)
        }

        with open(self.active_sessions_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

    def _create_default_session_locks(self) -> None:
        """기본 세션 잠금 파일 생성"""
        default_data = {
            "locked_files": {},
            "lock_history": [],
            "last_updated": datetime.now().isoformat()
        }

        with open(self.session_locks_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

    def generate_session_id(self) -> str:
        """고유한 세션 ID 생성"""
        timestamp = int(time.time())
        random_part = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{random_part}"

    def register_session(self, task_description: str, work_zone: Optional[str] = None) -> Tuple[str, bool]:
        """
        새로운 세션 등록

        Args:
            task_description: 작업 설명
            work_zone: 요청한 작업 영역 (Zone_A ~ Zone_E)

        Returns:
            Tuple[session_id, success]: (세션 ID, 등록 성공 여부)
        """
        try:
            # 비활성 세션 자동 정리
            self._cleanup_inactive_sessions()

            # 활성 세션 목록 로드
            sessions_data = self._load_active_sessions()

            # 최대 세션 수 체크
            if len(sessions_data['sessions']) >= sessions_data['max_sessions']:
                return "", False

            # 새 세션 ID 생성
            session_id = self.generate_session_id()

            # 세션 정보 생성
            session_info = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "task_description": task_description,
                "work_zone": work_zone,
                "status": "active",
                "locked_files": [],
                "git_branch": self._get_current_git_branch(),
                "git_commit": self._get_current_git_commit()
            }

            # 세션 목록에 추가
            sessions_data['sessions'].append(session_info)
            sessions_data['session_count'] = len(sessions_data['sessions'])
            sessions_data['last_updated'] = datetime.now().isoformat()

            # 파일에 저장
            self._save_active_sessions(sessions_data)

            # 개별 세션 파일 생성
            self._create_session_file(session_id, session_info)

            # 현재 세션 ID 설정
            self.current_session_id = session_id

            return session_id, True

        except Exception as e:
            print(f"⚠️ 세션 등록 실패: {e}")
            return "", False

    def update_session_activity(self, session_id: Optional[str] = None) -> bool:
        """
        세션 활동 시간 업데이트

        Args:
            session_id: 업데이트할 세션 ID (None이면 현재 세션)

        Returns:
            bool: 업데이트 성공 여부
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False

        try:
            sessions_data = self._load_active_sessions()

            # 해당 세션 찾기
            for session in sessions_data['sessions']:
                if session['session_id'] == target_session_id:
                    session['last_active'] = datetime.now().isoformat()
                    break
            else:
                return False  # 세션을 찾지 못함

            # 업데이트된 데이터 저장
            self._save_active_sessions(sessions_data)

            # 개별 세션 파일도 업데이트
            self._update_session_file(target_session_id, {'last_active': datetime.now().isoformat()})

            return True

        except Exception as e:
            print(f"⚠️ 세션 활동 업데이트 실패: {e}")
            return False

    def end_session(self, session_id: Optional[str] = None) -> bool:
        """
        세션 종료

        Args:
            session_id: 종료할 세션 ID (None이면 현재 세션)

        Returns:
            bool: 종료 성공 여부
        """
        target_session_id = session_id or self.current_session_id
        if not target_session_id:
            return False

        try:
            sessions_data = self._load_active_sessions()

            # 해당 세션 찾아서 제거
            sessions_data['sessions'] = [
                s for s in sessions_data['sessions']
                if s['session_id'] != target_session_id
            ]

            sessions_data['session_count'] = len(sessions_data['sessions'])
            sessions_data['last_updated'] = datetime.now().isoformat()

            # 업데이트된 데이터 저장
            self._save_active_sessions(sessions_data)

            # 개별 세션 파일 상태 업데이트
            self._update_session_file(target_session_id, {
                'status': 'completed',
                'ended_at': datetime.now().isoformat()
            })

            # 현재 세션이었다면 초기화
            if target_session_id == self.current_session_id:
                self.current_session_id = None

            return True

        except Exception as e:
            print(f"⚠️ 세션 종료 실패: {e}")
            return False

    def _cleanup_inactive_sessions(self) -> int:
        """
        비활성 세션 자동 정리 (30분 이상 비활성)

        Returns:
            int: 정리된 세션 수
        """
        try:
            sessions_data = self._load_active_sessions()
            current_time = datetime.now()
            cleaned_count = 0

            active_sessions = []

            for session in sessions_data['sessions']:
                last_active = datetime.fromisoformat(session['last_active'])
                time_diff = current_time - last_active

                if time_diff <= self.session_timeout:
                    active_sessions.append(session)
                else:
                    # 비활성 세션 정리
                    self._update_session_file(session['session_id'], {
                        'status': 'expired',
                        'expired_at': current_time.isoformat()
                    })
                    cleaned_count += 1

            # 활성 세션만 유지
            sessions_data['sessions'] = active_sessions
            sessions_data['session_count'] = len(active_sessions)
            sessions_data['last_updated'] = current_time.isoformat()

            self._save_active_sessions(sessions_data)

            return cleaned_count

        except Exception as e:
            print(f"⚠️ 비활성 세션 정리 실패: {e}")
            return 0

    def get_active_sessions(self) -> List[Dict]:
        """활성 세션 목록 조회"""
        try:
            sessions_data = self._load_active_sessions()
            return sessions_data['sessions']
        except Exception:
            return []

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """특정 세션 정보 조회"""
        try:
            session_file = self.sessions_dir / f"session_{session_id.split('_', 1)[1]}.json"

            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            return None

        except Exception:
            return None

    def _load_active_sessions(self) -> Dict:
        """활성 세션 데이터 로드"""
        try:
            with open(self.active_sessions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 파일이 없거나 손상된 경우 기본값 반환
            return {
                "sessions": [],
                "last_updated": datetime.now().isoformat(),
                "session_count": 0,
                "max_sessions": 10
            }

    def _save_active_sessions(self, data: Dict) -> None:
        """활성 세션 데이터 저장"""
        with open(self.active_sessions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _create_session_file(self, session_id: str, session_info: Dict) -> None:
        """개별 세션 파일 생성"""
        # session_timestamp_random.json 형태로 파일명 생성
        session_filename = f"session_{session_id.split('_', 1)[1]}.json"
        session_file_path = self.sessions_dir / session_filename

        with open(session_file_path, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, ensure_ascii=False, indent=2)

    def _update_session_file(self, session_id: str, updates: Dict) -> None:
        """개별 세션 파일 업데이트"""
        session_filename = f"session_{session_id.split('_', 1)[1]}.json"
        session_file_path = self.sessions_dir / session_filename

        if session_file_path.exists():
            try:
                with open(session_file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                # 업데이트 적용
                session_data.update(updates)

                with open(session_file_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)

            except (json.JSONDecodeError, IOError):
                pass  # 파일 오류 시 무시

    def _get_current_git_branch(self) -> str:
        """현재 Git 브랜치 조회"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.config.config_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    def _get_current_git_commit(self) -> str:
        """현재 Git 커밋 해시 조회"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=self.config.config_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            return "unknown"