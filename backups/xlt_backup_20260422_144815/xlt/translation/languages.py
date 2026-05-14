"""Language configuration for XLT translation system"""

from typing import Dict, List, Set


# 지원하는 언어 코드와 표시명
SUPPORTED_LANGUAGES: Dict[str, str] = {
    'ko_KR': '한국어',
    'en_US': 'English',
    'ja_JP': '日本語',
    'zh_TW': '中文(繁體)',
    'th_TH': 'ไทย'
}

# 기본 번역 언어 목록
DEFAULT_LANGUAGES: List[str] = [
    'ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH'
]

# Google Translate API 언어 코드 매핑
GOOGLE_TRANSLATE_MAPPING: Dict[str, str] = {
    'ko_KR': 'ko',
    'en_US': 'en',
    'ja_JP': 'ja',
    'zh_TW': 'zh-tw',
    'th_TH': 'th'
}

# EasyOCR 언어 코드 매핑 (OCR 엔진별 설정)
EASYOCR_LANGUAGE_SETS: Dict[str, List[str]] = {
    'korean_english': ['ko', 'en'],
    'japanese_english': ['ja', 'en'],
    'chinese_english': ['ch_sim', 'en'],  # 간체중국어+영어
    'thai_english': ['th', 'en']
}

# 언어별 OCR 리더 매핑
LANGUAGE_OCR_READERS: Dict[str, str] = {
    'ko_KR': 'korean_english',
    'en_US': 'korean_english',  # 기본적으로 한영 리더 사용
    'ja_JP': 'japanese_english',
    'zh_TW': 'chinese_english',
    'th_TH': 'thai_english'
}

# 언어 감지 우선순위 (자동 감지 시 사용)
LANGUAGE_DETECTION_PRIORITY: List[str] = [
    'ko_KR',  # 한국어 우선
    'en_US',
    'ja_JP',
    'zh_TW',
    'th_TH'
]


def validate_language_codes(language_codes: List[str]) -> List[str]:
    """언어 코드 유효성 검사 및 정규화

    Args:
        language_codes: 검사할 언어 코드 목록

    Returns:
        List[str]: 유효한 언어 코드 목록
    """
    valid_codes = []
    supported_set = set(SUPPORTED_LANGUAGES.keys())

    for code in language_codes:
        if code in supported_set:
            valid_codes.append(code)

    return valid_codes


def get_language_display_name(language_code: str) -> str:
    """언어 코드에 대한 표시명 반환

    Args:
        language_code: 언어 코드 (예: 'ko_KR')

    Returns:
        str: 언어 표시명 (예: '한국어')
    """
    return SUPPORTED_LANGUAGES.get(language_code, language_code)


def get_google_translate_code(language_code: str) -> str:
    """XLT 언어 코드를 Google Translate API 코드로 변환

    Args:
        language_code: XLT 언어 코드 (예: 'ko_KR')

    Returns:
        str: Google Translate API 언어 코드 (예: 'ko')
    """
    return GOOGLE_TRANSLATE_MAPPING.get(language_code, language_code.split('_')[0])


def get_required_ocr_readers(language_codes: List[str]) -> Set[str]:
    """주어진 언어들을 처리하기 위해 필요한 OCR 리더 목록 반환

    Args:
        language_codes: 언어 코드 목록

    Returns:
        Set[str]: 필요한 OCR 리더 이름 집합
    """
    readers = set()
    for code in language_codes:
        reader = LANGUAGE_OCR_READERS.get(code, 'korean_english')
        readers.add(reader)
    return readers


def detect_primary_language(text: str) -> str:
    """텍스트에서 주요 언어 감지 (간단한 휴리스틱)

    Args:
        text: 분석할 텍스트

    Returns:
        str: 감지된 언어 코드
    """
    # 한글 문자 확인
    korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
    if korean_chars > 0:
        return 'ko_KR'

    # 히라가나/가타카나 확인
    japanese_chars = sum(1 for char in text if
                        ('\u3040' <= char <= '\u309f') or  # 히라가나
                        ('\u30a0' <= char <= '\u30ff'))   # 가타카나
    if japanese_chars > 0:
        return 'ja_JP'

    # 중국어 문자 확인 (간체/번체 구분 없이)
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    if chinese_chars > 0:
        return 'zh_TW'  # 기본적으로 번체 중국어로 설정

    # 태국어 문자 확인
    thai_chars = sum(1 for char in text if '\u0e00' <= char <= '\u0e7f')
    if thai_chars > 0:
        return 'th_TH'

    # 기본값은 영어
    return 'en_US'


def get_excel_column_headers() -> List[str]:
    """Excel 파일의 컬럼 헤더 순서 반환

    Returns:
        List[str]: ['Key', 'en_US', 'ko_KR', 'ja_JP', 'zh_TW', 'th_TH'] 순서
    """
    return ['Key'] + DEFAULT_LANGUAGES


def format_language_list(language_codes: List[str]) -> str:
    """언어 코드 목록을 사용자 친화적 문자열로 포맷

    Args:
        language_codes: 언어 코드 목록

    Returns:
        str: 포맷된 문자열 (예: "한국어, English, 日本語")
    """
    display_names = [get_language_display_name(code) for code in language_codes]
    return ', '.join(display_names)