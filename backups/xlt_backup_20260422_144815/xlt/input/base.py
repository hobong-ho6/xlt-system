"""Base input processor for XLT system"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from PIL import Image
import os


class InputProcessor(ABC):
    """입력 처리를 위한 추상 기본 클래스"""

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def can_process(self, source: str) -> bool:
        """해당 소스를 처리할 수 있는지 확인"""
        pass

    @abstractmethod
    def process(self, source: str) -> Tuple[Image.Image, str]:
        """소스를 처리하여 PIL Image와 설명을 반환

        Args:
            source: 입력 소스 (파일 경로, URL, 특수 키워드 등)

        Returns:
            Tuple[Image.Image, str]: (처리된 이미지, 소스 설명)

        Raises:
            InputProcessingError: 처리 중 오류 발생 시
        """
        pass

    def cleanup(self) -> None:
        """임시 파일 정리 (필요한 경우 오버라이드)"""
        pass

    @staticmethod
    def detect_input_type(source: str) -> str:
        """입력 소스 타입 자동 감지

        Args:
            source: 입력 소스

        Returns:
            str: 'file', 'figma' 중 하나
        """
        if 'figma.com' in source.lower():
            return 'figma'
        elif os.path.isfile(source):
            return 'file'
        else:
            # 기본적으로 파일로 간주
            return 'file'

    def validate_image(self, image: Image.Image) -> bool:
        """이미지 유효성 검사

        Args:
            image: PIL Image 객체

        Returns:
            bool: 유효한 이미지인지 여부
        """
        if image is None:
            return False

        # 이미지 크기 검사
        width, height = image.size
        if width < 10 or height < 10:
            return False

        # 이미지 크기가 너무 큰 경우 (메모리 이슈 방지)
        if width * height > 50000000:  # 50MP 이상
            return False

        return True

    def resize_if_needed(self, image: Image.Image, max_size: int = 4000) -> Image.Image:
        """필요시 이미지 크기 조정

        Args:
            image: 원본 이미지
            max_size: 최대 허용 크기 (픽셀)

        Returns:
            Image.Image: 크기 조정된 이미지
        """
        width, height = image.size

        if max(width, height) <= max_size:
            return image

        # 비율 유지하면서 크기 조정
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)