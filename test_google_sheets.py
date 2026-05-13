#!/usr/bin/env python3
"""
Google Sheets 용어집 시스템 테스트 스크립트
Usage: python3 test_google_sheets.py
"""

import os
import sys
from typing import Dict, Any

# XLT System path 추가
sys.path.append('/Users/user/XLT-System')

def test_google_sheets_integration():
    """Google Sheets 통합 테스트"""

    print("🧪 Google Sheets 용어집 시스템 테스트 시작")
    print("=" * 60)

    # 1. 환경 변수 확인
    print("\n1️⃣ 환경 변수 확인")
    required_vars = [
        'GOOGLE_SHEETS_ENABLED',
        'GOOGLE_SHEETS_ID',
        'GOOGLE_SHEETS_CREDENTIALS'
    ]

    for var in required_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        print(f"  {status} {var}: {value or 'NOT SET'}")

    # 2. 인증 파일 확인
    print("\n2️⃣ 인증 파일 확인")
    creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    if creds_path and os.path.exists(creds_path):
        print(f"  ✅ 인증 파일 존재: {creds_path}")

        # JSON 파일 유효성 간단 체크
        try:
            import json
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            required_fields = ['client_email', 'private_key', 'project_id']
            missing_fields = [field for field in required_fields if field not in creds_data]

            if not missing_fields:
                print(f"  ✅ 인증 파일 형식 유효 (client_email: {creds_data['client_email']})")
            else:
                print(f"  ❌ 인증 파일 필수 필드 누락: {missing_fields}")
        except Exception as e:
            print(f"  ❌ 인증 파일 읽기 오류: {str(e)}")
    else:
        print(f"  ❌ 인증 파일 없음: {creds_path or 'NOT SET'}")

    # 3. XLT 모듈 로딩 테스트
    print("\n3️⃣ XLT 모듈 로딩 테스트")
    try:
        from xlt.core.config import XLTConfig
        from xlt.terminology import GoogleSheetsTerminology, TerminologyCache, GoogleSheetsAPI
        print("  ✅ XLT 모듈 import 성공")

        # Config 로딩
        config = XLTConfig()
        print(f"  ✅ Config 로딩 성공")
        print(f"    - Google Sheets 활성화: {config.google_sheets_enabled}")
        print(f"    - 시트 ID: {config.google_sheets_id}")
        print(f"    - 캐시 TTL: {config.terminology_cache_ttl}초")

    except Exception as e:
        print(f"  ❌ 모듈 로딩 실패: {str(e)}")
        return

    # 4. Google Sheets API 연결 테스트
    print("\n4️⃣ Google Sheets API 연결 테스트")
    try:
        terminology_system = GoogleSheetsTerminology(config)
        is_available = terminology_system.is_available()
        print(f"  {'✅' if is_available else '❌'} 시스템 가용성: {is_available}")

        if is_available:
            # API 연결 테스트
            status = terminology_system.get_system_status()
            print(f"  ✅ API 연결 상태: {status.get('api_connection', False)}")

            if 'available_sheets' in status:
                print(f"  ✅ 감지된 시트 탭: {status['available_sheets']}")
        else:
            print(f"  ⚠️  시스템이 비활성화 상태입니다. 설정을 확인하세요.")

    except Exception as e:
        print(f"  ❌ API 연결 테스트 실패: {str(e)}")

    # 5. 용어집 로딩 테스트
    print("\n5️⃣ 용어집 로딩 테스트")
    try:
        if terminology_system.is_available():
            print("  🔄 Google Sheets에서 용어집 로딩 시도...")
            terminology_data = terminology_system.load_terminology()

            if terminology_data:
                print(f"  ✅ 용어집 로딩 성공: {len(terminology_data)}개 용어")

                # 샘플 용어 출력
                sample_terms = list(terminology_data.items())[:3]
                for korean, translations in sample_terms:
                    print(f"    - {korean}: {translations}")

                # Claude 프롬프트 형식 테스트
                claude_prompt = terminology_system.format_for_claude_prompt(terminology_data, limit=5)
                print(f"  ✅ Claude 프롬프트 생성 성공 ({len(claude_prompt)} characters)")
                print(f"    미리보기: {claude_prompt[:100]}...")

            else:
                print("  ⚠️  Google Sheets에서 용어집을 로딩할 수 없음")
        else:
            print("  ⚠️  Google Sheets가 비활성화되어 있어 테스트를 건너뜁니다")

    except Exception as e:
        print(f"  ❌ 용어집 로딩 실패: {str(e)}")

    # 6. ClaudeTranslator 통합 테스트
    print("\n6️⃣ ClaudeTranslator 통합 테스트")
    try:
        from xlt.translation.claude_translator import ClaudeTranslator
        translator = ClaudeTranslator(config)

        # 용어집 로딩 (Google Sheets → guide.md 폴백)
        terminology_result = translator._load_guide_terminology()
        print(f"  ✅ ClaudeTranslator 용어집 로딩 성공")
        print(f"    - 길이: {len(terminology_result)} characters")
        print(f"    - 첫 번째 용어: {terminology_result.split('→')[0].strip() if '→' in terminology_result else 'N/A'}")

    except Exception as e:
        print(f"  ❌ ClaudeTranslator 통합 테스트 실패: {str(e)}")

    # 7. 캐시 시스템 테스트
    print("\n7️⃣ 캐시 시스템 테스트")
    try:
        cache = TerminologyCache(config)
        cache_stats = cache.get_cache_stats()

        print(f"  ✅ 캐시 시스템 초기화 성공")
        print(f"    - 캐시 디렉토리: {cache_stats['cache_directory']}")
        print(f"    - TTL: {cache_stats['cache_ttl_seconds']}초")
        print(f"    - 용어집 캐시 존재: {cache_stats['terminology_cache_exists']}")
        print(f"    - 용어집 캐시 유효: {cache_stats['terminology_cache_valid']}")

    except Exception as e:
        print(f"  ❌ 캐시 시스템 테스트 실패: {str(e)}")

    print("\n" + "=" * 60)
    print("🎯 테스트 완료!")
    print("\n💡 Google Sheets 활성화 방법:")
    print("1. 환경 변수 설정:")
    print("   export GOOGLE_SHEETS_ENABLED=true")
    print("   export GOOGLE_SHEETS_ID='your_spreadsheet_id'")
    print("   export GOOGLE_SHEETS_CREDENTIALS='credentials/google_sheets_service_account.json'")
    print("\n2. 서비스 계정 JSON 파일을 credentials/ 디렉토리에 배치")
    print("3. Google Sheets에 서비스 계정 이메일 공유")


if __name__ == "__main__":
    test_google_sheets_integration()