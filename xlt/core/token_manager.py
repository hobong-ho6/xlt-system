"""
macOS Keychain 기반 전역 토큰 관리 시스템

이 모듈은 XLT System의 토큰을 안전하고 편리하게 관리하기 위한
macOS Keychain 통합 토큰 관리자를 제공합니다.

주요 기능:
- macOS Keychain을 통한 안전한 토큰 저장/조회
- 토큰 유효성 검증
- 환경 변수 자동 설정
- 다중 프로젝트 간 토큰 공유

보안 특징:
- AES-256 암호화 저장 (macOS Keychain)
- Touch ID/Face ID 연동 가능
- iCloud Keychain 자동 백업 지원

사용 예제:
    from xlt.core.token_manager import TokenManager

    manager = TokenManager()

    # 토큰 저장
    manager.store_token('figma', 'figd_your_token_here')

    # 토큰 조회
    token = manager.get_token('figma')
"""

import subprocess
import json
import os
import requests
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import logging


class TokenManagerError(Exception):
    """토큰 관리 관련 오류"""
    pass


class TokenManager:
    """macOS Keychain 기반 토큰 관리자"""

    # 지원하는 서비스와 해당 Keychain 설정
    SUPPORTED_SERVICES = {
        'figma': {
            'keychain_account': 'xlt_figma',
            'keychain_service': 'XLT_FIGMA_TOKEN',
            'env_var': 'FIGMA_TOKEN',
            'validation_url': 'https://api.figma.com/v1/me'
        },
        'github': {
            'keychain_account': 'xlt_github',
            'keychain_service': 'XLT_GITHUB_TOKEN',
            'env_var': 'GITHUB_TOKEN',
            'validation_url': 'https://api.github.com/user'
        }
    }

    def __init__(self):
        """TokenManager 초기화"""
        self.logger = logging.getLogger(__name__)

        # macOS 플랫폼 확인
        if not self._is_macos():
            self.logger.warning("macOS가 아닌 환경에서는 Keychain 기능이 제한됩니다.")

    def _is_macos(self) -> bool:
        """macOS 환경인지 확인"""
        return os.uname().sysname == 'Darwin'

    def _get_service_config(self, service: str) -> Dict:
        """서비스 설정 조회"""
        service = service.lower()
        if service not in self.SUPPORTED_SERVICES:
            raise TokenManagerError(f"지원하지 않는 서비스: {service}")
        return self.SUPPORTED_SERVICES[service]

    def store_token(self, service: str, token: str, update: bool = True) -> bool:
        """
        Keychain에 토큰 저장

        Args:
            service: 서비스 이름 ('figma', 'github')
            token: 저장할 토큰
            update: 기존 토큰이 있으면 업데이트할지 여부

        Returns:
            bool: 저장 성공 여부
        """
        if not self._is_macos():
            self.logger.error("macOS에서만 Keychain 저장이 가능합니다.")
            return False

        config = self._get_service_config(service)

        try:
            cmd = [
                'security', 'add-generic-password',
                '-a', config['keychain_account'],  # account
                '-s', config['keychain_service'],  # service
                '-w', token,                       # password (토큰)
                '-T', '',                          # 모든 앱에서 접근 허용
            ]

            if update:
                cmd.append('-U')  # 기존값 업데이트

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"✅ {service} 토큰이 Keychain에 저장되었습니다.")
                return True
            else:
                self.logger.error(f"❌ {service} 토큰 저장 실패: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Keychain 저장 중 오류: {e}")
            return False

    def get_token_from_keychain(self, service: str) -> Optional[str]:
        """
        Keychain에서 토큰 조회

        Args:
            service: 서비스 이름

        Returns:
            Optional[str]: 토큰 (없으면 None)
        """
        if not self._is_macos():
            return None

        config = self._get_service_config(service)

        try:
            cmd = [
                'security', 'find-generic-password',
                '-a', config['keychain_account'],
                '-s', config['keychain_service'],
                '-w'  # 패스워드만 출력
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                token = result.stdout.strip()
                if token:
                    self.logger.debug(f"✅ {service} 토큰을 Keychain에서 조회했습니다.")
                    return token
            else:
                self.logger.debug(f"Keychain에서 {service} 토큰을 찾을 수 없습니다.")

        except Exception as e:
            self.logger.error(f"❌ Keychain 조회 중 오류: {e}")

        return None

    def get_token_from_env(self, service: str) -> Optional[str]:
        """
        환경 변수에서 토큰 조회

        Args:
            service: 서비스 이름

        Returns:
            Optional[str]: 토큰 (없으면 None)
        """
        config = self._get_service_config(service)
        env_var = config['env_var']

        # 여러 환경 변수명 시도 (slack의 경우)
        env_vars = [env_var]
        if service == 'github':
            env_vars.extend(['XLT_GITHUB_TOKEN'])
        elif service == 'figma':
            env_vars.extend(['XLT_FIGMA_TOKEN'])

        for var in env_vars:
            token = os.getenv(var)
            if token:
                self.logger.debug(f"✅ {service} 토큰을 환경 변수 {var}에서 조회했습니다.")
                return token

        return None

    def get_token_from_file(self, service: str) -> Optional[str]:
        """
        설정 파일에서 토큰 조회 (하위 호환성)

        Args:
            service: 서비스 이름

        Returns:
            Optional[str]: 토큰 (없으면 None)
        """
        # 프로젝트 로컬 파일 확인
        config_files = {
            'figma': 'figma_config.json',
            'github': 'github_config.json'
        }

        if service not in config_files:
            return None

        config_file = Path(config_files[service])

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # 서비스별 토큰 키명
                token_keys = {
                    'figma': ['access_token', 'token', 'figma_token'],
                    'github': ['access_token', 'token', 'github_token']
                }

                for key in token_keys[service]:
                    if key in config_data:
                        token = config_data[key]
                        if token:
                            self.logger.debug(f"✅ {service} 토큰을 파일 {config_file}에서 조회했습니다.")
                            return token

            except (json.JSONDecodeError, OSError) as e:
                self.logger.error(f"❌ 설정 파일 {config_file} 읽기 오류: {e}")

        return None

    def get_token(self, service: str) -> Optional[str]:
        """
        계층화된 토큰 조회 (최우선 → 최하위)

        우선순위:
        1. 환경 변수
        2. macOS Keychain
        3. 로컬 설정 파일 (하위 호환)

        Args:
            service: 서비스 이름

        Returns:
            Optional[str]: 토큰 (없으면 None)
        """
        # 1순위: 환경 변수
        if token := self.get_token_from_env(service):
            return token

        # 2순위: Keychain
        if token := self.get_token_from_keychain(service):
            return token

        # 3순위: 로컬 설정 파일 (하위 호환)
        if token := self.get_token_from_file(service):
            return token

        self.logger.warning(f"⚠️ {service} 토큰을 찾을 수 없습니다.")
        return None

    def validate_token(self, service: str, token: str) -> Tuple[bool, str]:
        """
        토큰 유효성 검증

        Args:
            service: 서비스 이름
            token: 검증할 토큰

        Returns:
            Tuple[bool, str]: (유효성, 메시지)
        """
        config = self._get_service_config(service)
        validation_url = config.get('validation_url')

        if not validation_url:
            return True, "검증 URL이 없습니다."

        try:
            headers = self._get_auth_headers(service, token)
            response = requests.get(validation_url, headers=headers, timeout=10)

            if response.status_code == 200:
                return True, "토큰이 유효합니다."
            elif response.status_code == 401:
                return False, "토큰이 만료되었거나 잘못되었습니다."
            else:
                return False, f"검증 실패 (HTTP {response.status_code})"

        except requests.RequestException as e:
            return False, f"네트워크 오류: {e}"

    def _get_auth_headers(self, service: str, token: str) -> Dict[str, str]:
        """서비스별 인증 헤더 생성"""
        if service == 'figma':
            return {'X-Figma-Token': token}
        elif service == 'github':
            return {'Authorization': f'token {token}'}
        else:
            return {'Authorization': f'Bearer {token}'}

    def delete_token(self, service: str) -> bool:
        """
        Keychain에서 토큰 삭제

        Args:
            service: 서비스 이름

        Returns:
            bool: 삭제 성공 여부
        """
        if not self._is_macos():
            return False

        config = self._get_service_config(service)

        try:
            cmd = [
                'security', 'delete-generic-password',
                '-a', config['keychain_account'],
                '-s', config['keychain_service']
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"✅ {service} 토큰이 Keychain에서 삭제되었습니다.")
                return True
            else:
                self.logger.error(f"❌ {service} 토큰 삭제 실패: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Keychain 삭제 중 오류: {e}")
            return False

    def list_stored_tokens(self) -> List[str]:
        """
        Keychain에 저장된 토큰 목록 조회

        Returns:
            List[str]: 저장된 서비스 목록
        """
        stored_services = []

        for service in self.SUPPORTED_SERVICES:
            if self.get_token_from_keychain(service):
                stored_services.append(service)

        return stored_services

    def migrate_from_file(self, service: str) -> bool:
        """
        설정 파일에서 Keychain으로 토큰 마이그레이션

        Args:
            service: 서비스 이름

        Returns:
            bool: 마이그레이션 성공 여부
        """
        # 파일에서 토큰 조회
        token = self.get_token_from_file(service)
        if not token:
            self.logger.warning(f"파일에서 {service} 토큰을 찾을 수 없습니다.")
            return False

        # 토큰 유효성 검증
        is_valid, message = self.validate_token(service, token)
        if not is_valid:
            self.logger.error(f"❌ {service} 토큰 검증 실패: {message}")
            return False

        # Keychain에 저장
        if self.store_token(service, token, update=True):
            self.logger.info(f"✅ {service} 토큰을 Keychain으로 마이그레이션했습니다.")
            return True

        return False

    def setup_env_vars(self, shell: str = 'zsh') -> str:
        """
        환경 변수 설정 스크립트 생성

        Args:
            shell: 셸 종류 ('zsh', 'bash')

        Returns:
            str: 환경 변수 설정 스크립트
        """
        lines = [
            f"# XLT System 토큰 자동 로드 (from Keychain)",
            f"# 생성 시간: {os.popen('date').read().strip()}",
            ""
        ]

        for service, config in self.SUPPORTED_SERVICES.items():
            account = config['keychain_account']
            service_name = config['keychain_service']
            env_var = config['env_var']

            lines.append(f"# {service.title()} 토큰")
            lines.append(f'export {env_var}=$(security find-generic-password -a "{account}" -s "{service_name}" -w 2>/dev/null)')
            lines.append("")

        lines.extend([
            "# XLT SSH 키 자동 추가 (GitHub 인증용)",
            "ssh-add --apple-use-keychain ~/.ssh/id_ed25519_xlt 2>/dev/null",
            ""
        ])

        return "\n".join(lines)

    def get_token_status(self) -> Dict[str, Dict]:
        """
        모든 토큰의 현재 상태 조회

        Returns:
            Dict: 서비스별 토큰 상태
        """
        status = {}

        for service in self.SUPPORTED_SERVICES:
            token = self.get_token(service)

            service_status = {
                'has_token': bool(token),
                'source': None,
                'valid': False,
                'message': ''
            }

            if token:
                # 토큰 출처 확인
                if self.get_token_from_env(service):
                    service_status['source'] = 'environment'
                elif self.get_token_from_keychain(service):
                    service_status['source'] = 'keychain'
                elif self.get_token_from_file(service):
                    service_status['source'] = 'file'

                # 토큰 유효성 검증
                is_valid, message = self.validate_token(service, token)
                service_status['valid'] = is_valid
                service_status['message'] = message
            else:
                service_status['message'] = '토큰이 설정되지 않았습니다.'

            status[service] = service_status

        return status


def main():
    """TokenManager CLI 테스트"""
    import argparse

    parser = argparse.ArgumentParser(description='XLT 토큰 관리자')
    parser.add_argument('action', choices=['list', 'status', 'migrate', 'setup-env'],
                       help='수행할 작업')
    parser.add_argument('--service', choices=['figma', 'github'],
                       help='대상 서비스')

    args = parser.parse_args()

    # 로깅 설정
    logging.basicConfig(level=logging.INFO,
                       format='%(levelname)s: %(message)s')

    manager = TokenManager()

    if args.action == 'list':
        stored = manager.list_stored_tokens()
        print(f"Keychain에 저장된 토큰: {stored}")

    elif args.action == 'status':
        status = manager.get_token_status()
        for service, info in status.items():
            print(f"{service}: {info}")

    elif args.action == 'migrate':
        if not args.service:
            print("--service 옵션이 필요합니다.")
            return

        success = manager.migrate_from_file(args.service)
        print(f"{args.service} 마이그레이션: {'성공' if success else '실패'}")

    elif args.action == 'setup-env':
        script = manager.setup_env_vars()
        print("다음 내용을 ~/.zshrc에 추가하세요:")
        print("=" * 50)
        print(script)


if __name__ == '__main__':
    main()