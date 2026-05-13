#!/usr/bin/env python3
"""
XLT System v3.1 System Tray Application (macOS Native)
rumps 기반 macOS 네이티브 시스템 트레이 앱
"""

import sys
import os
import webbrowser
import subprocess
import time
import socket
from pathlib import Path

try:
    # macOS 전용 트레이 라이브러리 (안정적, 크래시 없음)
    import rumps
    GUI_AVAILABLE = 'rumps'
except ImportError:
    print("❌ rumps 라이브러리를 찾을 수 없습니다.")
    print("💡 설치: pip install rumps")
    GUI_AVAILABLE = None

# XLT 시스템 import
sys.path.insert(0, os.path.dirname(__file__))

try:
    from xlt import XLTConfig, XLTPipeline
except ImportError:
    print("❌ XLT 시스템을 찾을 수 없습니다.")
    print("💡 install.sh 또는 install.bat을 먼저 실행해주세요.")
    sys.exit(1)


class XLTTrayApp(rumps.App):
    """XLT System 트레이 애플리케이션 (rumps 기반)"""

    def __init__(self):
        super(XLTTrayApp, self).__init__("XLT System", "🔷", quit_button=None)

        self.server_process = None
        self.is_server_running = False
        self.base_dir = Path(__file__).parent
        self.server_url = "http://localhost:5004"

        # XLT 시스템 초기화
        try:
            self.config = XLTConfig()
            self.pipeline = XLTPipeline(self.config)
            print("✅ XLT 시스템 초기화 완료")
        except Exception as e:
            print(f"❌ XLT 시스템 초기화 실패: {e}")
            rumps.alert("XLT System 오류", f"초기화 실패: {e}")
            sys.exit(1)

        # 초기 메뉴 구성
        self.setup_menu()

        # 상태 모니터링 타이머 (5초마다)
        self.timer = rumps.Timer(self.check_and_update_menu, 5)
        self.timer.start()

        # 시작 시 서버 자동 실행
        if not self.check_server_status():
            self.start_server_async()

    def setup_menu(self):
        """초기 메뉴 구성"""
        self.menu = [
            rumps.MenuItem('XLT System 열기', callback=self.open_browser),
            rumps.separator,
            rumps.MenuItem('서버 시작', callback=self.menu_start_server),
            rumps.MenuItem('서버 중지', callback=self.menu_stop_server),
            rumps.MenuItem('서버 재시작', callback=self.menu_restart_server),
            rumps.separator,
            rumps.MenuItem('로그 보기', callback=self.view_logs),
            rumps.MenuItem('상태 확인', callback=self.show_status),
            rumps.MenuItem('정보', callback=self.show_about),
            rumps.separator,
            rumps.MenuItem('종료', callback=self.quit_app)
        ]
        self.update_menu_state()

    def check_server_status(self):
        """실제 서버 상태 확인 (프로세스 + 포트)"""
        try:
            # 1. 포트 확인
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5004))
            sock.close()
            port_open = (result == 0)

            # 2. 프로세스 확인
            process_running = (self.server_process and
                             self.server_process.poll() is None)

            # 실제 상태 업데이트
            self.is_server_running = port_open or process_running
            return self.is_server_running

        except Exception:
            self.is_server_running = False
            return False

    def update_menu_state(self):
        """메뉴 항목 활성화/비활성화 업데이트"""
        # 서버 상태에 따라 메뉴 활성화/비활성화
        self.menu['서버 시작'].set_callback(self.menu_start_server if not self.is_server_running else None)
        self.menu['서버 중지'].set_callback(self.menu_stop_server if self.is_server_running else None)
        self.menu['서버 재시작'].set_callback(self.menu_restart_server if self.is_server_running else None)

        # 아이콘 상태 표시 업데이트
        if self.is_server_running:
            self.title = "🟢"  # 실행 중
        else:
            self.title = "🔴"  # 중지됨

    def check_and_update_menu(self, sender):
        """타이머 콜백: 주기적 상태 확인 및 메뉴 업데이트"""
        self.check_server_status()
        self.update_menu_state()

    def start_server_async(self):
        """XLT 웹 서버 비동기 시작"""
        if self.check_server_status():
            print("⚠️ 서버가 이미 실행 중입니다.")
            return

        try:
            # stable_web_server.py를 subprocess로 실행
            server_script = self.base_dir / "stable_web_server.py"

            if not server_script.exists():
                raise FileNotFoundError("stable_web_server.py를 찾을 수 없습니다.")

            # 백그라운드에서 서버 실행
            self.server_process = subprocess.Popen([
                sys.executable, str(server_script)
            ], cwd=str(self.base_dir),
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               text=True)

            print(f"🚀 XLT 서버가 시작되었습니다: {self.server_url}")

            # 서버 시작 대기 후 상태 업데이트
            time.sleep(2)
            self.check_server_status()
            self.update_menu_state()

        except Exception as e:
            print(f"❌ 서버 시작 실패: {e}")
            rumps.alert("서버 시작 실패", str(e))

    def menu_start_server(self, sender):
        """메뉴 콜백: 서버 시작"""
        self.start_server_async()

    def menu_stop_server(self, sender):
        """메뉴 콜백: 서버 중지"""
        try:
            # 프로세스 종료
            if self.server_process and self.server_process.poll() is None:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("🛑 XLT 서버가 종료되었습니다.")

            # 포트 강제 정리 (다른 프로세스가 사용 중일 경우)
            try:
                result = subprocess.run(['lsof', '-ti:5004'], capture_output=True, text=True)
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            subprocess.run(['kill', '-9', pid], check=False)
                        except:
                            pass
                    print("🔥 포트 5004의 모든 프로세스를 종료했습니다.")
            except:
                pass

        except subprocess.TimeoutExpired:
            if self.server_process:
                self.server_process.kill()
                print("🔥 XLT 서버를 강제 종료했습니다.")
        except Exception as e:
            print(f"⚠️ 서버 종료 중 오류: {e}")
        finally:
            # 상태 확인 후 메뉴 업데이트
            time.sleep(1)
            self.check_server_status()
            self.update_menu_state()

    def menu_restart_server(self, sender):
        """메뉴 콜백: 서버 재시작"""
        print("🔄 서버 재시작 중...")

        # 1. 서버 중지
        self.menu_stop_server(None)

        # 2. 잠시 대기
        time.sleep(2)

        # 3. 서버 시작
        self.start_server_async()

        # 사용자 알림
        rumps.notification(
            title="XLT System",
            subtitle="서버 재시작",
            message="서버가 재시작되었습니다."
        )

    def view_logs(self, sender):
        """메뉴 콜백: 로그 보기 (터미널 열기)"""
        try:
            log_file = self.base_dir / "server.log"

            # 로그 파일 존재 확인
            if not log_file.exists():
                rumps.alert("로그 파일 없음", "아직 서버 로그가 생성되지 않았습니다.")
                return

            # macOS 터미널 앱으로 로그 파일 실시간 표시
            # tail -f 명령으로 실시간 로그 확인
            script = f'''
            tell application "Terminal"
                activate
                do script "echo '🔍 XLT System 서버 로그 (실시간)'; echo ''; tail -f '{log_file}'"
            end tell
            '''

            subprocess.run(['osascript', '-e', script], check=True)
            print(f"📋 로그 보기 터미널 열림: {log_file}")

        except Exception as e:
            print(f"❌ 로그 보기 실패: {e}")
            rumps.alert("로그 보기 실패", f"터미널을 열 수 없습니다: {e}")

    def open_browser(self, sender=None):
        """웹 브라우저에서 XLT 시스템 열기"""
        webbrowser.open(self.server_url)

    def show_status(self, sender=None):
        """서버 상태 표시 (실시간 확인)"""
        # 실시간 상태 확인
        current_status = self.check_server_status()
        status_text = "🟢 실행 중" if current_status else "🔴 중지됨"

        # 추가 정보
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5004))
            sock.close()
            port_status = "✅ 포트 열림" if result == 0 else "❌ 포트 닫힘"
        except:
            port_status = "❓ 포트 상태 불명"

        process_status = "✅ 프로세스 실행 중" if (self.server_process and
                                               self.server_process.poll() is None) else "❌ 프로세스 없음"

        message = f"""XLT System v3.1

🔍 현재 상태: {status_text}
🌐 URL: {self.server_url}

📊 상세 정보:
   {port_status}
   {process_status}"""

        rumps.alert("XLT System 상태", message)

    def show_about(self, sender=None):
        """정보 표시"""
        about_text = f"""XLT System v3.1

🎯 피그마 디자인 → 다국어 번역 자동화 도구

✨ 주요 기능:
• 피그마 URL에서 텍스트 자동 추출
• AI 기반 OCR 및 텍스트 필터링
• 5개 언어 동시 번역 (한/영/일/중/태)
• 치환자 시스템 ({{{{0}}}}, {{{{1}}}} 등)
• Excel 파일 자동 생성

🖥️ 웹 인터페이스: {self.server_url}
📁 설치 폴더: {self.base_dir}
        """

        rumps.alert("XLT System 정보", about_text)

    def quit_app(self, sender=None):
        """앱 종료"""
        self.menu_stop_server(None)
        rumps.quit_application()



