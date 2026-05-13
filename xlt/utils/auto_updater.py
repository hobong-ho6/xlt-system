"""
XLT System 완전 자동화 업데이트 시스템
- 백그라운드 자동 감지
- 트레이 알림
- 원클릭 업데이트
"""

import time
import threading
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Callable
from .updater import XLTUpdater


class AutoUpdateManager:
    """완전 자동화 업데이트 관리자"""

    def __init__(self, check_interval: int = 6 * 3600):  # 6시간마다
        self.updater = XLTUpdater()
        self.check_interval = check_interval
        self.is_running = False
        self.background_thread = None

        # 콜백 함수들
        self.on_update_available = None  # 업데이트 발견 시 호출
        self.on_update_completed = None  # 업데이트 완료 시 호출
        self.on_error = None            # 에러 발생 시 호출

        # 상태 관리
        self.last_check_time = None
        self.last_known_version = None
        self.update_history = []

        # 설정 파일
        self.config_file = Path(__file__).parent.parent.parent / "auto_update_config.json"
        self.load_config()

    def load_config(self):
        """자동 업데이트 설정 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

                self.check_interval = config.get('check_interval', 6 * 3600)
                self.last_check_time = config.get('last_check_time')
                self.last_known_version = config.get('last_known_version')
                self.update_history = config.get('update_history', [])

                # datetime 객체로 변환
                if self.last_check_time:
                    self.last_check_time = datetime.fromisoformat(self.last_check_time)
        except Exception as e:
            print(f"⚠️ 자동 업데이트 설정 로드 실패: {e}")

    def save_config(self):
        """자동 업데이트 설정 저장"""
        try:
            config = {
                'check_interval': self.check_interval,
                'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'last_known_version': self.last_known_version,
                'update_history': self.update_history
            }

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"⚠️ 자동 업데이트 설정 저장 실패: {e}")

    def start_background_check(self):
        """백그라운드 업데이트 감지 시작"""
        if self.is_running:
            return

        self.is_running = True
        self.background_thread = threading.Thread(target=self._background_check_loop, daemon=True)
        self.background_thread.start()
        print("🔍 자동 업데이트 감지 시작됨 (6시간 간격)")

    def stop_background_check(self):
        """백그라운드 업데이트 감지 중지"""
        self.is_running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)
        print("⏹️ 자동 업데이트 감지 중지됨")

    def _background_check_loop(self):
        """백그라운드 체크 루프"""
        while self.is_running:
            try:
                # 즉시 첫 체크, 이후 간격대로
                should_check = (
                    self.last_check_time is None or
                    datetime.now() - self.last_check_time >= timedelta(seconds=self.check_interval)
                )

                if should_check:
                    self.check_for_updates_async()

                # 1분마다 체크 (실제 업데이트 확인은 간격에 따라)
                time.sleep(60)

            except Exception as e:
                print(f"⚠️ 백그라운드 업데이트 체크 오류: {e}")
                if self.on_error:
                    self.on_error(str(e))

    def check_for_updates_async(self) -> Optional[Dict]:
        """비동기 업데이트 확인"""
        try:
            self.last_check_time = datetime.now()
            print(f"🔍 업데이트 확인 중... ({self.last_check_time.strftime('%H:%M:%S')})")

            update_info = self.updater.check_for_updates()

            # 업데이트 가능한 경우
            if update_info.get('update_available'):
                remote_version = update_info.get('remote', {}).get('version', 'unknown')

                # 새로운 버전인지 확인 (중복 알림 방지)
                if remote_version != self.last_known_version:
                    self.last_known_version = remote_version

                    # 업데이트 분류
                    update_classification = self._classify_update(update_info)

                    # 콜백 호출 (트레이 알림 등)
                    if self.on_update_available:
                        self.on_update_available(update_info, update_classification)

                    # 기록 저장
                    self.update_history.append({
                        'detected_at': datetime.now().isoformat(),
                        'version': remote_version,
                        'classification': update_classification,
                        'auto_applied': False
                    })

                    print(f"🎉 새 업데이트 발견: v{remote_version} ({update_classification['priority']})")

            self.save_config()
            return update_info

        except Exception as e:
            print(f"❌ 업데이트 확인 실패: {e}")
            if self.on_error:
                self.on_error(str(e))
            return None

    def _classify_update(self, update_info: Dict) -> Dict[str, str]:
        """업데이트 중요도 및 타입 분류"""
        remote = update_info.get('remote', {})
        current = update_info.get('current', {})

        remote_version = remote.get('version', '0.0.0')
        current_version = current.get('version', '0.0.0').replace('-git', '')
        commit_message = remote.get('message', '').lower()

        # 버전 번호 비교
        try:
            remote_parts = [int(x) for x in remote_version.split('.')]
            current_parts = [int(x) for x in current_version.split('.')]

            # 메이저 버전 업데이트
            if remote_parts[0] > current_parts[0]:
                return {'type': 'major', 'priority': 'high', 'auto_update': False}

            # 마이너 버전 업데이트
            elif remote_parts[1] > current_parts[1]:
                # 중요한 기능 개선인지 확인
                if any(keyword in commit_message for keyword in
                       ['타임아웃', 'timeout', '근본', '성능', 'performance', '버그', 'bug', '수정', 'fix']):
                    return {'type': 'minor_critical', 'priority': 'high', 'auto_update': True}
                else:
                    return {'type': 'minor', 'priority': 'medium', 'auto_update': True}

            # 패치 버전 업데이트
            else:
                if any(keyword in commit_message for keyword in ['보안', 'security', '긴급', 'critical']):
                    return {'type': 'patch_critical', 'priority': 'urgent', 'auto_update': True}
                else:
                    return {'type': 'patch', 'priority': 'low', 'auto_update': True}

        except:
            return {'type': 'unknown', 'priority': 'medium', 'auto_update': False}

    def auto_update_if_safe(self, update_info: Dict, classification: Dict) -> bool:
        """안전한 업데이트인 경우 자동 실행"""
        if not classification.get('auto_update', False):
            return False

        try:
            print(f"🚀 자동 업데이트 시작: {classification['type']}")

            result = self.updater.perform_update(create_backup=True)

            if result['success']:
                # 업데이트 기록 업데이트
                if self.update_history:
                    self.update_history[-1]['auto_applied'] = True
                    self.update_history[-1]['completed_at'] = datetime.now().isoformat()

                self.save_config()

                if self.on_update_completed:
                    self.on_update_completed(result)

                print("✅ 자동 업데이트 완료!")
                return True
            else:
                print(f"❌ 자동 업데이트 실패: {result.get('error', 'unknown')}")
                return False

        except Exception as e:
            print(f"❌ 자동 업데이트 실행 오류: {e}")
            if self.on_error:
                self.on_error(str(e))
            return False

    def set_callbacks(self,
                     on_update_available: Callable = None,
                     on_update_completed: Callable = None,
                     on_error: Callable = None):
        """콜백 함수 설정"""
        self.on_update_available = on_update_available
        self.on_update_completed = on_update_completed
        self.on_error = on_error

    def get_status(self) -> Dict:
        """현재 자동 업데이트 상태 조회"""
        return {
            'is_running': self.is_running,
            'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
            'check_interval_hours': self.check_interval / 3600,
            'last_known_version': self.last_known_version,
            'update_history_count': len(self.update_history),
            'next_check_time': (
                self.last_check_time + timedelta(seconds=self.check_interval)
            ).isoformat() if self.last_check_time else None
        }


# macOS 트레이 알림 통합
def setup_tray_notifications(auto_updater: AutoUpdateManager):
    """트레이 시스템과 자동 업데이트 연동"""
    def on_update_available(update_info, classification):
        try:
            # macOS 알림 (rumps 사용)
            import rumps

            remote_version = update_info.get('remote', {}).get('version', 'unknown')
            priority = classification.get('priority', 'medium')

            # 우선도별 알림 스타일
            if priority == 'urgent':
                title = "🚨 긴급 업데이트 필요"
                message = f"v{remote_version} 보안 업데이트가 발견되었습니다."
            elif priority == 'high':
                title = "🎉 중요 업데이트 가능"
                message = f"v{remote_version} 주요 개선사항이 포함된 업데이트입니다."
            else:
                title = "📦 새 업데이트 발견"
                message = f"v{remote_version} 업데이트가 가능합니다."

            # macOS 시스템 알림
            rumps.notification(title=title, subtitle="XLT System", message=message)

            # 자동 업데이트 가능한 경우 실행
            if classification.get('auto_update'):
                auto_updater.auto_update_if_safe(update_info, classification)

        except ImportError:
            # rumps 없는 환경에서는 콘솔 출력
            print(f"🔔 업데이트 알림: v{update_info.get('remote', {}).get('version', 'unknown')}")
        except Exception as e:
            print(f"⚠️ 트레이 알림 실패: {e}")

    def on_update_completed(result):
        try:
            import rumps
            rumps.notification(
                title="✅ 업데이트 완료",
                subtitle="XLT System",
                message="서버를 재시작해주세요."
            )
        except:
            print("✅ 자동 업데이트 완료! 서버를 재시작해주세요.")

    def on_error(error_message):
        print(f"⚠️ 자동 업데이트 오류: {error_message}")

    # 콜백 설정
    auto_updater.set_callbacks(
        on_update_available=on_update_available,
        on_update_completed=on_update_completed,
        on_error=on_error
    )


# 전역 자동 업데이터 인스턴스
_global_auto_updater = None

def get_auto_updater() -> AutoUpdateManager:
    """전역 자동 업데이터 인스턴스 가져오기"""
    global _global_auto_updater
    if _global_auto_updater is None:
        _global_auto_updater = AutoUpdateManager()
        setup_tray_notifications(_global_auto_updater)
    return _global_auto_updater


if __name__ == "__main__":
    # 테스트 실행
    auto_updater = get_auto_updater()
    auto_updater.start_background_check()

    try:
        print("자동 업데이트 시스템 테스트 중... (Ctrl+C로 중지)")
        while True:
            time.sleep(10)
            status = auto_updater.get_status()
            print(f"상태: {status}")
    except KeyboardInterrupt:
        auto_updater.stop_background_check()
        print("테스트 종료")