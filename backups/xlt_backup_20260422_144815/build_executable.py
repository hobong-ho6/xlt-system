#!/usr/bin/env python3
"""
XLT System v3.0 실행 파일 빌드 스크립트
PyInstaller를 사용하여 독립 실행 파일 생성
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_pyinstaller():
    """PyInstaller 설치 확인"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller 설치됨 (버전: {PyInstaller.__version__})")
        return True
    except ImportError:
        print("❌ PyInstaller가 설치되지 않았습니다.")
        print("💡 설치 방법: pip install pyinstaller")
        return False


def build_tray_app():
    """트레이 앱 실행 파일 빌드"""
    print("🔨 XLT Tray App 빌드 중...")

    # 빌드 옵션
    options = [
        "pyinstaller",
        "--onefile",                    # 단일 실행 파일
        "--windowed",                   # 콘솔 창 숨김 (GUI 앱)
        "--name=XLT-System",           # 실행 파일 이름
        "--icon=assets/icon.ico" if Path("assets/icon.ico").exists() else "",  # 아이콘
        "--add-data=templates;templates",  # 템플릿 폴더 포함
        "--add-data=static;static",       # 정적 파일 폴더 포함
        "--add-data=xlt;xlt",            # XLT 패키지 포함
        "--hidden-import=xlt",           # 숨겨진 import
        "--hidden-import=PIL",
        "--hidden-import=easyocr",
        "--hidden-import=googletrans",
        "--hidden-import=openpyxl",
        "--hidden-import=flask",
        "--exclude-module=matplotlib",   # 불필요한 모듈 제외
        "--exclude-module=scipy",
        "--exclude-module=numpy.distutils",
        "xlt_tray.py"
    ]

    # 빈 옵션 제거
    options = [opt for opt in options if opt]

    try:
        result = subprocess.run(options, check=True, capture_output=True, text=True)
        print("✅ 트레이 앱 빌드 성공")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 트레이 앱 빌드 실패: {e}")
        print(f"   표준 출력: {e.stdout}")
        print(f"   표준 오류: {e.stderr}")
        return False


def build_web_server():
    """웹 서버 실행 파일 빌드 (선택사항)"""
    print("🔨 XLT Web Server 빌드 중...")

    options = [
        "pyinstaller",
        "--onefile",
        "--console",                     # 콘솔 창 표시 (서버 로그용)
        "--name=XLT-Server",
        "--add-data=templates;templates",
        "--add-data=static;static",
        "--add-data=xlt;xlt",
        "--hidden-import=xlt",
        "--hidden-import=PIL",
        "--hidden-import=easyocr",
        "--hidden-import=googletrans",
        "--hidden-import=openpyxl",
        "--hidden-import=flask",
        "stable_web_server.py"
    ]

    try:
        result = subprocess.run(options, check=True, capture_output=True, text=True)
        print("✅ 웹 서버 빌드 성공")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 웹 서버 빌드 실패: {e}")
        return False


def create_installer_package():
    """설치 패키지 생성"""
    print("📦 설치 패키지 생성 중...")

    # 패키지 디렉토리 생성
    package_dir = Path("XLT-System-Package")
    if package_dir.exists():
        shutil.rmtree(package_dir)

    package_dir.mkdir()

    # 실행 파일 복사
    dist_dir = Path("dist")
    if dist_dir.exists():
        for exe_file in dist_dir.glob("*.exe"):
            shutil.copy2(exe_file, package_dir)
            print(f"  📄 {exe_file.name} 복사됨")

    # 필수 파일들 복사
    essential_files = [
        "requirements.txt",
        "figma_config_example.json",
        "README.md",
        "CLAUDE.md",
        "guide.md"
    ]

    for file_name in essential_files:
        file_path = Path(file_name)
        if file_path.exists():
            shutil.copy2(file_path, package_dir)
            print(f"  📄 {file_name} 복사됨")

    # 폴더들 복사
    essential_dirs = [
        "templates",
        "static",
        "xlt",
        "Sample"
    ]

    for dir_name in essential_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.copytree(dir_path, package_dir / dir_name)
            print(f"  📁 {dir_name}/ 복사됨")

    # 설치 스크립트 생성
    create_installer_scripts(package_dir)

    print(f"✅ 설치 패키지 생성 완료: {package_dir}")
    return package_dir


