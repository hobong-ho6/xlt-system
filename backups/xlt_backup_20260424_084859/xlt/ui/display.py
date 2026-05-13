"""Display formatting utilities for XLT system"""

from typing import List, Dict, Any, Optional
from ..utils.helpers import truncate_text, format_confidence, format_duration


class DisplayFormatter:
    """XLT 시스템 표시 포맷팅 유틸리티"""

    def __init__(self, config):
        self.config = config

    def format_ocr_summary(self, ocr_results: List[Dict[str, Any]],
                          filter_stats: Optional[Dict[str, Any]] = None) -> str:
        """OCR 결과 요약 포맷

        Args:
            ocr_results: OCR 결과
            filter_stats: 필터링 통계 (옵션)

        Returns:
            str: 포맷된 요약
        """
        if not ocr_results:
            return "📄 추출된 텍스트가 없습니다."

        total_count = len(ocr_results)
        confidences = [r.get('confidence', 0) for r in ocr_results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        summary = [
            f"🔍 OCR 결과: {total_count}개 텍스트 추출",
            f"📊 평균 신뢰도: {format_confidence(avg_confidence)}"
        ]

        if filter_stats:
            removed_count = filter_stats.get('removed_count', 0)
            if removed_count > 0:
                summary.append(f"🗑️ 필터링으로 제거: {removed_count}개")

        return "\n".join(summary)

    def format_translation_summary(self, translations: List[Dict[str, str]],
                                 languages: List[str], processing_time: float) -> str:
        """번역 결과 요약 포맷

        Args:
            translations: 번역 결과
            languages: 번역된 언어 목록
            processing_time: 처리 시간

        Returns:
            str: 포맷된 요약
        """
        count = len(translations)
        lang_count = len(languages)

        summary = [
            f"🌐 번역 완료: {count}개 항목 × {lang_count}개 언어",
            f"⏱️ 처리 시간: {format_duration(processing_time)}"
        ]

        return "\n".join(summary)

    def format_error_message(self, error: Exception, context: str = "") -> str:
        """오류 메시지 포맷

        Args:
            error: 예외 객체
            context: 오류 발생 컨텍스트

        Returns:
            str: 포맷된 오류 메시지
        """
        error_type = type(error).__name__
        error_msg = str(error)

        if context:
            return f"❌ {context}: {error_type} - {error_msg}"
        else:
            return f"❌ 오류: {error_type} - {error_msg}"

    def format_progress_bar(self, current: int, total: int, width: int = 30) -> str:
        """진행률 바 포맷

        Args:
            current: 현재 값
            total: 전체 값
            width: 바 너비

        Returns:
            str: 포맷된 진행률 바
        """
        if total == 0:
            return "[" + " " * width + "] 0%"

        progress = min(current / total, 1.0)
        filled_width = int(progress * width)
        bar = "█" * filled_width + "░" * (width - filled_width)
        percentage = progress * 100

        return f"[{bar}] {percentage:.1f}%"

    def format_file_info(self, file_path: str, file_size: str, row_count: int) -> str:
        """파일 정보 포맷

        Args:
            file_path: 파일 경로
            file_size: 파일 크기
            row_count: 행 개수

        Returns:
            str: 포맷된 파일 정보
        """
        import os
        filename = os.path.basename(file_path)

        return f"📄 {filename} ({file_size}, {row_count}행)"

    def format_language_list(self, languages: List[str]) -> str:
        """언어 목록 포맷

        Args:
            languages: 언어 코드 목록

        Returns:
            str: 포맷된 언어 목록
        """
        from ..translation.languages import get_language_display_name

        display_names = [get_language_display_name(lang) for lang in languages]
        return ", ".join(display_names)

    def format_statistics_table(self, stats: Dict[str, Any], title: str = "통계") -> str:
        """통계 정보를 표 형태로 포맷

        Args:
            stats: 통계 데이터
            title: 표 제목

        Returns:
            str: 포맷된 통계 표
        """
        lines = [f"📊 {title}"]
        lines.append("=" * (len(title) + 3))

        for key, value in stats.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}: {sub_value}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    def format_text_list(self, texts: List[str], title: str = "텍스트 목록",
                        max_items: int = 10) -> str:
        """텍스트 목록 포맷

        Args:
            texts: 텍스트 목록
            title: 목록 제목
            max_items: 최대 표시 항목 수

        Returns:
            str: 포맷된 텍스트 목록
        """
        if not texts:
            return f"📝 {title}: (비어있음)"

        lines = [f"📝 {title} ({len(texts)}개):"]

        display_count = min(len(texts), max_items)
        for i, text in enumerate(texts[:display_count], 1):
            display_text = truncate_text(text, max_length=60)
            lines.append(f"  {i:2d}. {display_text}")

        if len(texts) > max_items:
            remaining = len(texts) - max_items
            lines.append(f"  ... (나머지 {remaining}개)")

        return "\n".join(lines)

    def format_confident_text_display(self, ocr_results: List[Dict[str, Any]]) -> str:
        """신뢰도가 포함된 텍스트 표시 포맷"""
        if not ocr_results:
            return "📄 표시할 텍스트가 없습니다."

        lines = []
        for i, result in enumerate(ocr_results, 1):
            text = result['text']
            confidence = result.get('confidence', 0.0)
            reader = result.get('reader', 'unknown')

            display_text = truncate_text(text, max_length=50)
            conf_str = format_confidence(confidence)

            lines.append(f"  {i:2d}. {display_text} ({conf_str}, {reader})")

        return "\n".join(lines)

    def format_selection_prompt(self, count: int, item_type: str = "항목") -> str:
        """선택 프롬프트 포맷

        Args:
            count: 선택 가능한 항목 수
            item_type: 항목 유형

        Returns:
            str: 포맷된 선택 프롬프트
        """
        prompt_lines = [
            f"🎯 번역할 {item_type}을 선택하세요:",
            f"  • 개별 선택: 1,3,5 (쉼표로 구분)",
            f"  • 범위 선택: 1-5 (하이픈으로 범위)",
            f"  • 전체 선택: all",
            f"  • 건너뛰기: skip",
            f"\n선택 (1-{count}): "
        ]

        return "\n".join(prompt_lines[:-1]) + prompt_lines[-1]

    def format_confirmation_prompt(self, items: List[str], action: str = "처리") -> str:
        """확인 프롬프트 포맷

        Args:
            items: 확인할 항목 목록
            action: 수행할 동작

        Returns:
            str: 포맷된 확인 프롬프트
        """
        count = len(items)
        preview = self.format_text_list(items, f"{action} 대상", max_items=5)

        return f"{preview}\n\n🚀 이 {count}개 항목을 {action}하시겠습니까? (y/N): "

    def show_welcome_message(self):
        """환영 메시지 표시"""
        print("🎯 XLT (eXtract, Localize, Translate) System v2.0")
        print("   피그마/이미지 → OCR → 번역 → Excel 자동화 시스템")
        print("=" * 50)

    def show_step_header(self, step_name: str, step_number: Optional[int] = None):
        """단계 헤더 표시"""
        if step_number:
            print(f"\n🔄 단계 {step_number}: {step_name}")
        else:
            print(f"\n🔄 {step_name}")
        print("-" * 30)