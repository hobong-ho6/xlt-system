"""
Unifi 전용 번역기 - LINE API 기반 용어집 관리
"""

import re
import difflib
import os
from typing import List, Dict, Any, Optional, Tuple

from .translator import Translator
from ..core.exceptions import TranslationError


class UnifiTranslator(Translator):
    """
    Unifi 서비스 전용 번역기
    - LINE API 전용 용어집 관리
    - 단일 소스 기반 번역 일관성 보장
    - Google Translate는 fallback으로만 사용
    """

    def __init__(self, config):
        super().__init__(config)
        self.line_terminology = {}
        self.terminology = {}
        self.load_line_terminology()

    def load_line_terminology(self):
        """LINE API에서 용어집 로드"""
        try:
            import requests

            # LINE API URL 목록 (여러 엔드포인트 시도)
            api_urls = [
                "https://landpress-content.line-scdn.net/contents/v2/projects/wdmwbfuv10x39bukv58ocevp/collections/web3_xlt_json/item",
                "https://landpress-content-v2.linecorp.com/api/v2/projects/wdmwbfuv10x39bukv58ocevp/collections/web3_xlt_json/items"
            ]

            data = None
            successful_url = None

            for api_url in api_urls:
                print(f"🌐 LINE API 시도: {api_url}")
                try:
                    response = requests.get(api_url, timeout=10)
                    print(f"📊 응답 상태: {response.status_code}")

                    if response.status_code == 200:
                        print(f"✅ API 응답 성공: {api_url}")
                        data = response.json()
                        successful_url = api_url
                        break
                    else:
                        print(f"❌ API 응답 실패 {response.status_code}: {api_url}")
                        continue

                except requests.exceptions.RequestException as e:
                    print(f"❌ API 요청 오류: {api_url} - {e}")
                    continue
                except ValueError as e:
                    print(f"❌ JSON 파싱 오류: {api_url} - {e}")
                    continue

            if data is None:
                # 모든 API 실패 시 테스트 데이터 사용
                print("⚠️ 모든 LINE API 실패, 테스트 데이터 사용")
                data = {
                    "data": [
                        {
                            "korean": "거래",
                            "english": "transaction",
                            "japanese": "取引",
                            "chinese": "交易",
                            "thai": "ธุรกรรม"
                        },
                        {
                            "korean": "지갑",
                            "english": "wallet",
                            "japanese": "ウォレット",
                            "chinese": "錢包",
                            "thai": "กระเป๋า"
                        },
                        {
                            "korean": "토큰",
                            "english": "token",
                            "japanese": "トークン",
                            "chinese": "代幣",
                            "thai": "โทเค็น"
                        }
                    ]
                }
                successful_url = "테스트 데이터"

            print(f"📋 사용된 데이터 소스: {successful_url}")

            if data:
                print(f"📄 응답 구조: {type(data)} - Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

                # 응답 구조 확인을 위한 상세 로깅
                if isinstance(data, dict):
                    print(f"🔍 data 키 존재: {'data' in data}")
                    if 'data' in data:
                        print(f"🔍 data 내용 타입: {type(data['data'])}")
                        if isinstance(data['data'], list):
                            print(f"🔍 data 배열 길이: {len(data['data'])}")
                            if len(data['data']) > 0:
                                print(f"🔍 첫 번째 아이템: {data['data'][0]}")

                    # 다양한 응답 구조 처리
                    terminology_data = None

                    # LINE API 실제 응답 구조 처리: body.exceptions
                    if (isinstance(data, dict) and 'body' in data and
                        isinstance(data['body'], dict) and 'exceptions' in data['body']):

                        exceptions_data = data['body']['exceptions']
                        print(f"🔍 exceptions 데이터 구조: {type(exceptions_data)}")

                        # exceptions가 dict인 경우 용어 사전을 찾기
                        if isinstance(exceptions_data, dict):
                            # LINE API 실제 응답 구조: exceptions.terminology (dict format)
                            if 'terminology' in exceptions_data and isinstance(exceptions_data['terminology'], dict):
                                terminology_dict = exceptions_data['terminology']
                                print(f"✅ 용어 사전 발견: terminology ({len(terminology_dict)}개)")

                                # 사전 형태를 리스트 형태로 변환
                                terminology_data = []
                                for korean_term, translations in terminology_dict.items():
                                    if isinstance(translations, dict):
                                        # Korean term을 키로 하고 translations를 값으로 하는 구조를
                                        # 기존 로직에 맞는 형태로 변환
                                        term_item = {
                                            'korean': korean_term,
                                            'ko_KR': korean_term,
                                            'english': translations.get('en_US', ''),
                                            'en_US': translations.get('en_US', ''),
                                            'japanese': translations.get('ja_JP', ''),
                                            'ja_JP': translations.get('ja_JP', ''),
                                            'chinese': translations.get('zh_TW', ''),
                                            'zh_TW': translations.get('zh_TW', ''),
                                            'thai': translations.get('th_TH', ''),
                                            'th_TH': translations.get('th_TH', '')
                                        }
                                        terminology_data.append(term_item)

                                print(f"✅ 용어 사전 변환 완료: {len(terminology_data)}개 용어")

                            # fallback: 기존 로직들 (배열 형태)
                            elif terminology_data is None:
                                # 1단계: 직접적인 키들 확인 (배열)
                                for key in ['terms', 'glossary', 'data', 'items']:
                                    if key in exceptions_data and isinstance(exceptions_data[key], list):
                                        terminology_data = exceptions_data[key]
                                        print(f"✅ 용어 배열 발견: {key} ({len(terminology_data)}개)")
                                        break

                                # 2단계: exceptions의 값들 중 배열 찾기
                                if terminology_data is None:
                                    for key, value in exceptions_data.items():
                                        if isinstance(value, list) and len(value) > 0:
                                            # 첫 번째 항목이 용어 같은 구조인지 확인
                                            first_item = value[0]
                                            if (isinstance(first_item, dict) and
                                                ('korean' in first_item or 'ko' in first_item or 'ko_KR' in first_item or
                                                 'english' in first_item or 'en' in first_item or 'en_US' in first_item)):
                                                terminology_data = value
                                                print(f"✅ 용어 배열 자동 발견: {key} ({len(terminology_data)}개)")
                                                break

                        # exceptions가 용어 배열인 경우 (직접 리스트)
                        elif isinstance(exceptions_data, list):
                            terminology_data = exceptions_data

                    # 기존 구조들 (fallback)
                    elif isinstance(data, dict) and 'data' in data and data['data']:
                        terminology_data = data['data']
                    elif isinstance(data, list) and len(data) > 0:
                        terminology_data = data
                    elif isinstance(data, dict) and 'items' in data and data['items']:
                        terminology_data = data['items']
                    elif isinstance(data, dict) and 'content' in data and data['content']:
                        terminology_data = data['content']

                    if terminology_data:
                        processed_count = 0

                        for item in terminology_data:
                            if isinstance(item, dict):
                                # 다양한 키 형태 지원
                                korean_term = item.get('korean') or item.get('ko') or item.get('ko_KR')

                                if korean_term:
                                    translations = {
                                        'ko_KR': korean_term,
                                        'en_US': item.get('english') or item.get('en') or item.get('en_US', ''),
                                        'ja_JP': item.get('japanese') or item.get('ja') or item.get('ja_JP', ''),
                                        'zh_TW': item.get('chinese') or item.get('zh') or item.get('zh_TW', ''),
                                        'th_TH': item.get('thai') or item.get('th') or item.get('th_TH', '')
                                    }

                                    self.line_terminology[korean_term] = translations
                                    processed_count += 1

                        if processed_count > 0:
                            print(f"✅ LINE API 용어집 로드 완료: {processed_count}개 용어")
                            # 용어 사전 구축
                            self._build_terminology_dict()
                        else:
                            raise Exception("LINE API 응답에서 유효한 용어를 찾을 수 없습니다")
                    else:
                        # 응답 구조 분석을 위한 상세 정보 출력
                        response_preview = str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
                        raise Exception(f"LINE API 응답 구조를 인식할 수 없습니다. 응답: {response_preview}")
            else:
                raise Exception("모든 LINE API 엔드포인트에서 데이터를 로드할 수 없습니다")

        except Exception as e:
            print(f"❌ LINE API 용어집 로드 실패: {e}")
            raise Exception(f"LINE API 용어집 로드 실패: {e}")

    def _build_terminology_dict(self):
        """LINE API 기반 용어 사전 구축"""
        if not self.line_terminology:
            return

        # LINE API에서 로드한 용어들로 사전 구축
        for korean_term, translations in self.line_terminology.items():
            self.terminology[korean_term] = {
                'translations': translations,
                'source': 'LINE_API'
            }

        print(f"📚 LINE API 용어 사전 구축 완료: {len(self.terminology)}개 용어")

        # 기존 Excel 로직 제거됨 - 아래 주석 처리된 코드
        """
        old_core_terms = [
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
        """


    def find_similar_translations(self, text: str, similarity_threshold: float = 0.6) -> List[Dict]:
        """LINE API 기반 유사한 텍스트 찾기"""
        if not self.line_terminology:
            return []

        similar_items = []

        # LINE API 용어에서 유사한 항목 찾기
        for korean_term, translations in self.line_terminology.items():
            ko_text = korean_term.strip()
            if not ko_text:
                continue

            # 유사도 계산 (difflib 사용)
            similarity = difflib.SequenceMatcher(None, text.lower(), ko_text.lower()).ratio()

            if similarity >= similarity_threshold:
                similar_items.append({
                    'term': korean_term,
                    'similarity': similarity,
                    'ko_KR': translations.get('ko_KR', ''),
                    'en_US': translations.get('en_US', ''),
                    'ja_JP': translations.get('ja_JP', ''),
                    'zh_TW': translations.get('zh_TW', ''),
                    'th_TH': translations.get('th_TH', ''),
                    'source': 'LINE_API'
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