def create_installer_scripts(package_dir):
    """설치 스크립트 생성"""
    # Windows 설치 스크립트
    windows_installer = package_dir / "install.bat"
    with open(windows_installer, 'w', encoding='utf-8') as f:
        f.write("""@echo off
chcp 65001 > nul
title XLT System v3.0 설치

echo 🚀 XLT System v3.0 설치를 시작합니다...
echo.

:: 설치 디렉토리 생성
set INSTALL_DIR=%PROGRAMFILES%\\XLT System
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: 파일 복사
echo 📂 파일 복사 중...
xcopy /E /I /Y "%~dp0*" "%INSTALL_DIR%"

:: 바로가기 생성
echo 🔗 바로가기 생성 중...
set SHORTCUT_PATH=%USERPROFILE%\\Desktop\\XLT System.lnk

:: PowerShell로 바로가기 생성
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%INSTALL_DIR%\\XLT-System.exe'; $Shortcut.Save()"

echo ✅ 설치가 완료되었습니다!
echo    바탕화면의 'XLT System' 바로가기를 실행하세요.

pause
""")

    # macOS/Linux 설치 스크립트
    unix_installer = package_dir / "install.sh"
    with open(unix_installer, 'w', encoding='utf-8') as f:
        f.write("""#!/bin/bash

echo "🚀 XLT System v3.0 설치를 시작합니다..."

# 설치 디렉토리
INSTALL_DIR="/opt/xlt-system"

# 관리자 권한 확인
if [ "$EUID" -ne 0 ]; then
    echo "❌ 이 스크립트는 관리자 권한으로 실행해야 합니다."
    echo "   사용법: sudo ./install.sh"
    exit 1
fi

# 설치 디렉토리 생성
echo "📂 설치 디렉토리 생성: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# 파일 복사
echo "📄 파일 복사 중..."
cp -r * "$INSTALL_DIR/"

# 실행 권한 설정
chmod +x "$INSTALL_DIR/XLT-System"

# 바로가기 생성 (모든 사용자)
echo "🔗 바로가기 생성 중..."
cat > /usr/share/applications/xlt-system.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=XLT System
Comment=피그마 디자인 다국어 번역 도구
Exec=$INSTALL_DIR/XLT-System
Icon=applications-internet
Terminal=false
Categories=Office;Development;
EOF

echo "✅ 설치가 완료되었습니다!"
echo "   애플리케이션 메뉴에서 'XLT System'을 찾아 실행하세요."
""")

    # 실행 권한 설정
    os.chmod(unix_installer, 0o755)

    print("  📄 설치 스크립트 생성됨")


def main():
    """메인 함수"""
    print("🏗️  XLT System v3.0 실행 파일 빌드")
    print("=====================================")

    # PyInstaller 확인
    if not check_pyinstaller():
        return

    # 이전 빌드 정리
    for dir_name in ["build", "dist", "__pycache__"]:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name)
            print(f"🗑️  {dir_name} 디렉토리 정리됨")

    # spec 파일 정리
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"🗑️  {spec_file} 정리됨")

    print()

    # 빌드 선택
    print("빌드 옵션:")
    print("  1. 트레이 앱만 빌드 (권장)")
    print("  2. 웹 서버만 빌드")
    print("  3. 둘 다 빌드")
    print("  4. 전체 설치 패키지 생성")

    choice = input("\n선택 (1-4): ").strip()

    success = False

    if choice == "1":
        success = build_tray_app()
    elif choice == "2":
        success = build_web_server()
    elif choice == "3":
        success = build_tray_app() and build_web_server()
    elif choice == "4":
        if build_tray_app():
            package_dir = create_installer_package()
            success = True
            print()
            print("🎉 전체 설치 패키지 생성 완료!")
            print(f"   패키지 위치: {package_dir}")
            print("   사용법:")
            print("     - Windows: install.bat 실행")
            print("     - macOS/Linux: sudo ./install.sh 실행")
    else:
        print("올바른 번호를 선택해주세요.")
        return

    if success:
        print()
        print("🎯 빌드 결과:")

        dist_dir = Path("dist")
        if dist_dir.exists():
            for exe_file in dist_dir.iterdir():
                size = exe_file.stat().st_size / (1024 * 1024)  # MB
                print(f"  📦 {exe_file.name} ({size:.1f} MB)")

        print()
        print("💡 사용 방법:")
        print("  - 생성된 실행 파일을 다른 PC에 복사하여 사용")
        print("  - Python 설치 없이도 독립적으로 실행 가능")
        print("  - 트레이 앱: 시스템 트레이에서 관리")
        print("  - 웹 서버: 콘솔에서 직접 실행")


if __name__ == "__main__":
    main()