def main():
    """메인 함수 - rumps 기반 트레이 앱"""
    print("🚀 XLT System v3.1 Tray App 시작 (macOS Native)...")

    if not GUI_AVAILABLE:
        print("❌ rumps 라이브러리가 설치되지 않았습니다.")
        print("💡 설치: pip install rumps")
        print("🔄 웹 서버만 실행합니다...")

        # Fallback: 웹 서버만 실행
        base_dir = Path(__file__).parent
        server_script = base_dir / "stable_web_server.py"
        subprocess.Popen([sys.executable, str(server_script)], cwd=str(base_dir))
        print(f"🌐 웹 서버가 시작되었습니다: http://localhost:5004")
        return

    try:
        print("✅ rumps 기반 macOS 네이티브 트레이 앱")
        print("🎯 시스템 트레이에 XLT 아이콘이 표시됩니다")
        print("💡 메뉴 상태는 5초마다 자동 업데이트됩니다")

        app = XLTTrayApp()
        app.run()

    except Exception as e:
        print(f"❌ 트레이 앱 실행 실패: {e}")
        print("🔄 웹 서버 fallback으로 전환합니다...")

        # Fallback: 웹 서버만 실행
        base_dir = Path(__file__).parent
        server_script = base_dir / "stable_web_server.py"
        subprocess.Popen([sys.executable, str(server_script)], cwd=str(base_dir))
        print(f"🌐 웹 서버가 시작되었습니다: http://localhost:5004")


if __name__ == "__main__":
    main()