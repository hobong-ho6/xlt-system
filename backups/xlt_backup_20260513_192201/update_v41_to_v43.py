#!/usr/bin/env python3
"""
v4.1.0 → v4.3.0 직접 업데이트 스크립트
GitHub API 레이트 리밋 우회
"""

import os
import requests
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

def get_remote_version():
    """Raw GitHub에서 버전 정보 조회 (레이트 리밋 없음)"""
    try:
        url = "https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/version.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 원격 버전 조회 실패: {e}")
        return None

def get_local_version():
    """로컬 버전 정보 조회"""
    try:
        current_dir = Path(__file__).parent
        version_file = current_dir / "version.json"

        if version_file.exists():
            with open(version_file, 'r') as f:
                return json.load(f)
        else:
            return {"version": "4.1.0", "name": "XLT System"}
    except Exception as e:
        print(f"⚠️ 로컬 버전 조회 실패: {e}")
        return {"version": "4.1.0", "name": "XLT System"}

def download_and_update():
    """GitHub ZIP 다운로드 및 업데이트 (레이트 리밋 없음)"""
    try:
        print("📦 최신 버전 다운로드 중...")

        # ZIP 다운로드 (레이트 리밋 없음)
        zip_url = "https://github.com/hobong-ho6/xlt-system/archive/refs/heads/main.zip"

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = Path(temp_dir) / "xlt-main.zip"

            # ZIP 파일 다운로드
            response = requests.get(zip_url, stream=True, timeout=60)
            response.raise_for_status()

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print("✅ 다운로드 완료")

            # ZIP 압축 해제
            extract_dir = Path(temp_dir) / "extracted"
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # 소스 디렉토리 찾기
            source_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not source_dirs:
                raise Exception("압축 해제된 소스를 찾을 수 없습니다")

            source_dir = source_dirs[0]  # xlt-system-main
            current_dir = Path(__file__).parent

            print("🔄 파일 업데이트 중...")

            # 중요 파일 백업
            backup_files = ['user_config.json', 'figma_config.json']
            backup_data = {}

            for backup_file in backup_files:
                file_path = current_dir / backup_file
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        backup_data[backup_file] = f.read()

            # 핵심 파일들 업데이트
            update_files = [
                'stable_web_server.py',
                'xlt/core/config.py',
                'xlt/translation/claude_translator.py',
                'xlt/utils/updater.py',
                'version.json'
            ]

            for file_path in update_files:
                source_file = source_dir / file_path
                target_file = current_dir / file_path

                if source_file.exists():
                    # 디렉토리 생성
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    # 파일 복사
                    shutil.copy2(source_file, target_file)
                    print(f"   ✅ {file_path}")

            # 설정 파일 복원
            for filename, content in backup_data.items():
                restore_path = current_dir / filename
                with open(restore_path, 'wb') as f:
                    f.write(content)
                print(f"   📁 {filename} 복원됨")

            print("🎉 v4.3.0 업데이트 완료!")
            print("🔄 서버를 재시작해주세요: python3 stable_web_server.py")
            return True

    except Exception as e:
        print(f"❌ 업데이트 실패: {e}")
        return False

def main():
    print("🔍 XLT System v4.1.0 → v4.3.0 업데이트 확인...")

    local_version = get_local_version()
    remote_version = get_remote_version()

    if not remote_version:
        print("❌ 원격 버전 정보를 가져올 수 없습니다.")
        return

    print(f"📊 현재 버전: {local_version.get('version', 'unknown')}")
    print(f"📊 최신 버전: {remote_version.get('version', 'unknown')}")

    local_ver = local_version.get('version', '0.0.0')
    remote_ver = remote_version.get('version', '0.0.0')

    if local_ver != remote_ver:
        print(f"🚀 업데이트 가능: {local_ver} → {remote_ver}")

        confirm = input("업데이트를 진행하시겠습니까? (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            success = download_and_update()
            if success:
                print("\n🎯 v4.3.0 주요 개선사항:")
                print("   - Claude CLI 타임아웃 근본 해결")
                print("   - 36개 텍스트 처리 시간 75% 단축")
                print("   - 엑셀 번역 성공률 100% 달성")
        else:
            print("❌ 업데이트가 취소되었습니다.")
    else:
        print("✅ 이미 최신 버전입니다!")

if __name__ == "__main__":
    main()