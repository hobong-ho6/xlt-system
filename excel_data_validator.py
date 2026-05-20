#!/usr/bin/env python3
"""
엑셀 데이터 완성도 검증 도구
XLT System의 번역 데이터 품질을 검증합니다.
"""

import pandas as pd
import json
import sys
from collections import defaultdict

def validate_excel_data(file_path):
    """엑셀 데이터의 완성도를 검증합니다."""

    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file_path)

        # 컬럼 확인
        expected_columns = ['Key', 'ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
        actual_columns = df.columns.tolist()

        print(f"실제 컬럼: {actual_columns}")

        # 기본 통계
        total_rows = len(df)
        missing_key_ids = 0
        missing_korean = 0
        missing_translations = 0
        duplicate_keys = 0

        issues = []

        # Key 컬럼 확인 (첫 번째 컬럼)
        key_column = df.columns[0]

        # 빈 Key ID 검사
        empty_keys = df[df[key_column].isna() | (df[key_column] == '')]
        missing_key_ids = len(empty_keys)

        for idx, row in empty_keys.iterrows():
            issues.append({
                "row_number": idx + 2,  # Excel 행 번호 (헤더 포함)
                "key_id": "비어있음",
                "issue_type": "필수 필드 누락",
                "missing_languages": [],
                "description": f"Key ID가 비어있습니다"
            })

        # 중복 Key ID 검사
        duplicates = df[df.duplicated(subset=[key_column], keep=False)]
        if not duplicates.empty:
            duplicate_groups = duplicates.groupby(key_column)
            for key_id, group in duplicate_groups:
                duplicate_keys += len(group) - 1  # 첫 번째 제외하고 카운트
                for idx, row in group.iterrows():
                    issues.append({
                        "row_number": idx + 2,
                        "key_id": str(key_id),
                        "issue_type": "중복 키",
                        "missing_languages": [],
                        "description": f"중복된 Key ID: {key_id}"
                    })

        # 언어별 누락 검사
        language_columns = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
        available_langs = [col for col in language_columns if col in df.columns]

        for idx, row in df.iterrows():
            key_id = row[key_column] if pd.notna(row[key_column]) else "비어있음"
            missing_languages = []

            # 한국어 필수 검사
            if 'ko_KR' in df.columns:
                if pd.isna(row['ko_KR']) or row['ko_KR'] == '' or str(row['ko_KR']).strip() == '':
                    missing_korean += 1
                    missing_languages.append('ko_KR')

            # 다른 언어 누락 검사
            for lang in available_langs:
                if lang != 'ko_KR':  # 한국어는 이미 위에서 처리
                    if pd.isna(row[lang]) or row[lang] == '' or str(row[lang]).strip() == '':
                        missing_languages.append(lang)

            # 누락된 번역이 있으면 이슈로 기록
            if missing_languages:
                missing_translations += 1
                issue_type = "필수 필드 누락" if 'ko_KR' in missing_languages else "빈 필드"

                issues.append({
                    "row_number": idx + 2,
                    "key_id": str(key_id),
                    "issue_type": issue_type,
                    "missing_languages": missing_languages,
                    "description": f"누락된 언어: {', '.join(missing_languages)}"
                })

        # 결과 정리
        result = {
            "summary": {
                "total_rows": total_rows,
                "missing_key_ids": missing_key_ids,
                "missing_korean": missing_korean,
                "missing_translations": missing_translations,
                "duplicate_keys": duplicate_keys,
                "available_columns": actual_columns
            },
            "issues": issues
        }

        return result

    except Exception as e:
        return {
            "error": f"파일 읽기 실패: {str(e)}",
            "summary": {
                "total_rows": 0,
                "missing_key_ids": 0,
                "missing_korean": 0,
                "missing_translations": 0,
                "duplicate_keys": 0
            },
            "issues": []
        }

if __name__ == "__main__":
    file_path = "/Users/user/XLT-System/test_validation.xlsx"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    result = validate_excel_data(file_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))