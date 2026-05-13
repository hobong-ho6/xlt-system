#!/usr/bin/env python3
"""
XLT System v3.0 System Tray Application
시스템 트레이에서 XLT 시스템을 관리하는 GUI 앱
"""

import sys
import os
import threading
import webbrowser
import subprocess
import time
from pathlib import Path

try:
    # GUI 라이브러리 시도 (우선순위: pystray > tkinter)
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    GUI_AVAILABLE = 'pystray'
except ImportError:
    try:
        import tkinter as tk
        from tkinter import messagebox
        GUI_AVAILABLE = 'tkinter'
        pystray = None
    except ImportError:
        GUI_AVAILABLE = None

# XLT 시스템 import
sys.path.insert(0, os.path.dirname(__file__))

try:
    from xlt import XLTConfig, XLTPipeline
except ImportError:
    print("❌ XLT 시스템을 찾을 수 없습니다.")
    print("💡 install.sh 또는 install.bat을 먼저 실행해주세요.")
    sys.exit(1)


class XLTTrayApp:
    """XLT System 트레이 애플리케이션"""

    def __init__(self):
        self.server_process = None
        self.server_thread = None
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
            if GUI_AVAILABLE == 'tkinter':
                messagebox.showerror("XLT System 오류", f"초기화 실패: {e}")
            sys.exit(1)

    def create_icon_image(self):
        """트레이 아이콘 이미지 생성"""
        # 간단한 아이콘 생성 (64x64)
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)

        # XLT 텍스트 그리기
        draw.rectangle([8, 8, 56, 56], fill='#3b82f6', outline='#1e40af', width=2)
        draw.text((16, 20), "XLT", fill='white')
        draw.text((12, 35), "v3.0", fill='white')

        return image

    def start_server(self):
        """XLT 웹 서버 시작"""
        if self.is_server_running:
            return

        def run_server():
            try:
                # stable_web_server.py를 subprocess로 실행
                server_script = self.base_dir / "stable_web_server.py"

                if not server_script.exists():
                    raise FileNotFoundError("stable_web_server.py를 찾을 수 없습니다.")

                # 서버 실행
                self.server_process = subprocess.Popen([
                    sys.executable, str(server_script)
                ], cwd=str(self.base_dir),
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   text=True)

                self.is_server_running = True
                print(f"🚀 XLT 서버가 시작되었습니다: {self.server_url}")

                # 서버 프로세스 모니터링
                self.server_process.wait()

            except Exception as e:
                print(f"❌ 서버 시작 실패: {e}")
                self.is_server_running = False
            finally:
                self.is_server_running = False

        # 백그라운드 스레드에서 서버 실행
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # 서버 시작 대기
        time.sleep(2)

    def stop_server(self):
        """XLT 웹 서버 종료"""
        if self.server_process and self.server_process.poll() is None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("🛑 XLT 서버가 종료되었습니다.")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                print("🔥 XLT 서버를 강제 종료했습니다.")
            finally:
                self.is_server_running = False

    def open_browser(self):
        """웹 브라우저에서 XLT 시스템 열기"""
        webbrowser.open(self.server_url)

    def show_status(self):
        """서버 상태 표시"""
        status = "🟢 실행 중" if self.is_server_running else "🔴 중지됨"
        message = f"XLT System v3.0\n상태: {status}\nURL: {self.server_url}"

        if GUI_AVAILABLE == 'tkinter':
            messagebox.showinfo("XLT System 상태", message)
        else:
            print(message)

    def show_about(self):
        """정보 표시"""
        about_text = """XLT System v3.0

🎯 피그마 디자인 → 다국어 번역 자동화 도구

✨ 주요 기능:
• 피그마 URL에서 텍스트 자동 추출
• AI 기반 OCR 및 텍스트 필터링
• 5개 언어 동시 번역 (한/영/일/중/태)
• 치환자 시스템 ({{0}}, {{1}} 등)
• Excel 파일 자동 생성

🖥️ 웹 인터페이스: http://localhost:5004
📁 설치 폴더: {install_dir}
        """.format(install_dir=self.base_dir)

        if GUI_AVAILABLE == 'tkinter':
            messagebox.showinfo("XLT System 정보", about_text)
        else:
            print(about_text)

    def quit_app(self):
        """앱 종료"""
        self.stop_server()
        if hasattr(self, 'icon'):
            self.icon.stop()

    def run_pystray(self):
        """PysTray로 실행"""
        # 메뉴 구성
        menu = pystray.Menu(
            item('XLT System 열기', self.open_browser, default=True),
            item('서버 시작', self.start_server, enabled=lambda: not self.is_server_running),
            item('서버 중지', self.stop_server, enabled=lambda: self.is_server_running),
            pystray.Menu.SEPARATOR,
            item('상태 확인', self.show_status),
            item('정보', self.show_about),
            pystray.Menu.SEPARATOR,
            item('종료', self.quit_app)
        )

        # 트레이 아이콘 생성
        self.icon = pystray.Icon("XLT System", self.create_icon_image(),
                                 "XLT System v3.0", menu)

        # 시작 시 자동으로 서버 실행
        self.start_server()

        # 트레이 아이콘 실행
        self.icon.run()

    def run_tkinter(self):
        """Tkinter로 실행 (PysTray 없을 때 대체)"""
        root = tk.Tk()
        root.title("XLT System v3.0")
        root.geometry("300x200")

        # UI 구성
        tk.Label(root, text="XLT System v3.0", font=("Arial", 14, "bold")).pack(pady=10)

        status_label = tk.Label(root, text="상태: 준비됨")
        status_label.pack(pady=5)

        # 버튼들
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="서버 시작", command=self.start_server).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="서버 중지", command=self.stop_server).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="브라우저 열기", command=self.open_browser).pack(side=tk.LEFT, padx=5)

        # 상태 업데이트 함수
        def update_status():
            status = "🟢 실행 중" if self.is_server_running else "🔴 중지됨"
            status_label.config(text=f"상태: {status}")
            root.after(1000, update_status)  # 1초마다 업데이트

        update_status()

        # 시작 시 자동으로 서버 실행
        self.start_server()

        # 종료 시 서버도 함께 종료
        def on_closing():
            self.stop_server()
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    def run(self):
        """앱 실행 (GUI 라이브러리에 따라 분기)"""
        if GUI_AVAILABLE == 'pystray':
            print("🎨 PysTray로 트레이 앱을 시작합니다...")
            self.run_pystray()
        elif GUI_AVAILABLE == 'tkinter':
            print("🖥️  Tkinter로 GUI 앱을 시작합니다...")
            self.run_tkinter()
        else:
            print("❌ GUI 라이브러리를 찾을 수 없습니다.")
            print("💡 다음 중 하나를 설치해주세요:")
            print("   pip install pystray pillow  # 권장 (시스템 트레이)")
            print("   또는 기본 Tkinter 사용 (Python 기본 포함)")
            return False

        return True


