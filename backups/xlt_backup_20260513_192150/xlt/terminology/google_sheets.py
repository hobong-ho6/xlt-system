"""
구글 시트 기반 용어집 관리 시스템 메인 클래스
기존 guide.md 시스템을 대체하여 실시간 협업 가능한 용어집 관리를 제공
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .sheets_api import GoogleSheetsAPI, GoogleSheetsAPIError
from .cache import TerminologyCache, TerminologyCacheError
from ..core.exceptions import XLTException


class TerminologyError(XLTException):
    """용어집 관련 오류"""

    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"용어집 오류 ({operation}): {message}")


class GoogleSheetsTerminology:
    """구글 시트 기반 용어집 관리 클래스"""

    def __init__(self, config):
        """
        구글 시트 용어집 관리 시스템 초기화

        Args:
            config: XLTConfig 인스턴스
        """
        self.config = config

        # 구글 시트 설정
        self.sheet_id = getattr(config, 'google_sheets_id', None)
        self.credentials_path = getattr(config, 'google_sheets_credentials', None)

        # 시트 탭 이름 (설정 가능하도록)
        self.terminology_sheet = getattr(config, 'terminology_sheet_name', 'Terminology')
        self.exceptions_sheet = getattr(config, 'exceptions_sheet_name', 'Exceptions')
        self.metadata_sheet = getattr(config, 'metadata_sheet_name', 'Metadata')

        # 언어 매핑 (구글 시트 컬럼명 → XLT 언어 코드)
        self.language_mapping = {
            'Korean': 'ko_KR',
            'English': 'en_US',
            'Japanese': 'ja_JP',
            'TraditionalChinese': 'zh_TW',
            'Thai': 'th_TH'
        }

        # 컴포넌트 초기화
        self.api = None
        self.cache = TerminologyCache(config)

        # 초기화 시도
        self._initialize_api()

    def _initialize_api(self) -> None:
        """Google Sheets API 초기화"""
        try:
            if not self.sheet_id:
                raise TerminologyError("initialization", "Google Sheets ID가 설정되지 않았습니다")

            # 인증 정보 확인
            credentials_path = self._resolve_credentials_path()
            if not credentials_path:
                raise TerminologyError("initialization", "Google Sheets 인증 정보를 찾을 수 없습니다")

            # API 클래스 초기화
            self.api = GoogleSheetsAPI(credentials_path)

            # 연결 테스트
            if not self.api.test_connection(self.sheet_id):
                raise TerminologyError("initialization", "Google Sheets 연결 테스트 실패")

            print(f"✅ Google Sheets 용어집 시스템 초기화 완료: {self.sheet_id}")

        except Exception as e:
            if isinstance(e, (TerminologyError, GoogleSheetsAPIError)):
                print(f"⚠️ Google Sheets 용어집 시스템 초기화 실패: {str(e)}")
                self.api = None  # API를 None으로 설정하여 폴백 가능하게
            else:
                raise TerminologyError("initialization", f"예상치 못한 오류: {str(e)}")

    def _resolve_credentials_path(self) -> Optional[str]:
        """인증 파일 경로 해결 (기존 XLT 패턴 활용)"""
        # 1순위: 설정에서 지정된 경로
        if self.credentials_path and os.path.exists(self.credentials_path):
            return self.credentials_path

        # 2순위: 환경 변수
        env_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if env_path and os.path.exists(env_path):
            return env_path

        # 3순위: 프로젝트 루트의 credentials 디렉토리
        base_dir = getattr(self.config, 'config_path', os.getcwd())
        default_path = os.path.join(base_dir, 'credentials', 'google_sheets_service_account.json')
        if os.path.exists(default_path):
            return default_path

        return None

    def load_terminology(self) -> Dict[str, Dict[str, str]]:
        """
        용어집 데이터 로드 (캐시 우선, 구글 시트 폴백)

        Returns:
            Dict[str, Dict[str, str]]: 용어집 데이터
            예: {'거래': {'en_US': 'transaction', 'ja_JP': '取引', ...}, ...}
        """
        try:
            # 1단계: 캐시에서 조회 시도
            cached_data = self.cache.get_cached_terminology()
            if cached_data:
                print(f"📚 용어집 캐시 사용: {len(cached_data)}개 용어")
                return cached_data

            # 2단계: 구글 시트에서 로드
            if not self.api:
                raise TerminologyError("load_terminology", "Google Sheets API가 초기화되지 않았습니다")

            print(f"🔄 Google Sheets에서 용어집 로드 중: {self.sheet_id}")
            fresh_data = self._fetch_terminology_from_sheets()

            # 3단계: 캐시에 저장
            if fresh_data:
                sheet_metadata = self._get_sheet_metadata()
                self.cache.store_terminology(fresh_data, sheet_metadata)
                print(f"✅ 용어집 로드 완료: {len(fresh_data)}개 용어")

            return fresh_data

        except Exception as e:
            if isinstance(e, (TerminologyError, GoogleSheetsAPIError)):
                raise e
            else:
                raise TerminologyError("load_terminology", f"용어집 로드 실패: {str(e)}")

    def _fetch_terminology_from_sheets(self) -> Dict[str, Dict[str, str]]:
        """구글 시트에서 실제 용어집 데이터 가져오기"""
        try:
            # 용어집 시트 데이터 조회
            range_name = f"{self.terminology_sheet}!A:J"  # ID부터 CreatedBy까지
            sheet_data = self.api.get_sheet_values(self.sheet_id, range_name)

            if not sheet_data:
                print("⚠️ 용어집 시트가 비어있습니다")
                return {}

            # 헤더 행 확인 및 컬럼 인덱스 추출
            headers = sheet_data[0] if sheet_data else []
            column_indices = self._parse_terminology_headers(headers)

            if not column_indices:
                raise TerminologyError("fetch_terminology",
                                     f"용어집 시트 헤더가 올바르지 않습니다. 예상: {list(self.language_mapping.keys())}")

            # 데이터 행 처리
            terminology_data = {}
            for row_index, row in enumerate(sheet_data[1:], start=2):  # 헤더 제외
                try:
                    processed_row = self._process_terminology_row(row, column_indices, row_index)
                    if processed_row:
                        korean_term, translations = processed_row
                        terminology_data[korean_term] = translations
                except Exception as e:
                    print(f"⚠️ 용어집 행 {row_index} 처리 실패: {str(e)}")
                    continue

            print(f"📊 용어집 데이터 파싱 완료: {len(terminology_data)}개 용어")
            return terminology_data

        except Exception as e:
            raise TerminologyError("fetch_terminology", f"시트 데이터 조회 실패: {str(e)}")

    def _parse_terminology_headers(self, headers: List[str]) -> Dict[str, int]:
        """용어집 시트 헤더 파싱하여 컬럼 인덱스 추출"""
        column_indices = {}

        for i, header in enumerate(headers):
            # 언어 컬럼 매핑
            if header in self.language_mapping:
                xlt_lang_code = self.language_mapping[header]
                column_indices[xlt_lang_code] = i

        # 필수 언어 컬럼 확인
        required_languages = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
        missing_languages = [lang for lang in required_languages if lang not in column_indices]

        if missing_languages:
            print(f"⚠️ 누락된 언어 컬럼: {missing_languages}")
            print(f"📋 발견된 헤더: {headers}")

        return column_indices

    def _process_terminology_row(self, row: List[str], column_indices: Dict[str, int],
                                row_index: int) -> Optional[Tuple[str, Dict[str, str]]]:
        """용어집 행 데이터 처리"""
        try:
            # 한국어 컬럼 확인 (필수)
            korean_col_index = column_indices.get('ko_KR')
            if korean_col_index is None or korean_col_index >= len(row):
                return None

            korean_term = row[korean_col_index].strip()
            if not korean_term:
                return None

            # 각 언어별 번역 추출
            translations = {}
            for lang_code, col_index in column_indices.items():
                if col_index < len(row):
                    translation = row[col_index].strip()
                    if translation:
                        translations[lang_code] = translation

            # 최소한 한국어 + 1개 이상 언어가 있어야 유효
            if len(translations) < 2:
                print(f"⚠️ 행 {row_index}: '{korean_term}' - 번역이 부족합니다 ({len(translations)}개 언어)")
                return None

            return korean_term, translations

        except Exception as e:
            print(f"⚠️ 행 {row_index} 처리 오류: {str(e)}")
            return None

    def load_exceptions(self) -> List[Dict[str, Any]]:
        """
        예외 항목 로드

        Returns:
            List[Dict[str, Any]]: 예외 항목 목록
        """
        try:
            # 캐시에서 조회 시도
            cached_exceptions = self.cache.get_cached_exceptions()
            if cached_exceptions:
                print(f"📚 예외 항목 캐시 사용: {len(cached_exceptions)}개 항목")
                return cached_exceptions

            # 구글 시트에서 로드
            if not self.api:
                raise TerminologyError("load_exceptions", "Google Sheets API가 초기화되지 않았습니다")

            print(f"🔄 Google Sheets에서 예외 항목 로드 중")
            fresh_exceptions = self._fetch_exceptions_from_sheets()

            # 캐시에 저장
            if fresh_exceptions:
                sheet_metadata = self._get_sheet_metadata()
                self.cache.store_exceptions(fresh_exceptions, sheet_metadata)
                print(f"✅ 예외 항목 로드 완료: {len(fresh_exceptions)}개 항목")

            return fresh_exceptions

        except Exception as e:
            if isinstance(e, (TerminologyError, GoogleSheetsAPIError)):
                raise e
            else:
                raise TerminologyError("load_exceptions", f"예외 항목 로드 실패: {str(e)}")

    def _fetch_exceptions_from_sheets(self) -> List[Dict[str, Any]]:
        """구글 시트에서 예외 항목 데이터 가져오기"""
        try:
            range_name = f"{self.exceptions_sheet}!A:K"  # ID부터 Active까지
            sheet_data = self.api.get_sheet_values(self.sheet_id, range_name)

            if not sheet_data:
                print("📝 예외 항목 시트가 비어있거나 없습니다")
                return []

            # 헤더 확인
            headers = sheet_data[0] if sheet_data else []
            expected_headers = ['ID', 'Pattern', 'ExceptionType', 'Korean', 'English',
                              'Japanese', 'TraditionalChinese', 'Thai', 'Note', 'Active']

            # 데이터 처리
            exceptions_data = []
            for row_index, row in enumerate(sheet_data[1:], start=2):
                try:
                    exception_item = self._process_exception_row(row, headers, row_index)
                    if exception_item:
                        exceptions_data.append(exception_item)
                except Exception as e:
                    print(f"⚠️ 예외 항목 행 {row_index} 처리 실패: {str(e)}")
                    continue

            return exceptions_data

        except Exception as e:
            raise TerminologyError("fetch_exceptions", f"예외 항목 시트 조회 실패: {str(e)}")

    def _process_exception_row(self, row: List[str], headers: List[str],
                              row_index: int) -> Optional[Dict[str, Any]]:
        """예외 항목 행 처리"""
        try:
            if len(row) < 4:  # 최소 필수 컬럼 수
                return None

            # Active 컬럼 확인 (비활성화된 항목 제외)
            active_col_index = -1
            for i, header in enumerate(headers):
                if header == 'Active' and i < len(row):
                    active_col_index = i
                    break

            if active_col_index != -1 and active_col_index < len(row):
                active_value = row[active_col_index].strip().lower()
                if active_value in ['false', '0', 'no', '비활성']:
                    return None

            # 패턴 추출 (필수)
            pattern = row[1].strip() if len(row) > 1 else ''
            if not pattern:
                return None

            # 기본 정보
            exception_item = {
                'id': row[0].strip() if len(row) > 0 else str(row_index - 1),
                'pattern': pattern,
                'exception_type': row[2].strip() if len(row) > 2 else 'unknown',
                'translations': {},
                'note': row[8].strip() if len(row) > 8 else '',
                'active': True
            }

            # 언어별 번역 추가
            lang_start_index = 3  # Korean 컬럼부터
            for i, lang_key in enumerate(self.language_mapping.keys()):
                col_index = lang_start_index + i
                if col_index < len(row):
                    translation = row[col_index].strip()
                    if translation:
                        xlt_lang_code = self.language_mapping[lang_key]
                        exception_item['translations'][xlt_lang_code] = translation

            return exception_item

        except Exception as e:
            print(f"⚠️ 예외 항목 행 {row_index} 처리 오류: {str(e)}")
            return None

    def _get_sheet_metadata(self) -> Dict[str, Any]:
        """시트 메타데이터 조회"""
        try:
            if not self.api:
                return {}

            # 시트 목록 조회
            available_sheets = self.api.get_available_sheets(self.sheet_id)

            # 메타데이터 시트에서 추가 정보 조회 시도
            metadata_info = {}
            try:
                metadata_range = f"{self.metadata_sheet}!A:C"
                metadata_data = self.api.get_sheet_values(self.sheet_id, metadata_range)

                for row in metadata_data:
                    if len(row) >= 2:
                        key = row[0].strip()
                        value = row[1].strip()
                        if key and value:
                            metadata_info[key] = value
            except:
                # 메타데이터 시트가 없거나 오류가 있어도 계속 진행
                pass

            return {
                'sheet_id': self.sheet_id,
                'available_sheets': available_sheets,
                'metadata_info': metadata_info,
                'sync_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"⚠️ 시트 메타데이터 조회 실패: {str(e)}")
            return {'sheet_id': self.sheet_id, 'error': str(e)}

    def format_for_claude_prompt(self, terminology_data: Optional[Dict[str, Dict[str, str]]] = None,
                                limit: int = 50) -> str:
        """
        Claude 번역 프롬프트용 형식으로 변환 (기존 guide.md와 동일한 형식)

        Args:
            terminology_data: 용어집 데이터 (None이면 자동 로드)
            limit: 최대 용어 수 (프롬프트 길이 제한)

        Returns:
            str: Claude 프롬프트용 용어집 문자열
        """
        try:
            if terminology_data is None:
                terminology_data = self.load_terminology()

            if not terminology_data:
                print("⚠️ 용어집 데이터가 없어 빈 문자열 반환")
                return ""

            # 기존 guide.md 형식으로 변환
            terminology_lines = []
            processed_count = 0

            for korean_term, translations in terminology_data.items():
                if processed_count >= limit:
                    break

                # 5개 언어 모두 있는 경우만 포함 (품질 보장)
                required_langs = ['ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']
                if not all(lang in translations for lang in required_langs):
                    continue

                # 기존 형식: - "한국어" → EN: "English", JA: "日本語", ZH: "中文", TH: "ไทย"
                line = (f'- "{korean_term}" → '
                       f'EN: "{translations["en_US"]}", '
                       f'JA: "{translations["ja_JP"]}", '
                       f'ZH: "{translations["zh_TW"]}", '
                       f'TH: "{translations["th_TH"]}"')

                terminology_lines.append(line)
                processed_count += 1

            result = '\n'.join(terminology_lines)
            print(f"📝 Claude 프롬프트용 용어집 생성: {processed_count}개 용어 (제한: {limit}개)")

            return result

        except Exception as e:
            print(f"⚠️ Claude 프롬프트 형식 변환 실패: {str(e)}")
            return ""

    def is_available(self) -> bool:
        """구글 시트 시스템 사용 가능 여부 확인"""
        return (self.api is not None and
                self.sheet_id is not None and
                bool(self._resolve_credentials_path()))

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 정보 반환"""
        try:
            # 기본 상태
            status = {
                'available': self.is_available(),
                'sheet_id': self.sheet_id,
                'credentials_path': self._resolve_credentials_path(),
                'sheet_names': {
                    'terminology': self.terminology_sheet,
                    'exceptions': self.exceptions_sheet,
                    'metadata': self.metadata_sheet
                }
            }

            # API 상태 확인
            if self.api:
                try:
                    connection_test = self.api.test_connection(self.sheet_id)
                    status['api_connection'] = connection_test

                    if connection_test:
                        available_sheets = self.api.get_available_sheets(self.sheet_id)
                        status['available_sheets'] = [sheet['title'] for sheet in available_sheets]
                except Exception as e:
                    status['api_error'] = str(e)
            else:
                status['api_connection'] = False

            # 캐시 상태
            status['cache_stats'] = self.cache.get_cache_stats()

            return status

        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'sheet_id': self.sheet_id
            }