"""
Git 통합 및 충돌 감지 시스템

XLT System v5.1.0 호환 Git 모니터링 시스템
- 실시간 Git 상태 모니터링
- 충돌 위험도 자동 계산
- 안전한 병합 타이밍 제안
"""

import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import re
import os

from ..core.config import XLTConfig


class GitIntegration:
    """Git 통합 및 충돌 감지 시스템"""

    def __init__(self, config: Optional[XLTConfig] = None):
        """
        Args:
            config: XLTConfig 인스턴스 (None이면 기본 설정)
        """
        self.config = config or XLTConfig()

        # 프로젝트 루트 경로
        self.repo_path = Path(self.config.config_path)

        # 협업 디렉토리 경로
        self.claude_dir = Path.home() / ".claude" / "projects" / "-Users-user-Documents-XLTTT"
        self.collab_dir = self.claude_dir / "collaboration"
        self.git_dir = self.collab_dir / "git_integration"

        # JSON 파일 경로
        self.conflict_history_file = self.git_dir / "conflict_history.json"
        self.merge_queue_file = self.git_dir / "merge_queue.json"

        # Git 상태 캐시 (30초 TTL)
        self._git_status_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 30

        # 위험 파일 패턴 (정규표현식)
        self.high_risk_patterns = [
            r'stable_web_server\.py',
            r'version\.json',
            r'auto_update_config\.json',
            r'xlt/core/config\.py',
        ]

        # 중요 영역별 라인 패턴 (파일별 민감 구간)
        self.sensitive_line_patterns = {
            'stable_web_server.py': [
                r'@app\.route',  # Flask 라우트 정의
                r'def.*\(',      # 함수 정의
                r'class.*:',     # 클래스 정의
                r'import.*',     # Import 구문
            ],
            'version.json': [
                r'"version"',    # 버전 필드
                r'"build"',      # 빌드 필드
                r'"features"',   # 기능 목록
            ],
            'xlt/translation/claude_translator.py': [
                r'def.*translate',    # 번역 메서드
                r'def.*quality',      # 품질 관련 메서드
                r'class.*Translator', # 번역기 클래스
            ]
        }

        # 디렉토리 존재 확인
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리가 존재하는지 확인하고 생성"""
        self.git_dir.mkdir(parents=True, exist_ok=True)

        # 기본 JSON 파일들이 없으면 생성
        if not self.conflict_history_file.exists():
            self._create_default_conflict_history()

        if not self.merge_queue_file.exists():
            self._create_default_merge_queue()

    def _create_default_conflict_history(self) -> None:
        """기본 충돌 히스토리 파일 생성"""
        default_data = {
            "conflicts": [],
            "resolved_conflicts": [],
            "conflict_patterns": {
                "stable_web_server.py": {
                    "common_areas": ["routes", "logging", "error_handling"],
                    "risk_factors": ["line_proximity", "function_overlap"]
                },
                "version.json": {
                    "common_areas": ["version_number", "features"],
                    "risk_factors": ["concurrent_version_bump"]
                }
            },
            "last_updated": datetime.now().isoformat()
        }

        with open(self.conflict_history_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

    def _create_default_merge_queue(self) -> None:
        """기본 병합 대기열 파일 생성"""
        default_data = {
            "queue": [],
            "processing": [],
            "completed": [],
            "last_updated": datetime.now().isoformat()
        }

        with open(self.merge_queue_file, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)

    def get_git_status(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Git 상태 조회 (캐시 지원)

        Args:
            use_cache: 캐시 사용 여부

        Returns:
            Dict: Git 상태 정보
        """
        current_time = time.time()

        # 캐시 유효성 검사
        if use_cache and (current_time - self._cache_timestamp) < self._cache_ttl:
            return self._git_status_cache

        try:
            # Git 상태 정보 수집
            git_status = self._collect_git_status()

            # 캐시 업데이트
            self._git_status_cache = git_status
            self._cache_timestamp = current_time

            return git_status

        except Exception as e:
            return {
                "error": str(e),
                "branch": "unknown",
                "modified_files": [],
                "staged_files": [],
                "untracked_files": [],
                "is_clean": False
            }

    def calculate_conflict_risk(self, session1_files: List[str], session2_files: List[str]) -> Dict[str, Any]:
        """
        두 세션 간 충돌 위험도 계산

        Args:
            session1_files: 세션1에서 수정 중인 파일 목록
            session2_files: 세션2에서 수정 중인 파일 목록

        Returns:
            Dict: 충돌 위험도 분석 결과
        """
        try:
            # 파일 교집합 계산
            overlapping_files = set(session1_files) & set(session2_files)

            if not overlapping_files:
                return {
                    "risk_score": 0.0,
                    "risk_level": "safe",
                    "overlapping_files": [],
                    "recommendation": "병렬 작업 가능",
                    "details": "수정 파일이 겹치지 않음"
                }

            # 파일별 위험도 계산
            file_risks = []
            total_risk = 0.0

            for file_path in overlapping_files:
                file_risk = self._calculate_file_risk(file_path)
                file_risks.append({
                    "file": file_path,
                    "risk_score": file_risk,
                    "risk_factors": self._analyze_file_risk_factors(file_path)
                })
                total_risk += file_risk

            # 평균 위험도
            avg_risk = total_risk / len(overlapping_files) if overlapping_files else 0.0

            # 위험 수준 결정
            risk_level = self._determine_risk_level(avg_risk)

            # 추천 사항 생성
            recommendation = self._generate_recommendation(avg_risk, overlapping_files)

            return {
                "risk_score": round(avg_risk, 3),
                "risk_level": risk_level,
                "overlapping_files": list(overlapping_files),
                "file_risks": file_risks,
                "recommendation": recommendation,
                "details": self._generate_risk_details(overlapping_files, avg_risk)
            }

        except Exception as e:
            return {
                "error": str(e),
                "risk_score": 1.0,
                "risk_level": "high",
                "recommendation": "수동 확인 필요"
            }

    def check_merge_safety(self, target_files: List[str]) -> Dict[str, Any]:
        """
        병합 안전성 검사

        Args:
            target_files: 병합 대상 파일 목록

        Returns:
            Dict: 병합 안전성 분석 결과
        """
        try:
            git_status = self.get_git_status()

            # 현재 Git 상태 검사
            safety_checks = {
                "is_clean_working_tree": len(git_status["modified_files"]) == 0,
                "no_staged_changes": len(git_status["staged_files"]) == 0,
                "no_conflicts": self._check_existing_conflicts(),
                "safe_branch": git_status["branch"] in ["main", "master", "develop"],
                "recent_commits": self._check_recent_commits(hours=1)
            }

            # 전체 안전성 점수 계산
            safety_score = sum(safety_checks.values()) / len(safety_checks)

            # 병합 추천 여부
            is_safe_to_merge = safety_score >= 0.8

            # 위험 요소 분석
            risk_factors = []
            if not safety_checks["is_clean_working_tree"]:
                risk_factors.append("작업 트리에 수정된 파일 존재")

            if not safety_checks["no_staged_changes"]:
                risk_factors.append("스테이지된 변경사항 존재")

            if not safety_checks["no_conflicts"]:
                risk_factors.append("기존 병합 충돌 존재")

            return {
                "is_safe": is_safe_to_merge,
                "safety_score": round(safety_score, 3),
                "safety_checks": safety_checks,
                "risk_factors": risk_factors,
                "recommendation": "병합 가능" if is_safe_to_merge else "병합 전 정리 필요",
                "suggested_actions": self._generate_safety_actions(safety_checks)
            }

        except Exception as e:
            return {
                "error": str(e),
                "is_safe": False,
                "recommendation": "수동 확인 필요"
            }

    def detect_file_conflicts(self, file_path: str, session_ids: List[str]) -> Dict[str, Any]:
        """
        특정 파일의 세션 간 충돌 감지

        Args:
            file_path: 검사할 파일 경로
            session_ids: 관련 세션 ID 목록

        Returns:
            Dict: 파일 충돌 분석 결과
        """
        try:
            # 파일 내용 분석
            file_analysis = self._analyze_file_content(file_path)

            # Git diff 분석 (최근 변경사항)
            recent_changes = self._get_recent_file_changes(file_path, hours=24)

            # 충돌 위험 영역 식별
            conflict_zones = self._identify_conflict_zones(file_path, recent_changes)

            # 세션별 수정 예상 영역 (휴리스틱 기반)
            session_zones = self._predict_session_modification_zones(file_path, session_ids)

            # 충돌 확률 계산
            conflict_probability = self._calculate_zone_overlap_probability(conflict_zones, session_zones)

            return {
                "file_path": file_path,
                "conflict_probability": round(conflict_probability, 3),
                "conflict_zones": conflict_zones,
                "session_zones": session_zones,
                "recent_changes": recent_changes,
                "file_analysis": file_analysis,
                "recommendation": self._generate_file_conflict_recommendation(conflict_probability)
            }

        except Exception as e:
            return {
                "error": str(e),
                "file_path": file_path,
                "conflict_probability": 1.0,
                "recommendation": "수동 확인 필요"
            }

    def log_conflict_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """충돌 이벤트 로그 기록"""
        try:
            conflict_data = self._load_conflict_history()

            event_entry = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "details": details,
                "resolved": False if event_type == "conflict_detected" else True
            }

            if event_type == "conflict_detected":
                conflict_data["conflicts"].append(event_entry)
            else:
                conflict_data["resolved_conflicts"].append(event_entry)

            # 히스토리 크기 제한
            if len(conflict_data["conflicts"]) > 50:
                conflict_data["conflicts"] = conflict_data["conflicts"][-50:]

            if len(conflict_data["resolved_conflicts"]) > 100:
                conflict_data["resolved_conflicts"] = conflict_data["resolved_conflicts"][-100:]

            conflict_data["last_updated"] = datetime.now().isoformat()

            self._save_conflict_history(conflict_data)

        except Exception as e:
            print(f"⚠️ 충돌 이벤트 로그 실패: {e}")

    def _collect_git_status(self) -> Dict[str, Any]:
        """Git 상태 정보 수집"""
        try:
            # git status --porcelain 실행
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Git 상태 조회 실패: {result.stderr}")

            # 현재 브랜치 조회
            branch_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

            # 상태 파싱
            modified_files = []
            staged_files = []
            untracked_files = []

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                status = line[:2]
                file_path = line[3:]

                if status[0] in ['M', 'A', 'D', 'R', 'C']:  # 스테이지된 파일
                    staged_files.append(file_path)

                if status[1] in ['M', 'D']:  # 작업 트리 수정된 파일
                    modified_files.append(file_path)

                if status == '??':  # 추적되지 않는 파일
                    untracked_files.append(file_path)

            return {
                "branch": current_branch,
                "modified_files": modified_files,
                "staged_files": staged_files,
                "untracked_files": untracked_files,
                "is_clean": len(modified_files) == 0 and len(staged_files) == 0,
                "timestamp": datetime.now().isoformat()
            }

        except subprocess.TimeoutExpired:
            raise Exception("Git 명령어 타임아웃")
        except Exception as e:
            raise Exception(f"Git 상태 수집 실패: {e}")

    def _calculate_file_risk(self, file_path: str) -> float:
        """파일별 위험도 계산 (0.0 ~ 1.0)"""
        risk_score = 0.0

        # 고위험 파일 패턴 체크
        for pattern in self.high_risk_patterns:
            if re.search(pattern, file_path):
                risk_score += 0.4
                break

        # 파일 크기 및 복잡도 체크
        try:
            full_path = self.repo_path / file_path
            if full_path.exists():
                file_size = full_path.stat().st_size

                # 큰 파일일수록 위험도 증가
                if file_size > 100000:  # 100KB 이상
                    risk_score += 0.3
                elif file_size > 50000:  # 50KB 이상
                    risk_score += 0.2
                elif file_size > 10000:  # 10KB 이상
                    risk_score += 0.1

                # 최근 수정 빈도 체크
                recent_changes = self._get_recent_file_changes(file_path, hours=168)  # 1주일
                if len(recent_changes) > 10:
                    risk_score += 0.2
                elif len(recent_changes) > 5:
                    risk_score += 0.1

        except Exception:
            # 파일 접근 실패 시 중간 위험도
            risk_score += 0.3

        return min(risk_score, 1.0)

    def _analyze_file_risk_factors(self, file_path: str) -> List[str]:
        """파일 위험 요소 분석"""
        risk_factors = []

        # 고위험 파일 체크
        for pattern in self.high_risk_patterns:
            if re.search(pattern, file_path):
                risk_factors.append(f"고위험 파일: {pattern}")

        # 민감한 영역 체크
        if file_path in self.sensitive_line_patterns:
            risk_factors.append("민감한 코드 영역 포함")

        # 파일 크기 체크
        try:
            full_path = self.repo_path / file_path
            if full_path.exists():
                file_size = full_path.stat().st_size
                if file_size > 50000:
                    risk_factors.append("대용량 파일")

        except Exception:
            risk_factors.append("파일 접근 불가")

        return risk_factors

    def _determine_risk_level(self, risk_score: float) -> str:
        """위험도 점수를 기반으로 위험 수준 결정"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.3:
            return "medium"
        else:
            return "low"

    def _generate_recommendation(self, risk_score: float, overlapping_files: Set[str]) -> str:
        """위험도 기반 추천 사항 생성"""
        if risk_score >= 0.8:
            return "순차 작업 강력 권장 - 충돌 위험 매우 높음"
        elif risk_score >= 0.6:
            return "순차 작업 권장 - 사전 조율 필요"
        elif risk_score >= 0.3:
            return "주의깊은 병렬 작업 가능 - 실시간 동기화 권장"
        else:
            return "안전한 병렬 작업 가능"

    def _generate_risk_details(self, overlapping_files: Set[str], avg_risk: float) -> str:
        """위험도 상세 설명 생성"""
        file_count = len(overlapping_files)
        risk_level = self._determine_risk_level(avg_risk)

        details = f"중복 파일 {file_count}개, 평균 위험도: {avg_risk:.3f} ({risk_level})"

        if any(re.search(pattern, str(overlapping_files)) for pattern in self.high_risk_patterns):
            details += " - 고위험 파일 포함"

        return details

    def _check_existing_conflicts(self) -> bool:
        """기존 병합 충돌 확인"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=U'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return len(result.stdout.strip()) == 0
        except Exception:
            return False

    def _check_recent_commits(self, hours: int = 1) -> bool:
        """최근 커밋 여부 확인"""
        try:
            since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
            result = subprocess.run(
                ['git', 'log', '--since', since_time, '--oneline'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return len(result.stdout.strip()) > 0
        except Exception:
            return False

    def _generate_safety_actions(self, safety_checks: Dict[str, bool]) -> List[str]:
        """안전성 체크 결과 기반 권장 액션 생성"""
        actions = []

        if not safety_checks["is_clean_working_tree"]:
            actions.append("작업 트리 정리: git add . && git commit 또는 git stash")

        if not safety_checks["no_staged_changes"]:
            actions.append("스테이지된 변경사항 처리: git commit 또는 git reset")

        if not safety_checks["no_conflicts"]:
            actions.append("기존 충돌 해결: git status로 충돌 파일 확인")

        if not actions:
            actions.append("모든 안전성 검사 통과 - 병합 진행 가능")

        return actions

    def _analyze_file_content(self, file_path: str) -> Dict[str, Any]:
        """파일 내용 분석"""
        try:
            full_path = self.repo_path / file_path

            if not full_path.exists():
                return {"error": "파일이 존재하지 않음"}

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "line_count": len(content.split('\n')),
                "file_size": len(content),
                "has_sensitive_patterns": any(
                    re.search(pattern, content)
                    for pattern in self.sensitive_line_patterns.get(file_path, [])
                )
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_recent_file_changes(self, file_path: str, hours: int = 24) -> List[Dict]:
        """파일의 최근 변경사항 조회"""
        try:
            since_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')

            result = subprocess.run(
                ['git', 'log', '--since', since_time, '--oneline', '--', file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            changes = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    commit_hash, *message_parts = line.split(' ')
                    changes.append({
                        "commit": commit_hash,
                        "message": ' '.join(message_parts)
                    })

            return changes

        except Exception:
            return []

    def _identify_conflict_zones(self, file_path: str, recent_changes: List[Dict]) -> List[Dict]:
        """파일 내 충돌 위험 영역 식별"""
        # 간단한 휴리스틱: 민감한 패턴이 있는 라인들
        zones = []

        try:
            patterns = self.sensitive_line_patterns.get(file_path, [])
            if patterns:
                zones.append({
                    "zone_type": "sensitive_patterns",
                    "description": f"민감한 코드 영역 ({len(patterns)}개 패턴)",
                    "risk_level": "medium"
                })

        except Exception:
            pass

        return zones

    def _predict_session_modification_zones(self, file_path: str, session_ids: List[str]) -> Dict[str, List]:
        """세션별 수정 예상 영역 예측 (휴리스틱)"""
        # 간단한 예측 로직
        zones = {}

        for session_id in session_ids:
            # 세션별 일반적인 수정 패턴 (실제로는 더 정교한 ML 모델 사용 가능)
            if "stable_web_server.py" in file_path:
                zones[session_id] = ["routes", "api_endpoints", "error_handling"]
            elif "version.json" in file_path:
                zones[session_id] = ["version_number", "features"]
            else:
                zones[session_id] = ["general"]

        return zones

    def _calculate_zone_overlap_probability(self, conflict_zones: List[Dict], session_zones: Dict[str, List]) -> float:
        """영역 겹침 확률 계산"""
        if not conflict_zones or not session_zones:
            return 0.0

        # 간단한 겹침 확률 계산
        overlap_count = 0
        total_combinations = 0

        session_list = list(session_zones.keys())
        for i in range(len(session_list)):
            for j in range(i + 1, len(session_list)):
                total_combinations += 1
                zones1 = set(session_zones[session_list[i]])
                zones2 = set(session_zones[session_list[j]])
                if zones1 & zones2:  # 교집합이 있으면
                    overlap_count += 1

        return overlap_count / total_combinations if total_combinations > 0 else 0.0

    def _generate_file_conflict_recommendation(self, probability: float) -> str:
        """파일 충돌 확률 기반 추천사항 생성"""
        if probability >= 0.8:
            return "높은 충돌 확률 - 순차 작업 필수"
        elif probability >= 0.5:
            return "중간 충돌 확률 - 사전 조율 권장"
        elif probability >= 0.2:
            return "낮은 충돌 확률 - 주의깊은 병렬 작업"
        else:
            return "충돌 확률 낮음 - 안전한 병렬 작업"

    def _load_conflict_history(self) -> Dict:
        """충돌 히스토리 데이터 로드"""
        try:
            with open(self.conflict_history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "conflicts": [],
                "resolved_conflicts": [],
                "conflict_patterns": {},
                "last_updated": datetime.now().isoformat()
            }

    def _save_conflict_history(self, data: Dict) -> None:
        """충돌 히스토리 데이터 저장"""
        with open(self.conflict_history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)