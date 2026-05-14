"""Text filtering system for OCR results"""

import re
from typing import List, Dict, Any, Set
from ..utils.helpers import clean_text, is_meaningful_text


class TextFilter:
    """OCR 결과 텍스트 필터링 클래스"""

    def __init__(self, config):
        self.config = config

        # UI 필터링 설정
        self.ui_zones = config.ui_filter_zones

        # 배지/라벨 패턴 (설정에서 가져오거나 기본값)
        self.badge_patterns = self.ui_zones.get('badge_patterns', [
            r'\d+[a-zA-Z]\s*\)\s*\d+[가-힣]*',  # "6f ) 3일" 패턴
            r'\d+[a-zA-Z]\s+\d+[!]*',  # "7a 39!" 패턴
        ])

        # 시간 패턴들
        self.time_patterns = [
            r'^\d{1,2}:\d{2}(:\d{2})?$',  # 12:34, 12:34:56
            r'^\d{1,2}시\s*\d{1,2}분$',  # 12시 34분
            r'^\d{1,2}월\s*\d{1,2}일$',  # 12월 34일
        ]

        # 노이즈 패턴들
        self.noise_patterns = [
            r'^[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>?/~`]+$',  # 특수문자만
            r'^[A-Z]{1,3}$',  # 단독 대문자 (UI 요소일 가능성)
            r'^x\d+$',  # x2, x10 등
            r'^\+\d+$',  # +10, +50 등
        ]

        # 게임 UI 특화 패턴들
        self.game_ui_patterns = [
            r'\d+/\d+',  # 10/20, 5/10 등 (진행률, HP)
            r'Lv?\.\?\d+',  # Lv.10, Level 5 등
            r'LV\d+',  # LV10, LV20 등
            r'^\d+%$',  # 100%, 50% 등
            r'^HP:\d+$',  # HP:100 등
            r'^MP:\d+$',  # MP:50 등
        ]

        # 한국어 맞춤법 교정 사전 (설정에서 가져오기)
        self.ocr_corrections = config.ocr_corrections

    def apply_all_filters(self, ocr_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """모든 필터를 순차적으로 적용

        Args:
            ocr_results: 원본 OCR 결과

        Returns:
            List[Dict[str, Any]]: 필터링된 결과
        """
        # 1. UI 영역 필터링
        filtered = self.filter_ui_zones(ocr_results)

        # 2. 배지/라벨 패턴 필터링
        filtered = self.filter_badge_patterns(filtered)

        # 3. 시간 패턴 필터링
        filtered = self.filter_time_patterns(filtered)

        # 4. 노이즈 패턴 필터링
        filtered = self.filter_noise_patterns(filtered)

        # 5. 게임 UI 패턴 필터링
        filtered = self.filter_game_ui_patterns(filtered)

        # 6. 텍스트 정리 및 교정
        filtered = self.clean_and_correct_texts(filtered)

        # 7. 의미있는 텍스트 여부 확인
        filtered = self.filter_meaningful_texts(filtered)

        # 8. 중복 제거
        filtered = self.remove_duplicates(filtered)

        return filtered

    def filter_ui_zones(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """UI 영역 (상단 GNB, 하단 탭) 필터링"""
        if not results:
            return results

        # 이미지 높이 추정 (가장 아래 텍스트의 Y 좌표 기준)
        max_y = max(r['bbox'][2][1] for r in results)  # bottom-right Y 좌표

        top_threshold = self.ui_zones.get('top_gnb_threshold', 100)
        bottom_threshold_ratio = self.ui_zones.get('bottom_tab_threshold', 0.8)
        bottom_threshold = max_y * bottom_threshold_ratio

        filtered = []
        for result in results:
            bbox = result['bbox']
            top_y = bbox[0][1]  # top-left Y 좌표
            bottom_y = bbox[2][1]  # bottom-right Y 좌표

            # 상단 GNB 영역 제외
            if top_y < top_threshold:
                continue

            # 하단 탭 영역 제외
            if bottom_y > bottom_threshold:
                continue

            filtered.append(result)

        return filtered

    def filter_badge_patterns(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """배지/라벨 패턴 필터링"""
        filtered = []

        for result in results:
            text = result['text'].strip()
            is_badge = False

            for pattern in self.badge_patterns:
                if re.match(pattern, text):
                    is_badge = True
                    break

            if not is_badge:
                filtered.append(result)

        return filtered

    def filter_time_patterns(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """시간 관련 패턴 필터링"""
        filtered = []

        for result in results:
            text = result['text'].strip()
            is_time = False

            for pattern in self.time_patterns:
                if re.match(pattern, text):
                    is_time = True
                    break

            if not is_time:
                filtered.append(result)

        return filtered

    def filter_noise_patterns(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """노이즈 패턴 필터링"""
        filtered = []

        for result in results:
            text = result['text'].strip()
            is_noise = False

            for pattern in self.noise_patterns:
                if re.match(pattern, text):
                    is_noise = True
                    break

            if not is_noise:
                filtered.append(result)

        return filtered

    def filter_game_ui_patterns(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """게임 UI 특화 패턴 필터링"""
        filtered = []

        for result in results:
            text = result['text'].strip()
            is_game_ui = False

            for pattern in self.game_ui_patterns:
                if re.match(pattern, text):
                    is_game_ui = True
                    break

            if not is_game_ui:
                filtered.append(result)

        return filtered

    def clean_and_correct_texts(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """텍스트 정리 및 한국어 맞춤법 교정"""
        corrected = []

        for result in results:
            original_text = result['text']
            cleaned_text = clean_text(original_text)

            # 한국어 맞춤법 교정
            corrected_text = cleaned_text
            for wrong, correct in self.ocr_corrections.items():
                corrected_text = corrected_text.replace(wrong, correct)

            # 텍스트가 변경된 경우 업데이트
            if corrected_text != original_text:
                result = result.copy()  # 원본 수정 방지
                result['text'] = corrected_text
                result['original_text'] = original_text  # 원본 보존

            corrected.append(result)

        return corrected

    def filter_meaningful_texts(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """의미있는 텍스트만 필터링"""
        return [r for r in results if is_meaningful_text(r['text'])]

    def remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 텍스트 제거 (대소문자 구분 없이)"""
        seen_texts = set()
        unique_results = []

        for result in results:
            text_lower = result['text'].lower().strip()

            if text_lower not in seen_texts:
                seen_texts.add(text_lower)
                unique_results.append(result)

        return unique_results

    def get_filter_statistics(self, original_results: List[Dict[str, Any]],
                             filtered_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """필터링 통계 정보 반환"""
        original_count = len(original_results)
        filtered_count = len(filtered_results)
        removed_count = original_count - filtered_count

        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'removed_count': removed_count,
            'filter_ratio': removed_count / original_count if original_count > 0 else 0.0
        }

    def debug_filtered_texts(self, original_results: List[Dict[str, Any]],
                            filtered_results: List[Dict[str, Any]]) -> List[str]:
        """필터링된 텍스트 목록 반환 (디버깅용)"""
        original_texts = {r['text'] for r in original_results}
        filtered_texts = {r['text'] for r in filtered_results}
        removed_texts = original_texts - filtered_texts

        return sorted(list(removed_texts))