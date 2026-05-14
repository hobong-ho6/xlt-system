#!/usr/bin/env python3
"""
XLT System v4.x → v5.0.0 자동화 시스템 업그레이드
기존 사용자를 위한 원클릭 전환 스크립트
"""

import os
import requests
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
import subprocess

def check_current_version():
    """현재 버전 확인"""
    try:
        current_dir = Path(__file__).parent
        version_file = current_dir / "version.json"

        if version_file.exists():
            with open(version_file, 'r') as f:
                data = json.load(f)
                return data.get('version', 'unknown')

        # Git 환경에서 커밋 메시지로 버전 추정
        try:
            result = subprocess.run(['git', 'log', '-1', '--pretty=%s'],
                                  capture_output=True, text=True, cwd=current_dir)
            commit_msg = result.stdout.strip()

            if 'v4.3' in commit_msg:
                return '4.3.0'
            elif 'v4.2' in commit_msg:
                return '4.2.0'
            elif 'v4.1' in commit_msg:
                return '4.1.0'
            else:
                return 'unknown'
        except:
            return 'unknown'

    except:
        return 'unknown'

def needs_upgrade(current_version):
    """업그레이드 필요 여부 확인"""
    if current_version == 'unknown':
        return True

    # 5.0.0 미만은 모두 업그레이드 필요
    try:
        major = int(current_version.split('.')[0])
        return major < 5
    except:
        return True

def download_latest():
    """최신 v5.0.0 다운로드"""
    print("📦 XLT System v5.0.0 자동화 시스템 다운로드 중...")

    zip_url = "https://github.com/hobong-ho6/xlt-system/archive/refs/heads/main.zip"

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "xlt-v5.zip"

        # ZIP 다운로드
        response = requests.get(zip_url, stream=True, timeout=60)
        response.raise_for_status()

        with open(zip_path, 'wb') as f:
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total_size += len(chunk)
                if total_size > 50 * 1024 * 1024:  # 50MB 제한
                    break

        # ZIP 압축 해제
        extract_dir = Path(temp_dir) / "extracted"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # 소스 디렉토리 찾기
        source_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
        if not source_dirs:
            raise Exception("압축 해제된 소스를 찾을 수 없습니다")

        return source_dirs[0]

def backup_user_settings(base_dir):
    """사용자 설정 백업"""
    backup_files = [
        'user_config.json',
        'figma_config.json',
        'logging_config.json',
        'auto_update_config.json',
        'github_config.json'
    ]

    backup_data = {}
    for filename in backup_files:
        file_path = base_dir / filename
        if file_path.exists():
            with open(file_path, 'rb') as f:
                backup_data[filename] = f.read()
                print(f"   📁 {filename} 백업됨")

    return backup_data

def install_v5_files(source_dir, target_dir, backup_data):
    """v5.0.0 핵심 파일들 설치"""
    print("🔄 v5.0.0 자동화 시스템 설치 중...")

    # 핵심 업데이트 파일 목록
    core_files = [
        'xlt/utils/updater.py',           # 다중 소스 업데이터
        'xlt/utils/auto_updater.py',      # 완전 자동화 시스템
        'xlt_tray.py',                    # 트레이 자동화 통합
        'stable_web_server.py',           # 웹서버 자동화 통합
        'version.json',                   # 버전 정보
        'GITHUB_TOKEN_SETUP.md'           # 설정 가이드
    ]

    # 파일별 설치
    for file_path in core_files:
        source_file = source_dir / file_path
        target_file = target_dir / file_path

        if source_file.exists():
            # 디렉토리 생성
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # 파일 복사
            shutil.copy2(source_file, target_file)
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️ {file_path} 찾을 수 없음")

    # 사용자 설정 복원
    for filename, content in backup_data.items():
        restore_path = target_dir / filename
        with open(restore_path, 'wb') as f:
            f.write(content)
        print(f"   📁 {filename} 복원됨")

    # v5.0.0 표시를 위한 version.json 업데이트
    version_file = target_dir / "version.json"
    version_data = {
        "name": "XLT System",
        "version": "5.0.0",
        "build": "2026-05-06",
        "installation_type": "upgraded_to_auto",
        "upgrade_date": "2026-05-06",
        "auto_update_enabled": True
    }

    with open(version_file, 'w') as f:
        json.dump(version_data, f, indent=2, ensure_ascii=False)
    print(f"   🏷️ v5.0.0 버전 정보 업데이트됨")

