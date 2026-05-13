#!/usr/bin/env python3
"""
Line API 기반 용어집 연동 테스트
"""

import requests
import json
from typing import Dict, Any

def test_line_api_terminology():
    """Line API에서 용어집 데이터 로드 및 XLT 형식으로 변환 테스트"""

    # Line API URL
    api_url = "https://landpress-content.line-scdn.net/contents/v2/projects/wdmwbfuv10x39bukv58ocevp/collections/web3_xlt_json/item"

    try:
        print("🔄 Line API에서 용어집 데이터 로드 중...")
        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            print(f"❌ API 호출 실패: HTTP {response.status_code}")
            return None

        # JSON 파싱
        data = response.json()

        if not data.get('header', {}).get('success'):
            print("❌ API 응답 오류")
            return None

        # 용어집 데이터 추출 (exceptions 키 안에 실제 데이터가 있음)
        terminology_data = data['body']['exceptions']

        print("✅ Line API 데이터 로드 성공!")
        print(f"📊 총 용어: {terminology_data['metadata']['total_terms']}개")
        print(f"🔖 예외 항목: {terminology_data['metadata']['total_exceptions']}개")
        print(f"🌐 언어: {len(terminology_data['metadata']['languages'])}개")

        # Claude 프롬프트 형식으로 변환
        claude_prompt = convert_to_claude_format(terminology_data['terminology'])

        print(f"\n🤖 Claude 프롬프트 생성 완료 ({len(claude_prompt)} characters):")
        print("=" * 50)
        print(claude_prompt[:300] + "..." if len(claude_prompt) > 300 else claude_prompt)
        print("=" * 50)

        return terminology_data

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return None

def convert_to_claude_format(terminology: Dict[str, Dict[str, str]]) -> str:
    """용어집을 Claude 프롬프트 형식으로 변환"""

    lines = []
    required_langs = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']

    for korean_term, translations in terminology.items():
        # 5개 언어 모두 있는지 확인
        if all(lang in translations for lang in required_langs):
            line = (f'- "{korean_term}" → '
                   f'EN: "{translations["en_US"]}", '
                   f'JA: "{translations["ja_JP"]}", '
                   f'ZH: "{translations["zh_TW"]}", '
                   f'TH: "{translations["th_TH"]}"')
            lines.append(line)

    return '\n'.join(lines)

def test_api_performance():
    """API 성능 테스트"""
    api_url = "https://landpress-content.line-scdn.net/contents/v2/projects/wdmwbfuv10x39bukv58ocevp/collections/web3_xlt_json/item"

    import time

    print("\n⚡ API 성능 테스트 (3회 측정):")

    times = []
    for i in range(3):
        start_time = time.time()
        try:
            response = requests.get(api_url, timeout=10)
            end_time = time.time()

            if response.status_code == 200:
                elapsed = end_time - start_time
                times.append(elapsed)
                print(f"  {i+1}회: {elapsed:.3f}초 ✅")
            else:
                print(f"  {i+1}회: HTTP {response.status_code} ❌")
        except Exception as e:
            print(f"  {i+1}회: 오류 - {str(e)} ❌")

    if times:
        avg_time = sum(times) / len(times)
        print(f"\n📊 평균 응답시간: {avg_time:.3f}초")
        print(f"📊 최소 응답시간: {min(times):.3f}초")
        print(f"📊 최대 응답시간: {max(times):.3f}초")

if __name__ == "__main__":
    print("🧪 Line API 용어집 연동 테스트")
    print("=" * 60)

    # 데이터 로드 및 변환 테스트
    terminology_data = test_line_api_terminology()

    # 성능 테스트
    if terminology_data:
        test_api_performance()

    print("\n🎯 테스트 완료!")
    print("\n💡 XLT 시스템 연동 준비:")
    print("1. Line API URL 설정")
    print("2. ClaudeTranslator에 Line API 연동 추가")
    print("3. 캐시 시스템 적용")
    print("4. 폴백 메커니즘 유지")