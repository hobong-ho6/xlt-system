"""
Claude 세션 간 협업 시스템 메인 관리자

XLT System v5.1.0 통합 협업 시스템
- 전체 협업 시스템 조율
- 세션 등록/해제 자동화
- 충돌 감지 및 해결 가이드
- 작업 영역 할당 관리
"""

import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import uuid

from .config import XLTConfig
from .session_manager import SessionManager
from .file_lock_manager import FileLockManager
from ..utils.git_integration import GitIntegration


class CollaborationManager:
    """메인 협업 시스템 관리자"""

    def __init__(self, config: Optional[XLTConfig] = None):
        """
        Args:
            config: XLTConfig 인스턴스 (None이면 기본 설정)
        """
        self.config = config or XLTConfig()

        # 협업 디렉토리 경로
        self.claude_dir = Path.home() / ".claude" / "projects" / "-Users-user-Documents-XLTTT"
        self.collab_dir = self.claude_dir / "collaboration"
        self.work_zones_dir = self.collab_dir / "work_zones"

        # 작업 영역 관리 파일
        self.zone_assignments_file = self.work_zones_dir / "zone_assignments.json"
        self.zone_conflicts_file = self.work_zones_dir / "zone_conflicts.json"

        # 핵심 컴포넌트 초기화
        self.session_manager = SessionManager(config)
        self.file_lock_manager = FileLockManager(config)
        self.git_integration = GitIntegration(config)

        # 작업 영역 정의
        self.work_zones = {
            "Zone_A": {
                "name": "Version Control",
                "files": ["version.json", "auto_update_config.json"],
                "risk_level": "critical",
                "max_concurrent": 1,
                "description": "버전 정보 및 자동 업데이트 설정"
            },
            "Zone_B": {
                "name": "Web Server",
                "files": ["stable_web_server.py"],
                "risk_level": "high",
                "max_concurrent": 1,
                "description": "Flask 웹 서버 및 API 엔드포인트"
            },
            "Zone_C": {
                "name": "Translation Engine",
                "files": ["xlt/translation/*"],
                "risk_level": "medium",
                "max_concurrent": 2,
                "description": "번역 엔진 및 Claude 통합"
            },
            "Zone_D": {
                "name": "Input Processing",
                "files": ["xlt/input/*", "xlt/ocr/*"],
                "risk_level": "low",
                "max_concurrent": -1,  # 무제한
                "description": "입력 처리 및 OCR 시스템"
            },
            "Zone_E": {
                "name": "UI/Templates",
                "files": ["templates/*", "static/*"],
                "risk_level": "low",
                "max_concurrent": -1,  # 무제한
                "description": "사용자 인터페이스 및 템플릿"
            }
        }

        # 영역 의존성 매트릭스 (0: 독립, 1: 약간 의존, 2: 강한 의존)
        self.zone_dependencies = {
            "Zone_A": {"Zone_B": 1, "Zone_C": 0, "Zone_D": 0, "Zone_E": 1},
            "Zone_B": {"Zone_A": 1, "Zone_C": 2, "Zone_D": 1, "Zone_E": 1},
            "Zone_C": {"Zone_A": 0, "Zone_B": 2, "Zone_D": 1, "Zone_E": 0},
            "Zone_D": {"Zone_A": 0, "Zone_B": 1, "Zone_C": 1, "Zone_E": 1},
            "Zone_E": {"Zone_A": 1, "Zone_B": 1, "Zone_C": 0, "Zone_D": 1}
        }

        # 백그라운드 모니터링 설정
        self._monitoring_active = False
        self._monitoring_thread = None
        self._monitoring_interval = 30  # 30초 간격

        # 디렉토리 존재 확인
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리가 존재하는지 확인하고 생성"""
        self.work_zones_dir.mkdir(parents=True, exist_ok=True)

        # 기본 파일들 생성
        if not self.zone_assignments_file.exists():
            self._create_default_zone_assignments()

        if not self.zone_conflicts_file.exists():
            self._create_default_zone_conflicts()

    def _create_default_zone_assignments(self) -> None:
        """기본 작업 영역 할당 파일 생성"""
        assignments = {
            "zones": {},
            "last_updated": datetime.now().isoformat()
        }

        # 각 영역 초기화
        for zone_id, zone_info in self.work_zones.items():
            assignments["zones"][zone_id] = {
                **zone_info,
                "current_assignees": [],
                "assignment_history": []
            }

        with open(self.zone_assignments_file, 'w', encoding='utf-8') as f:
            json.dump(assignments, f, ensure_ascii=False, indent=2)

    def _create_default_zone_conflicts(self) -> None:
        """기본 영역 충돌 파일 생성"""
        conflicts = {
            "active_conflicts": [],
            "resolved_conflicts": [],
            "conflict_statistics": {
                "total_conflicts": 0,
                "resolved_count": 0,
                "avg_resolution_time": 0
            },
            "last_updated": datetime.now().isoformat()
        }

        with open(self.zone_conflicts_file, 'w', encoding='utf-8') as f:
            json.dump(conflicts, f, ensure_ascii=False, indent=2)

    def start_collaboration_session(self, task_description: str, requested_zone: Optional[str] = None) -> Dict[str, Any]:
        """
        협업 세션 시작

        Args:
            task_description: 작업 설명
            requested_zone: 요청한 작업 영역 (Zone_A ~ Zone_E)

        Returns:
            Dict: 세션 시작 결과
        """
        try:
            # 1. 세션 등록
            session_id, success = self.session_manager.register_session(task_description, requested_zone)

            if not success:
                return {
                    "success": False,
                    "message": "세션 등록 실패 - 최대 세션 수 초과",
                    "session_id": None
                }

            # 2. 작업 영역 할당
            zone_result = self._assign_work_zone(session_id, requested_zone, task_description)

            # 3. 충돌 감지 및 위험 분석
            conflict_analysis = self._analyze_potential_conflicts(session_id, zone_result.get("assigned_zone"))

            # 4. 파일 잠금 (필요한 경우)
            lock_results = []
            if zone_result.get("success") and zone_result.get("critical_files"):
                for file_path in zone_result["critical_files"]:
                    lock_success, lock_message = self.file_lock_manager.acquire_lock(file_path, session_id)
                    lock_results.append({
                        "file": file_path,
                        "locked": lock_success,
                        "message": lock_message
                    })

            # 5. 백그라운드 모니터링 시작 (아직 활성화되지 않았다면)
            if not self._monitoring_active:
                self.start_background_monitoring()

            return {
                "success": True,
                "session_id": session_id,
                "zone_assignment": zone_result,
                "conflict_analysis": conflict_analysis,
                "file_locks": lock_results,
                "recommendations": self._generate_session_recommendations(
                    conflict_analysis, zone_result
                ),
                "message": "협업 세션 시작 성공"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"협업 세션 시작 실패: {e}",
                "session_id": None
            }

    def end_collaboration_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        협업 세션 종료

        Args:
            session_id: 종료할 세션 ID (None이면 현재 세션)

        Returns:
            Dict: 세션 종료 결과
        """
        try:
            target_session_id = session_id or self.session_manager.current_session_id

            if not target_session_id:
                return {
                    "success": False,
                    "message": "종료할 세션이 없습니다"
                }

            # 1. 파일 잠금 해제
            released_locks = self.file_lock_manager.release_session_locks(target_session_id)

            # 2. 작업 영역 할당 해제
            zone_release_result = self._release_work_zone(target_session_id)

            # 3. 세션 종료
            session_end_success = self.session_manager.end_session(target_session_id)

            # 4. 세션 통계 생성
            session_stats = self._generate_session_statistics(target_session_id)

            return {
                "success": session_end_success,
                "session_id": target_session_id,
                "released_locks": released_locks,
                "zone_release": zone_release_result,
                "session_statistics": session_stats,
                "message": "협업 세션 종료 성공" if session_end_success else "세션 종료 중 오류 발생"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"협업 세션 종료 실패: {e}"
            }

    def check_collaboration_status(self) -> Dict[str, Any]:
        """현재 협업 상태 확인"""
        try:
            # 1. 활성 세션 목록
            active_sessions = self.session_manager.get_active_sessions()

            # 2. 작업 영역 할당 현황
            zone_assignments = self._load_zone_assignments()

            # 3. 파일 잠금 현황
            locked_files = self._get_all_locked_files()

            # 4. 충돌 위험 분석
            conflict_risks = self._analyze_current_conflicts()

            # 5. Git 상태
            git_status = self.git_integration.get_git_status()

            # 6. 시스템 건강 상태
            system_health = self._check_system_health()

            return {
                "timestamp": datetime.now().isoformat(),
                "active_sessions": len(active_sessions),
                "session_details": active_sessions,
                "zone_assignments": self._summarize_zone_assignments(zone_assignments),
                "locked_files": locked_files,
                "conflict_risks": conflict_risks,
                "git_status": git_status,
                "system_health": system_health,
                "monitoring_active": self._monitoring_active
            }

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def request_zone_assignment(self, session_id: str, zone_id: str, force: bool = False) -> Dict[str, Any]:
        """
        작업 영역 할당 요청

        Args:
            session_id: 요청하는 세션 ID
            zone_id: 요청할 영역 ID (Zone_A ~ Zone_E)
            force: 강제 할당 여부

        Returns:
            Dict: 할당 결과
        """
        try:
            # 영역 유효성 검사
            if zone_id not in self.work_zones:
                return {
                    "success": False,
                    "message": f"유효하지 않은 영역: {zone_id}"
                }

            # 현재 할당 현황 확인
            zone_assignments = self._load_zone_assignments()
            zone_info = zone_assignments["zones"][zone_id]

            # 할당 가능성 검사
            current_count = len(zone_info["current_assignees"])
            max_count = zone_info["max_concurrent"]

            if max_count != -1 and current_count >= max_count and not force:
                return {
                    "success": False,
                    "message": f"영역 {zone_id} 할당 한계 초과 ({current_count}/{max_count})",
                    "current_assignees": zone_info["current_assignees"],
                    "suggested_alternatives": self._suggest_alternative_zones(zone_id)
                }

            # 의존성 충돌 검사
            dependency_conflicts = self._check_zone_dependencies(session_id, zone_id)

            if dependency_conflicts and not force:
                return {
                    "success": False,
                    "message": "영역 의존성 충돌 감지",
                    "conflicts": dependency_conflicts,
                    "recommendation": "순차 작업 또는 사전 조율 필요"
                }

            # 할당 실행
            assignment_result = self._execute_zone_assignment(session_id, zone_id)

            return assignment_result

        except Exception as e:
            return {
                "success": False,
                "message": f"영역 할당 요청 실패: {e}"
            }

    def detect_conflicts(self, session_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        충돌 감지 및 분석

        Args:
            session_ids: 분석할 세션 ID 목록 (None이면 모든 활성 세션)

        Returns:
            Dict: 충돌 분석 결과
        """
        try:
            # 활성 세션 조회
            if session_ids is None:
                active_sessions = self.session_manager.get_active_sessions()
                session_ids = [s["session_id"] for s in active_sessions]

            if len(session_ids) < 2:
                return {
                    "conflicts_detected": False,
                    "message": "충돌 분석에 필요한 최소 세션 수 부족"
                }

            # 세션 조합별 충돌 분석
            conflicts = []
            for i in range(len(session_ids)):
                for j in range(i + 1, len(session_ids)):
                    session1_id = session_ids[i]
                    session2_id = session_ids[j]

                    # 각 세션의 잠긴 파일 조회
                    files1 = self.file_lock_manager.get_locked_files_by_session(session1_id)
                    files2 = self.file_lock_manager.get_locked_files_by_session(session2_id)

                    # 충돌 위험도 계산
                    risk_analysis = self.git_integration.calculate_conflict_risk(files1, files2)

                    if risk_analysis["risk_score"] > 0.1:  # 임계치 이상일 때만 충돌로 간주
                        conflicts.append({
                            "session1": session1_id,
                            "session2": session2_id,
                            "risk_analysis": risk_analysis,
                            "timestamp": datetime.now().isoformat()
                        })

            # 충돌 로그 기록
            if conflicts:
                self.git_integration.log_conflict_event("conflict_detected", {
                    "conflicts": conflicts,
                    "total_sessions": len(session_ids)
                })

            return {
                "conflicts_detected": len(conflicts) > 0,
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
                "overall_risk": self._calculate_overall_risk(conflicts),
                "recommendations": self._generate_conflict_recommendations(conflicts)
            }

        except Exception as e:
            return {
                "error": str(e),
                "conflicts_detected": False
            }

    def start_background_monitoring(self) -> bool:
        """백그라운드 모니터링 시작"""
        try:
            if self._monitoring_active:
                return True

            self._monitoring_active = True
            self._monitoring_thread = threading.Thread(
                target=self._background_monitoring_loop,
                daemon=True
            )
            self._monitoring_thread.start()

            print("🔍 백그라운드 협업 모니터링 시작")
            return True

        except Exception as e:
            print(f"⚠️ 백그라운드 모니터링 시작 실패: {e}")
            return False

    def stop_background_monitoring(self) -> bool:
        """백그라운드 모니터링 중지"""
        try:
            self._monitoring_active = False

            if self._monitoring_thread and self._monitoring_thread.is_alive():
                self._monitoring_thread.join(timeout=5)

            print("🔍 백그라운드 협업 모니터링 중지")
            return True

        except Exception as e:
            print(f"⚠️ 백그라운드 모니터링 중지 실패: {e}")
            return False

    def _background_monitoring_loop(self) -> None:
        """백그라운드 모니터링 루프"""
        while self._monitoring_active:
            try:
                # 1. 비활성 세션 정리
                cleaned_sessions = self.session_manager._cleanup_inactive_sessions()
                if cleaned_sessions > 0:
                    print(f"🧹 비활성 세션 {cleaned_sessions}개 정리됨")

                # 2. 만료된 파일 잠금 정리
                cleaned_locks = self.file_lock_manager.cleanup_expired_locks()
                if cleaned_locks > 0:
                    print(f"🔓 만료된 잠금 {cleaned_locks}개 해제됨")

                # 3. 충돌 감지
                conflict_result = self.detect_conflicts()
                if conflict_result.get("conflicts_detected"):
                    conflict_count = conflict_result.get("conflict_count", 0)
                    print(f"⚠️ 충돌 {conflict_count}개 감지됨")

                # 4. Git 상태 캐시 갱신
                self.git_integration.get_git_status(use_cache=False)

                time.sleep(self._monitoring_interval)

            except Exception as e:
                print(f"⚠️ 백그라운드 모니터링 오류: {e}")
                time.sleep(5)  # 오류 시 짧은 대기

    def _assign_work_zone(self, session_id: str, requested_zone: Optional[str], task_description: str) -> Dict[str, Any]:
        """작업 영역 할당 로직"""
        try:
            if requested_zone:
                # 특정 영역 요청
                return self.request_zone_assignment(session_id, requested_zone)
            else:
                # 자동 할당 (작업 설명 기반)
                suggested_zone = self._suggest_zone_from_task(task_description)
                return self.request_zone_assignment(session_id, suggested_zone)

        except Exception as e:
            return {
                "success": False,
                "message": f"작업 영역 할당 실패: {e}"
            }

    def _analyze_potential_conflicts(self, session_id: str, assigned_zone: Optional[str]) -> Dict[str, Any]:
        """잠재적 충돌 분석"""
        try:
            # 현재 활성 세션들과의 충돌 분석
            active_sessions = self.session_manager.get_active_sessions()
            other_sessions = [s for s in active_sessions if s["session_id"] != session_id]

            if not other_sessions:
                return {
                    "conflict_risk": 0.0,
                    "risk_level": "none",
                    "message": "다른 활성 세션이 없어 충돌 위험 없음"
                }

            # 각 세션과의 위험도 계산
            total_risk = 0.0
            session_risks = []

            for other_session in other_sessions:
                other_zone = other_session.get("work_zone")

                if assigned_zone and other_zone:
                    # 영역 기반 위험도
                    zone_risk = self._calculate_zone_conflict_risk(assigned_zone, other_zone)

                    session_risks.append({
                        "other_session": other_session["session_id"],
                        "other_zone": other_zone,
                        "risk_score": zone_risk,
                        "task": other_session.get("task_description", "")
                    })

                    total_risk += zone_risk

            avg_risk = total_risk / len(other_sessions) if other_sessions else 0.0

            return {
                "conflict_risk": round(avg_risk, 3),
                "risk_level": self._determine_risk_level(avg_risk),
                "session_risks": session_risks,
                "total_active_sessions": len(other_sessions),
                "message": self._generate_risk_message(avg_risk)
            }

        except Exception as e:
            return {
                "error": str(e),
                "conflict_risk": 1.0,
                "risk_level": "high"
            }

    def _determine_risk_level(self, risk_score: float) -> str:
        """위험도 점수를 레벨로 변환"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.3:
            return "medium"
        elif risk_score > 0.0:
            return "low"
        else:
            return "none"

    def _generate_risk_message(self, risk_score: float) -> str:
        """위험도 기반 메시지 생성"""
        level = self._determine_risk_level(risk_score)

        messages = {
            "critical": "매우 높은 충돌 위험 - 즉시 조율 필요",
            "high": "높은 충돌 위험 - 순차 작업 권장",
            "medium": "중간 충돌 위험 - 주의 깊은 협업 필요",
            "low": "낮은 충돌 위험 - 일반적인 주의 필요",
            "none": "충돌 위험 없음"
        }

        return messages.get(level, "위험도 분석 불가")

    def _calculate_zone_conflict_risk(self, zone1: str, zone2: str) -> float:
        """영역 간 충돌 위험도 계산"""
        if zone1 == zone2:
            return 0.9  # 같은 영역은 높은 위험도

        # 의존성 매트릭스 기반 위험도
        dependency_score = self.zone_dependencies.get(zone1, {}).get(zone2, 0)

        # 의존성 점수를 위험도로 변환 (0~2 → 0~0.6)
        return dependency_score * 0.3

    def _generate_session_recommendations(self, conflict_analysis: Dict, zone_result: Dict) -> List[str]:
        """세션 시작 시 추천사항 생성"""
        recommendations = []

        # 충돌 위험 기반 추천
        risk_level = conflict_analysis.get("risk_level", "none")

        if risk_level == "critical":
            recommendations.append("🚨 즉시 다른 세션과 조율하세요")
            recommendations.append("📞 Slack/이메일로 사전 협의 필수")
        elif risk_level == "high":
            recommendations.append("⚠️ 순차 작업을 권장합니다")
            recommendations.append("🔄 실시간 Git 상태 모니터링 필요")
        elif risk_level == "medium":
            recommendations.append("💡 주의 깊은 협업이 필요합니다")
            recommendations.append("📋 정기적인 충돌 체크 권장")
        elif risk_level == "low":
            recommendations.append("✅ 일반적인 Git 워크플로우 준수")
        else:
            recommendations.append("🚀 안전한 독립 작업 가능")

        # 영역 기반 추천
        if zone_result.get("assigned_zone") == "Zone_A":
            recommendations.append("🔒 version.json 수정 시 즉시 커밋 필요")
        elif zone_result.get("assigned_zone") == "Zone_B":
            recommendations.append("🌐 웹 서버 재시작 시 다른 세션에 알림")

        return recommendations

    def _suggest_zone_from_task(self, task_description: str) -> str:
        """작업 설명에서 적절한 영역 추천"""
        task_lower = task_description.lower()

        # 키워드 기반 영역 매핑
        zone_keywords = {
            "Zone_A": ["version", "update", "config", "버전", "업데이트", "설정"],
            "Zone_B": ["server", "api", "route", "endpoint", "flask", "서버", "API"],
            "Zone_C": ["translation", "translate", "claude", "번역", "품질"],
            "Zone_D": ["ocr", "input", "figma", "이미지", "입력"],
            "Zone_E": ["ui", "template", "html", "css", "frontend", "템플릿", "프론트"]
        }

        # 키워드 매칭 점수 계산
        best_zone = "Zone_C"  # 기본값 (가장 일반적)
        best_score = 0

        for zone, keywords in zone_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > best_score:
                best_score = score
                best_zone = zone

        return best_zone

    # 추가 헬퍼 메서드들...
    def _load_zone_assignments(self) -> Dict:
        """작업 영역 할당 데이터 로드"""
        try:
            with open(self.zone_assignments_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._create_default_zone_assignments()
            return self._load_zone_assignments()

    def _save_zone_assignments(self, data: Dict) -> None:
        """작업 영역 할당 데이터 저장"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.zone_assignments_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _execute_zone_assignment(self, session_id: str, zone_id: str) -> Dict[str, Any]:
        """영역 할당 실행"""
        try:
            zone_assignments = self._load_zone_assignments()

            # 할당 실행
            zone_assignments["zones"][zone_id]["current_assignees"].append(session_id)

            # 히스토리 추가
            assignment_entry = {
                "session_id": session_id,
                "assigned_at": datetime.now().isoformat(),
                "status": "active"
            }
            zone_assignments["zones"][zone_id]["assignment_history"].append(assignment_entry)

            # 저장
            self._save_zone_assignments(zone_assignments)

            # 중요 파일 목록 반환
            critical_files = self._get_zone_critical_files(zone_id)

            return {
                "success": True,
                "assigned_zone": zone_id,
                "zone_name": self.work_zones[zone_id]["name"],
                "critical_files": critical_files,
                "current_assignees": zone_assignments["zones"][zone_id]["current_assignees"],
                "message": f"영역 {zone_id} 할당 성공"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"영역 할당 실행 실패: {e}"
            }

    def _get_zone_critical_files(self, zone_id: str) -> List[str]:
        """영역별 중요 파일 목록 조회"""
        zone_info = self.work_zones.get(zone_id, {})
        return zone_info.get("files", [])

    def _release_work_zone(self, session_id: str) -> Dict[str, Any]:
        """작업 영역 할당 해제"""
        try:
            zone_assignments = self._load_zone_assignments()
            released_zones = []

            for zone_id, zone_info in zone_assignments["zones"].items():
                if session_id in zone_info["current_assignees"]:
                    # 할당자 목록에서 제거
                    zone_info["current_assignees"].remove(session_id)

                    # 히스토리 업데이트
                    for entry in zone_info["assignment_history"]:
                        if entry["session_id"] == session_id and entry.get("status") == "active":
                            entry["status"] = "completed"
                            entry["released_at"] = datetime.now().isoformat()
                            break

                    released_zones.append(zone_id)

            # 저장
            self._save_zone_assignments(zone_assignments)

            return {
                "success": True,
                "released_zones": released_zones,
                "message": f"{len(released_zones)}개 영역에서 할당 해제됨"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"영역 할당 해제 실패: {e}"
            }

    def _get_all_locked_files(self) -> Dict[str, Dict]:
        """모든 잠긴 파일 현황 조회"""
        try:
            locks_data = self.file_lock_manager._load_session_locks()
            return locks_data.get("locked_files", {})
        except Exception:
            return {}

    def _summarize_zone_assignments(self, zone_assignments: Dict) -> Dict[str, Any]:
        """영역 할당 현황 요약"""
        summary = {}

        for zone_id, zone_info in zone_assignments.get("zones", {}).items():
            assignee_count = len(zone_info.get("current_assignees", []))
            max_count = zone_info.get("max_concurrent", -1)

            summary[zone_id] = {
                "name": zone_info.get("name", ""),
                "assignee_count": assignee_count,
                "max_concurrent": max_count,
                "is_full": max_count != -1 and assignee_count >= max_count,
                "current_assignees": zone_info.get("current_assignees", [])
            }

        return summary

    def _analyze_current_conflicts(self) -> Dict[str, Any]:
        """현재 충돌 위험 분석"""
        try:
            conflict_result = self.detect_conflicts()
            return {
                "has_conflicts": conflict_result.get("conflicts_detected", False),
                "conflict_count": conflict_result.get("conflict_count", 0),
                "overall_risk": conflict_result.get("overall_risk", 0.0)
            }
        except Exception:
            return {
                "has_conflicts": False,
                "conflict_count": 0,
                "overall_risk": 0.0,
                "error": "충돌 분석 실패"
            }

    def _check_system_health(self) -> Dict[str, Any]:
        """시스템 건강 상태 확인"""
        try:
            health_checks = {
                "session_manager": self.session_manager is not None,
                "file_lock_manager": self.file_lock_manager is not None,
                "git_integration": self.git_integration is not None,
                "directories_exist": all([
                    self.collab_dir.exists(),
                    self.work_zones_dir.exists(),
                    self.zone_assignments_file.exists()
                ]),
                "monitoring_active": self._monitoring_active
            }

            health_score = sum(health_checks.values()) / len(health_checks)

            return {
                "health_score": round(health_score, 3),
                "status": "healthy" if health_score >= 0.8 else "degraded",
                "checks": health_checks
            }

        except Exception as e:
            return {
                "health_score": 0.0,
                "status": "error",
                "error": str(e)
            }

    def _calculate_overall_risk(self, conflicts: List[Dict]) -> float:
        """전체 위험도 계산"""
        if not conflicts:
            return 0.0

        total_risk = sum(c["risk_analysis"]["risk_score"] for c in conflicts)
        return round(total_risk / len(conflicts), 3)

    def _generate_conflict_recommendations(self, conflicts: List[Dict]) -> List[str]:
        """충돌 기반 추천사항 생성"""
        if not conflicts:
            return ["🚀 충돌 없음 - 안전한 병렬 작업 가능"]

        recommendations = []
        high_risk_count = sum(1 for c in conflicts if c["risk_analysis"]["risk_score"] >= 0.6)

        if high_risk_count > 0:
            recommendations.append(f"🚨 고위험 충돌 {high_risk_count}개 - 즉시 조율 필요")
            recommendations.append("📞 관련 세션과 사전 협의 권장")

        if len(conflicts) > 2:
            recommendations.append("🔄 순차 작업 고려")
            recommendations.append("📋 작업 우선순위 재조정 필요")

        recommendations.append("🔍 실시간 모니터링 활성화")

        return recommendations

    def _generate_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """세션 통계 생성"""
        try:
            session_info = self.session_manager.get_session_info(session_id)

            if not session_info:
                return {"error": "세션 정보를 찾을 수 없음"}

            created_at = datetime.fromisoformat(session_info["created_at"])
            duration = datetime.now() - created_at

            locked_files = self.file_lock_manager.get_locked_files_by_session(session_id)

            return {
                "session_duration": str(duration),
                "duration_minutes": int(duration.total_seconds() / 60),
                "locked_files_count": len(locked_files),
                "work_zone": session_info.get("work_zone"),
                "task_description": session_info.get("task_description", ""),
                "git_branch": session_info.get("git_branch", "unknown"),
                "git_commit": session_info.get("git_commit", "unknown")
            }

        except Exception as e:
            return {"error": str(e)}

    def _suggest_alternative_zones(self, requested_zone: str) -> List[str]:
        """대안 영역 제안"""
        alternatives = []

        # 의존성이 낮은 영역들을 대안으로 제안
        for zone_id in self.work_zones.keys():
            if zone_id != requested_zone:
                dependency = self.zone_dependencies.get(requested_zone, {}).get(zone_id, 0)
                if dependency <= 1:  # 낮은 의존성
                    alternatives.append(zone_id)

        return alternatives

    def _check_zone_dependencies(self, session_id: str, zone_id: str) -> List[Dict]:
        """영역 의존성 충돌 검사"""
        conflicts = []

        try:
            zone_assignments = self._load_zone_assignments()

            # 의존성이 있는 다른 영역들의 할당 상태 확인
            for other_zone, dependency_level in self.zone_dependencies.get(zone_id, {}).items():
                if dependency_level >= 2:  # 강한 의존성만 체크
                    other_assignees = zone_assignments["zones"][other_zone]["current_assignees"]
                    if other_assignees and session_id not in other_assignees:
                        conflicts.append({
                            "conflicting_zone": other_zone,
                            "dependency_level": dependency_level,
                            "current_assignees": other_assignees,
                            "message": f"강한 의존성이 있는 {other_zone}에 다른 세션이 작업 중"
                        })

            return conflicts

        except Exception as e:
            return [{"error": str(e)}]