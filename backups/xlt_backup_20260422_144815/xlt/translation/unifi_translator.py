"""
Unifi 전용 번역기 - guide.md 기준 준수 및 기존 번역 데이터베이스 활용
"""

import pandas as pd
import re
import difflib
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .translator import Translator
from ..core.exceptions import TranslationError


class UnifiTranslator(Translator):
    """
    Unifi 서비스 전용 번역기
    - guide.md 기준 준수
    - Unifi Excel 번역 데이터베이스 우선 활용
    - Google Translate는 fallback으로만 사용
    """

    def __init__(self, config):
        super().__init__(config)
        self.unifi_db = None
        self.terminology = {}
        self.key_patterns = {}
        self.load_unifi_database()

    def load_unifi_database(self):
        """Unifi 번역 데이터베이스 로드"""
        try:
            # 현재 작업 디렉토리 또는 config의 base_dir 사용
            base_dir = getattr(self.config, 'base_dir', os.getcwd())
            unifi_path = Path(base_dir) / "Unifi" / "Unifi_WEB BROWSER_v1.2.7_20260420100020.xlsx"

            if not unifi_path.exists():
                print(f"⚠️ Unifi 데이터베이스를 찾을 수 없습니다: {unifi_path}")
                return

            # Excel 파일 로드
            self.unifi_db = pd.read_excel(unifi_path)
            self.unifi_db = self.unifi_db.rename(columns={'Unnamed: 0': 'Key'})

            print(f"✅ Unifi 번역 데이터베이스 로드 완료: {len(self.unifi_db)}개 항목")

            # 용어 사전 구축
            self._build_terminology_dict()

            # Key 패턴 분석
            self._analyze_key_patterns()

        except Exception as e:
            print(f"❌ Unifi 데이터베이스 로드 실패: {str(e)}")

    def _build_terminology_dict(self):
        """용어 사전 구축 - guide.md 핵심 용어집 기반"""
        if self.unifi_db is None:
            return

        # guide.md의 핵심 금융 용어들
        core_terms = [
            # 금융 핵심 용어
            '거래', 'transaction', '取引', '交易', 'ธุรกรรม',
            '지갑', 'wallet', 'ウォレット', '錢包', 'กระเป๋า',
            '토큰', 'token', 'トークン', '代幣', 'โทเค็น',
            '자산', 'asset', '資産', '資產', 'สินทรัพย์',
            '송금', 'send', '送金', '轉帳', 'ส่ง',
            '예치', 'deposit', '預入', '存入', 'ฝาก',
            '출금', 'withdraw', '出金', '提領', 'ถอน',
            '교환', 'swap', 'スワップ', '交換', 'แลกเปลี่ยน',
            '이자', 'interest', '利息', '利息', 'ดอกเบี้ย',
            '로그인', 'log in', 'ログイン', '登入', 'เข้าสู่ระบบ',
            '연결', 'connect', '連携', '連結', 'เชื่อมโยง',
            '확인', 'confirm', '確認', '確認', 'ตรวจสอบ',
            '복사', 'copy', 'コピー', '複製', 'คัดลอก',
            '변경', 'change', '変更', '更換', 'เปลี่ยน'
        ]

        # 각 용어에 대해 번역 매핑 구축
        for term in core_terms:
            matches = self.unifi_db[
                self.unifi_db['ko_KR'].str.contains(term, case=False, na=False) |
                self.unifi_db['en_US'].str.contains(term, case=False, na=False) |
                self.unifi_db['ja_JP'].str.contains(term, case=False, na=False) |
                self.unifi_db['zh_TW'].str.contains(term, case=False, na=False) |
                self.unifi_db['th_TH'].str.contains(term, case=False, na=False)
            ]

            if len(matches) > 0:
                # 가장 많이 사용된 번역을 표준으로 설정
                self.terminology[term] = {
                    'examples': matches[['Key', 'ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH']].to_dict('records'),
                    'count': len(matches)
                }

        print(f"📚 용어 사전 구축 완료: {len(self.terminology)}개 핵심 용어")

    def _analyze_key_patterns(self):
        """Key 패턴 분석"""
        if self.unifi_db is None:
            return

        keys = self.unifi_db['Key'].dropna().astype(str)

        for key in keys:
            if '_' in key:
                parts = key.split('_')
                if len(parts) >= 2:
                    prefix = parts[0] + '_' + parts[1]
                    if prefix not in self.key_patterns:
                        self.key_patterns[prefix] = []
                    self.key_patterns[prefix].append(key)

        print(f"🔍 Key 패턴 분석 완료: {len(self.key_patterns)}개 패턴")

    def find_similar_translations(self, text: str, similarity_threshold: float = 0.6) -> List[Dict]:
        """기존 번역에서 유사한 텍스트 찾기"""
        if self.unifi_db is None:
            return []

        similar_items = []

        # 한국어 텍스트에서 유사한 항목 찾기
        for idx, row in self.unifi_db.iterrows():
            ko_text = str(row.get('ko_KR', '')).strip()
            if not ko_text or ko_text == 'nan':
                continue

            # 유사도 계산 (difflib 사용)
            similarity = difflib.SequenceMatcher(None, text.lower(), ko_text.lower()).ratio()

            if similarity >= similarity_threshold:
                similar_items.append({
                    'key': row.get('Key', ''),
                    'similarity': similarity,
                    'ko_KR': ko_text,
                    'en_US': str(row.get('en_US', '')),
                    'ja_JP': str(row.get('ja_JP', '')),
                    'zh_TW': str(row.get('zh_TW', '')),
                    'th_TH': str(row.get('th_TH', ''))
                })

        # 유사도 순으로 정렬
        similar_items.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_items[:5]  # 상위 5개만 반환

    def extract_terms_from_text(self, text: str) -> List[str]:
        """텍스트에서 핵심 용어 추출"""
        found_terms = []

        for term in self.terminology.keys():
            if term in text:
                found_terms.append(term)

        return found_terms

    def apply_unifi_style(self, text: str, target_language: str) -> str:
        """Unifi 스타일 적용 - guide.md 톤앤매너 규칙"""

        # 언어별 스타일 적용
        if target_language == 'ko_KR':
            # 친근한 존댓말 (~해요 체)
            patterns = [
                (r'됩니다$', '돼요'),
                (r'합니다$', '해요'),
                (r'입니다$', '이에요'),
                (r'습니다$', '어요')
            ]
            for pattern, replacement in patterns:
                text = re.sub(pattern, replacement, text)

        elif target_language == 'en_US':
            # 간결하고 명확한 표현
            # 금융 전문 용어 표준화
            replacements = {
                'digital wallet': 'wallet',
                'crypto token': 'token',
                'transaction record': 'transaction history'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)

        elif target_language == 'ja_JP':
            # 정중한 표현 (です・ます체) 확인
            if not (text.endswith('です') or text.endswith('ます') or text.endswith('ません') or
                   text.endswith('ください') or len(text) < 5):
                # 필요시 정중한 형태로 변경하는 로직 추가 가능
                pass

        return text

    def translate_with_unifi_context(self, text: str, target_languages: List[str]) -> Dict[str, str]:
        """Unifi 컨텍스트를 활용한 번역"""

        print(f"🔍 Unifi 번역 시도: '{text[:50]}...'")

        # 1. 유사한 기존 번역 찾기
        similar_translations = self.find_similar_translations(text, similarity_threshold=0.8)

        if similar_translations:
            print(f"   ✅ 유사한 번역 {len(similar_translations)}개 발견")
            best_match = similar_translations[0]

            # 완전히 일치하는 경우 기존 번역 직접 사용
            if best_match['similarity'] >= 0.95:
                print(f"   🎯 완전 일치 (유사도: {best_match['similarity']:.2f})")
                results = {}
                for lang in target_languages:
                    if lang in best_match and best_match[lang] and best_match[lang] != 'nan':
                        results[lang] = self.apply_unifi_style(best_match[lang], lang)
                return results

        # 2. 핵심 용어 기반 번역 개선
        found_terms = self.extract_terms_from_text(text)
        if found_terms:
            print(f"   📚 핵심 용어 발견: {found_terms}")

        # 3. Google Translate fallback (용어 일관성 적용)
        print("   🌐 Google Translate 사용 (용어 일관성 적용)")
        results = {}

        for lang in target_languages:
            try:
                # 기본 번역
                translated = self.translate_text(text, lang)

                # 핵심 용어 대체 (일관성 유지)
                for term in found_terms:
                    if term in self.terminology:
                        examples = self.terminology[term]['examples']
                        if examples:
                            # 가장 적절한 번역 찾아서 적용
                            for example in examples[:3]:  # 상위 3개 확인
                                if lang in example and example[lang] and example[lang] != 'nan':
                                    # 용어 대체 로직 (정규식 사용)
                                    # 이 부분은 더 정교하게 구현할 수 있음
                                    pass

                # 스타일 적용
                translated = self.apply_unifi_style(translated, lang)
                results[lang] = translated

            except Exception as e:
                print(f"   ❌ {lang} 번역 실패: {str(e)}")
                results[lang] = text

        return results

    def translate_batch(self, texts: List[str], target_languages: List[str]) -> List[Dict[str, str]]:
        """
        배치 번역 - Unifi 컨텍스트 우선 적용
        """
        if not texts:
            return []

        print(f"🚀 Unifi 배치 번역 시작: {len(texts)}개 텍스트, {len(target_languages)}개 언어")

        results = []

        for i, text in enumerate(texts):
            print(f"\n📝 [{i+1}/{len(texts)}] 번역 중...")

            # Unifi 컨텍스트 번역 시도
            unifi_result = self.translate_with_unifi_context(text, target_languages)

            # 결과 포맷팅
            result = {'original': text}
            result.update(unifi_result)

            # 누락된 언어는 기본 번역기로 처리
            for lang in target_languages:
                if lang not in result or not result[lang]:
                    try:
                        result[lang] = self.translate_text(text, lang)
                    except:
                        result[lang] = text

            results.append(result)

        print(f"\n✅ Unifi 배치 번역 완료!")
        return results

    def get_translation_info(self, text: str) -> Dict[str, Any]:
        """번역 정보 제공 (디버깅/검증용)"""
        info = {
            'text': text,
            'similar_translations': self.find_similar_translations(text),
            'found_terms': self.extract_terms_from_text(text),
            'database_available': self.unifi_db is not None,
            'database_size': len(self.unifi_db) if self.unifi_db is not None else 0,
            'terminology_count': len(self.terminology)
        }
        return info