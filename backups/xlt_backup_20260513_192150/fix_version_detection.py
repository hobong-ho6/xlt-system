#!/usr/bin/env python3
"""
다른 PC 버전 감지 문제 해결 스크립트
version.json 파일을 강제로 생성하여 업데이트 감지가 작동하도록 수정
"""

import json
import os
from pathlib import Path

def fix_version_detection():
    """버전 감지 문제 해결"""

    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    version_file = current_dir / "version.json"

    print(f"🔍 현재 디렉토리: {current_dir}")
    print(f"📁 version.json 경로: {version_file}")

    # version.json 파일 존재 확인
    if version_file.exists():
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                current_version = json.load(f)
            print(f"✅ 현재 version.json 발견: v{current_version.get('version', 'unknown')}")
            print(f"   설치 타입: {current_version.get('installation_type', 'unknown')}")
            return current_version
        except Exception as e:
            print(f"❌ version.json 파일 손상: {e}")
    else:
        print("❌ version.json 파일 없음")

    # Git 저장소 상태 확인
    git_dir = current_dir / ".git"
    if git_dir.exists():
        print("✅ Git 저장소 감지됨")
        installation_type = "git"
    else:
        print("❌ Git 저장소 없음 (ZIP 설치로 추정)")
        installation_type = "zip"

    # 강제로 이전 버전 생성 (업데이트가 감지되도록)
    fallback_version = {
        "name": "XLT System",
        "version": "5.0.6",  # 현재보다 낮은 버전으로 설정
        "build": "2026-05-06",
        "installation_type": installation_type,
        "priority": "urgent",
        "features": [
            "버전 감지 문제 해결을 위한 임시 버전 파일"
        ]
    }

    try:
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(fallback_version, f, ensure_ascii=False, indent=2)

        print(f"✅ version.json 생성 완료: v{fallback_version['version']}")
        print(f"   이제 v5.0.7 업데이트가 감지될 것입니다!")

        return fallback_version

    except Exception as e:
        print(f"❌ version.json 생성 실패: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 XLT System 버전 감지 문제 해결")
    print("=" * 60)

    result = fix_version_detection()

    if result:
        print("\n" + "=" * 60)
        print("✅ 해결 완료! 이제 다음을 테스트하세요:")
        print("   curl -s http://localhost:5004/api/update/check")
        print("   또는 설정페이지에서 '업데이트 확인' 버튼 클릭")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 해결 실패. 수동으로 version.json을 생성해야 합니다.")
        print("=" * 60)