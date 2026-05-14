"""Interactive user interface for text selection and modification"""

import re
from typing import List, Dict, Any, Optional, Tuple

from ..ocr.extractors import TextExtractor
from ..utils.helpers import parse_range, truncate_text
from .display import DisplayFormatter


class InteractiveUI:
    """대화형 사용자 인터페이스 클래스"""

    def __init__(self, config):
        self.config = config
        self.extractor = TextExtractor(config)
        self.formatter = DisplayFormatter(config)

    def select_texts(self, ocr_results: List[Dict[str, Any]]) -> List[str]:
        """사용자 텍스트 선택 인터페이스

        Args:
            ocr_results: OCR 결과 목록

        Returns:
            List[str]: 사용자가 선택한 텍스트 목록
        """
        if not ocr_results:
            print("📄 추출된 텍스트가 없습니다.")
            return []

        print(f"🔍 총 {len(ocr_results)}개의 텍스트가 추출되었습니다.")
        print()

        # OCR 결과 준비 (원본 + 필터링된 결과)
        original_results, meaningful_results = self.extractor.prepare_for_user_selection(ocr_results)

        # 1. 전체 OCR 결과 표시
        print("📋 전체 OCR 결과:")
        self._display_ocr_results(original_results, show_confidence=True)

        # 2. 필터링된 의미있는 텍스트 표시
        if meaningful_results:
            print(f"\n✨ 의미있는 텍스트 ({len(meaningful_results)}개):")
            self._display_meaningful_texts(meaningful_results)
        else:
            print("\n⚠️ 필터링 후 의미있는 텍스트가 없습니다.")

        # 3. 선택 모드 결정
        selection_mode = self._get_selection_mode()

        if selection_mode == 'skip':
            print("⏭️ 텍스트 선택을 건너뜁니다.")
            return []

        # 4. 텍스트 선택
        if selection_mode == 'ocr':
            selected_indices = self._get_user_selection(original_results, "OCR 원본")
            selected_results = [original_results[i-1] for i in selected_indices if 1 <= i <= len(original_results)]
        else:  # meaningful
            if not meaningful_results:
                print("❌ 선택할 의미있는 텍스트가 없습니다.")
                return []
            selected_indices = self._get_user_selection(meaningful_results, "의미있는 텍스트")
            selected_results = [meaningful_results[i-1] for i in selected_indices if 1 <= i <= len(meaningful_results)]

        if not selected_results:
            print("ℹ️ 선택된 텍스트가 없습니다.")
            return []

        # 5. 텍스트 수정 및 치환
        final_texts = self._modify_selected_texts(selected_results)

        # 6. 최종 확인
        if self._confirm_final_selection(final_texts):
            return final_texts
        else:
            print("🚫 번역이 취소되었습니다.")
            return []

    def _display_ocr_results(self, results: List[Dict[str, Any]], show_confidence: bool = True):
        """OCR 결과 표시"""
        for i, result in enumerate(results, 1):
            text = result['text']
            display_text = truncate_text(text, max_length=60)

            if show_confidence:
                confidence = result.get('confidence', 0.0)
                conf_str = f" ({confidence*100:.0f}%)"
            else:
                conf_str = ""

            print(f"  {i:2d}. {display_text}{conf_str}")

    def _display_meaningful_texts(self, results: List[Dict[str, Any]]):
        """의미있는 텍스트를 카테고리별로 표시"""
        categories = self.extractor.categorize_texts(results)

        category_icons = {
            'numbered_items': '📝',
            'general_text': '💬',
            'buttons': '🔘',
            'titles': '📋',
            'values': '🔢'
        }

        category_names = {
            'numbered_items': '번호 항목',
            'general_text': '일반 텍스트',
            'buttons': '버튼',
            'titles': '제목',
            'values': '값'
        }

        displayed_count = 0
        for category, items in categories.items():
            if items:
                icon = category_icons.get(category, '📄')
                name = category_names.get(category, category)
                print(f"\n  {icon} {name}:")

                for item in items:
                    displayed_count += 1
                    text = truncate_text(item['text'], max_length=50)
                    print(f"    {displayed_count:2d}. {text}")

    def _get_selection_mode(self) -> str:
        """선택 모드 결정"""
        while True:
            print("\n📋 텍스트 선택 모드:")
            print("  1. OCR 원본 텍스트에서 선택 (모든 인식된 텍스트 포함)")
            print("  2. 의미있는 텍스트에서 선택 (필터링된 텍스트만)")
            print("  3. 건너뛰기")

            try:
                choice = input("\n선택하세요 (1-3): ").strip()

                if choice == '1':
                    return 'ocr'
                elif choice == '2':
                    return 'meaningful'
                elif choice == '3':
                    return 'skip'
                else:
                    print("❌ 1, 2, 3 중에서 선택해주세요.")

            except KeyboardInterrupt:
                print("\n\n🚫 사용자가 중단했습니다.")
                return 'skip'
            except:
                print("❌ 입력 오류가 발생했습니다.")

    def _get_user_selection(self, results: List[Dict[str, Any]], source_name: str) -> List[int]:
        """사용자 텍스트 선택 입력"""
        while True:
            print(f"\n🎯 {source_name}에서 번역할 텍스트를 선택하세요:")
            print("  • 개별 선택: 1,3,5 (쉼표로 구분)")
            print("  • 범위 선택: 1-5 (하이픈으로 범위)")
            print("  • 전체 선택: all")
            print("  • 건너뛰기: skip")

            try:
                selection = input(f"\n선택 (1-{len(results)}): ").strip().lower()

                if selection == 'skip':
                    return []
                elif selection == 'all':
                    return list(range(1, len(results) + 1))
                elif selection:
                    # 범위/개별 선택 파싱
                    indices = parse_range(selection, len(results))
                    if indices:
                        print(f"✅ {len(indices)}개 텍스트가 선택되었습니다.")
                        return indices
                    else:
                        print(f"❌ 유효하지 않은 선택입니다. 1-{len(results)} 범위에서 선택해주세요.")
                else:
                    print("❌ 선택을 입력해주세요.")

            except KeyboardInterrupt:
                print("\n\n🚫 사용자가 중단했습니다.")
                return []
            except:
                print("❌ 입력 처리 중 오류가 발생했습니다.")

    def _modify_selected_texts(self, selected_results: List[Dict[str, Any]]) -> List[str]:
        """선택된 텍스트 수정 및 치환"""
        from ..utils.placeholder_detector import PlaceholderDetector

        print(f"\n✏️ 선택된 {len(selected_results)}개 텍스트를 수정할 수 있습니다:")
        print("  • OCR 오류 수정: '미선' → '미션'")
        print("  • 치환자 사용: '2 USDT' → '{{0}} USDT', '레벨 10' → '{{1}}'")
        print("  • 시스템 치환 제안: 자동으로 감지된 항목 선택")
        print("  • 그대로 유지: Enter만 누르기")
        print()

        # 치환 제안 시스템 초기화
        detector = PlaceholderDetector()
        texts = [r['text'] for r in selected_results]
        smart_suggestions = detector.get_smart_suggestions(texts)

        # 치환 제안 통계 표시
        stats = smart_suggestions['stats']
        if stats['texts_with_suggestions'] > 0:
            print(f"🤖 {stats['texts_with_suggestions']}개 텍스트에서 {stats['total_suggestions']}개 치환 항목을 발견했습니다!")
            print("   📊 발견된 패턴:", ', '.join(f"{k}({v}개)" for k, v in stats['pattern_frequency'].items()))
            print()

        final_texts = []

        for i, result in enumerate(selected_results, 1):
            original_text = result['text']
            suggestion_data = smart_suggestions['suggestions'][i-1]

            # 치환 제안이 있는 경우 먼저 표시
            if suggestion_data['has_suggestions']:
                print(f"📝 {i}/{len(selected_results)}: {original_text}")
                print("🤖 시스템 치환 제안:")

                for j, suggestion in enumerate(suggestion_data['suggestions'], 1):
                    matched = suggestion['matched_text']
                    replacement = suggestion['suggested_replacement']
                    description = suggestion['description']
                    print(f"   {j}. '{matched}' → '{replacement}' ({description})")

                # 자동 치환 옵션 제공
                try:
                    auto_choice = input("🎯 자동 치환 적용? (y/N/manual): ").strip().lower()

                    if auto_choice == 'y':
                        # 모든 제안 자동 적용
                        modified_text = detector.apply_suggestions(original_text, suggestion_data['suggestions'])
                        print(f"   🤖 자동 적용: '{original_text}' → '{modified_text}'")
                        final_texts.append(modified_text)
                        continue
                    elif auto_choice == 'manual':
                        # 수동 선택 모드
                        selected_nums = input("선택할 치환 번호 (예: 1,3 또는 Enter=없음): ").strip()
                        if selected_nums:
                            try:
                                indices = [int(x.strip()) - 1 for x in selected_nums.split(',')]
                                valid_indices = [i for i in indices if 0 <= i < len(suggestion_data['suggestions'])]
                                selected_suggestions = [suggestion_data['suggestions'][i] for i in valid_indices]

                                if selected_suggestions:
                                    modified_text = detector.apply_suggestions(original_text, selected_suggestions)
                                    print(f"   ✏️ 부분 적용: '{original_text}' → '{modified_text}'")
                                    final_texts.append(modified_text)
                                    continue
                            except ValueError:
                                print("   ⚠️ 잘못된 입력, 수동 모드로 전환")
                except KeyboardInterrupt:
                    print("\n\n🚫 수정이 중단되었습니다.")
                    final_texts.extend([r['text'] for r in selected_results[i-1:]])
                    break

            # 기본 수동 수정 모드
            print(f"📝 {i}/{len(selected_results)}: {original_text}")

            try:
                modified_text = input("수정 (Enter=그대로): ").strip()

                if modified_text:
                    final_texts.append(modified_text)
                    if modified_text != original_text:
                        print(f"   ✏️ '{original_text}' → '{modified_text}'")
                else:
                    final_texts.append(original_text)
                    print(f"   ✅ 그대로 사용")

            except KeyboardInterrupt:
                print("\n\n🚫 수정이 중단되었습니다.")
                # 지금까지 수정한 것들 + 나머지는 원본 사용
                final_texts.extend([r['text'] for r in selected_results[i-1:]])
                break
            except:
                print("   ⚠️ 입력 오류, 원본 텍스트 사용")
                final_texts.append(original_text)

        return final_texts

    def _confirm_final_selection(self, texts: List[str]) -> bool:
        """최종 선택 확인"""
        print(f"\n🎯 최종 번역 대상 ({len(texts)}개):")
        for i, text in enumerate(texts, 1):
            display_text = truncate_text(text, max_length=60)
            print(f"  {i:2d}. {display_text}")

        print(f"\n🚀 이 {len(texts)}개 텍스트를 번역하시겠습니까?")

        while True:
            try:
                confirm = input("진행하시겠습니까? (y/N): ").strip().lower()

                if confirm in ['y', 'yes', 'ㅇ']:
                    return True
                elif confirm in ['n', 'no', '', 'ㄴ']:
                    return False
                else:
                    print("y(예) 또는 n(아니오)로 답해주세요.")

            except KeyboardInterrupt:
                print("\n\n🚫 사용자가 중단했습니다.")
                return False
            except:
                print("❌ 입력 오류가 발생했습니다.")

    def show_processing_progress(self, step: str, current: int, total: int):
        """처리 진행상황 표시"""
        if total > 0:
            progress = (current / total) * 100
            print(f"🔄 {step}: {current}/{total} ({progress:.1f}%)")
        else:
            print(f"🔄 {step}: {current}")

    def show_results_summary(self, results: Dict[str, Any]):
        """결과 요약 표시"""
        print("\n✅ 처리 완료!")

        if results.get('status') == 'success':
            print(f"  📊 번역된 항목: {results.get('processed_count', 0)}개")
            print(f"  📄 출력 파일: {results.get('output_file', 'Unknown')}")
            print(f"  📁 소스: {results.get('source', 'Unknown')}")
        elif results.get('status') == 'no_selection':
            print(f"  ℹ️ {results.get('message', '선택된 텍스트가 없습니다')}")
        else:
            print(f"  ❌ 오류: {results.get('error', '알 수 없는 오류')}")