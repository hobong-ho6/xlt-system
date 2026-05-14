#!/usr/bin/env python3
"""
Claude 세션 간 협업 시스템 CLI 인터페이스

XLT System v5.1.0 협업 시스템 명령줄 도구
사용법:
  python claude_collaboration.py status                      # 현재 상태 확인
  python claude_collaboration.py start "작업설명" [--zone=Zone_B]  # 세션 시작
  python claude_collaboration.py end [session_id]           # 세션 종료
  python claude_collaboration.py check-conflicts            # 충돌 검사
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# XLT 모듈 import
sys.path.append(str(Path(__file__).parent))
from xlt.core.collaboration_manager import CollaborationManager
from xlt.core.config import XLTConfig


class CollaborationCLI:
    """협업 시스템 CLI 인터페이스"""

    def __init__(self):
        """CLI 초기화"""
        try:
            self.config = XLTConfig()
            self.collaboration_manager = CollaborationManager(self.config)
            self.success = True
        except Exception as e:
            print(f"❌ 협업 시스템 초기화 실패: {e}")
            self.success = False

    def cmd_status(self, args) -> int:
        """현재 협업 상태 확인"""
        if not self.success:
            return 1

        try:
            print("🔍 협업 시스템 상태 확인 중...")
            status = self.collaboration_manager.check_collaboration_status()

            if "error" in status:
                print(f"❌ 상태 확인 실패: {status['error']}")
                return 1

            # 상태 정보 출력
            print("\n" + "="*60)
            print("🤝 XLT System v5.1.0 - Claude 협업 시스템 상태")
            print("="*60)

            # 기본 정보
            print(f"📅 확인 시간: {status['timestamp']}")
            print(f"🔄 백그라운드 모니터링: {'활성' if status['monitoring_active'] else '비활성'}")

            # 활성 세션
            active_count = status['active_sessions']
            print(f"\n👥 활성 세션: {active_count}개")

            if active_count > 0:
                for i, session in enumerate(status['session_details'], 1):
                    print(f"  {i}. {session['session_id']}")
                    print(f"     📝 작업: {session.get('task_description', 'N/A')}")
                    print(f"     🏷️  영역: {session.get('work_zone', 'N/A')}")
                    print(f"     ⏰ 시작: {session.get('created_at', 'N/A')}")

            # 작업 영역 할당
            print(f"\n🎯 작업 영역 할당 현황:")
            zones = status['zone_assignments']
            for zone_id, zone_info in zones.items():
                status_icon = "🔴" if zone_info['is_full'] else ("🟡" if zone_info['assignee_count'] > 0 else "🟢")
                max_info = f"/{zone_info['max_concurrent']}" if zone_info['max_concurrent'] != -1 else ""
                print(f"  {status_icon} {zone_id}: {zone_info['assignee_count']}{max_info} - {zone_info['name']}")

            # 파일 잠금
            locked_files = status['locked_files']
            if locked_files:
                print(f"\n🔒 잠긴 파일: {len(locked_files)}개")
                for file_path, lock_info in list(locked_files.items())[:5]:  # 최대 5개만 표시
                    print(f"  📁 {file_path} (by {lock_info.get('session_id', 'unknown')})")
                if len(locked_files) > 5:
                    print(f"  ... 외 {len(locked_files) - 5}개")

            # 충돌 위험
            conflict_risks = status['conflict_risks']
            risk_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get("low", "⚪")
            has_conflicts = conflict_risks.get('has_conflicts', False)
            print(f"\n⚠️ 충돌 위험: {risk_color} {'있음' if has_conflicts else '없음'}")
            if has_conflicts:
                print(f"  📊 충돌 수: {conflict_risks.get('conflict_count', 0)}")
                print(f"  📈 위험도: {conflict_risks.get('overall_risk', 0.0)}")

            # Git 상태
            git_status = status['git_status']
            if "error" not in git_status:
                clean_icon = "✅" if git_status.get('is_clean', False) else "⚠️"
                print(f"\n📋 Git 상태: {clean_icon}")
                print(f"  🌿 브랜치: {git_status.get('branch', 'unknown')}")
                modified_count = len(git_status.get('modified_files', []))
                if modified_count > 0:
                    print(f"  📝 수정된 파일: {modified_count}개")

            # 시스템 건강도
            system_health = status['system_health']
            health_score = system_health.get('health_score', 0.0)
            health_icon = "✅" if health_score >= 0.8 else ("⚠️" if health_score >= 0.5 else "❌")
            print(f"\n🏥 시스템 건강도: {health_icon} {health_score:.1%}")

            print("\n" + "="*60)

            return 0

        except Exception as e:
            print(f"❌ 상태 확인 실패: {e}")
            return 1

    def cmd_start(self, args) -> int:
        """협업 세션 시작"""
        if not self.success:
            return 1

        try:
            task_description = args.task_description
            requested_zone = getattr(args, 'zone', None)

            print(f"🚀 협업 세션 시작: {task_description}")
            if requested_zone:
                print(f"🎯 요청 영역: {requested_zone}")

            result = self.collaboration_manager.start_collaboration_session(
                task_description=task_description,
                requested_zone=requested_zone
            )

            if not result['success']:
                print(f"❌ 세션 시작 실패: {result['message']}")
                return 1

            # 성공 정보 출력
            print("\n" + "="*50)
            print("✅ 협업 세션 시작 성공!")
            print("="*50)

            print(f"🆔 세션 ID: {result['session_id']}")

            # 영역 할당 결과
            zone_assignment = result.get('zone_assignment', {})
            if zone_assignment.get('success'):
                zone_id = zone_assignment.get('assigned_zone')
                zone_name = zone_assignment.get('zone_name')
                print(f"🎯 할당된 영역: {zone_id} - {zone_name}")

                # 중요 파일
                critical_files = zone_assignment.get('critical_files', [])
                if critical_files:
                    print(f"📁 관련 파일: {', '.join(critical_files)}")

            # 충돌 분석 결과
            conflict_analysis = result.get('conflict_analysis', {})
            risk_level = conflict_analysis.get('risk_level', 'none')
            risk_score = conflict_analysis.get('conflict_risk', 0.0)

            risk_icons = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢',
                'none': '✅'
            }

            print(f"⚠️ 충돌 위험: {risk_icons.get(risk_level, '⚪')} {risk_level.upper()} (점수: {risk_score})")

            # 파일 잠금 결과
            file_locks = result.get('file_locks', [])
            locked_count = sum(1 for lock in file_locks if lock['locked'])
            if locked_count > 0:
                print(f"🔒 파일 잠금: {locked_count}개 성공")

            # 추천사항
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"\n💡 추천사항:")
                for rec in recommendations:
                    print(f"  • {rec}")

            print(f"\n🔍 실시간 상태 확인: python claude_collaboration.py status")
            print(f"⏹️  세션 종료: python claude_collaboration.py end {result['session_id']}")

            print("\n" + "="*50)

            return 0

        except Exception as e:
            print(f"❌ 세션 시작 실패: {e}")
            return 1

    def cmd_end(self, args) -> int:
        """협업 세션 종료"""
        if not self.success:
            return 1

        try:
            session_id = getattr(args, 'session_id', None)

            if session_id:
                print(f"⏹️ 세션 종료: {session_id}")
            else:
                print("⏹️ 현재 세션 종료")

            result = self.collaboration_manager.end_collaboration_session(session_id)

            if not result['success']:
                print(f"❌ 세션 종료 실패: {result['message']}")
                return 1

            # 성공 정보 출력
            print("\n" + "="*50)
            print("✅ 협업 세션 종료 완료!")
            print("="*50)

            print(f"🆔 세션 ID: {result['session_id']}")
            print(f"🔓 해제된 잠금: {result['released_locks']}개")

            # 세션 통계
            session_stats = result.get('session_statistics', {})
            if 'duration_minutes' in session_stats:
                duration = session_stats['duration_minutes']
                print(f"⏱️ 작업 시간: {duration}분")

            if 'work_zone' in session_stats:
                work_zone = session_stats['work_zone']
                print(f"🎯 작업 영역: {work_zone}")

            locked_files_count = session_stats.get('locked_files_count', 0)
            if locked_files_count > 0:
                print(f"📁 처리된 파일: {locked_files_count}개")

            print("\n🔍 현재 상태 확인: python claude_collaboration.py status")

            print("\n" + "="*50)

            return 0

        except Exception as e:
            print(f"❌ 세션 종료 실패: {e}")
            return 1

    def cmd_check_conflicts(self, args) -> int:
        """충돌 검사"""
        if not self.success:
            return 1

        try:
            print("🔍 충돌 검사 중...")

            result = self.collaboration_manager.detect_conflicts()

            if "error" in result:
                print(f"❌ 충돌 검사 실패: {result['error']}")
                return 1

            # 결과 출력
            print("\n" + "="*50)
            print("🔍 충돌 검사 결과")
            print("="*50)

            conflicts_detected = result.get('conflicts_detected', False)
            conflict_count = result.get('conflict_count', 0)

            if not conflicts_detected:
                print("✅ 충돌 없음 - 안전한 병렬 작업 가능")
            else:
                print(f"⚠️ 충돌 감지: {conflict_count}개")

                # 개별 충돌 정보
                conflicts = result.get('conflicts', [])
                for i, conflict in enumerate(conflicts, 1):
                    risk_info = conflict['risk_analysis']
                    risk_score = risk_info['risk_score']
                    risk_level = risk_info['risk_level']

                    print(f"\n{i}. 충돌 #{i}")
                    print(f"   세션: {conflict['session1']} ↔ {conflict['session2']}")
                    print(f"   위험도: {risk_score} ({risk_level.upper()})")
                    print(f"   파일: {', '.join(risk_info.get('overlapping_files', []))}")
                    print(f"   권장: {risk_info.get('recommendation', 'N/A')}")

            # 전체 위험도
            overall_risk = result.get('overall_risk', 0.0)
            print(f"\n📊 전체 위험도: {overall_risk}")

            # 추천사항
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"\n💡 추천사항:")
                for rec in recommendations:
                    print(f"  • {rec}")

            print("\n" + "="*50)

            return 0

        except Exception as e:
            print(f"❌ 충돌 검사 실패: {e}")
            return 1

    def cmd_monitor(self, args) -> int:
        """백그라운드 모니터링 제어"""
        if not self.success:
            return 1

        try:
            action = getattr(args, 'action', 'status')

            if action == 'start':
                success = self.collaboration_manager.start_background_monitoring()
                if success:
                    print("✅ 백그라운드 모니터링 시작됨")
                else:
                    print("❌ 백그라운드 모니터링 시작 실패")
                return 0 if success else 1

            elif action == 'stop':
                success = self.collaboration_manager.stop_background_monitoring()
                if success:
                    print("⏹️ 백그라운드 모니터링 중지됨")
                else:
                    print("❌ 백그라운드 모니터링 중지 실패")
                return 0 if success else 1

            elif action == 'status':
                is_active = self.collaboration_manager._monitoring_active
                print(f"🔍 백그라운드 모니터링: {'활성' if is_active else '비활성'}")
                return 0

            else:
                print(f"❌ 알 수 없는 액션: {action}")
                return 1

        except Exception as e:
            print(f"❌ 모니터링 제어 실패: {e}")
            return 1

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="XLT System v5.1.0 - Claude 세션 간 협업 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  %(prog)s status                                    # 현재 상태 확인
  %(prog)s start "API 엔드포인트 추가" --zone=Zone_B      # 특정 영역으로 세션 시작
  %(prog)s start "번역 기능 개선"                        # 자동 영역 할당으로 세션 시작
  %(prog)s end                                       # 현재 세션 종료
  %(prog)s end session_1234567890_abcd1234          # 특정 세션 종료
  %(prog)s check-conflicts                          # 충돌 검사
  %(prog)s monitor start                            # 백그라운드 모니터링 시작
  %(prog)s monitor stop                             # 백그라운드 모니터링 중지
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')

    # status 명령어
    status_parser = subparsers.add_parser('status', help='현재 협업 상태 확인')

    # start 명령어
    start_parser = subparsers.add_parser('start', help='협업 세션 시작')
    start_parser.add_argument('task_description', help='작업 설명')
    start_parser.add_argument('--zone', choices=['Zone_A', 'Zone_B', 'Zone_C', 'Zone_D', 'Zone_E'],
                             help='요청할 작업 영역')

    # end 명령어
    end_parser = subparsers.add_parser('end', help='협업 세션 종료')
    end_parser.add_argument('session_id', nargs='?', help='종료할 세션 ID (생략 시 현재 세션)')

    # check-conflicts 명령어
    conflicts_parser = subparsers.add_parser('check-conflicts', help='충돌 검사')

    # monitor 명령어
    monitor_parser = subparsers.add_parser('monitor', help='백그라운드 모니터링 제어')
    monitor_parser.add_argument('action', choices=['start', 'stop', 'status'],
                               default='status', nargs='?', help='모니터링 액션')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # CLI 인스턴스 생성
    cli = CollaborationCLI()

    # 명령어 실행
    command_methods = {
        'status': cli.cmd_status,
        'start': cli.cmd_start,
        'end': cli.cmd_end,
        'check-conflicts': cli.cmd_check_conflicts,
        'monitor': cli.cmd_monitor
    }

    method = command_methods.get(args.command)
    if method:
        return method(args)
    else:
        print(f"❌ 알 수 없는 명령어: {args.command}")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        sys.exit(1)