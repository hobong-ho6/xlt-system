#!/usr/bin/env python3
"""
엑셀 데이터 완성도 검증 스크립트
"""
import pandas as pd
import json
from collections import Counter
import sys
import os

def validate_excel_data(file_path):
    """엑셀 데이터의 완성도를 검증하는 함수"""

    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file_path)
        print(f"✅ 파일 읽기 성공: {len(df)}개 행")

        # 컬럼명 확인
        print(f"📋 컬럼명: {list(df.columns)}")

        # 결과 초기화
        result = {
            "summary": {
                "total_rows": len(df),
                "missing_key_ids": 0,
                "missing_korean": 0,
                "missing_translations": 0,
                "duplicate_keys": 0
            },
            "issues": []
        }

        # 예상 컬럼명들 (유연하게 매칭)
        key_col = None
        lang_cols = {}

        # Key ID 컬럼 찾기
        for col in df.columns:
            if any(keyword in str(col).lower() for keyword in ['key', 'id']):
                key_col = col
                break

        # 언어 컬럼들 찾기
        lang_mapping = {
            'ko_kr': ['ko_kr', 'korean', '한국어', 'ko'],
            'en_us': ['en_us', 'english', '영어', 'en'],
            'ja_jp': ['ja_jp', 'japanese', '일본어', 'ja'],
            'zh_tw': ['zh_tw', 'chinese', '중국어', 'zh'],
            'th_th': ['th_th', 'thai', '태국어', 'th']
        }

        for target_lang, possible_names in lang_mapping.items():
            for col in df.columns:
                if any(name in str(col).lower() for name in possible_names):
                    lang_cols[target_lang] = col
                    break

        print(f"🔍 감지된 Key 컬럼: {key_col}")
        print(f"🌐 감지된 언어 컬럼들: {lang_cols}")

        if not key_col:
            print("❌ Key ID 컬럼을 찾을 수 없습니다.")
            return result

        # 데이터 검증 시작
        for idx, row in df.iterrows():
            row_number = idx + 1
            key_id = row[key_col] if key_col else None

            # 1. Key ID가 비어있는 행 체크
            if pd.isna(key_id) or str(key_id).strip() == '':
                result["summary"]["missing_key_ids"] += 1
                result["issues"].append({
                    "row_number": row_number,
                    "key_id": "N/A",
                    "issue_type": "필수 필드 누락",
                    "missing_languages": [],
                    "description": f"Key ID가 비어있음"
                })
                continue

            # 2. 한국어(ko_KR) 필수 필드 체크
            if 'ko_kr' in lang_cols:
                ko_value = row[lang_cols['ko_kr']]
                if pd.isna(ko_value) or str(ko_value).strip() == '' or str(ko_value).strip() == 'N/A':
                    result["summary"]["missing_korean"] += 1
                    result["issues"].append({
                        "row_number": row_number,
                        "key_id": str(key_id),
                        "issue_type": "필수 필드 누락",
                        "missing_languages": ["ko_KR"],
                        "description": f"한국어(필수) 번역이 비어있음"
                    })

            # 3. 번역이 누락된 언어들 체크
            missing_langs = []
            for lang_code, col_name in lang_cols.items():
                if lang_code == 'ko_kr':  # 한국어는 이미 위에서 체크
                    continue

                value = row[col_name]
                if pd.isna(value) or str(value).strip() == '' or str(value).strip() == 'N/A':
                    missing_langs.append(lang_code.upper())

            if missing_langs:
                result["summary"]["missing_translations"] += 1
                result["issues"].append({
                    "row_number": row_number,
                    "key_id": str(key_id),
                    "issue_type": "빈 필드",
                    "missing_languages": missing_langs,
                    "description": f"번역 누락: {', '.join(missing_langs)}"
                })

        # 4. 중복된 Key ID 체크
        key_counts = Counter(df[key_col].dropna().astype(str))
        duplicates = {key: count for key, count in key_counts.items() if count > 1}

        if duplicates:
            result["summary"]["duplicate_keys"] = len(duplicates)
            for duplicate_key, count in duplicates.items():
                # 중복된 행들의 위치 찾기
                duplicate_rows = df[df[key_col].astype(str) == duplicate_key].index.tolist()
                for row_idx in duplicate_rows:
                    result["issues"].append({
                        "row_number": row_idx + 1,
                        "key_id": duplicate_key,
                        "issue_type": "중복 키",
                        "missing_languages": [],
                        "description": f"Key ID '{duplicate_key}'가 {count}번 중복됨"
                    })

        return result

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return {
            "summary": {
                "total_rows": 0,
                "missing_key_ids": 0,
                "missing_korean": 0,
                "missing_translations": 0,
                "duplicate_keys": 0
            },
            "issues": [{"error": str(e)}]
        }

def main():
    # 현재 디렉토리의 엑셀 파일들 확인
    excel_files = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]

    if not excel_files:
        print("❌ 엑셀 파일을 찾을 수 없습니다.")
        return

    # 사용자가 지정한 파일이 있는지 확인
    target_file = None
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        # 가장 큰 파일 선택 (1583행이 있는 파일일 가능성)
        largest_file = None
        largest_size = 0

        for file in excel_files:
            try:
                df = pd.read_excel(file)
                if len(df) > largest_size:
                    largest_size = len(df)
                    largest_file = file
            except:
                continue

        target_file = largest_file

    if not target_file:
        print("❌ 유효한 엑셀 파일을 찾을 수 없습니다.")
        return

    print(f"🔍 검증 대상 파일: {target_file}")

    # 데이터 검증 실행
    result = validate_excel_data(target_file)

    # 결과 출력
    print("\n" + "="*50)
    print("📊 데이터 완성도 검증 결과")
    print("="*50)

    # JSON 형식으로 결과 출력
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 요약 정보 출력
    summary = result["summary"]
    print(f"\n📈 요약:")
    print(f"  - 전체 행 수: {summary['total_rows']:,}개")
    print(f"  - Key ID 누락: {summary['missing_key_ids']:,}개")
    print(f"  - 한국어 누락: {summary['missing_korean']:,}개")
    print(f"  - 번역 누락: {summary['missing_translations']:,}개")
    print(f"  - 중복 키: {summary['duplicate_keys']:,}개")

    total_issues = len(result["issues"])
    completion_rate = ((summary['total_rows'] - total_issues) / summary['total_rows'] * 100) if summary['total_rows'] > 0 else 0
    print(f"  - 완성도: {completion_rate:.1f}% ({summary['total_rows'] - total_issues:,}/{summary['total_rows']:,})")

    if total_issues == 0:
        print("✅ 모든 데이터가 완성되었습니다!")
    else:
        print(f"⚠️ {total_issues:,}개의 문제가 발견되었습니다.")

if __name__ == "__main__":
    main()