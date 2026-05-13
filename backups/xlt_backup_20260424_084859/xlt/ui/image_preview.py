"""Image preview and confirmation utilities for XLT system"""

import os
from typing import Optional, Tuple, Dict, Any, List
from PIL import Image
import requests


class ImagePreview:
    """이미지 미리보기 및 확인 유틸리티 클래스"""

    def __init__(self, config):
        self.config = config

    def verify_and_preview_source(self, source: str) -> Dict[str, Any]:
        """소스를 확인하고 미리보기 정보 제공

        Args:
            source: 이미지 소스 (파일 경로, 피그마 URL)

        Returns:
            Dict[str, Any]: 확인 결과 및 미리보기 정보
        """
        from ..input.base import InputProcessor

        # 입력 타입 감지
        input_type = InputProcessor.detect_input_type(source)

        if input_type == 'file':
            return self._verify_local_image(source)
        elif input_type == 'figma':
            return self._verify_figma_url(source)
        else:
            return {
                'valid': False,
                'error': f"지원하지 않는 입력 타입: {input_type}",
                'source_type': input_type
            }

    def _verify_local_image(self, file_path: str) -> Dict[str, Any]:
        """로컬 이미지 파일 확인"""
        result = {
            'valid': False,
            'source_type': 'file',
            'source': file_path
        }

        try:
            # 파일 존재 여부 확인
            if not os.path.isfile(file_path):
                result['error'] = f"파일을 찾을 수 없습니다: {file_path}"
                return result

            # 이미지 파일인지 확인
            try:
                with Image.open(file_path) as img:
                    result.update({
                        'valid': True,
                        'width': img.size[0],
                        'height': img.size[1],
                        'format': img.format,
                        'mode': img.mode,
                        'file_size': os.path.getsize(file_path)
                    })

            except Exception as e:
                result['error'] = f"이미지 파일이 아니거나 손상되었습니다: {str(e)}"
                return result

        except Exception as e:
            result['error'] = f"파일 확인 중 오류: {str(e)}"

        return result

    def _verify_figma_url(self, figma_url: str) -> Dict[str, Any]:
        """피그마 URL 확인"""
        result = {
            'valid': False,
            'source_type': 'figma',
            'source': figma_url
        }

        try:
            from ..input.figma import FigmaProcessor

            # 피그마 프로세서로 URL 파싱 테스트
            figma_processor = FigmaProcessor(self.config)

            # 토큰 확인
            if not figma_processor.figma_token:
                result['error'] = "피그마 액세스 토큰이 설정되지 않았습니다"
                result['help'] = "figma_config.json에 토큰을 설정하거나 FIGMA_TOKEN 환경변수를 설정해주세요"
                return result

            # URL 파싱 테스트
            try:
                file_key, node_id = figma_processor._parse_figma_url(figma_url)
                result['file_key'] = file_key
                result['node_id'] = node_id
            except Exception as e:
                result['error'] = f"올바르지 않은 피그마 URL입니다: {str(e)}"
                return result

            # API 연결 테스트
            if not figma_processor.test_figma_connection():
                result['error'] = "피그마 API에 연결할 수 없습니다. 토큰을 확인해주세요"
                return result

            # 파일 정보 가져오기
            file_info = figma_processor.get_figma_file_info(file_key)
            if 'error' not in file_info:
                result.update({
                    'valid': True,
                    'file_name': file_info.get('name', 'Unknown'),
                    'last_modified': file_info.get('lastModified', 'Unknown'),
                    'thumbnail_url': file_info.get('thumbnailUrl', '')
                })
            else:
                result['error'] = f"피그마 파일 정보를 가져올 수 없습니다: {file_info['error']}"

        except Exception as e:
            result['error'] = f"피그마 URL 확인 중 오류: {str(e)}"

        return result


    def format_preview_info(self, verification_result: Dict[str, Any]) -> str:
        """확인 결과를 사용자 친화적으로 포맷

        Args:
            verification_result: verify_and_preview_source 결과

        Returns:
            str: 포맷된 정보 문자열
        """
        if not verification_result['valid']:
            error_msg = verification_result.get('error', '알 수 없는 오류')
            help_msg = verification_result.get('help', '')

            result = f"❌ {error_msg}"
            if help_msg:
                result += f"\n💡 {help_msg}"
            return result

        source_type = verification_result['source_type']
        source = verification_result['source']

        if source_type == 'file':
            width = verification_result['width']
            height = verification_result['height']
            file_size = verification_result['file_size']
            format_type = verification_result['format']

            size_mb = file_size / (1024 * 1024)
            return (f"✅ 로컬 이미지 파일 확인됨\n"
                   f"   📄 파일: {os.path.basename(source)}\n"
                   f"   📏 크기: {width}x{height}px\n"
                   f"   📊 용량: {size_mb:.1f}MB\n"
                   f"   🎨 형식: {format_type}")

        elif source_type == 'figma':
            file_name = verification_result.get('file_name', 'Unknown')
            file_key = verification_result.get('file_key', 'Unknown')
            last_modified = verification_result.get('last_modified', 'Unknown')

            return (f"✅ 피그마 파일 확인됨\n"
                   f"   📄 파일명: {file_name}\n"
                   f"   🆔 파일 키: {file_key[:15]}...\n"
                   f"   📅 수정일: {last_modified}")

        return "✅ 이미지 소스 확인됨"

    def get_user_confirmation(self, verification_result: Dict[str, Any]) -> bool:
        """사용자에게 확인을 받음

        Args:
            verification_result: 확인 결과

        Returns:
            bool: 사용자 승인 여부
        """
        if not verification_result['valid']:
            return False

        source_type = verification_result['source_type']

        print(f"\n🎯 이 {'이미지' if source_type == 'file' else '소스'}로 XLT 처리를 시작하시겠습니까?")

        while True:
            try:
                choice = input("진행하시겠습니까? (Y/n): ").strip().lower()

                if choice in ['y', 'yes', '', 'ㅇ']:
                    return True
                elif choice in ['n', 'no', 'ㄴ']:
                    return False
                else:
                    print("y(예) 또는 n(아니오)로 답해주세요.")

            except KeyboardInterrupt:
                print(f"\n🚫 사용자가 취소했습니다.")
                return False
            except:
                print("❌ 입력 오류가 발생했습니다.")

    def suggest_alternatives(self, failed_source: str) -> List[str]:
        """실패한 소스에 대해 대안 제시

        Args:
            failed_source: 실패한 소스

        Returns:
            List[str]: 대안 제안 목록
        """
        suggestions = []

        # 로컬 파일 경우
        if os.path.sep in failed_source or '.' in failed_source:
            # 현재 디렉토리의 이미지 파일들 찾기
            try:
                current_dir = os.getcwd()
                image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.gif'}

                image_files = []
                for file in os.listdir(current_dir):
                    if os.path.splitext(file.lower())[1] in image_extensions:
                        image_files.append(file)

                if image_files:
                    suggestions.extend(image_files[:3])  # 최대 3개만

                # Learning 폴더 확인
                learning_dir = os.path.join(current_dir, 'Learning')
                if os.path.exists(learning_dir):
                    for file in os.listdir(learning_dir):
                        if os.path.splitext(file.lower())[1] in image_extensions:
                            suggestions.append(f"Learning/{file}")
                            if len(suggestions) >= 5:  # 최대 5개로 제한
                                break

            except:
                pass

        # 피그마 URL인 경우
        elif 'figma' in failed_source.lower():
            suggestions.extend([
                "https://figma.com/design/YOUR_FILE_ID/...",
                "https://figma.com/board/YOUR_FILE_ID/..."
            ])

        # 기타 일반적인 제안
        if not suggestions:
            suggestions.extend([
                "Learning/일일 미션.png (샘플 이미지)",
                "image.png (현재 폴더의 이미지 파일)"
            ])

        return suggestions[:5]  # 최대 5개로 제한