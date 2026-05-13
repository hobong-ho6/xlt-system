"""Automatic placeholder detection for XLT system"""

import re
from typing import List, Dict, Any, Tuple


class PlaceholderDetector:
    """텍스트에서 치환 가능한 항목을 자동으로 감지하는 클래스"""

    def __init__(self):
        # 치환 후보 패턴들 (우선순위 순서: 위에서 아래로) - 성능 최적화
        self.patterns = [
            # 금액 패턴 (숫자만 치환, 통화 단위는 lookahead로 확인)
            {
                'pattern': r'\d+(?:[,.]?\d+)*(?=\s*(?:USDT|USD|ETH|BTC|만원|원|달러|엔))',
                'placeholder': 'amount',
                'description': '금액',
                'examples': ['100원', '50 USDT', '1,000달러', '100만원']
            },
            # 레벨/순위 패턴
            {
                'pattern': r'(?:레벨|Level|Lv\.?|LV)\s*\d+',
                'placeholder': 'level',
                'description': '레벨',
                'examples': ['레벨 10', 'Level 5', 'Lv.3']
            },
            # 시간/날짜 패턴
            {
                'pattern': r'\d+\s*(?:일|시간|분|초|년|월|주)',
                'placeholder': 'duration',
                'description': '기간',
                'examples': ['7일', '24시간', '30분']
            },
            # 횟수 패턴 (번, 회)
            {
                'pattern': r'\d+\s*(?:번|회)',
                'placeholder': 'times',
                'description': '횟수',
                'examples': ['3번', '5회', '10번']
            },
            # 개수 패턴 (개, 명 등)
            {
                'pattern': r'\d+\s*(?:개|명|x|X)',
                'placeholder': 'count',
                'description': '개수',
                'examples': ['5개', '3명', '2x']
            },
            # 퍼센트 패턴
            {
                'pattern': r'\d+(?:\.\d+)?%',
                'placeholder': 'percent',
                'description': '퍼센트',
                'examples': ['50%', '12.5%']
            },
            # 순수 숫자 패턴 (가장 마지막, 가장 일반적)
            {
                'pattern': r'\b\d+(?:[,.]?\d+)*\b',
                'placeholder': 'number',
                'description': '숫자',
                'examples': ['100', '1,000', '3.14']
            }
        ]

        # 성능 최적화: 정규표현식 미리 컴파일
        self._compiled_patterns = []
        for pattern_info in self.patterns:
            compiled_pattern = re.compile(pattern_info['pattern'], re.IGNORECASE)
            self._compiled_patterns.append({
                'compiled': compiled_pattern,
                'placeholder': pattern_info['placeholder'],
                'description': pattern_info['description']
            })

    def detect_placeholders(self, texts: List[str]) -> List[Dict[str, Any]]:
        """텍스트 목록에서 치환 가능한 항목들을 감지 (성능 최적화)

        Args:
            texts: 분석할 텍스트 목록

        Returns:
            List[Dict]: 각 텍스트별 치환 제안 정보
        """
        # 빠른 반환: 빈 목록
        if not texts:
            return []

        results = []

        # 성능 최적화: 배치 처리
        for text in texts:
            # 빈 텍스트 빠른 처리
            if not text or not text.strip():
                results.append({
                    'original_text': text,
                    'suggestions': [],
                    'has_suggestions': False
                })
                continue

            suggestions = self._analyze_text(text)
            results.append({
                'original_text': text,
                'suggestions': suggestions,
                'has_suggestions': len(suggestions) > 0
            })

        return results

    def _analyze_text(self, text: str) -> List[Dict[str, Any]]:
        """단일 텍스트 분석 (성능 최적화)"""
        # 빠른 반환: 빈 텍스트나 너무 짧은 텍스트
        if not text or len(text.strip()) < 2:
            return []

        all_matches = []

        # 성능 최적화: 미리 컴파일된 패턴 사용
        for pattern_info in self._compiled_patterns:
            matches = pattern_info['compiled'].finditer(text)

            for match in matches:
                matched_text = match.group()
                start_pos = match.start()
                end_pos = match.end()

                match_info = {
                    'matched_text': matched_text,
                    'pattern_type': pattern_info['placeholder'],
                    'description': pattern_info['description'],
                    'start_pos': start_pos,
                    'end_pos': end_pos
                }

                all_matches.append(match_info)

        # 빠른 반환: 매치가 없으면 바로 반환
        if not all_matches:
            return []

        # 위치 순서대로 정렬 (앞에서부터 {{0}}, {{1}}, {{2}} 순서)
        all_matches.sort(key=lambda x: x['start_pos'])

        # 중복 제거 (동일한 위치에 여러 패턴이 매치되는 경우 가장 구체적인 것 선택)
        filtered_matches = self._remove_overlapping_matches(all_matches)

        # 숫자 인덱스 기반 치환자 생성
        suggestions = []
        for i, match in enumerate(filtered_matches):
            suggestion = {
                'matched_text': match['matched_text'],
                'placeholder_name': f"{i}",  # 숫자 인덱스
                'description': match['description'],
                'start_pos': match['start_pos'],
                'end_pos': match['end_pos'],
                'suggested_replacement': f"{{{{{i}}}}}"  # {{0}}, {{1}}, {{2}} 형태
            }
            suggestions.append(suggestion)

        return suggestions

    def _remove_overlapping_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """겹치는 매치 제거 (더 구체적이고 긴 매치 우선)"""
        if not matches:
            return []

        # 우선순위: 금액 > 레벨 > 기간 > 횟수 > 개수 > 퍼센트 > 숫자
        priority_order = ['amount', 'level', 'duration', 'times', 'count', 'percent', 'number']

        def get_priority(pattern_type: str) -> int:
            try:
                return priority_order.index(pattern_type)
            except ValueError:
                return len(priority_order)

        filtered = []
        for current_match in matches:
            current_start = current_match['start_pos']
            current_end = current_match['end_pos']

            # 기존 매치들과 겹치는지 확인
            is_overlapping = False
            for existing_match in filtered:
                existing_start = existing_match['start_pos']
                existing_end = existing_match['end_pos']

                # 겹침 여부 확인
                if not (current_end <= existing_start or current_start >= existing_end):
                    is_overlapping = True

                    # 더 구체적인 패턴을 선택 (우선순위가 낮을수록 구체적)
                    current_priority = get_priority(current_match['pattern_type'])
                    existing_priority = get_priority(existing_match['pattern_type'])

                    if current_priority < existing_priority:
                        # 현재 매치가 더 구체적이면 기존 것 제거하고 현재 것 추가
                        filtered.remove(existing_match)
                        is_overlapping = False
                    break

            if not is_overlapping:
                filtered.append(current_match)

        # 다시 위치 순서로 정렬
        filtered.sort(key=lambda x: x['start_pos'])
        return filtered

    def apply_suggestions(self, text: str, selected_suggestions: List[Dict[str, Any]]) -> str:
        """선택된 제안사항을 텍스트에 적용

        Args:
            text: 원본 텍스트
            selected_suggestions: 사용자가 선택한 제안사항들

        Returns:
            str: 치환자가 적용된 텍스트
        """
        # 위치 순서대로 정렬 (뒤에서부터 치환해야 위치가 꼬이지 않음)
        sorted_suggestions = sorted(selected_suggestions, key=lambda x: x['start_pos'], reverse=True)

        result_text = text
        for suggestion in sorted_suggestions:
            start = suggestion['start_pos']
            end = suggestion['end_pos']
            replacement = suggestion['suggested_replacement']

            result_text = result_text[:start] + replacement + result_text[end:]

        return result_text

    def format_suggestion_display(self, text: str, suggestions: List[Dict[str, Any]]) -> str:
        """제안사항을 사용자 친화적으로 표시

        Args:
            text: 원본 텍스트
            suggestions: 제안사항 목록

        Returns:
            str: 포맷된 표시 문자열
        """
        if not suggestions:
            return f"   📝 {text} (치환 제안 없음)"

        lines = [f"   📝 {text}"]

        for i, suggestion in enumerate(suggestions, 1):
            matched = suggestion['matched_text']
            replacement = suggestion['suggested_replacement']
            description = suggestion['description']

            lines.append(f"      {i}. '{matched}' → '{replacement}' ({description})")

        return '\n'.join(lines)

    def get_smart_suggestions(self, texts: List[str]) -> Dict[str, Any]:
        """스마트한 치환 제안 생성

        Args:
            texts: 텍스트 목록

        Returns:
            Dict: 통합 분석 결과
        """
        all_suggestions = self.detect_placeholders(texts)

        # 통계 정보
        total_texts = len(texts)
        texts_with_suggestions = sum(1 for result in all_suggestions if result['has_suggestions'])
        total_suggestions = sum(len(result['suggestions']) for result in all_suggestions)

        # 패턴별 빈도 분석
        pattern_frequency = {}
        for result in all_suggestions:
            for suggestion in result['suggestions']:
                pattern_name = suggestion['placeholder_name']
                pattern_frequency[pattern_name] = pattern_frequency.get(pattern_name, 0) + 1

        return {
            'suggestions': all_suggestions,
            'stats': {
                'total_texts': total_texts,
                'texts_with_suggestions': texts_with_suggestions,
                'total_suggestions': total_suggestions,
                'pattern_frequency': pattern_frequency
            }
        }

    def create_interactive_replacement(self, text: str) -> str:
        """대화형 치환자 적용

        Args:
            text: 원본 텍스트

        Returns:
            str: 사용자 선택에 따라 치환자가 적용된 텍스트
        """
        suggestions = self._analyze_text(text)

        if not suggestions:
            return text

        print(f"\n🔍 '{text}'에서 치환 가능한 항목을 발견했습니다:")

        selected_suggestions = []
        for i, suggestion in enumerate(suggestions, 1):
            matched = suggestion['matched_text']
            replacement = suggestion['suggested_replacement']
            description = suggestion['description']

            print(f"   {i}. '{matched}' → '{replacement}' ({description})")

        try:
            user_input = input("치환할 항목 번호 (예: 1,3 또는 Enter=건너뛰기): ").strip()

            if user_input:
                # 사용자 선택 파싱
                selected_indices = []
                for part in user_input.split(','):
                    try:
                        idx = int(part.strip()) - 1
                        if 0 <= idx < len(suggestions):
                            selected_indices.append(idx)
                    except ValueError:
                        continue

                selected_suggestions = [suggestions[i] for i in selected_indices]

        except KeyboardInterrupt:
            print("\n치환 건너뛰기...")
            return text

        if selected_suggestions:
            result = self.apply_suggestions(text, selected_suggestions)
            print(f"   ✏️ 결과: '{result}'")
            return result
        else:
            return text