"""Common utility functions for XLT system"""

import os
import re
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """파일명에서 특수문자 제거 및 정규화

    Args:
        filename: 원본 파일명

    Returns:
        str: 정규화된 파일명
    """
    # 특수문자를 언더스코어로 치환
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # 연속된 언더스코어를 하나로 축소
    sanitized = re.sub(r'_+', '_', sanitized)

    # 앞뒤 공백 및 점 제거
    sanitized = sanitized.strip('. ')

    # 빈 문자열인 경우 기본값
    if not sanitized:
        sanitized = "untitled"

    # 길이 제한 (Windows 호환성)
    if len(sanitized) > 200:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:200-len(ext)] + ext

    return sanitized


def generate_output_filename(source_description: str, extension: str = '.xlsx') -> str:
    """소스 설명을 기반으로 출력 파일명 생성

    Args:
        source_description: 소스 설명
        extension: 파일 확장자

    Returns:
        str: 생성된 파일명
    """
    # 타임스탬프 추가
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 소스에서 의미있는 부분 추출
    base_name = re.sub(r'\s*\([^)]*\)', '', source_description)  # 괄호 내용 제거
    base_name = sanitize_filename(base_name)

    # 파일명 조합
    if len(base_name) > 50:
        base_name = base_name[:50]

    filename = f"{base_name}_{timestamp}{extension}"
    return filename


def clean_text(text: str) -> str:
    """텍스트 정리 및 정규화

    Args:
        text: 원본 텍스트

    Returns:
        str: 정리된 텍스트
    """
    if not text:
        return ""

    # 앞뒤 공백 제거
    cleaned = text.strip()

    # 연속된 공백을 하나로 축소
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # 특수 문자 정리 (선택적)
    # cleaned = re.sub(r'[^\w\s가-힣ぁ-ゖァ-ヺ一-龯\u0E00-\u0E7F]', '', cleaned)

    return cleaned


def is_meaningful_text(text: str, min_length: int = 2) -> bool:
    """의미있는 텍스트인지 판단

    Args:
        text: 검사할 텍스트
        min_length: 최소 길이

    Returns:
        bool: 의미있는 텍스트 여부
    """
    if not text or len(text.strip()) < min_length:
        return False

    # 숫자만 있는 경우
    if text.strip().isdigit():
        return False

    # 특수문자만 있는 경우
    if re.match(r'^[^\w가-힣ぁ-ゖァ-ヺ一-龯\u0E00-\u0E7F]+$', text.strip()):
        return False

    # 의미없는 패턴들
    meaningless_patterns = [
        r'^\d+[a-zA-Z]\s*\)\s*\d+',  # "6f ) 3일" 패턴
        r'^\d+:\d+',  # 시간 패턴
        r'^[a-zA-Z]{1,2}$',  # 단일/이중 알파벳
        r'^\d+[!@#$%^&*()]+$',  # 숫자+특수문자
    ]

    for pattern in meaningless_patterns:
        if re.match(pattern, text.strip()):
            return False

    return True


def format_confidence(confidence: float) -> str:
    """신뢰도를 백분율 문자열로 포맷

    Args:
        confidence: 신뢰도 (0.0-1.0)

    Returns:
        str: 포맷된 백분율 문자열
    """
    return f"{confidence * 100:.1f}%"


def format_duration(seconds: float) -> str:
    """초 단위 시간을 사람이 읽기 쉬운 형태로 포맷

    Args:
        seconds: 초 단위 시간

    Returns:
        str: 포맷된 시간 문자열
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes)}분 {secs:.0f}초"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{int(hours)}시간 {int(minutes)}분 {secs:.0f}초"


def calculate_text_hash(text: str) -> str:
    """텍스트의 해시값 계산 (중복 방지용)

    Args:
        text: 해시를 계산할 텍스트

    Returns:
        str: MD5 해시값
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]


def ensure_directory(dir_path: str) -> Path:
    """디렉토리 존재 확인 및 생성

    Args:
        dir_path: 디렉토리 경로

    Returns:
        Path: Path 객체
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_str(file_path: str) -> str:
    """파일 크기를 사람이 읽기 쉬운 형태로 반환

    Args:
        file_path: 파일 경로

    Returns:
        str: 포맷된 파일 크기
    """
    try:
        size = os.path.getsize(file_path)
    except OSError:
        return "알 수 없음"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def parse_range(range_str: str, max_value: int) -> List[int]:
    """범위 문자열을 파싱하여 인덱스 목록 반환

    Args:
        range_str: 범위 문자열 (예: "1,3,5-8,10")
        max_value: 최대값

    Returns:
        List[int]: 파싱된 인덱스 목록
    """
    indices = []

    for part in range_str.split(','):
        part = part.strip()

        if '-' in part:
            # 범위 처리 (예: "5-8")
            try:
                start, end = map(int, part.split('-'))
                indices.extend(range(max(1, start), min(max_value + 1, end + 1)))
            except ValueError:
                continue
        else:
            # 개별 숫자 처리
            try:
                num = int(part)
                if 1 <= num <= max_value:
                    indices.append(num)
            except ValueError:
                continue

    return sorted(list(set(indices)))  # 중복 제거 및 정렬


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """텍스트를 지정된 길이로 자르기

    Args:
        text: 원본 텍스트
        max_length: 최대 길이
        suffix: 생략 표시

    Returns:
        str: 잘린 텍스트
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """함수 실행 실패 시 재시도

    Args:
        func: 실행할 함수
        max_retries: 최대 재시도 횟수
        delay: 재시도 간격 (초)

    Returns:
        함수 실행 결과
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                time.sleep(delay * (attempt + 1))  # 지수 백오프

    # 모든 재시도 실패
    raise last_exception