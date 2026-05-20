"""
Claude AI 기반 엑셀 검증 엔진

모든 검증 과정을 Claude AI로 처리하는 통합 시스템
"""

import json
import logging
import openpyxl
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import time
import traceback

from ..translation.claude_translator import ClaudeTranslator
from ..translation.unifi_translator import UnifiTranslator
from .claude_prompts import ClaudePrompts

logger = logging.getLogger(__name__)

class ExcelValidator:
    """Claude AI 기반 엑셀 파일 검증기"""

    def __init__(self, config):
        """초기화"""
        self.config = config
        self.claude_translator = ClaudeTranslator(config)
        self.unifi_translator = UnifiTranslator(config)
        self.prompts = ClaudePrompts()

        # 검증 결과 저장
        self.validation_results = {}
        self.excel_data = {}
        self.terminology_data = {}

        logger.info("✅ ExcelValidator 초기화 완료")

    def validate_excel_file(self, file_path: str, session_id: str) -> Dict[str, Any]:
        """
        엑셀 파일 전체 검증 실행

        Args:
            file_path: 엑셀 파일 경로
            session_id: 세션 ID

        Returns:
            검증 결과 딕셔너리
        """
        try:
            logger.info(f"📊 엑셀 검증 시작: {file_path}")

            # 1. 엑셀 파일 로드 및 구조 검증
            self.excel_data = self._load_excel_file(file_path)
            if not self.excel_data:
                return self._create_error_result("엑셀 파일 로드 실패")

            # 2. 용어집 데이터 로드
            self.terminology_data = self._load_terminology_data()

            # 3. 5단계 Claude AI 검증 실행
            validation_results = {
                'session_id': session_id,
                'file_path': file_path,
                'total_rows': len(self.excel_data),
                'validation_summary': {
                    'total_issues': 0,
                    'spelling_errors': 0,
                    'terminology_errors': 0,
                    'language_mismatches': 0,
                    'multilingual_errors': 0,
                    'completeness_issues': 0
                },
                'detailed_results': {}
            }

            # Step 1: 한글 맞춤법/띄어쓰기 검증
            logger.info("1️⃣ 한글 맞춤법/띄어쓰기 검증 시작")
            spelling_results = self._validate_korean_spelling()
            validation_results['detailed_results']['spelling_validation'] = spelling_results
            validation_results['validation_summary']['spelling_errors'] = len(spelling_results.get('issues', []))

            # Step 2: 한글 용어집 비교 검증
            logger.info("2️⃣ 한글 용어집 비교 검증 시작")
            terminology_results = self._validate_korean_terminology()
            validation_results['detailed_results']['terminology_validation'] = terminology_results
            validation_results['validation_summary']['terminology_errors'] = len(terminology_results.get('issues', []))

            # Step 3: 언어 일치성 검증
            logger.info("3️⃣ 언어 일치성 검증 시작")
            language_results = self._validate_language_consistency()
            validation_results['detailed_results']['language_validation'] = language_results
            validation_results['validation_summary']['language_mismatches'] = len(language_results.get('issues', []))

            # Step 4: 다국어 용어집 비교 검증
            logger.info("4️⃣ 다국어 용어집 비교 검증 시작")
            multilingual_results = self._validate_multilingual_terminology()
            validation_results['detailed_results']['multilingual_validation'] = multilingual_results
            validation_results['validation_summary']['multilingual_errors'] = len(multilingual_results.get('issues', []))

            # Step 5: 빈 행 및 완성도 검증
            logger.info("5️⃣ 데이터 완성도 검증 시작")
            completeness_results = self._validate_data_completeness()
            validation_results['detailed_results']['completeness_validation'] = completeness_results
            validation_results['validation_summary']['completeness_issues'] = len(completeness_results.get('issues', []))

            # 전체 문제 수 계산
            total_issues = sum([
                validation_results['validation_summary']['spelling_errors'],
                validation_results['validation_summary']['terminology_errors'],
                validation_results['validation_summary']['language_mismatches'],
                validation_results['validation_summary']['multilingual_errors'],
                validation_results['validation_summary']['completeness_issues']
            ])
            validation_results['validation_summary']['total_issues'] = total_issues

            # 검증 완료 시간
            validation_results['completed_at'] = time.time()
            validation_results['has_issues'] = total_issues > 0

            # 결과 저장
            self.validation_results[session_id] = validation_results

            logger.info(f"✅ 엑셀 검증 완료: 총 {total_issues}개 문제 발견")
            return validation_results

        except Exception as e:
            logger.error(f"❌ 엑셀 검증 오류: {e}")
            logger.error(traceback.format_exc())
            return self._create_error_result(f"검증 처리 오류: {str(e)}")

    def _load_excel_file(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """엑셀 파일 로드 및 데이터 구조화"""
        try:
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active

            # 헤더 행 확인 (빈 헤더도 처리)
            headers = []
            for col in range(1, ws.max_column + 1):
                header = ws.cell(row=1, column=col).value
                if header:
                    headers.append(str(header))
                else:
                    # 첫 번째 열이 빈값이면 'Key ID'로 가정
                    if col == 1:
                        headers.append('Key ID')
                        logger.info(f"📝 첫 번째 열 헤더가 빈값 - 'Key ID'로 가정")
                    else:
                        # 다른 열이 빈값이면 중단
                        break

            logger.info(f"📋 엑셀 데이터 로드 완료: {ws.max_row-1}행, 헤더: {headers}")

            expected_headers = ['Key ID', 'en_US', 'ko_KR', 'ja_JP', 'zh_TW', 'th_TH']
            if len(headers) < 3:  # 최소 Key ID, 언어1, 언어2는 있어야 함
                logger.error(f"❌ 헤더가 부족합니다: {headers}")
                return {}

            # 한국어 열 확인
            if 'ko_KR' not in headers:
                logger.warning(f"⚠️ 한국어(ko_KR) 열을 찾을 수 없습니다: {headers}")

            # 데이터 행 처리
            excel_data = {}
            for row in range(2, ws.max_row + 1):
                key_id = ws.cell(row=row, column=1).value
                if not key_id:
                    continue

                row_data = {}
                for col, header in enumerate(headers[1:], start=2):  # Key ID 제외
                    cell_value = ws.cell(row=row, column=col).value
                    row_data[header] = str(cell_value) if cell_value is not None else ""

                excel_data[str(key_id)] = row_data

            logger.info(f"✅ 데이터 파싱 완료: {len(excel_data)}개 키 로드됨")
            return excel_data

        except Exception as e:
            logger.error(f"❌ 엑셀 파일 로드 실패: {e}")
            return {}

    def _load_terminology_data(self) -> Dict[str, Any]:
        """용어집 데이터 로드"""
        try:
            # UnifiTranslator에서 용어집 데이터 가져오기
            terminology = self.unifi_translator.line_terminology
            logger.info(f"📚 용어집 데이터 로드 완료: {len(terminology)}개 용어")
            return terminology
        except Exception as e:
            logger.error(f"⚠️ 용어집 로드 실패: {e}")
            return {}

    def _validate_korean_spelling(self) -> Dict[str, Any]:
        """한글 맞춤법/띄어쓰기 검증"""
        try:
            # 한글 텍스트와 Key ID 매핑 추출
            korean_data = []
            row_number = 2  # 엑셀은 2행부터 데이터 시작
            for key_id, row_data in self.excel_data.items():
                korean_text = row_data.get('ko_KR', '')
                if korean_text and korean_text.strip():
                    korean_data.append({
                        'key_id': key_id,
                        'text': korean_text,
                        'row_number': row_number
                    })
                row_number += 1

            if not korean_data:
                return {'status': 'no_korean_text', 'issues': []}

            # Claude AI로 맞춤법 검증 (처음 10개만)
            sample_data = korean_data[:10]
            prompt = self.prompts.get_spelling_validation_prompt([item['text'] for item in sample_data], [item['key_id'] for item in sample_data])
            logger.info(f"📝 맞춤법 검증 프롬프트 생성 완료 - {len(sample_data)}개 텍스트")

            response = self._call_claude_ai(prompt)

            if response and 'results' in response:
                logger.info(f"✅ 맞춤법 검증 응답 처리 - {len(response['results'])}개 결과")
                # 결과 처리
                issues = []
                for i, result in enumerate(response['results']):
                    if not result.get('is_correct', True) and i < len(sample_data):
                        for error in result.get('errors', []):
                            issues.append({
                                'key_id': sample_data[i]['key_id'],
                                'row_number': sample_data[i]['row_number'],
                                'text': result['original_text'],
                                'error_type': error['type'],
                                'error': error['error'],
                                'suggestion': error['suggestion']
                            })

                return {
                    'status': 'completed',
                    'issues': issues,
                    'total_checked': len(sample_data)
                }

            return {'status': 'claude_error', 'issues': []}

        except Exception as e:
            logger.error(f"❌ 한글 맞춤법 검증 오류: {e}")
            return {'status': 'error', 'issues': [], 'error': str(e)}

    def _validate_korean_terminology(self) -> Dict[str, Any]:
        """한글 용어집 비교 검증"""
        try:
            # 한글 텍스트와 Key ID 매핑 추출
            korean_data = []
            row_number = 2  # 엑셀은 2행부터 데이터 시작
            for key_id, row_data in self.excel_data.items():
                korean_text = row_data.get('ko_KR', '')
                if korean_text and korean_text.strip():
                    korean_data.append({
                        'key_id': key_id,
                        'text': korean_text,
                        'row_number': row_number
                    })
                row_number += 1

            if not korean_data:
                return {'status': 'no_korean_text', 'issues': []}

            # Claude AI로 용어집 검증 (처음 10개만)
            sample_data = korean_data[:10]
            prompt = self.prompts.get_terminology_validation_prompt([item['text'] for item in sample_data], self.terminology_data, [item['key_id'] for item in sample_data])
            response = self._call_claude_ai(prompt)

            if response and 'results' in response:
                # 결과 처리
                issues = []
                exceptions = []
                for i, result in enumerate(response['results']):
                    if i >= len(sample_data):
                        continue

                    current_data = sample_data[i]
                    if result.get('has_terminology_issue', False):
                        for issue in result.get('issues', []):
                            issues.append({
                                'key_id': current_data['key_id'],
                                'row_number': current_data['row_number'],
                                'text': result['original_text'],
                                'wrong_term': issue['wrong_term'],
                                'suggested_term': issue['suggested_term'],
                                'reason': issue['reason']
                            })

                    # exceptional 항목 처리
                    if result.get('is_exception', False):
                        exceptions.append({
                            'key_id': current_data['key_id'],
                            'row_number': current_data['row_number'],
                            'text': result['original_text'],
                            'exception_reason': result.get('exception_reason', 'exceptional 항목으로 검증 통과')
                        })

                return {
                    'status': 'completed',
                    'issues': issues,
                    'exceptions': exceptions,
                    'total_checked': len(sample_data)
                }

            return {'status': 'claude_error', 'issues': []}

        except Exception as e:
            logger.error(f"❌ 한글 용어집 검증 오류: {e}")
            return {'status': 'error', 'issues': [], 'error': str(e)}

    def _validate_language_consistency(self) -> Dict[str, Any]:
        """언어 일치성 검증"""
        try:
            # 언어별 텍스트와 Key ID 매핑 수집
            texts_by_column = {}
            languages = ['en_US', 'ko_KR', 'ja_JP', 'zh_TW', 'th_TH']

            for lang in languages:
                texts_data = []
                row_number = 2  # 엑셀은 2행부터 데이터 시작
                for key_id, row_data in self.excel_data.items():
                    text = row_data.get(lang, '')
                    if text and text.strip():
                        texts_data.append({
                            'key_id': key_id,
                            'text': text,
                            'row_number': row_number
                        })
                    row_number += 1

                if texts_data:
                    texts_by_column[lang] = texts_data[:5]  # 처음 5개만 샘플로

            if not texts_by_column:
                return {'status': 'no_text_data', 'issues': []}

            # Claude AI로 언어 감지
            prompt = self.prompts.get_language_detection_prompt(texts_by_column)
            response = self._call_claude_ai(prompt)

            if response and 'results' in response:
                # 결과 처리
                issues = []
                for result in response['results']:
                    column = result['column']
                    for detected_issue in result.get('detected_issues', []):
                        # 해당 텍스트의 key_id와 row_number 찾기
                        target_text = detected_issue['text']
                        matched_data = None
                        if column in texts_by_column:
                            for data in texts_by_column[column]:
                                if data['text'] == target_text:
                                    matched_data = data
                                    break

                        issues.append({
                            'key_id': matched_data['key_id'] if matched_data else 'unknown',
                            'row_number': matched_data['row_number'] if matched_data else 0,
                            'column': result['column'],
                            'expected_language': result['expected_language'],
                            'text': detected_issue['text'],
                            'detected_language': detected_issue['detected_language'],
                            'issue': detected_issue['issue']
                        })

                return {
                    'status': 'completed',
                    'issues': issues,
                    'checked_languages': list(texts_by_column.keys())
                }

            return {'status': 'claude_error', 'issues': []}

        except Exception as e:
            logger.error(f"❌ 언어 일치성 검증 오류: {e}")
            return {'status': 'error', 'issues': [], 'error': str(e)}

    def _validate_multilingual_terminology(self) -> Dict[str, Any]:
        """다국어 용어집 비교 검증"""
        try:
            # 언어별 텍스트와 Key ID 매핑 수집
            texts_by_language = {}
            languages = ['en_US', 'ja_JP', 'zh_TW', 'th_TH']  # 한국어 제외

            for lang in languages:
                texts_data = []
                row_number = 2  # 엑셀은 2행부터 데이터 시작
                for key_id, row_data in self.excel_data.items():
                    text = row_data.get(lang, '')
                    if text and text.strip():
                        texts_data.append({
                            'key_id': key_id,
                            'text': text,
                            'row_number': row_number
                        })
                    row_number += 1

                if texts_data:
                    texts_by_language[lang] = texts_data[:5]  # 샘플

            if not texts_by_language:
                return {'status': 'no_multilingual_data', 'issues': []}

            # Claude AI로 다국어 용어 검증
            prompt = self.prompts.get_multilingual_terminology_prompt(texts_by_language, self.terminology_data)
            response = self._call_claude_ai(prompt)

            if response and 'results' in response:
                # 결과 처리
                issues = []
                for result in response['results']:
                    language = result['language']
                    for issue in result.get('issues', []):
                        # 해당 텍스트의 key_id와 row_number 찾기
                        target_text = issue['text']
                        matched_data = None
                        if language in texts_by_language:
                            for data in texts_by_language[language]:
                                if data['text'] == target_text:
                                    matched_data = data
                                    break

                        issues.append({
                            'key_id': matched_data['key_id'] if matched_data else 'unknown',
                            'row_number': matched_data['row_number'] if matched_data else 0,
                            'language': result['language'],
                            'text': issue['text'],
                            'wrong_term': issue['wrong_term'],
                            'suggested_term': issue['suggested_term'],
                            'issue_type': issue['issue_type']
                        })

                return {
                    'status': 'completed',
                    'issues': issues,
                    'checked_languages': list(texts_by_language.keys())
                }

            return {'status': 'claude_error', 'issues': []}

        except Exception as e:
            logger.error(f"❌ 다국어 용어집 검증 오류: {e}")
            return {'status': 'error', 'issues': [], 'error': str(e)}

    def _validate_data_completeness(self) -> Dict[str, Any]:
        """데이터 완성도 검증"""
        try:
            # 완성도 데이터 준비 (Key ID와 행번호 포함)
            completeness_data = []
            row_number = 2  # 엑셀은 2행부터 데이터 시작
            for key_id, row_data in self.excel_data.items():
                completeness_data.append({
                    'key_id': key_id,
                    'row_number': row_number,
                    'row_data': row_data
                })
                row_number += 1

            # Claude AI로 완성도 검증
            prompt = self.prompts.get_completeness_validation_prompt(completeness_data)
            response = self._call_claude_ai(prompt)

            if response:
                # 결과 처리 - key_id와 row_number 정보 보존
                issues = []
                for issue in response.get('issues', []):
                    # Claude AI가 반환한 key_id 사용 (실제 엑셀 데이터)
                    issues.append({
                        'key_id': issue.get('key_id', 'unknown'),
                        'row_number': issue.get('row_number', 0),
                        'issue_type': issue.get('issue_type', 'completeness'),
                        'description': issue.get('description', ''),
                        'missing_languages': issue.get('missing_languages', [])
                    })

                summary = response.get('summary', {})

                return {
                    'status': 'completed',
                    'issues': issues,
                    'summary': summary
                }

            return {'status': 'claude_error', 'issues': []}

        except Exception as e:
            logger.error(f"❌ 데이터 완성도 검증 오류: {e}")
            return {'status': 'error', 'issues': [], 'error': str(e)}

    def _call_claude_ai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Claude AI 호출"""
        try:
            # claude_translator를 통해 Claude AI 호출
            response = self.claude_translator._call_claude_api(prompt)

            if response and 'text' in response:
                # JSON 응답 파싱
                text = response['text']

                # JSON 블록 추출
                if '```json' in text:
                    json_start = text.find('```json') + 7
                    json_end = text.find('```', json_start)
                    json_text = text[json_start:json_end].strip()
                else:
                    json_text = text.strip()

                try:
                    return json.loads(json_text)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Claude AI 응답 JSON 파싱 실패: {e}")
                    logger.error(f"응답 텍스트: {text[:500]}...")
                    return None

            return None

        except Exception as e:
            logger.error(f"❌ Claude AI 호출 오류: {e}")
            return None

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """에러 결과 생성"""
        return {
            'status': 'error',
            'error': error_message,
            'has_issues': True,
            'validation_summary': {
                'total_issues': -1,
                'spelling_errors': 0,
                'terminology_errors': 0,
                'language_mismatches': 0,
                'multilingual_errors': 0,
                'completeness_issues': 0
            },
            'detailed_results': {}
        }

    def get_validation_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 검증 결과 조회"""
        return self.validation_results.get(session_id)

    def has_validation_issues(self, session_id: str) -> bool:
        """검증 결과에 문제가 있는지 확인"""
        results = self.get_validation_results(session_id)
        if results:
            return results.get('has_issues', False)
        return False