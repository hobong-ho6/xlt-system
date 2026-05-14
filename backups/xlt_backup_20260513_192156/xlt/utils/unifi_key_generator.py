"""
Unifi 기준 XLT 키 자동 생성기
기존 Unifi Excel 데이터베이스의 Key 패턴을 분석하여 일관성 있는 키 생성
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class UnifiKeyGenerator:
    """
    Unifi Excel 데이터베이스 기준 XLT 키 자동 생성기
    """

    def __init__(self, unifi_db_path: Optional[str] = None):
        self.unifi_db = None
        self.category_patterns = {}
        self.existing_keys = set()

        # 텍스트 → 카테고리 매핑 규칙
        self.category_mapping = {
            'asset': ['자산', '토큰', '코인', '잔액', '지갑', '포트폴리오', 'wallet', 'token', 'coin', 'balance', 'asset'],
            'send': ['송금', '전송', '보내기', '출금', '이체', 'send', 'transfer', 'withdraw', 'remit'],
            'signin': ['로그인', '로그아웃', '인증', '비밀번호', 'login', 'logout', 'auth', 'password', 'sign'],
            'settings': ['설정', '환경설정', '구성', '옵션', 'settings', 'config', 'option', 'preference'],
            'history': ['내역', '기록', '히스토리', '거래', 'history', 'record', 'transaction', 'log'],
            'interest': ['이자', '수익', '리워드', '보상', '스테이킹', 'interest', 'reward', 'yield', 'staking'],
            'guide': ['가이드', '도움말', '안내', '튜토리얼', 'guide', 'help', 'tutorial', 'info'],
            'common': ['확인', '취소', '완료', '저장', '삭제', 'confirm', 'cancel', 'done', 'save', 'delete'],
            'main': ['메인', '홈', '대시보드', '시작', 'main', 'home', 'dashboard', 'start']
        }

        # UI 컴포넌트 → 서브카테고리 매핑
        self.component_mapping = {
            'btn': ['버튼', '클릭', '누르', '선택', 'button', 'click', 'press', 'select'],
            'title': ['제목', '타이틀', '헤더', 'title', 'header', 'heading'],
            'desc': ['설명', '내용', '텍스트', '메시지', 'description', 'text', 'message', 'content'],
            'popup': ['팝업', '모달', '대화상자', '알림', 'popup', 'modal', 'dialog', 'alert'],
            'input': ['입력', '필드', '박스', 'input', 'field', 'box', 'form'],
            'list': ['목록', '리스트', '배열', 'list', 'array', 'items'],
            'tab': ['탭', '메뉴', '네비게이션', 'tab', 'menu', 'navigation', 'nav'],
            'toast': ['토스트', '알림', '메시지', 'toast', 'notification', 'snackbar']
        }

        if unifi_db_path:
            self.load_unifi_database(unifi_db_path)

    def load_unifi_database(self, db_path: str):
        """Unifi 데이터베이스 로드 및 패턴 분석"""
        try:
            # 상대 경로 처리
            if not Path(db_path).is_absolute():
                db_path = Path.cwd() / db_path

            self.unifi_db = pd.read_excel(db_path)
            if 'Unnamed: 0' in self.unifi_db.columns:
                self.unifi_db = self.unifi_db.rename(columns={'Unnamed: 0': 'Key'})

            print(f"✅ Unifi 키 데이터베이스 로드: {len(self.unifi_db)}개 항목")

            # 기존 키 패턴 분석
            self._analyze_existing_patterns()

        except Exception as e:
            print(f"⚠️ Unifi 데이터베이스 로드 실패: {str(e)}")

    def _analyze_existing_patterns(self):
        """기존 키 패턴 분석"""
        if self.unifi_db is None:
            return

        keys = self.unifi_db['Key'].dropna().astype(str)
        self.existing_keys = set(keys)

        # 카테고리별 패턴 분석
        for key in keys:
            if '_' in key:
                parts = key.split('_')
                if len(parts) >= 2:
                    prefix = parts[0]
                    category = parts[1]

                    if prefix not in self.category_patterns:
                        self.category_patterns[prefix] = {}
                    if category not in self.category_patterns[prefix]:
                        self.category_patterns[prefix][category] = []

                    self.category_patterns[prefix][category].append(key)

        print(f"📊 키 패턴 분석 완료: {len(self.category_patterns)}개 PREFIX")

    def analyze_text_content(self, text: str) -> Tuple[str, str, List[str]]:
        """텍스트 내용 분석하여 카테고리 추출

        Args:
            text: 분석할 텍스트

        Returns:
            Tuple[str, str, List[str]]: (category, component, keywords)
        """
        text_lower = text.lower()

        # 1. 카테고리 분석
        category = 'common'  # 기본값
        category_scores = {}

        for cat, keywords in self.category_mapping.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += len(keyword)
            if score > 0:
                category_scores[cat] = score

        if category_scores:
            category = max(category_scores.items(), key=lambda x: x[1])[0]

        # 2. 컴포넌트 분석
        component = 'text'  # 기본값
        component_scores = {}

        for comp, keywords in self.component_mapping.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += len(keyword)
            if score > 0:
                component_scores[comp] = score

        if component_scores:
            component = max(component_scores.items(), key=lambda x: x[1])[0]

        # 3. 핵심 키워드 추출
        keywords = []
        for word in text.split():
            # 의미있는 단어만 추출 (길이 2 이상, 특수문자 제외)
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) >= 2 and clean_word not in ['이다', '있다', '한다', 'and', 'the', 'for']:
                keywords.append(clean_word.lower())

        return category, component, keywords[:3]  # 최대 3개 키워드

    def generate_simple_key(self, prefix: str, index: int) -> str:
        """단순 prefix + 번호 키 생성 (v3.3 신규)

        Args:
            prefix: 사용자 정의 prefix
            index: 순서 번호

        Returns:
            str: 생성된 키 (예: MY_PREFIX_001)
        """
        # 기본 키 생성
        base_key = f"{prefix}_{index:03d}"

        # 중복 방지
        final_key = base_key
        counter = 1
        while final_key in self.existing_keys:
            final_key = f"{prefix}_{index:03d}_{counter:02d}"
            counter += 1

        # 새로운 키를 기존 키 목록에 추가
        self.existing_keys.add(final_key)

        return final_key

    def generate_unifi_key(self, text: str, index: int, simple_mode: bool = False, custom_prefix: str = None) -> str:
        """Unifi 패턴 기준 키 생성

        Args:
            text: 원본 텍스트
            index: 순서 번호
            simple_mode: True이면 단순 prefix + 번호 모드 (v3.3)
            custom_prefix: simple_mode일 때 사용할 사용자 정의 prefix (v3.3)

        Returns:
            str: 생성된 XLT 키
        """
        # v3.3: 단순 모드
        if simple_mode and custom_prefix:
            return self.generate_simple_key(custom_prefix, index)

        # 기존: Unifi 지능형 키 생성
        # 텍스트 분석
        category, component, keywords = self.analyze_text_content(text)

        # 키 구조: XLT_[CATEGORY]_[COMPONENT]_[DETAIL]
        prefix = "XLT"

        # 세부 정보 생성
        detail_parts = []

        # 핵심 키워드가 있으면 사용
        if keywords:
            detail = '_'.join(keywords[:2])  # 최대 2개 키워드
            detail_parts.append(detail)

        # 인덱스 추가
        detail_parts.append(f"{index:03d}")

        detail = '_'.join(detail_parts)

        # 최종 키 조합
        base_key = f"{prefix}_{category}_{component}_{detail}"

        # 길이 제한 (최대 50자)
        if len(base_key) > 50:
            base_key = base_key[:47] + f"{index:03d}"

        # 중복 방지
        final_key = base_key
        counter = 1
        while final_key in self.existing_keys:
            final_key = f"{base_key}_{counter:02d}"
            counter += 1

        # 새로운 키를 기존 키 목록에 추가
        self.existing_keys.add(final_key)

        return final_key

    def validate_key_format(self, key: str) -> bool:
        """키 형식 유효성 검사

        Args:
            key: 검사할 키

        Returns:
            bool: 유효 여부
        """
        # 기본 패턴: PREFIX_CATEGORY_COMPONENT_DETAIL (한글 및 유니코드 허용)
        # 영문자, 숫자, 한글, 언더스코어 허용
        pattern = r'^[A-Za-z가-힣_][A-Za-z0-9가-힣_]+$'

        if not re.match(pattern, key):
            return False

        parts = key.split('_')
        if len(parts) < 4:
            return False

        # 길이 제한 (한글 고려하여 증가)
        if len(key) > 80:
            return False

        # 연속된 언더스코어 방지
        if '__' in key:
            return False

        return True

    def suggest_similar_keys(self, text: str, limit: int = 5) -> List[Dict[str, any]]:
        """유사한 기존 키 추천

        Args:
            text: 검색할 텍스트
            limit: 결과 제한

        Returns:
            List[Dict]: 유사 키 정보
        """
        if self.unifi_db is None:
            return []

        suggestions = []
        text_lower = text.lower()

        # Unifi 데이터베이스에서 유사한 텍스트 검색
        for _, row in self.unifi_db.iterrows():
            ko_text = str(row.get('ko_KR', '')).lower()
            en_text = str(row.get('en_US', '')).lower()

            # 텍스트 유사도 계산 (간단한 키워드 매칭)
            similarity_score = 0

            for word in text_lower.split():
                if len(word) >= 2:
                    if word in ko_text:
                        similarity_score += 2
                    if word in en_text:
                        similarity_score += 1

            if similarity_score > 0:
                suggestions.append({
                    'key': row.get('Key', ''),
                    'ko_text': row.get('ko_KR', ''),
                    'en_text': row.get('en_US', ''),
                    'similarity': similarity_score
                })

        # 유사도 순으로 정렬
        suggestions.sort(key=lambda x: x['similarity'], reverse=True)

        return suggestions[:limit]

    def get_category_statistics(self) -> Dict[str, any]:
        """카테고리별 통계 정보

        Returns:
            Dict: 통계 정보
        """
        if not self.category_patterns:
            return {}

        stats = {}

        for prefix, categories in self.category_patterns.items():
            stats[prefix] = {}
            for category, keys in categories.items():
                stats[prefix][category] = len(keys)

        return stats

    def export_key_mapping(self, output_path: str):
        """키 매핑 정보 내보내기

        Args:
            output_path: 출력 파일 경로
        """
        import json

        mapping_data = {
            'category_mapping': self.category_mapping,
            'component_mapping': self.component_mapping,
            'existing_patterns': self.category_patterns,
            'statistics': self.get_category_statistics()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 키 매핑 정보 내보내기 완료: {output_path}")