def test_auto_update_system(base_dir):
    """자동 업데이트 시스템 테스트"""
    print("🔍 자동 업데이트 시스템 테스트 중...")

    try:
        import sys
        sys.path.insert(0, str(base_dir))

        # 업데이터 테스트
        from xlt.utils.updater import XLTUpdater
        updater = XLTUpdater()

        remote_version = updater.get_remote_version()
        if remote_version:
            print(f"   ✅ 원격 버전 조회 성공: v{remote_version.get('version', 'unknown')}")
            print(f"   📊 사용 소스: {remote_version.get('source', 'unknown')}")
        else:
            print("   ❌ 원격 버전 조회 실패")
            return False

        # 자동 업데이터 테스트
        from xlt.utils.auto_updater import AutoUpdateManager
        auto_updater = AutoUpdateManager()

        status = auto_updater.get_status()
        print(f"   ✅ 자동 업데이터 초기화 성공")
        print(f"   ⏰ 체크 간격: {status['check_interval_hours']}시간")

        return True

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def main():
    print("🚀 XLT System v5.0.0 자동화 시스템 업그레이드")
    print("=" * 50)

    # 현재 위치 확인
    current_dir = Path(__file__).parent

    # 현재 버전 확인
    current_version = check_current_version()
    print(f"📊 현재 버전: v{current_version}")

    # 업그레이드 필요성 확인
    if not needs_upgrade(current_version):
        print("✅ 이미 v5.0.0 이상입니다. 업그레이드가 필요하지 않습니다.")
        return

    print(f"🎯 v{current_version} → v5.0.0 업그레이드가 필요합니다.")

    # 사용자 확인
    confirm = input("\n완전 자동화 시스템으로 업그레이드하시겠습니까? (y/N): ")
    if confirm.lower() not in ['y', 'yes']:
        print("❌ 업그레이드가 취소되었습니다.")
        return

    try:
        # 1. 사용자 설정 백업
        print("\n1️⃣ 사용자 설정 백업 중...")
        backup_data = backup_user_settings(current_dir)

        # 2. 최신 버전 다운로드
        print("\n2️⃣ v5.0.0 다운로드 중...")
        source_dir = download_latest()

        # 3. 핵심 파일 업그레이드
        print("\n3️⃣ 자동화 시스템 설치 중...")
        install_v5_files(source_dir, current_dir, backup_data)

        # 4. 시스템 테스트
        print("\n4️⃣ 시스템 테스트 중...")
        test_success = test_auto_update_system(current_dir)

        if test_success:
            print("\n🎉 v5.0.0 자동화 시스템 업그레이드 완료!")
            print("\n✨ 새로운 기능:")
            print("   🔍 백그라운드 자동 업데이트 감지 (6시간마다)")
            print("   📱 macOS 트레이 시스템 알림")
            print("   ⚡ 중요 업데이트 자동 설치")
            print("   🌐 GitHub 계정 불필요 (레이트 리밋 해결)")

            print("\n🔄 서버 재시작이 필요합니다:")
            print("   트레이: ~/Desktop/'XLT System (Tray).command'")
            print("   웹서버: python3 stable_web_server.py")

        else:
            print("\n⚠️ 업그레이드는 완료되었지만 테스트에서 일부 문제가 발견되었습니다.")
            print("   서버를 재시작한 후 정상 작동할 가능성이 높습니다.")

    except Exception as e:
        print(f"\n❌ 업그레이드 실패: {e}")
        print("💡 해결 방법:")
        print("   1. 인터넷 연결 확인")
        print("   2. 완전 재설치: curl -sL https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/install/install_v2.sh | bash")

if __name__ == "__main__":
    main()