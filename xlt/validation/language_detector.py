"""
유니코드 범위 기반 정확한 언어 감지 시스템

다른 Claude에서 작성한 검증 로직을 XLT 시스템에 통합
"""

import re
from typing import Dict, List, Set


class LanguageDetector:
    """유니코드 범위 기반 언어 감지기"""

    def __init__(self):
        # 언어별 식별 유니코드 범위 (다른 Claude 시스템 동일)
        self.RE_KOREAN = re.compile(r"[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]")
        self.RE_KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30fa\u30fc-\u30ff]")
        self.RE_THAI = re.compile(r"[\u0e00-\u0e7f]")
        self.RE_CJK = re.compile(r"[\u4e00-\u9fff]")
        self.RE_LATIN = re.compile(r"[a-zA-Z]")

        # Placeholder 패턴들 (7가지)
        self.PLACEHOLDER_PATTERNS = [
            re.compile(r"\{\{[^}]+\}\}"),  # {{name}}
            re.compile(r"\{[^{}]+\}"),    # {0}, {name}
            re.compile(r"<[^>]+>"),       # <br/>, <span>
            re.compile(r"\\n|\\t"),       # \n, \t
            re.compile(r"%[sd]"),         # %s, %d
            re.compile(r"\$\{[^}]+\}"),   # ${var}
        ]

        # 정상 케이스 (예외 처리)
        self.LANGUAGE_LABELS = {
            "한국어", "日本語", "中文(繁體)", "中文（繁體）", "繁體中文",
            "ภาษาไทย", "English", "한 국 어"
        }

        self.CURRENCY_PATTERN = re.compile(r"[A-Z]{2,5}\s*\([^)]+\)")  # JPY (¥)

    def has_korean(self, text: str) -> bool:
        """한국어 문자 포함 여부"""
        return bool(self.RE_KOREAN.search(text))

    def has_kana(self, text: str) -> bool:
        """일본어 가나 문자 포함 여부"""
        return bool(self.RE_KANA.search(text))

    def has_thai(self, text: str) -> bool:
        """태국어 문자 포함 여부"""
        return bool(self.RE_THAI.search(text))

    def has_cjk(self, text: str) -> bool:
        """한자 (중국어/일본어 공용) 포함 여부"""
        return bool(self.RE_CJK.search(text))

    def has_latin(self, text: str) -> bool:
        """라틴 알파벳 포함 여부"""
        return bool(self.RE_LATIN.search(text))

    def extract_placeholders(self, text: str) -> List[str]:
        """텍스트에서 모든 placeholder 추출"""
        if not isinstance(text, str):
            return []

        result = []
        remaining = text

        # 우선순위가 높은 {{...}}부터 추출
        for pattern in self.PLACEHOLDER_PATTERNS:
            matches = pattern.findall(remaining)
            result.extend(matches)
            # 매칭된 부분을 빈 칸으로 치환해서 중복 매칭 방지
            remaining = pattern.sub(" ", remaining)

        return sorted(result)

    def is_symbol_only(self, text: str) -> bool:
        """텍스트가 placeholder/숫자/순수 기호만으로 구성되어 있는지 확인"""
        if not text:
            return True

        # placeholder 제거
        cleaned = text
        for pattern in self.PLACEHOLDER_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        cleaned = cleaned.strip()

        if not cleaned:
            return True

        # 영문 단어(2자 이상)가 있으면 symbol_only가 아님 (실제 텍스트)
        if re.search(r"[a-zA-Z]{2,}", cleaned):
            return False

        # 어떤 언어 문자도 없으면 (숫자/단일 기호/통화 등) symbol_only
        if not (self.has_korean(cleaned) or self.has_kana(cleaned) or
                self.has_thai(cleaned) or self.has_cjk(cleaned)):
            return True

        return False

    def is_language_label(self, text: str) -> bool:
        """언어 선택 UI 라벨인지 확인 (정상 케이스)"""
        return text.strip() in self.LANGUAGE_LABELS

    def is_currency_label(self, text: str) -> bool:
        """통화 코드/기호 라벨인지 확인 (정상 케이스)"""
        return bool(self.CURRENCY_PATTERN.fullmatch(text.strip()))

    def detect_language_issues(self, text: str, expected_lang: str) -> List[str]:
        """특정 언어 열에서 다른 언어 문자 혼입 감지"""
        if not isinstance(text, str) or not text.strip():
            return []

        # 정상 케이스 제외
        if (self.is_symbol_only(text) or
            self.is_language_label(text) or
            self.is_currency_label(text)):
            return []

        problems = []

        if expected_lang == "en_US":
            if self.has_korean(text):
                problems.append("한국어")
            if self.has_kana(text):
                problems.append("일본어(가나)")
            if self.has_thai(text):
                problems.append("태국어")
            if self.has_cjk(text):
                problems.append("한자/중국어")

        elif expected_lang == "ko_KR":
            if self.has_kana(text):
                problems.append("일본어(가나)")
            if self.has_thai(text):
                problems.append("태국어")
            if self.has_cjk(text) and not self.has_korean(text) and not self.has_latin(text):
                problems.append("한자만 있음")

        elif expected_lang == "ja_JP":
            if self.has_korean(text):
                problems.append("한국어")
            if self.has_thai(text):
                problems.append("태국어")

        elif expected_lang == "zh_TW":
            if self.has_korean(text):
                problems.append("한국어")
            if self.has_kana(text):
                problems.append("일본어(가나)")
            if self.has_thai(text):
                problems.append("태국어")

        elif expected_lang == "th_TH":
            if self.has_korean(text):
                problems.append("한국어")
            if self.has_kana(text):
                problems.append("일본어(가나)")
            if self.has_cjk(text):
                problems.append("한자(중국어 의심)")
            # 길이가 있고 태국 문자가 전혀 없으면 의심
            if (not self.has_thai(text) and len(text) > 5 and
                (self.has_korean(text) or self.has_kana(text) or self.has_cjk(text))):
                problems.append("태국 문자 없음")

        return problems

    def check_slash_n_typo(self, text: str) -> bool:
        """/n 오타 감지 (\\n 대신 /n 사용)"""
        if not isinstance(text, str):
            return False

        # /n 패턴 검색 (URL이나 경로의 일부는 제외)
        return bool(re.search(r"(?<![a-zA-Z0-9:])/n(?![a-zA-Z0-9])", text))

    def check_placeholder_consistency(self, ko_text: str, target_text: str) -> Dict:
        """Placeholder 일관성 검증"""
        ko_placeholders = self.extract_placeholders(ko_text)
        target_placeholders = self.extract_placeholders(target_text)

        return {
            'is_consistent': ko_placeholders == target_placeholders,
            'ko_placeholders': ko_placeholders,
            'target_placeholders': target_placeholders,
            'missing': list(set(ko_placeholders) - set(target_placeholders)),
            'extra': list(set(target_placeholders) - set(ko_placeholders))
        }

    def detect_translation_missing(self, ko_text: str, target_text: str,
                                   target_lang: str) -> Dict:
        """번역 누락 감지"""
        if not isinstance(ko_text, str) or not isinstance(target_text, str):
            return {'is_missing': False}

        ko_stripped = ko_text.strip()
        target_stripped = target_text.strip()

        # 케이스 1: 한국어 원문이 다른 언어 열에 그대로
        if (self.has_korean(ko_stripped) and
            ko_stripped == target_stripped and
            not self.is_language_label(ko_stripped) and
            not self.is_symbol_only(ko_stripped)):
            return {
                'is_missing': True,
                'type': 'same_as_korean',
                'description': f'{target_lang} 열에 한국어 원문이 그대로 들어감',
                'severity': 'critical'
            }

        return {'is_missing': False}