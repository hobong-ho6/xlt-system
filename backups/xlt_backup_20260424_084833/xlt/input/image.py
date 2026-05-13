"""Local image file processor for XLT system"""

import os
from typing import Tuple
from PIL import Image

from .base import InputProcessor
from ..core.exceptions import InputProcessingError


class ImageProcessor(InputProcessor):
    """로컬 이미지 파일 처리기"""

    # 지원하는 이미지 형식
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.gif'}

    def can_process(self, source: str) -> bool:
        """이미지 파일 처리 가능 여부 확인

        Args:
            source: 파일 경로

        Returns:
            bool: 처리 가능 여부
        """
        if not os.path.isfile(source):
            return False

        # 파일 확장자 확인
        _, ext = os.path.splitext(source.lower())
        return ext in self.SUPPORTED_FORMATS

    def process(self, source: str) -> Tuple[Image.Image, str]:
        """이미지 파일 처리

        Args:
            source: 이미지 파일 경로

        Returns:
            Tuple[Image.Image, str]: (PIL 이미지, 설명)

        Raises:
            InputProcessingError: 파일 처리 중 오류 발생
        """
        if not self.can_process(source):
            raise InputProcessingError(
                "image",
                f"지원하지 않는 파일이거나 파일이 존재하지 않습니다: {source}"
            )

        try:
            # 이미지 파일 열기
            with Image.open(source) as img:
                # RGB 모드로 변환 (일부 OCR 엔진에서 요구)
                if img.mode not in ['RGB', 'RGBA']:
                    img = img.convert('RGB')

                # 이미지 복사 (원본 파일 핸들 해제)
                image = img.copy()

            # 이미지 유효성 검사
            if not self.validate_image(image):
                raise InputProcessingError("image", f"유효하지 않은 이미지: {source}")

            # 필요시 크기 조정
            image = self.resize_if_needed(image)

            # 파일 정보 생성
            file_name = os.path.basename(source)
            file_size = os.path.getsize(source)
            description = f"{file_name} ({image.size[0]}x{image.size[1]}, {file_size:,} bytes)"

            return image, description

        except FileNotFoundError:
            raise InputProcessingError("image", f"파일을 찾을 수 없습니다: {source}")

        except PermissionError:
            raise InputProcessingError("image", f"파일 접근 권한이 없습니다: {source}")

        except Image.UnidentifiedImageError:
            raise InputProcessingError("image", f"이미지 형식을 인식할 수 없습니다: {source}")

        except OSError as e:
            raise InputProcessingError("image", f"파일 처리 중 오류: {str(e)}")

        except Exception as e:
            raise InputProcessingError("image", f"예기치 않은 오류: {str(e)}")

    def get_image_info(self, source: str) -> dict:
        """이미지 파일 정보 반환 (처리 없이)

        Args:
            source: 이미지 파일 경로

        Returns:
            dict: 이미지 정보
        """
        if not os.path.isfile(source):
            return {}

        try:
            with Image.open(source) as img:
                return {
                    'filename': os.path.basename(source),
                    'size': img.size,
                    'mode': img.mode,
                    'format': img.format,
                    'file_size': os.path.getsize(source)
                }
        except:
            return {}

    @staticmethod
    def list_supported_formats() -> list:
        """지원하는 이미지 형식 목록 반환

        Returns:
            list: 지원 형식 목록
        """
        return list(ImageProcessor.SUPPORTED_FORMATS)