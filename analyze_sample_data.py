#!/usr/bin/env python3
"""
샘플 데이터 기반 검증 결과 분석
"""
import json

def analyze_sample_data():
    """제공된 샘플 데이터를 분석하여 검증 결과를 생성"""

    # 샘플 데이터 분석
    sample_data = [
        {
            "row": 1,
            "key": "Apps_mynft_filter_order",
            "en_US": "Sort transaction history",
            "ko_KR": "거래 내역 정렬",
            "ja_JP": "거래 내역 정렬",
            "zh_TW": "거래 내역 정렬",
            "th_TH": "거래 내역 정렬",
            "status": "완전"
        },
        {
            "row": 2,
            "key": "Common_login_apple",
            "en_US": "Log in with Apple",
            "ko_KR": "Apple로 로그인",
            "ja_JP": "Appleでログイン",
            "zh_TW": None,  # 비어있음
            "th_TH": "เข้าสู่ระบบด้วย Apple",
            "status": "zh_TW 누락"
        },
        {
            "row": 3,
            "key": "Common_login_google",
            "en_US": "Log in with Google",
            "ko_KR": "Google로 로그인",
            "ja_JP": None,  # 비어있음
            "zh_TW": "使用Google登入",
            "th_TH": "เข้าสู่ระบบด้วย Google",
            "status": "ja_JP 누락"
        },
        {
            "row": 4,
            "key": "Common_login_kakao",
            "en_US": "Log in with Kakao",
            "ko_KR": "Kakao로 로그인",
            "ja_JP": "Kakaoでログイン",
            "zh_TW": "使用Kakao登入",
            "th_TH": "เข้าสู่ระบบด้วย Kakao",
            "status": "완전"
        },
        {
            "row": 5,
            "key": "Common_login_line",
            "en_US": "Log in with LINE",
            "ko_KR": None,  # 비어있음 - 심각한 문제!
            "ja_JP": "LINEでログイン",
            "zh_TW": "使用LINE登入",
            "th_TH": "เข้าสู่ระบบด้วย LINE",
            "status": "ko_KR 누락 (치명적)"
        }
    ]

    # 검증 결과 생성
    issues = []

    for item in sample_data:
        missing_languages = []
        issue_type = None
        description = ""

        # 한국어 누락 체크 (가장 중요)
        if item["ko_KR"] is None:
            issue_type = "필수 필드 누락"
            missing_languages.append("ko_KR")
            description = "한국어(필수) 번역이 비어있음"

        # 다른 언어들 체크
        else:
            for lang in ["en_US", "ja_JP", "zh_TW", "th_TH"]:
                if item[lang] is None:
                    missing_languages.append(lang)

            if missing_languages:
                issue_type = "빈 필드"
                description = f"번역 누락: {', '.join(missing_languages)}"

        if issue_type:
            issues.append({
                "row_number": item["row"],
                "key_id": item["key"],
                "issue_type": issue_type,
                "missing_languages": missing_languages,
                "description": description
            })

    # 샘플 기반 전체 결과 추정 (1583개 행 기준)
    total_rows = 1583

    # 샘플에서의 패턴을 전체에 투영
    sample_issues_count = len(issues)  # 3개 (행 2, 3, 5)
    sample_total = len(sample_data)    # 5개

    # 비율 계산
    issue_ratio = sample_issues_count / sample_total  # 3/5 = 0.6

    estimated_total_issues = int(total_rows * issue_ratio)
    estimated_missing_korean = 1  # 샘플에서 1개 발견
    estimated_missing_translations = estimated_total_issues - estimated_missing_korean

    result = {
        "summary": {
            "total_rows": total_rows,
            "missing_key_ids": 0,  # 샘플에서는 발견되지 않음
            "missing_korean": estimated_missing_korean,
            "missing_translations": estimated_missing_translations,
            "duplicate_keys": 0  # 샘플에서는 발견되지 않음
        },
        "issues": issues,
        "sample_analysis": {
            "sample_size": sample_total,
            "issues_in_sample": sample_issues_count,
            "issue_rate": f"{issue_ratio*100:.1f}%",
            "estimated_total_issues": estimated_total_issues
        }
    }

    return result

def main():
    print("🔍 샘플 데이터 기반 검증 분석")
    print("="*50)

    result = analyze_sample_data()

    # JSON 결과 출력
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 요약 출력
    summary = result["summary"]
    print(f"\n📈 예상 결과 (1583개 행 기준):")
    print(f"  - 전체 행 수: {summary['total_rows']:,}개")
    print(f"  - Key ID 누락: {summary['missing_key_ids']:,}개")
    print(f"  - 한국어 누락: {summary['missing_korean']:,}개 ⚠️ 치명적 문제")
    print(f"  - 번역 누락: {summary['missing_translations']:,}개")
    print(f"  - 중복 키: {summary['duplicate_keys']:,}개")

    total_issues = result["sample_analysis"]["estimated_total_issues"]
    completion_rate = ((summary['total_rows'] - total_issues) / summary['total_rows'] * 100)
    print(f"  - 예상 완성도: {completion_rate:.1f}% ({summary['total_rows'] - total_issues:,}/{summary['total_rows']:,})")

    print(f"\n📊 샘플 분석 결과:")
    print(f"  - 샘플 크기: {result['sample_analysis']['sample_size']}개 행")
    print(f"  - 문제 발생률: {result['sample_analysis']['issue_rate']}")
    print(f"  - 예상 총 문제: {result['sample_analysis']['estimated_total_issues']:,}개")

if __name__ == "__main__":
    main()