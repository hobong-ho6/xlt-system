"""Text extractors for processing OCR results"""

import re
from typing import List, Dict, Any, Tuple
from ..utils.helpers import is_meaningful_text, truncate_text


class TextExtractor:
    """OCR 결과에서 의미있는 텍스트를 추출하고 분류하는 클래스"""

    def __init__(self, config):
        self.config = config

    def extract_meaningful_texts(self, ocr_results: List[Dict[str, Any]]) -> List[str]:
        """의미있는 텍스트만 추출하여 반환 (자동 모드용)

        Args:
            ocr_results: OCR 결과 (필터링 적용 전)

        Returns:
            List[str]: 추출된 의미있는 텍스트 목록
        """
        from .filters import TextFilter

        # 필터링 적용
        filter_system = TextFilter(self.config)
        filtered_results = filter_system.apply_all_filters(ocr_results)

        # 텍스트만 추출하여 반환
        meaningful_texts = []
        for result in filtered_results:
            text = result['text'].strip()
            if text and is_meaningful_text(text):
                meaningful_texts.append(text)

        return meaningful_texts

    def categorize_texts(self, ocr_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """텍스트를 카테고리별로 분류

        Args:
            ocr_results: OCR 결과

        Returns:
            Dict[str, List]: 카테고리별 텍스트 분류
        """
        categories = {
            'numbered_items': [],  # 번호가 있는 항목들
            'general_text': [],    # 일반 텍스트
            'buttons': [],         # 버튼 텍스트
            'titles': [],          # 제목 텍스트
            'values': []           # 숫자/값 텍스트
        }

        for result in ocr_results:
            text = result['text'].strip()
            category = self._classify_text(text, result)
            categories[category].append(result)

        return categories

    def _classify_text(self, text: str, result: Dict[str, Any]) -> str:
        """개별 텍스트를 카테고리로 분류

        Args:
            text: 텍스트 내용
            result: OCR 결과 (bbox 정보 포함)

        Returns:
            str: 카테고리명
        """
        # 번호 패턴 확인 (1., 2), ①, ② 등)
        if re.match(r'^\d+[.)]\s*', text) or re.match(r'^[①-⑳]\s*', text):
            return 'numbered_items'

        # 버튼 패턴 (짧고 동사형)
        button_keywords = ['확인', '취소', '시작', '완료', '다음', '이전', '저장', '삭제']
        if any(keyword in text for keyword in button_keywords) and len(text) <= 10:
            return 'buttons'

        # 제목 패턴 (길고 설명적)
        if len(text) > 20 and not re.search(r'\d', text):
            return 'titles'

        # 값 패턴 (주로 숫자)
        if re.match(r'^\d+([,.]?\d+)*\s*[가-힣]*$', text):
            return 'values'

        # 기본값: 일반 텍스트
        return 'general_text'

    def prepare_for_user_selection(self, ocr_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """사용자 선택을 위한 텍스트 준비

        Args:
            ocr_results: 원본 OCR 결과

        Returns:
            Tuple: (원본 OCR 결과, 필터링된 의미있는 텍스트)
        """
        from .filters import TextFilter

        # 필터링 적용
        filter_system = TextFilter(self.config)
        meaningful_results = filter_system.apply_all_filters(ocr_results)

        # Y 좌표 순서로 정렬 (상단에서 하단으로)
        ocr_results_sorted = sorted(ocr_results, key=lambda x: x['bbox'][0][1])
        meaningful_results_sorted = sorted(meaningful_results, key=lambda x: x['bbox'][0][1])

        return ocr_results_sorted, meaningful_results_sorted

    def format_for_display(self, results: List[Dict[str, Any]], mode: str = 'numbered') -> List[str]:
        """결과를 사용자 표시용으로 포맷

        Args:
            results: OCR 결과 목록
            mode: 표시 모드 ('numbered', 'categorized', 'simple')

        Returns:
            List[str]: 포맷된 표시 문자열 목록
        """
        if mode == 'numbered':
            return self._format_numbered(results)
        elif mode == 'categorized':
            return self._format_categorized(results)
        elif mode == 'simple':
            return self._format_simple(results)
        else:
            return self._format_numbered(results)

    def _format_numbered(self, results: List[Dict[str, Any]]) -> List[str]:
        """번호 매기기 방식으로 포맷"""
        formatted = []
        for i, result in enumerate(results, 1):
            text = result['text']
            confidence = result.get('confidence', 0.0)

            # 텍스트가 너무 길면 자르기
            display_text = truncate_text(text, max_length=60)

            # 신뢰도 표시
            conf_str = f"{confidence*100:.0f}%" if confidence > 0 else ""

            formatted.append(f"{i:2d}. {display_text} {conf_str}")

        return formatted

    def _format_categorized(self, results: List[Dict[str, Any]]) -> List[str]:
        """카테고리별로 분류하여 포맷"""
        categories = self.categorize_texts(results)
        formatted = []

        category_names = {
            'numbered_items': '📝 번호 항목',
            'general_text': '💬 일반 텍스트',
            'buttons': '🔘 버튼',
            'titles': '📋 제목',
            'values': '🔢 값'
        }

        for category, items in categories.items():
            if items:
                formatted.append(f"\n{category_names.get(category, category)}:")
                for i, item in enumerate(items, 1):
                    text = truncate_text(item['text'], max_length=50)
                    formatted.append(f"  {i}. {text}")

        return formatted

    def _format_simple(self, results: List[Dict[str, Any]]) -> List[str]:
        """간단한 텍스트만 표시"""
        return [result['text'] for result in results]

    def analyze_text_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """텍스트 분포 분석

        Args:
            results: OCR 결과

        Returns:
            Dict[str, Any]: 분석 결과
        """
        if not results:
            return {'total_count': 0}

        categories = self.categorize_texts(results)

        # 길이별 분포
        lengths = [len(r['text']) for r in results]
        length_stats = {
            'min': min(lengths),
            'max': max(lengths),
            'avg': sum(lengths) / len(lengths)
        }

        # 언어별 분포 (간단한 휴리스틱)
        language_counts = {
            'korean': 0,
            'english': 0,
            'numbers': 0,
            'mixed': 0
        }

        for result in results:
            text = result['text']
            if re.search(r'[가-힣]', text):
                if re.search(r'[a-zA-Z0-9]', text):
                    language_counts['mixed'] += 1
                else:
                    language_counts['korean'] += 1
            elif re.search(r'[a-zA-Z]', text):
                language_counts['english'] += 1
            elif re.search(r'\d', text):
                language_counts['numbers'] += 1

        return {
            'total_count': len(results),
            'category_distribution': {cat: len(items) for cat, items in categories.items()},
            'length_statistics': length_stats,
            'language_distribution': language_counts,
            'confidence_stats': {
                'avg': sum(r.get('confidence', 0) for r in results) / len(results),
                'min': min(r.get('confidence', 0) for r in results),
                'max': max(r.get('confidence', 0) for r in results)
            } if results else {'avg': 0, 'min': 0, 'max': 0}
        }

    def extract_by_patterns(self, results: List[Dict[str, Any]], patterns: List[str]) -> List[Dict[str, Any]]:
        """특정 패턴에 맞는 텍스트만 추출

        Args:
            results: OCR 결과
            patterns: 정규표현식 패턴 목록

        Returns:
            List[Dict[str, Any]]: 패턴에 맞는 텍스트 결과
        """
        matched_results = []

        for result in results:
            text = result['text']
            for pattern in patterns:
                if re.search(pattern, text):
                    matched_results.append(result)
                    break  # 하나라도 매칭되면 포함

        return matched_results