def main():
    """메인 함수"""
    print("🚀 XLT System v3.0 Tray App 시작...")

    # GUI 라이브러리 확인 및 안내
    if GUI_AVAILABLE == 'pystray':
        print("✅ PysTray 사용 (시스템 트레이 지원)")
    elif GUI_AVAILABLE == 'tkinter':
        print("✅ Tkinter 사용 (기본 GUI)")
        print("💡 더 나은 경험을 위해 PysTray 설치 권장: pip install pystray pillow")
    else:
        print("❌ GUI 라이브러리 없음")

    # 앱 실행
    app = XLTTrayApp()
    success = app.run()

    if not success:
        # GUI 없을 때 콘솔 모드로 실행
        print("\n📱 콘솔 모드로 실행합니다...")
        print("명령어:")
        print("  start - 서버 시작")
        print("  stop  - 서버 종료")
        print("  open  - 브라우저 열기")
        print("  quit  - 종료")

        app.start_server()

        while True:
            try:
                cmd = input("\n> ").strip().lower()

                if cmd == 'start':
                    app.start_server()
                elif cmd == 'stop':
                    app.stop_server()
                elif cmd == 'open':
                    app.open_browser()
                elif cmd in ['quit', 'exit', 'q']:
                    break
                else:
                    print("알 수 없는 명령어입니다.")

            except KeyboardInterrupt:
                break

        app.quit_app()


if __name__ == "__main__":
    main()