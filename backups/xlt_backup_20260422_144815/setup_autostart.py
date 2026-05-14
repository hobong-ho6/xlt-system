#!/usr/bin/env python3
"""
XLT System v3.0 자동 시작 설정
부팅 시 XLT System이 자동으로 시작되도록 설정
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


class AutoStartSetup:
    """자동 시작 설정 관리 클래스"""

    def __init__(self):
        self.system = platform.system()
        self.install_dir = Path(__file__).parent.resolve()
        self.tray_script = self.install_dir / "xlt_tray.py"

    def setup_windows(self):
        """Windows 자동 시작 설정"""
        try:
            import winreg
        except ImportError:
            print("❌ Windows 전용 기능입니다.")
            return False

        try:
            # 레지스트리에 자동 시작 등록
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

            # Python 실행 경로 + 트레이 앱 스크립트
            command = f'"{sys.executable}" "{self.tray_script}"'
            winreg.SetValueEx(key, "XLT System", 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)

            print("✅ Windows 자동 시작이 설정되었습니다.")
            print(f"   실행 명령: {command}")
            return True

        except Exception as e:
            print(f"❌ Windows 자동 시작 설정 실패: {e}")
            return False

    def setup_macos(self):
        """macOS 자동 시작 설정 (LaunchAgent)"""
        try:
            # ~/Library/LaunchAgents 디렉토리 생성
            launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
            launch_agents_dir.mkdir(parents=True, exist_ok=True)

            # plist 파일 생성
            plist_path = launch_agents_dir / "com.xlt.system.plist"

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.xlt.system</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{self.tray_script}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{self.install_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{self.install_dir / "logs" / "autostart.log"}</string>
    <key>StandardErrorPath</key>
    <string>{self.install_dir / "logs" / "autostart_error.log"}</string>
</dict>
</plist>"""

            # plist 파일 저장
            with open(plist_path, 'w', encoding='utf-8') as f:
                f.write(plist_content)

            # 권한 설정
            os.chmod(plist_path, 0o644)

            # LaunchAgent 로드
            result = subprocess.run([
                'launchctl', 'load', str(plist_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ macOS 자동 시작이 설정되었습니다.")
                print(f"   LaunchAgent: {plist_path}")
                return True
            else:
                print(f"❌ LaunchAgent 로드 실패: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ macOS 자동 시작 설정 실패: {e}")
            return False

    def setup_linux(self):
        """Linux 자동 시작 설정 (.desktop 파일)"""
        try:
            # ~/.config/autostart 디렉토리 생성
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)

            # .desktop 파일 생성
            desktop_path = autostart_dir / "xlt-system.desktop"

            desktop_content = f"""[Desktop Entry]
Type=Application
Name=XLT System
Comment=피그마 디자인 다국어 번역 도구
Exec={sys.executable} "{self.tray_script}"
Path={self.install_dir}
Icon=applications-internet
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
Categories=Office;Development;
"""

            # .desktop 파일 저장
            with open(desktop_path, 'w', encoding='utf-8') as f:
                f.write(desktop_content)

            # 실행 권한 설정
            os.chmod(desktop_path, 0o755)

            print("✅ Linux 자동 시작이 설정되었습니다.")
            print(f"   Desktop 파일: {desktop_path}")
            return True

        except Exception as e:
            print(f"❌ Linux 자동 시작 설정 실패: {e}")
            return False

    def remove_windows(self):
        """Windows 자동 시작 제거"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "XLT System")
            winreg.CloseKey(key)
            print("✅ Windows 자동 시작이 제거되었습니다.")
            return True
        except Exception as e:
            print(f"❌ Windows 자동 시작 제거 실패: {e}")
            return False

    def remove_macos(self):
        """macOS 자동 시작 제거"""
        try:
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.xlt.system.plist"

            if plist_path.exists():
                # LaunchAgent 언로드
                subprocess.run(['launchctl', 'unload', str(plist_path)],
                              capture_output=True, text=True)

                # plist 파일 삭제
                plist_path.unlink()

            print("✅ macOS 자동 시작이 제거되었습니다.")
            return True
        except Exception as e:
            print(f"❌ macOS 자동 시작 제거 실패: {e}")
            return False

    def remove_linux(self):
        """Linux 자동 시작 제거"""
        try:
            desktop_path = Path.home() / ".config" / "autostart" / "xlt-system.desktop"

            if desktop_path.exists():
                desktop_path.unlink()

            print("✅ Linux 자동 시작이 제거되었습니다.")
            return True
        except Exception as e:
            print(f"❌ Linux 자동 시start 제거 실패: {e}")
            return False

    def setup(self):
        """플랫폼에 맞는 자동 시작 설정"""
        print(f"🔧 {self.system} 자동 시작 설정 중...")

        # 트레이 스크립트 존재 확인
        if not self.tray_script.exists():
            print(f"❌ 트레이 스크립트를 찾을 수 없습니다: {self.tray_script}")
            return False

        # 로그 폴더 생성
        logs_dir = self.install_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        # 플랫폼별 설정
        if self.system == "Windows":
            return self.setup_windows()
        elif self.system == "Darwin":  # macOS
            return self.setup_macos()
        elif self.system == "Linux":
            return self.setup_linux()
        else:
            print(f"❌ 지원하지 않는 플랫폼입니다: {self.system}")
            return False

    def remove(self):
        """자동 시작 설정 제거"""
        print(f"🗑️  {self.system} 자동 시작 제거 중...")

        if self.system == "Windows":
            return self.remove_windows()
        elif self.system == "Darwin":
            return self.remove_macos()
        elif self.system == "Linux":
            return self.remove_linux()
        else:
            print(f"❌ 지원하지 않는 플랫폼입니다: {self.system}")
            return False

    def check_status(self):
        """자동 시작 설정 상태 확인"""
        print(f"📋 {self.system} 자동 시작 상태 확인...")

        if self.system == "Windows":
            try:
                import winreg
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                value, _ = winreg.QueryValueEx(key, "XLT System")
                winreg.CloseKey(key)
                print(f"✅ 자동 시작 설정됨: {value}")
                return True
            except Exception:
                print("❌ 자동 시작 설정되지 않음")
                return False

        elif self.system == "Darwin":
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.xlt.system.plist"
            if plist_path.exists():
                print(f"✅ 자동 시작 설정됨: {plist_path}")
                return True
            else:
                print("❌ 자동 시작 설정되지 않음")
                return False

        elif self.system == "Linux":
            desktop_path = Path.home() / ".config" / "autostart" / "xlt-system.desktop"
            if desktop_path.exists():
                print(f"✅ 자동 시작 설정됨: {desktop_path}")
                return True
            else:
                print("❌ 자동 시작 설정되지 않음")
                return False

        return False


def main():
    """메인 함수"""
    setup = AutoStartSetup()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "setup":
            setup.setup()
        elif command == "remove":
            setup.remove()
        elif command == "status":
            setup.check_status()
        else:
            print("사용법: python setup_autostart.py [setup|remove|status]")
    else:
        # 대화형 모드
        print("🚀 XLT System v3.0 자동 시작 설정")
        print()

        # 현재 상태 확인
        setup.check_status()
        print()

        print("옵션:")
        print("  1. 자동 시작 설정")
        print("  2. 자동 시작 해제")
        print("  3. 상태 확인")
        print("  4. 종료")

        while True:
            try:
                choice = input("\n선택 (1-4): ").strip()

                if choice == "1":
                    if setup.setup():
                        print("\n🎉 자동 시작 설정이 완료되었습니다!")
                        print("   다음 부팅 시부터 XLT System이 자동으로 시작됩니다.")
                    break

                elif choice == "2":
                    if setup.remove():
                        print("\n🗑️  자동 시작 설정이 제거되었습니다.")
                    break

                elif choice == "3":
                    setup.check_status()

                elif choice == "4":
                    print("종료합니다.")
                    break

                else:
                    print("올바른 번호를 입력해주세요.")

            except KeyboardInterrupt:
                print("\n종료합니다.")
                break


if __name__ == "__main__":
    main()