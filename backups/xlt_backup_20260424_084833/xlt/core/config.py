"""XLT System Configuration Management"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import os


@dataclass
class XLTConfig:
    """XLT 시스템 설정 관리 클래스"""

    # 기본 언어 설정
    default_languages: List[str] = field(default_factory=lambda: [
        'ko_KR', 'en_US', 'ja_JP', 'zh_TW', 'th_TH'
    ])

    # OCR 설정
    ocr_confidence_threshold: float = 0.5
    ocr_readers: Dict[str, List[str]] = field(default_factory=lambda: {
        'korean_english': ['ko', 'en'],
        'japanese_english': ['ja', 'en'],
        'chinese_english': ['ch_sim', 'en'],
        'thai_english': ['th', 'en']
    })

    # UI 필터링 설정
    ui_filter_zones: Dict[str, Any] = field(default_factory=lambda: {
        'top_gnb_threshold': 100,  # 상단 GNB 영역 Y 좌표
        'bottom_tab_threshold': 0.8,  # 화면 하단 탭 비율
        'badge_patterns': [
            r'\d+[a-zA-Z]\s*\)\s*\d+[가-힣]*',  # "6f ) 3일" 패턴
            r'\d+[a-zA-Z]\s+\d+[!]*',  # "7a 39!" 패턴
        ]
    })

    # 번역 설정
    translation_batch_size: int = 10
    translation_timeout: int = 120

    # 출력 설정
    excel_output_dir: str = 'output'
    excel_key_format: str = 'item_{number}'
    create_backups: bool = False

    # 피그마 설정
    figma_config_file: str = 'figma_config.json'
    figma_temp_dir: str = 'figma'

    # 로깅 설정
    log_dir: str = 'logs'
    log_level: str = 'INFO'
    keep_session_logs_only: bool = True

    # 한국어 OCR 교정 사전
    ocr_corrections: Dict[str, str] = field(default_factory=lambda: {
        '이울': '이율',
        '미선': '미션',
        '토근': '토큰',
        '받앉어요': '받았어요',
        '다사': '다시',
        '빈상': '빈상금',
        '수로': '수료',
        '찬성': '참성',
    })

    @classmethod
    def from_file(cls, config_file: str) -> 'XLTConfig':
        """설정 파일에서 XLTConfig 인스턴스 생성"""
        if not os.path.exists(config_file):
            return cls()

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 기본 설정에 파일 설정 오버라이드
            config = cls()
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            return config
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️ 설정 파일 로드 실패: {e}")
            return cls()

    def to_file(self, config_file: str) -> None:
        """현재 설정을 파일에 저장"""
        try:
            os.makedirs(os.path.dirname(config_file) if os.path.dirname(config_file) else '.', exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.__dict__, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"⚠️ 설정 파일 저장 실패: {e}")

    def get_figma_token(self) -> Optional[str]:
        """피그마 액세스 토큰 가져오기"""
        # 환경 변수에서 먼저 확인
        token = os.getenv('FIGMA_TOKEN')
        if token:
            return token

        # 설정 파일에서 확인
        if os.path.exists(self.figma_config_file):
            try:
                with open(self.figma_config_file, 'r', encoding='utf-8') as f:
                    figma_config = json.load(f)
                return figma_config.get('access_token')
            except (json.JSONDecodeError, OSError):
                pass

        return None

    def validate(self) -> List[str]:
        """설정 유효성 검사 및 경고 메시지 반환"""
        warnings = []

        if self.ocr_confidence_threshold < 0 or self.ocr_confidence_threshold > 1:
            warnings.append("OCR 신뢰도 임계값은 0과 1 사이여야 합니다")

        if not self.default_languages:
            warnings.append("기본 언어 설정이 비어있습니다")

        if not self.get_figma_token():
            warnings.append("피그마 액세스 토큰이 설정되지 않았습니다")

        return warnings