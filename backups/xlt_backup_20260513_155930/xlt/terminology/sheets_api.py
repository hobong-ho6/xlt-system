"""
Google Sheets API v4 연동 클래스
Service Account 인증 기반으로 구글 시트에서 데이터를 읽어오는 기능을 제공
"""

import os
import json
import time
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

import requests
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

from ..core.exceptions import XLTException
from ..utils.helpers import retry_on_failure


class GoogleSheetsAPIError(XLTException):
    """Google Sheets API 관련 오류"""

    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(f"Google Sheets API 오류: {message}")


class GoogleSheetsAPI:
    """Google Sheets API v4 래퍼 클래스"""

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Google Sheets API 클래스 초기화

        Args:
            credentials_path: Service Account JSON 파일 경로
        """
        self.credentials_path = credentials_path
        self.session = requests.Session()
        self.base_url = "https://sheets.googleapis.com/v4/spreadsheets"
        self.credentials = None
        self.access_token = None

        # 재시도 설정 (기존 XLT 패턴 활용)
        self.max_retries = 3
        self.base_delay = 1.0

        # 인증 초기화
        self._authenticate()

    def _authenticate(self) -> None:
        """Service Account 방식으로 Google API 인증"""
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Service Account JSON 파일 사용
                self.credentials = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                print(f"✅ Google Sheets 인증 완료: {self.credentials_path}")
            else:
                # 환경변수에서 자격증명 조회 시도
                cred_env = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if cred_env and os.path.exists(cred_env):
                    self.credentials = Credentials.from_service_account_file(
                        cred_env,
                        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                    )
                    print(f"✅ Google Sheets 인증 완료 (환경변수): {cred_env}")
                else:
                    raise GoogleSheetsAPIError(
                        "Google 서비스 계정 인증 정보를 찾을 수 없습니다. "
                        "credentials_path 또는 GOOGLE_APPLICATION_CREDENTIALS 환경변수를 설정해주세요.",
                        error_code="CREDENTIALS_NOT_FOUND"
                    )

            # Access Token 획득
            self._refresh_access_token()

        except Exception as e:
            if isinstance(e, GoogleSheetsAPIError):
                raise e
            raise GoogleSheetsAPIError(f"Google Sheets 인증 실패: {str(e)}", error_code="AUTH_FAILED")

    def _refresh_access_token(self) -> None:
        """Access Token 갱신"""
        try:
            if not self.credentials.valid or self.credentials.expired:
                self.credentials.refresh(Request())

            self.access_token = self.credentials.token

            # 세션 헤더 업데이트
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })

        except Exception as e:
            raise GoogleSheetsAPIError(f"Access Token 갱신 실패: {str(e)}", error_code="TOKEN_REFRESH_FAILED")

    def _handle_api_error(self, response: requests.Response) -> None:
        """Google Sheets API 에러 응답 처리"""
        if response.status_code == 200:
            return

        try:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            error_code = error_data.get('error', {}).get('code', response.status_code)
        except json.JSONDecodeError:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            error_code = response.status_code

        if response.status_code == 401:
            raise GoogleSheetsAPIError(
                "인증이 만료되었거나 유효하지 않습니다. 서비스 계정 권한을 확인해주세요.",
                status_code=401,
                error_code="UNAUTHORIZED"
            )
        elif response.status_code == 403:
            raise GoogleSheetsAPIError(
                f"권한이 없습니다: {error_msg}. 시트에 대한 읽기 권한을 확인해주세요.",
                status_code=403,
                error_code="PERMISSION_DENIED"
            )
        elif response.status_code == 404:
            raise GoogleSheetsAPIError(
                "시트를 찾을 수 없습니다. 시트 ID나 시트명을 확인해주세요.",
                status_code=404,
                error_code="NOT_FOUND"
            )
        elif response.status_code == 429:
            raise GoogleSheetsAPIError(
                "API 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.",
                status_code=429,
                error_code="QUOTA_EXCEEDED"
            )
        else:
            raise GoogleSheetsAPIError(
                f"API 오류 (HTTP {response.status_code}): {error_msg}",
                status_code=response.status_code,
                error_code=str(error_code)
            )

    def get_sheet_values(self, sheet_id: str, range_name: str, timeout: int = 30) -> List[List[str]]:
        """
        시트에서 데이터 조회

        Args:
            sheet_id: 구글 시트 ID
            range_name: 범위 (예: "Sheet1!A1:Z1000", "Terminology!A:J")
            timeout: 타임아웃 (초)

        Returns:
            List[List[str]]: 2차원 배열 형태의 시트 데이터
        """
        def _fetch():
            # Access Token 유효성 체크 및 갱신
            if not self.credentials.valid or self.credentials.expired:
                self._refresh_access_token()

            url = f"{self.base_url}/{sheet_id}/values/{range_name}"
            params = {
                'valueRenderOption': 'UNFORMATTED_VALUE',  # 원본 값 가져오기
                'dateTimeRenderOption': 'FORMATTED_STRING'  # 날짜는 문자열로
            }

            response = self.session.get(url, params=params, timeout=timeout)
            self._handle_api_error(response)

            data = response.json()
            return data.get('values', [])

        try:
            # 기존 XLT 패턴의 재시도 로직 활용
            return retry_on_failure(_fetch, max_retries=self.max_retries, delay=self.base_delay)

        except Exception as e:
            if isinstance(e, GoogleSheetsAPIError):
                raise e
            raise GoogleSheetsAPIError(f"시트 데이터 조회 실패: {str(e)}")

    def batch_get_values(self, sheet_id: str, ranges: List[str], timeout: int = 30) -> Dict[str, List[List[str]]]:
        """
        여러 범위의 데이터를 한번에 조회 (성능 최적화)

        Args:
            sheet_id: 구글 시트 ID
            ranges: 조회할 범위 목록 (예: ["Terminology!A:J", "Exceptions!A:K"])
            timeout: 타임아웃 (초)

        Returns:
            Dict[str, List[List[str]]]: 범위별 시트 데이터
        """
        def _batch_fetch():
            # Access Token 유효성 체크 및 갱신
            if not self.credentials.valid or self.credentials.expired:
                self._refresh_access_token()

            url = f"{self.base_url}/{sheet_id}/values:batchGet"
            params = {
                'ranges': ranges,
                'valueRenderOption': 'UNFORMATTED_VALUE',
                'dateTimeRenderOption': 'FORMATTED_STRING'
            }

            response = self.session.get(url, params=params, timeout=timeout)
            self._handle_api_error(response)

            data = response.json()

            # 결과를 범위명으로 매핑
            result = {}
            for i, value_range in enumerate(data.get('valueRanges', [])):
                range_name = ranges[i] if i < len(ranges) else f"range_{i}"
                result[range_name] = value_range.get('values', [])

            return result

        try:
            return retry_on_failure(_batch_fetch, max_retries=self.max_retries, delay=self.base_delay)

        except Exception as e:
            if isinstance(e, GoogleSheetsAPIError):
                raise e
            raise GoogleSheetsAPIError(f"배치 데이터 조회 실패: {str(e)}")

    def get_sheet_metadata(self, sheet_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        시트 메타데이터 조회 (시트명 목록, 속성 등)

        Args:
            sheet_id: 구글 시트 ID
            timeout: 타임아웃 (초)

        Returns:
            Dict[str, Any]: 시트 메타데이터
        """
        def _fetch_metadata():
            # Access Token 유효성 체크 및 갱신
            if not self.credentials.valid or self.credentials.expired:
                self._refresh_access_token()

            url = f"{self.base_url}/{sheet_id}"
            params = {
                'fields': 'sheets.properties,properties.title'
            }

            response = self.session.get(url, params=params, timeout=timeout)
            self._handle_api_error(response)

            return response.json()

        try:
            return retry_on_failure(_fetch_metadata, max_retries=self.max_retries, delay=self.base_delay)

        except Exception as e:
            if isinstance(e, GoogleSheetsAPIError):
                raise e
            raise GoogleSheetsAPIError(f"메타데이터 조회 실패: {str(e)}")

    def test_connection(self, sheet_id: str) -> bool:
        """
        구글 시트 연결 테스트

        Args:
            sheet_id: 테스트할 구글 시트 ID

        Returns:
            bool: 연결 성공 여부
        """
        try:
            # 간단한 메타데이터 조회로 연결 테스트
            metadata = self.get_sheet_metadata(sheet_id, timeout=10)
            return 'properties' in metadata

        except Exception as e:
            print(f"⚠️ Google Sheets 연결 테스트 실패: {str(e)}")
            return False

    def get_available_sheets(self, sheet_id: str) -> List[Dict[str, Any]]:
        """
        시트 내 사용 가능한 탭(워크시트) 목록 조회

        Args:
            sheet_id: 구글 시트 ID

        Returns:
            List[Dict[str, Any]]: 탭 정보 목록 (제목, ID 등)
        """
        try:
            metadata = self.get_sheet_metadata(sheet_id)
            sheets = []

            for sheet in metadata.get('sheets', []):
                properties = sheet.get('properties', {})
                sheets.append({
                    'title': properties.get('title', ''),
                    'sheet_id': properties.get('sheetId', 0),
                    'index': properties.get('index', 0),
                    'sheet_type': properties.get('sheetType', 'GRID')
                })

            return sorted(sheets, key=lambda x: x['index'])

        except Exception as e:
            raise GoogleSheetsAPIError(f"시트 목록 조회 실패: {str(e)}")