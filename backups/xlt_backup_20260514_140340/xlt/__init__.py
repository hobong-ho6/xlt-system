"""
XLT (eXtract, Localize, Translate) System v3.0

피그마 URL 또는 이미지를 OCR로 처리하여 텍스트를 추출하고
Unifi guide.md 기준을 준수하여 다국어 번역하는 현지화 자동 생성 시스템
"""

__version__ = "3.0.0"
__author__ = "XLT Team"

from .core.pipeline import XLTPipeline
from .core.config import XLTConfig

# 번역기 (필요시 직접 사용)
try:
    from .translation.unifi_translator import UnifiTranslator
    __all__ = ["XLTPipeline", "XLTConfig", "UnifiTranslator"]
except ImportError:
    from .translation.translator import Translator
    __all__ = ["XLTPipeline", "XLTConfig", "Translator"]