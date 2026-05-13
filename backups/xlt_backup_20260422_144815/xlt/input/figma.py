"""Figma URL processor for XLT system"""

import os
import re
import tempfile
import requests
from typing import Tuple, Optional
from urllib.parse import urlparse, parse_qs
from PIL import Image

from .base import InputProcessor
from ..core.exceptions import InputProcessingError, FigmaAPIError


class FigmaProcessor(InputProcessor):
    """피그마 URL 처리기"""

    def __init__(self, config):
        super().__init__(config)
        self.figma_token = config.get_figma_token()
        self.temp_dir = config.figma_temp_dir
        self.session = requests.Session()

        # Figma API 기본 설정
        if self.figma_token:
            self.session.headers.update({
                'X-Figma-Token': self.figma_token,
                'User-Agent': 'XLT-System/2.0'
            })

    def can_process(self, source: str) -> bool:
        """피그마 URL 처리 가능 여부 확인

        Args:
            source: URL 문자열

        Returns:
            bool: 처리 가능 여부
        """
        return 'figma.com' in source.lower()

    def process(self, source: str) -> Tuple[Image.Image, str]:
        """피그마 URL 처리

        Args:
            source: 피그마 URL

        Returns:
            Tuple[Image.Image, str]: (PIL 이미지, 설명)

        Raises:
            InputProcessingError: 피그마 처리 중 오류 발생
        """
        if not self.can_process(source):
            raise InputProcessingError("figma", f"피그마 URL이 아닙니다: {source}")

        if not self.figma_token:
            raise FigmaAPIError("피그마 액세스 토큰이 설정되지 않았습니다")

        try:
            # URL 파싱
            file_key, node_id = self._parse_figma_url(source)

            # 이미지 다운로드 (임시 파일로 처리)
            image_path = self._download_figma_image(file_key, node_id, source)

            # ✅ v3.0 누락 수정: 웹 서버에서 접근할 수 있도록 파일 경로 저장
            self.last_saved_file = image_path

            # 이미지 로드
            with Image.open(image_path) as img:
                image = img.convert('RGB').copy()

            # 이미지 유효성 검사
            if not self.validate_image(image):
                raise InputProcessingError("figma", "다운로드된 피그마 이미지가 유효하지 않습니다")

            # 필요시 크기 조정
            image = self.resize_if_needed(image)

            # 설명 생성 (임시 파일 처리)
            description = f"Figma: {file_key}"
            if node_id:
                description += f" (node: {node_id})"
            description += f" ({image.size[0]}x{image.size[1]})"

            return image, description

        except (InputProcessingError, FigmaAPIError):
            raise
        except Exception as e:
            raise InputProcessingError("figma", f"피그마 처리 중 오류: {str(e)}")

    def _parse_figma_url(self, url: str) -> Tuple[str, Optional[str]]:
        """피그마 URL에서 file_key와 node_id 추출

        Args:
            url: 피그마 URL

        Returns:
            Tuple[str, Optional[str]]: (file_key, node_id)

        Raises:
            InputProcessingError: URL 파싱 실패 시
        """
        try:
            parsed = urlparse(url)

            # URL 패턴별 처리
            path_parts = parsed.path.strip('/').split('/')

            # Design URL: /design/FILE_KEY/NAME
            if 'design' in path_parts:
                design_idx = path_parts.index('design')
                if design_idx + 1 < len(path_parts):
                    file_key = path_parts[design_idx + 1]
                else:
                    raise ValueError("파일 키를 찾을 수 없습니다")

            # Board URL: /board/FILE_KEY/NAME (FigJam)
            elif 'board' in path_parts:
                board_idx = path_parts.index('board')
                if board_idx + 1 < len(path_parts):
                    file_key = path_parts[board_idx + 1]
                else:
                    raise ValueError("파일 키를 찾을 수 없습니다")

            # Make URL: /make/FILE_KEY/NAME
            elif 'make' in path_parts:
                make_idx = path_parts.index('make')
                if make_idx + 1 < len(path_parts):
                    file_key = path_parts[make_idx + 1]
                else:
                    raise ValueError("파일 키를 찾을 수 없습니다")

            else:
                raise ValueError("지원하지 않는 피그마 URL 형식입니다")

            # node-id 추출
            node_id = None
            query_params = parse_qs(parsed.query)

            if 'node-id' in query_params:
                raw_node_id = query_params['node-id'][0]
                # node-id의 '-'를 ':'로 변환 (피그마 API 형식)
                node_id = raw_node_id.replace('-', ':')

            return file_key, node_id

        except Exception as e:
            raise InputProcessingError("figma", f"피그마 URL 파싱 실패: {str(e)}")

    def _download_figma_image(self, file_key: str, node_id: Optional[str], source_url: str) -> str:
        """피그마에서 이미지 다운로드

        Args:
            file_key: 피그마 파일 키
            node_id: 노드 ID (옵션)
            source_url: 원본 URL (로깅용)

        Returns:
            str: 다운로드된 이미지 파일 경로

        Raises:
            FigmaAPIError: 피그마 API 오류 시
        """
        try:
            # 임시 디렉토리 생성
            os.makedirs(self.temp_dir, exist_ok=True)

            # Figma API URL 생성
            api_url = f"https://api.figma.com/v1/images/{file_key}"

            # API 파라미터
            params = {
                'format': 'png',
                'scale': '2',  # 고해상도
            }

            if node_id:
                params['ids'] = node_id

            # 이미지 URL 요청
            response = self.session.get(api_url, params=params, timeout=30)

            if response.status_code == 401:
                raise FigmaAPIError("피그마 액세스 토큰이 유효하지 않습니다", response.status_code)
            elif response.status_code == 404:
                raise FigmaAPIError("피그마 파일을 찾을 수 없습니다", response.status_code)
            elif response.status_code != 200:
                raise FigmaAPIError(f"피그마 API 오류: {response.text}", response.status_code)

            # 응답 파싱
            data = response.json()

            if 'images' not in data or not data['images']:
                raise FigmaAPIError("피그마에서 이미지를 생성할 수 없습니다")

            # 이미지 URL 가져오기
            images = data['images']
            if node_id and node_id in images:
                image_url = images[node_id]
            else:
                # 첫 번째 이미지 사용
                image_url = next(iter(images.values()))

            if not image_url:
                raise FigmaAPIError("이미지 URL이 생성되지 않았습니다")

            # 이미지 다운로드 (임시 파일로 처리)
            file_path = self._download_image_from_url(image_url, file_key, node_id)

            return file_path

        except requests.RequestException as e:
            raise FigmaAPIError(f"네트워크 오류: {str(e)}")
        except Exception as e:
            if isinstance(e, FigmaAPIError):
                raise
            raise FigmaAPIError(f"이미지 다운로드 실패: {str(e)}")

    def _download_image_from_url(self, image_url: str, file_key: str, node_id: Optional[str]) -> str:
        """URL에서 이미지 다운로드 (임시 파일로 처리)

        Args:
            image_url: 다운로드할 이미지 URL
            file_key: 파일 키 (메타데이터용)
            node_id: 노드 ID (메타데이터용)

        Returns:
            str: 다운로드된 임시 파일 경로
        """
        try:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                # 이미지 다운로드
                response = requests.get(image_url, stream=True, timeout=60)
                response.raise_for_status()

                # 임시 파일에 저장
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)

                tmp_file_path = tmp_file.name

            # 파일 크기 확인
            if os.path.getsize(tmp_file_path) == 0:
                os.unlink(tmp_file_path)
                raise FigmaAPIError("다운로드된 파일이 비어있습니다")

            return tmp_file_path

        except requests.RequestException as e:
            raise FigmaAPIError(f"이미지 다운로드 실패: {str(e)}")

    def get_figma_file_info(self, file_key: str) -> dict:
        """피그마 파일 정보 가져오기

        Args:
            file_key: 피그마 파일 키

        Returns:
            dict: 파일 정보
        """
        if not self.figma_token:
            return {'error': 'No token'}

        try:
            url = f"https://api.figma.com/v1/files/{file_key}"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                return {'error': f'API error: {response.status_code}'}

            data = response.json()
            return {
                'name': data.get('name', 'Unknown'),
                'lastModified': data.get('lastModified', 'Unknown'),
                'thumbnailUrl': data.get('thumbnailUrl', ''),
                'version': data.get('version', 'Unknown')
            }

        except Exception as e:
            return {'error': str(e)}

    def cleanup(self):
        """피그마 관련 임시 파일 정리"""
        # 임시 파일들은 시스템이 자동으로 정리하므로 별도 작업 불필요
        pass


    def test_figma_connection(self) -> bool:
        """피그마 API 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        if not self.figma_token:
            return False

        try:
            # 간단한 API 호출로 토큰 유효성 확인
            url = "https://api.figma.com/v1/me"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200

        except Exception:
            return False

    def extract_text_from_node(self, file_key: str, node_id: Optional[str] = None) -> dict:
        """피그마 노드에서 텍스트 직접 추출 (OCR 대신 API 사용)

        Args:
            file_key: 피그마 파일 키
            node_id: 노드 ID (옵션, 없으면 전체 파일)

        Returns:
            dict: {'status': 'success'/'error', 'texts': [...], 'count': int}
        """
        if not self.figma_token:
            return {
                'status': 'error',
                'error': '피그마 액세스 토큰이 설정되지 않았습니다',
                'texts': [],
                'count': 0
            }

        try:
            # 피그마 API 호출
            if node_id:
                # 특정 노드만 가져오기
                url = f"https://api.figma.com/v1/files/{file_key}/nodes"
                params = {'ids': node_id}
            else:
                # 전체 파일 가져오기
                url = f"https://api.figma.com/v1/files/{file_key}"
                params = {}

            print(f"🔍 피그마 API로 텍스트 추출 중...")
            print(f"   URL: {url}")
            if node_id:
                print(f"   Node ID: {node_id}")

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 401:
                return {
                    'status': 'error',
                    'error': '피그마 액세스 토큰이 유효하지 않습니다',
                    'texts': [],
                    'count': 0
                }
            elif response.status_code == 404:
                return {
                    'status': 'error',
                    'error': '피그마 파일 또는 노드를 찾을 수 없습니다',
                    'texts': [],
                    'count': 0
                }
            elif response.status_code != 200:
                return {
                    'status': 'error',
                    'error': f'피그마 API 오류: {response.status_code}',
                    'texts': [],
                    'count': 0
                }

            data = response.json()

            # 텍스트 추출
            texts = []

            if node_id and 'nodes' in data:
                # 특정 노드에서 추출
                node_data = data['nodes'].get(node_id)
                if node_data and 'document' in node_data:
                    texts = self._traverse_node(node_data['document'])
            elif 'document' in data:
                # 전체 파일에서 추출
                texts = self._traverse_node(data['document'])

            print(f"✅ 피그마 API로 {len(texts)}개 텍스트 추출 완료")

            return {
                'status': 'success',
                'texts': texts,
                'count': len(texts)
            }

        except requests.RequestException as e:
            return {
                'status': 'error',
                'error': f'네트워크 오류: {str(e)}',
                'texts': [],
                'count': 0
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'텍스트 추출 실패: {str(e)}',
                'texts': [],
                'count': 0
            }

    def _traverse_node(self, node: dict, texts: list = None) -> list:
        """노드 트리를 재귀적으로 순회하며 TEXT 타입 노드 찾기

        Args:
            node: 피그마 노드 객체
            texts: 누적된 텍스트 리스트

        Returns:
            list: 추출된 텍스트 리스트 [{'text': str, 'confidence': 1.0}, ...]
        """
        if texts is None:
            texts = []

        # TEXT 타입 노드인지 확인
        if node.get('type') == 'TEXT':
            text_content = node.get('characters', '').strip()
            if text_content:  # 비어있지 않은 텍스트만 추가
                texts.append({
                    'text': text_content,
                    'confidence': 1.0,  # API에서 직접 가져온 텍스트는 신뢰도 100%
                    'source': 'figma_api'
                })

        # 자식 노드 재귀 순회
        if 'children' in node:
            for child in node['children']:
                self._traverse_node(child, texts)

        return texts

    @staticmethod
    def extract_file_key_from_url(url: str) -> Optional[str]:
        """URL에서 파일 키만 추출 (토큰 없이도 사용 가능)

        Args:
            url: 피그마 URL

        Returns:
            Optional[str]: 파일 키 또는 None
        """
        try:
            processor = FigmaProcessor(type('Config', (), {'get_figma_token': lambda: None, 'figma_temp_dir': 'temp'})())
            file_key, _ = processor._parse_figma_url(url)
            return file_key
        except:
            return None