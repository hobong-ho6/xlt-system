#!/usr/bin/env python3
"""
XLT System v3.0 배포 패키지 검증 스크립트
개인 PC 설치 전 시스템 호환성 확인
"""

import sys
import os
import subprocess
import platform
from pathlib import Path


def check_python_version():
    """Python 버전 확인 (3.8+ 필요)"""
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (호환)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (3.8+ 필요)")
        return False


def check_dependencies():
    """필수 패키지 설치 확인"""
    required_packages = [
        'flask', 'easyocr', 'googletrans', 'openpyxl',
        'PIL', 'requests', 'psutil'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (누락)")
            missing_packages.append(package)

    return len(missing_packages) == 0, missing_packages


def check_xlt_system():
    """XLT 시스템 초기화 확인"""
    try:
        from xlt import XLTConfig, XLTPipeline
        config = XLTConfig()
        pipeline = XLTPipeline(config)
        print("✅ XLT System 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ XLT System 초기화 실패: {e}")
        return False


def check_gui_libraries():
    """GUI 라이브러리 확인 (트레이 앱용)"""
    gui_available = []

    try:
        import pystray
        gui_available.append('PysTray (권장)')
        print("✅ PysTray 사용 가능")
    except ImportError:
        print("⚠️  PysTray 없음 (설치 권장: pip install pystray)")

    try:
        import tkinter
        gui_available.append('Tkinter (기본)')
        print("✅ Tkinter 사용 가능")
    except ImportError:
        print("❌ Tkinter 없음 (Python 재설치 필요)")

    return len(gui_available) > 0, gui_available


def check_deployment_files():
    """배포 파일들 존재 확인"""
    required_files = [
        'stable_web_server.py',
        'xlt_tray.py',
        'install.sh',
        'install.bat',
        'setup_autostart.py',
        'build_executable.py',
        'requirements.txt',
        'figma_config_example.json'
    ]

    missing_files = []
    for file_name in required_files:
        if Path(file_name).exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} (누락)")
            missing_files.append(file_name)

    return len(missing_files) == 0, missing_files


def check_directories():
    """필수 디렉토리 확인"""
    required_dirs = ['xlt/', 'templates/', 'static/', 'Sample/']

    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}")
        else:
            print(f"❌ {dir_name} (누락)")
            return False

    return True


def check_platform_support():
    """플랫폼 지원 확인"""
    system = platform.system()
    print(f"🖥️  플랫폼: {system}")

    if system in ['Windows', 'Darwin', 'Linux']:
        print(f"✅ {system} 지원됨")
        return True
    else:
        print(f"❌ {system} 지원되지 않음")
        return False


def main():
    """메인 검증 함수"""
    print("🔬 XLT System v3.0 배포 패키지 검증")
    print("="*50)

    checks = [
        ("Python 버전", check_python_version),
        ("필수 패키지", lambda: check_dependencies()[0]),
        ("XLT 시스템", check_xlt_system),
        ("GUI 라이브러리", lambda: check_gui_libraries()[0]),
        ("배포 파일", lambda: check_deployment_files()[0]),
        ("필수 디렉토리", check_directories),
        ("플랫폼 지원", check_platform_support)
    ]

    results = []
    for name, check_func in checks:
        print(f"\n📋 {name} 확인:")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 검증 오류: {e}")
            results.append(False)

    # 최종 결과
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print("🎉 모든 검증을 통과했습니다!")
        print("✅ 개인 PC 설치가 가능합니다.")
        print("\n📋 설치 방법:")
        print("  - Windows: install.bat 실행")
        print("  - macOS/Linux: ./install.sh 실행")
        print("  - 트레이 앱: python3 xlt_tray.py")
        print("  - 웹 서버: python3 stable_web_server.py")
    else:
        print(f"❌ {total-passed}/{total}개 검증 실패")
        print("💡 문제를 해결한 후 다시 시도해주세요.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)