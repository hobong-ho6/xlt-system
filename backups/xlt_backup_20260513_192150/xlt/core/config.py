"""XLT System Configuration Management"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import os

# TokenManager 지연 import (순환 import 방지)
_token_manager = None


def get_token_manager():
    """TokenManager 인스턴스 가져오기 (지연 로딩)"""
    global _token_manager
    if _token_manager is None:
        try:
            from .token_manager import TokenManager
            _token_manager = TokenManager()
        except ImportError:
            # token_manager 모듈이 없는 경우 None 반환
            _token_manager = None
    return _token_manager


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

    # Claude CLI 설정
    claude_timeout: int = 120  # Claude CLI 타임아웃 (초)
    claude_chunk_size: int = 10  # 청크 크기 (성능 최적화)

    # Google Sheets 용어집 관리 설정 (v5.1.1 추가)
    google_sheets_enabled: bool = False  # Google Sheets 용어집 사용 여부
    google_sheets_id: Optional[str] = None  # 구글 시트 ID
    google_sheets_credentials: Optional[str] = None  # Service Account JSON 파일 경로
    terminology_cache_ttl: int = 7200  # 용어집 캐시 TTL (초) - 2시간
    terminology_sheet_name: str = 'Terminology'  # 용어집 시트 탭 이름
    exceptions_sheet_name: str = 'Exceptions'  # 예외 항목 시트 탭 이름
    metadata_sheet_name: str = 'Metadata'  # 메타데이터 시트 탭 이름
    fallback_to_guide_md: bool = True  # Google Sheets 실패 시 guide.md 폴백 여부

    # 출력 설정
    excel_output_dir: str = 'output'
    excel_key_format: str = 'item_{number}'
    create_backups: bool = False

    # 피그마 설정
    figma_config_file: str = 'figma_config.json'
    figma_temp_dir: str = 'figma'

    # 프로젝트 설정 경로
    config_path: str = ''  # 설정 파일 기본 경로 (guide.md 위치)

    def __post_init__(self):
        """XLTConfig 초기화 후 실행"""
        if not self.config_path:
            # 현재 파일 위치에서 프로젝트 루트 찾기
            current_file = os.path.abspath(__file__)
            # xlt/core/config.py -> 프로젝트 루트 (2 levels up)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            self.config_path = project_root

    # 로깅 설정
    log_dir: str = 'logs'
    log_level: str = 'INFO'
    keep_session_logs_only: bool = True

    # ❌ 정적 OCR 교정 사전 제거됨 - Claude AI 전용으로 전환
    # 모든 교정은 Claude AI를 통해 실시간으로 처리됩니다.
    # ocr_corrections: 제거됨

    # 협업 시스템 설정 (v5.1.0 추가)
    collaboration_enabled: bool = True
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 10
    auto_conflict_resolution: bool = True
    zone_lock_timeout_seconds: int = 300
    background_monitoring: bool = True
    monitoring_interval_seconds: int = 30


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
        """
        Figma 액세스 토큰 가져오기

        조회 순서:
        1. TokenManager (환경변수 → Keychain → 로컬파일)
        2. 기존 방식 (하위 호환성)

        Returns:
            Optional[str]: Figma 토큰 (없으면 None)
        """
        # TokenManager를 통한 통합 조회 (새로운 방식)
        token_manager = get_token_manager()
        if token_manager:
            token = token_manager.get_token('figma')
            if token:
                return token

        # 기존 방식 (하위 호환성 - TokenManager 실패 시)
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


    def get_github_token(self) -> Optional[str]:
        """
        GitHub 액세스 토큰 가져오기

        조회 순서:
        1. TokenManager (환경변수 → Keychain → 로컬파일)
        2. 환경 변수 직접 조회 (하위 호환성)

        Returns:
            Optional[str]: GitHub 토큰 (없으면 None)
        """
        # TokenManager를 통한 통합 조회 (새로운 방식)
        token_manager = get_token_manager()
        if token_manager:
            token = token_manager.get_token('github')
            if token:
                return token

        # 기존 방식 (하위 호환성 - TokenManager 실패 시)
        # 환경 변수에서 확인
        token = os.getenv('GITHUB_TOKEN') or os.getenv('XLT_GITHUB_TOKEN')
        if token:
            return token

        return None

    def get_google_credentials(self) -> Optional[str]:
        """
        Google Sheets 서비스 계정 인증 정보 경로 가져오기

        조회 순서:
        1. 설정 파일의 google_sheets_credentials 경로
        2. 환경 변수 GOOGLE_SHEETS_CREDENTIALS
        3. 환경 변수 GOOGLE_APPLICATION_CREDENTIALS
        4. 기본 경로 (credentials/google_sheets_service_account.json)

        Returns:
            Optional[str]: 인증 파일 경로 (없거나 유효하지 않으면 None)
        """
        # 1순위: 설정에서 지정된 경로
        if self.google_sheets_credentials and os.path.exists(self.google_sheets_credentials):
            return self.google_sheets_credentials

        # 2순위: 환경 변수 (Google Sheets 전용)
        env_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        if env_path and os.path.exists(env_path):
            return env_path

        # 3순위: 환경 변수 (Google 공통)
        common_env_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if common_env_path and os.path.exists(common_env_path):
            return common_env_path

        # 4순위: 프로젝트 기본 경로
        default_path = os.path.join(self.config_path, 'credentials', 'google_sheets_service_account.json')
        if os.path.exists(default_path):
            return default_path

        return None

    def is_google_sheets_enabled(self) -> bool:
        """
        Google Sheets 용어집 시스템 사용 가능 여부 확인

        Returns:
            bool: 사용 가능하면 True
        """
        return (self.google_sheets_enabled and
                bool(self.google_sheets_id) and
                bool(self.get_google_credentials()))

    def get_token(self, service: str) -> Optional[str]:
        """
        통합 토큰 조회 함수

        Args:
            service: 서비스 이름 ('figma', 'github')

        Returns:
            Optional[str]: 토큰 (없으면 None)
        """
        service = service.lower()

        if service == 'figma':
            return self.get_figma_token()
        elif service == 'github':
            return self.get_github_token()
        else:
            # TokenManager를 통한 직접 조회 (새로운 서비스)
            token_manager = get_token_manager()
            if token_manager:
                return token_manager.get_token(service)
            return None

    def get_token_status(self) -> Dict[str, Dict]:
        """
        모든 토큰의 상태 조회

        Returns:
            Dict: 서비스별 토큰 상태 정보
        """
        token_manager = get_token_manager()
        if token_manager:
            return token_manager.get_token_status()

        # TokenManager가 없는 경우 기본 정보만 반환
        status = {}
        for service in ['figma', 'github']:
            token = self.get_token(service)
            status[service] = {
                'has_token': bool(token),
                'source': 'legacy',
                'valid': None,  # 검증 불가
                'message': '토큰이 있습니다' if token else '토큰이 없습니다'
            }
        return status


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