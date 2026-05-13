"""Input processing modules for various sources"""

from .base import InputProcessor
from .image import ImageProcessor
from .figma import FigmaProcessor

__all__ = ["InputProcessor", "ImageProcessor", "FigmaProcessor"]