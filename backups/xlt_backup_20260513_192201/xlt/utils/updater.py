"""
XLT 시스템 자동 업데이트 관리자
GitHub 저장소와 동기화하여 최신 버전 유지
"""

import os
import subprocess
import json
import requests
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import shutil
import tempfile


class XLTUpdater:
    """XLT 시스템 자동 업데이트 관리"""

    def __init__(self, repo_url: str = "https://github.com/hobong-ho6/xlt-system.git"):
        self.repo_url = repo_url
        self.api_url = "https://api.github.com/repos/hobong-ho6/xlt-system"
        self.project_root = Path(__file__).parent.parent.parent
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # GitHub API 인증 설정 (레이트 리밋 해결)
        self.github_token = self._get_github_token()
        self.headers = {}
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'

    def _get_github_token(self) -> Optional[str]:
        """GitHub Personal Access Token 조회 (다중 소스)"""
        # 1순위: 환경 변수
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            return token

        # 2순위: 설정 파일
        try:
            config_file = self.project_root / "github_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('github_token')
        except:
            pass

        # 3순위: Git 설정
        try:
            result = subprocess.run(['git', 'config', '--global', 'github.token'],
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass

        # 토큰 없으면 None (Raw GitHub으로 fallback)
        return None

    def get_current_version(self) -> Optional[Dict[str, str]]:
        """현재 로컬 버전 정보 조회 (설치 방식 자동 감지)"""
        # 1단계: Git 저장소 우선 확인 (개발 환경)
        try:
            os.chdir(self.project_root)

            # Git 저장소 존재하고 작동하는지 확인
            if (self.project_root / ".git").exists():
                # Git 저장소 기능 테스트
                result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                      capture_output=True, text=True, check=True)
                current_hash = result.stdout.strip()

                # 현재 커밋 메시지
                result = subprocess.run(['git', 'log', '-1', '--pretty=%s'],
                                      capture_output=True, text=True, check=True)
                current_message = result.stdout.strip()

                # 현재 커밋 날짜
                result = subprocess.run(['git', 'log', '-1', '--pretty=%cd', '--date=iso'],
                                      capture_output=True, text=True, check=True)
                current_date = result.stdout.strip()

                return {
                    'hash': current_hash,
                    'short_hash': current_hash[:7],
                    'message': current_message,
                    'date': current_date,
                    'branch': self._get_current_branch(),
                    'version': '5.0.1-git',
                    'source': 'git_repo'
                }
        except Exception as e:
            print(f"⚠️ Git 버전 정보 조회 실패: {str(e)}")

        # 2단계: version.json 파일 시도 (ZIP 설치 환경)
        try:
            version_file = self.project_root / "version.json"
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)

                # ZIP 설치 마커 확인 (commit_hash, installation_type 등)
                if version_data.get('commit_hash') or version_data.get('installation_type') == 'zip':
                    return {
                        'hash': version_data.get('commit_hash', 'unknown'),
                        'short_hash': version_data.get('commit_hash', 'unknown')[:7] if version_data.get('commit_hash') else 'zip-inst',
                        'message': version_data.get('commit_message', 'Installed from ZIP archive'),
                        'date': version_data.get('build_date', datetime.now().isoformat()),
                        'branch': 'main',
                        'version': version_data.get('version', '5.0.1'),
                        'source': 'zip_install'
                    }
                else:
                    # version.json 있지만 ZIP 마커 없음 → Git 환경에서 생성된 파일
                    print("⚠️ version.json 존재하지만 ZIP 마커 없음. Git 환경으로 추정됨.")
        except Exception as e:
            print(f"⚠️ version.json 읽기 실패: {str(e)}")

        # 3단계: Git 저장소가 없고 version.json도 불완전한 경우

            # 현재 커밋 해시
            result = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True, check=True)
            current_hash = result.stdout.strip()

            # 현재 커밋 메시지
            result = subprocess.run(['git', 'log', '-1', '--pretty=%s'],
                                  capture_output=True, text=True, check=True)
            current_message = result.stdout.strip()

            # 현재 커밋 날짜
            result = subprocess.run(['git', 'log', '-1', '--pretty=%cd', '--date=iso'],
                                  capture_output=True, text=True, check=True)
            current_date = result.stdout.strip()

            return {
                'hash': current_hash,
                'short_hash': current_hash[:7],
                'message': current_message,
                'date': current_date,
                'branch': self._get_current_branch(),
                'version': '5.0.1-git',
                'source': 'git_repo'
            }
        except Exception as e:
            print(f"⚠️ Git 버전 정보 조회 실패: {str(e)}")

            # 3단계: 폴백 버전 정보
            return {
                'hash': 'unknown',
                'short_hash': 'unknown',
                'message': 'Version information unavailable',
                'date': datetime.now().isoformat(),
                'branch': 'main',
                'version': '5.0.1',
                'source': 'fallback'
            }

    def get_remote_version(self) -> Optional[Dict[str, str]]:
        """GitHub 원격 저장소 최신 버전 정보 조회 (다중 소스 + 인증)"""

        # 1순위: GitHub API with Token (상세 정보 + 레이트 리밋 해결)
        if self.github_token:
            try:
                response = requests.get(f"{self.api_url}/commits/main",
                                      headers=self.headers, timeout=10)
                response.raise_for_status()

                commit_data = response.json()
                return {
                    'hash': commit_data['sha'],
                    'short_hash': commit_data['sha'][:7],
                    'message': commit_data['commit']['message'].split('\n')[0],
                    'date': commit_data['commit']['committer']['date'],
                    'author': commit_data['commit']['author']['name'],
                    'url': commit_data['html_url'],
                    'version': self._extract_version_from_message(commit_data['commit']['message']),
                    'source': 'github_api_authenticated'
                }
            except Exception as e:
                print(f"⚠️ GitHub API 인증 호출 실패: {e}, Raw URL로 fallback")

        # 2순위: Raw GitHub URL (레이트 리밋 우회)
        try:
            raw_version_url = "https://raw.githubusercontent.com/hobong-ho6/xlt-system/main/version.json"
            response = requests.get(raw_version_url, timeout=10)
            response.raise_for_status()

            version_data = response.json()
            return {
                'hash': 'latest',
                'short_hash': 'latest',
                'message': f"XLT System v{version_data.get('version', 'unknown')} release",
                'date': f"{version_data.get('build', 'unknown')}T00:00:00Z",
                'author': 'XLT System',
                'url': 'https://github.com/hobong-ho6/xlt-system',
                'version': version_data.get('version', 'unknown'),
                'source': 'raw_github'
            }
        except Exception as e:
            print(f"⚠️ Raw GitHub 조회 실패: {e}")

        # 3순위: 완전 실패
        return None

    def _extract_version_from_message(self, commit_message: str) -> str:
        """커밋 메시지에서 버전 번호 추출"""
        import re
        # v4.3.0, 4.3.0 패턴 찾기
        match = re.search(r'v?(\d+\.\d+\.\d+)', commit_message)
        return match.group(1) if match else 'unknown'

    def check_for_updates(self) -> Dict[str, any]:
        """업데이트 확인 (ZIP/Git 환경 모두 지원)"""
        current = self.get_current_version()
        remote = self.get_remote_version()

        if not current or not remote:
            return {
                'update_available': False,
                'error': '버전 정보 조회 실패',
                'current': current,
                'remote': remote
            }

        # 업데이트 가능 여부 판단 로직 개선
        update_available = False

        if current.get('source') == 'version_file' or current.get('source') == 'zip_install':
            # ZIP 설치 환경: 버전 번호 기반 비교 우선
            try:
                current_version = current.get('version', '0.0.0')
                remote_version = remote.get('version', '0.0.0')

                # 버전 번호 비교 (v5.0.4 vs v5.0.5)
                def version_tuple(v):
                    return tuple(map(int, v.replace('v', '').split('.')))

                current_tuple = version_tuple(current_version)
                remote_tuple = version_tuple(remote_version)

                # 원격 버전이 현재 버전보다 높으면 업데이트 가능
                update_available = remote_tuple > current_tuple

                print(f"🔍 버전 비교: {current_version} → {remote_version} = {'업데이트 가능' if update_available else '최신 버전'}")

            except Exception as e:
                print(f"⚠️ 버전 비교 실패, 날짜/해시로 대체: {str(e)}")
                # 폴백: 날짜 비교 (기존 로직)
                try:
                    from datetime import datetime
                    current_date = datetime.fromisoformat(current['date'].replace('Z', '+00:00'))
                    remote_date = datetime.fromisoformat(remote['date'].replace('Z', '+00:00'))

                    # 날짜가 다르면 업데이트 가능 (24시간 제한 제거)
                    update_available = remote_date > current_date

                except:
                    # 최종 폴백: 해시 비교
                    update_available = current.get('hash', '') != remote.get('hash', '')

        elif current.get('source') == 'git_repo':
            # Git 저장소 환경: 해시 비교 (단, 해시가 없으면 항상 업데이트 가능)
            if remote.get('hash') and remote['hash'] != 'latest' and current.get('hash'):
                update_available = current['hash'] != remote['hash']
            else:
                # 해시 비교 불가능 시 (레이트 리밋 등) 업데이트 가능으로 표시
                update_available = True

        else:
            # 폴백: 보수적으로 업데이트 없다고 판단
            update_available = False

        result = {
            'update_available': update_available,
            'current': current,
            'remote': remote,
            'behind_commits': 0,
            'comparison_method': current.get('source', 'unknown')
        }

        if update_available and current.get('source') == 'git_repo':
            # Git 환경에서만 커밋 수 계산
            try:
                result['behind_commits'] = self._count_behind_commits()
            except Exception as e:
                print(f"⚠️ 커밋 수 계산 실패: {str(e)}")
                result['behind_commits'] = 0

        return result

    def _count_behind_commits(self) -> int:
        """뒤처진 커밋 수 계산"""
        try:
            os.chdir(self.project_root)
            subprocess.run(['git', 'fetch', 'origin', 'main'],
                          capture_output=True, check=True)

            result = subprocess.run(['git', 'rev-list', '--count', 'HEAD..origin/main'],
                                  capture_output=True, text=True, check=True)
            return int(result.stdout.strip())
        except:
            return 0

    def _get_current_branch(self) -> str:
        """현재 브랜치 조회"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'],
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except:
            return 'unknown'

    def has_local_changes(self) -> bool:
        """로컬 변경사항 확인"""
        try:
            os.chdir(self.project_root)

            # Staged changes 확인
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'],
                                  capture_output=True)
            has_staged = result.returncode != 0

            # Unstaged changes 확인
            result = subprocess.run(['git', 'diff', '--quiet'],
                                  capture_output=True)
            has_unstaged = result.returncode != 0

            return has_staged or has_unstaged
        except:
            return True  # 안전을 위해 변경사항이 있다고 가정

    def create_backup(self) -> str:
        """현재 상태 백업"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"xlt_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name

        try:
            # 전체 프로젝트 백업 (git 히스토리 제외)
            shutil.copytree(
                self.project_root,
                backup_path,
                ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'backups')
            )

            print(f"✅ 백업 생성 완료: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"⚠️ 백업 생성 실패: {str(e)}")
            raise

    def perform_update(self, create_backup: bool = True) -> Dict[str, any]:
        """업데이트 실행 (설치 환경별 분기 처리)"""
        update_log = []

        try:
            # 현재 설치 환경 감지
            current_version = self.get_current_version()
            installation_type = current_version.get('source', 'unknown')

            update_log.append(f"설치 환경 감지: {installation_type}")

            # 1. 백업 생성
            backup_path = None
            if create_backup:
                backup_path = self.create_backup()
                update_log.append(f"백업 생성: {backup_path}")

            # 2. 환경별 업데이트 실행
            if installation_type == 'git_repo':
                return self._perform_git_update(backup_path, update_log)
            else:
                return self._perform_zip_update(backup_path, update_log)

        except Exception as e:
            error_msg = f"업데이트 실패: {str(e)}"
            update_log.append(f"❌ {error_msg}")

            return {
                'success': False,
                'error': error_msg,
                'backup_path': backup_path,
                'update_log': update_log,
                'message': '업데이트 중 오류가 발생했습니다. 백업에서 복원이 필요할 수 있습니다.'
            }

    def _perform_git_update(self, backup_path: str, update_log: list) -> Dict[str, any]:
        """Git 저장소 기반 업데이트 실행"""
        try:
            os.chdir(self.project_root)

            # 로컬 변경사항 확인
            if self.has_local_changes():
                # Git user 설정 확인 및 자동 설정 (git stash 요구사항)
                try:
                    subprocess.run(['git', 'config', 'user.email'],
                                  capture_output=True, check=True)
                except:
                    # Git user 설정이 없으면 임시 설정
                    subprocess.run(['git', 'config', 'user.email', 'xlt-system@local'],
                                  capture_output=True, check=False)
                    subprocess.run(['git', 'config', 'user.name', 'XLT System'],
                                  capture_output=True, check=False)
                    update_log.append("Git 설정 자동 구성")

                # 로컬 변경사항 임시 저장
                try:
                    subprocess.run(['git', 'stash', 'push', '-m', f'Auto-stash before update {datetime.now()}'],
                                  capture_output=True, check=True)
                    update_log.append("로컬 변경사항 임시 저장")
                except subprocess.CalledProcessError as e:
                    # stash 실패 시 경고만 표시하고 계속 진행
                    update_log.append(f"⚠️ 로컬 변경사항 저장 실패 (무시하고 진행)")
                    print(f"⚠️ git stash 실패: {e}, 계속 진행...")

            # 원격 저장소에서 최신 버전 가져오기
            subprocess.run(['git', 'fetch', 'origin', 'main'],
                          capture_output=True, check=True)
            update_log.append("원격 저장소 정보 업데이트")

            # 메인 브랜치로 체크아웃
            subprocess.run(['git', 'checkout', 'main'],
                          capture_output=True, check=True)
            update_log.append("메인 브랜치 체크아웃")

            # 최신 코드로 업데이트
            result = subprocess.run(['git', 'pull', 'origin', 'main'],
                                  capture_output=True, text=True, check=True)
            update_log.append("최신 코드 다운로드 완료")

            # 의존성 업데이트 확인
            if (self.project_root / "requirements.txt").exists():
                try:
                    subprocess.run(['pip', 'install', '-r', 'requirements.txt'],
                                  capture_output=True, check=True)
                    update_log.append("의존성 패키지 업데이트 완료")
                except:
                    update_log.append("⚠️ 의존성 업데이트 실패 (수동 확인 필요)")

            # 커맨드 파일 업데이트 (데스크톱 트레이 앱 실행 스크립트)
            self._update_desktop_command_files(update_log)

            return {
                'success': True,
                'backup_path': backup_path,
                'update_log': update_log,
                'message': 'Git 기반 업데이트가 성공적으로 완료되었습니다!'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Git 업데이트 실패: {str(e)}",
                'backup_path': backup_path,
                'update_log': update_log
            }

    def _update_desktop_command_files(self, update_log: list):
        """데스크톱 커맨드 파일 경로 업데이트"""
        try:
            desktop_path = Path.home() / "Desktop"
            command_files = [
                "XLT System (Tray).command",
                "XLT_System_Tray.command",
                "XLT_System_Tray_FINAL.command"
            ]

            current_install_dir = str(self.project_root)
            updated_files = []

            for file_name in command_files:
                command_file = desktop_path / file_name
                if command_file.exists():
                    try:
                        # 파일 읽기
                        content = command_file.read_text(encoding='utf-8')

                        # 이전 경로들을 현재 경로로 교체
                        old_patterns = [
                            'INSTALL_DIR="/Users/user/XLT-System"',
                            'INSTALL_DIR="/Users/user/Documents/XLTTT"',
                            '/Users/user/XLT-System',
                            '/Users/user/Documents/XLTTT'
                        ]

                        modified = False
                        for old_pattern in old_patterns:
                            if old_pattern in content:
                                if old_pattern.startswith('INSTALL_DIR='):
                                    content = content.replace(old_pattern, f'INSTALL_DIR="{current_install_dir}"')
                                else:
                                    content = content.replace(old_pattern, current_install_dir)
                                modified = True

                        # 파일 업데이트
                        if modified:
                            command_file.write_text(content, encoding='utf-8')
                            updated_files.append(file_name)

                    except Exception as e:
                        update_log.append(f"⚠️ 커맨드 파일 업데이트 실패: {file_name} - {e}")

            if updated_files:
                update_log.append(f"✅ 커맨드 파일 업데이트: {', '.join(updated_files)}")
            else:
                update_log.append("ℹ️ 업데이트할 커맨드 파일 없음")

        except Exception as e:
            update_log.append(f"⚠️ 커맨드 파일 업데이트 중 오류: {e}")

    def _perform_zip_update(self, backup_path: str, update_log: list) -> Dict[str, any]:
        """ZIP 파일 기반 업데이트 실행"""
        try:
            # GitHub에서 최신 ZIP 다운로드
            zip_url = "https://github.com/hobong-ho6/xlt-system/archive/refs/heads/main.zip"
            temp_dir = tempfile.mkdtemp()
            zip_path = Path(temp_dir) / "xlt-system-main.zip"

            update_log.append("최신 ZIP 파일 다운로드 중...")

            # ZIP 파일 다운로드
            response = requests.get(zip_url, stream=True, timeout=60)
            response.raise_for_status()

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            update_log.append(f"ZIP 파일 다운로드 완료: {zip_path}")

            # ZIP 파일 압축 해제
            import zipfile
            extract_dir = Path(temp_dir) / "extracted"

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # 압축 해제된 소스 디렉토리 찾기
            source_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if not source_dirs:
                raise Exception("압축 해제된 소스 디렉토리를 찾을 수 없습니다")

            source_dir = source_dirs[0]  # xlt-system-main 폴더
            update_log.append(f"ZIP 압축 해제 완료: {source_dir}")

            # 중요 파일 보존 목록
            preserve_files = [
                'user_config.json',
                'figma_config.json',
                'logging_config.json',
                'environment.json',
                '*.log'
            ]

            # 사용자 설정 파일 백업
            config_backup = {}
            for pattern in preserve_files:
                for file_path in self.project_root.glob(pattern):
                    if file_path.is_file():
                        with open(file_path, 'rb') as f:
                            config_backup[file_path.name] = f.read()
                        update_log.append(f"설정 파일 백업: {file_path.name}")

            # 파일 교체 (선택적)
            exclude_patterns = ['.git', '__pycache__', '*.pyc', '.DS_Store', 'backups']

            for item in source_dir.iterdir():
                if any(pattern in str(item) for pattern in exclude_patterns):
                    continue

                target_path = self.project_root / item.name

                if item.is_file():
                    # 파일 복사
                    shutil.copy2(item, target_path)
                    update_log.append(f"파일 업데이트: {item.name}")
                elif item.is_dir():
                    # 디렉토리 복사 (기존 디렉토리 제거 후)
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(item, target_path)
                    update_log.append(f"디렉토리 업데이트: {item.name}")

            # 설정 파일 복원
            for filename, content in config_backup.items():
                restore_path = self.project_root / filename
                with open(restore_path, 'wb') as f:
                    f.write(content)
                update_log.append(f"설정 파일 복원: {filename}")

            # GitHub에서 최신 커밋 정보 가져오기
            try:
                commit_info = self._get_latest_commit_info()
                self._update_version_json_with_commit(commit_info)
                update_log.append(f"버전 정보 업데이트: {commit_info.get('sha', 'unknown')[:7]}")
            except Exception as e:
                update_log.append(f"⚠️ 버전 정보 업데이트 실패: {str(e)}")

            # 커맨드 파일 업데이트 (데스크톱 트레이 앱 실행 스크립트)
            self._update_desktop_command_files(update_log)

            # 임시 파일 정리
            shutil.rmtree(temp_dir)
            update_log.append("임시 파일 정리 완료")

            return {
                'success': True,
                'backup_path': backup_path,
                'update_log': update_log,
                'message': 'ZIP 기반 업데이트가 성공적으로 완료되었습니다!'
            }

        except Exception as e:
            # 임시 파일 정리
            try:
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir)
            except:
                pass

            return {
                'success': False,
                'error': f"ZIP 업데이트 실패: {str(e)}",
                'backup_path': backup_path,
                'update_log': update_log,
                'message': 'ZIP 업데이트 중 오류가 발생했습니다. 백업에서 복원해주세요.'
            }

    def _get_latest_commit_info(self) -> Dict[str, any]:
        """GitHub API에서 최신 커밋 정보 가져오기"""
        try:
            response = requests.get(f"{self.api_url}/commits/main", timeout=10)
            response.raise_for_status()
            commit_data = response.json()

            return {
                'sha': commit_data['sha'],
                'message': commit_data['commit']['message'],
                'date': commit_data['commit']['committer']['date'],
                'author': commit_data['commit']['author']['name']
            }
        except Exception as e:
            print(f"⚠️ GitHub 커밋 정보 조회 실패: {str(e)}")
            return {
                'sha': 'unknown',
                'message': 'Updated from ZIP',
                'date': datetime.now().isoformat(),
                'author': 'ZIP Update'
            }

    def _update_version_json_with_commit(self, commit_info: Dict[str, any]):
        """version.json에 커밋 정보 업데이트"""
        try:
            version_file = self.project_root / "version.json"

            # 기존 version.json 읽기 (없으면 기본값)
            if version_file.exists():
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
            else:
                version_data = {}

            # 커밋 정보로 업데이트
            version_data.update({
                'name': 'XLT System',
                'version': '5.0.1',
                'build_date': datetime.now().isoformat(),
                'commit_hash': commit_info['sha'],
                'commit_message': commit_info['message'],
                'installation_type': 'zip',
                'last_update': datetime.now().isoformat(),
                'description': '피그마 디자인 → 다국어 번역 자동화 시스템'
            })

            # version.json 업데이트
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ version.json 업데이트 실패: {str(e)}")

    def restore_from_backup(self, backup_path: str) -> bool:
        """백업에서 복원"""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                print(f"⚠️ 백업 디렉토리를 찾을 수 없습니다: {backup_path}")
                return False

            # 현재 프로젝트 백업
            temp_backup = tempfile.mkdtemp(prefix='xlt_temp_')
            shutil.move(str(self.project_root), temp_backup)

            # 백업에서 복원
            shutil.copytree(backup_dir, self.project_root)

            print(f"✅ 백업에서 복원 완료: {backup_path}")
            return True

        except Exception as e:
            print(f"❌ 복원 실패: {str(e)}")
            return False

    def get_update_history(self, limit: int = 10) -> list:
        """최근 업데이트 히스토리 조회"""
        try:
            response = requests.get(f"{self.api_url}/commits/main?per_page={limit}", timeout=10)
            response.raise_for_status()

            commits = response.json()
            history = []

            for commit in commits:
                history.append({
                    'hash': commit['sha'][:7],
                    'message': commit['commit']['message'].split('\n')[0],
                    'author': commit['commit']['author']['name'],
                    'date': commit['commit']['committer']['date'],
                    'url': commit['html_url']
                })

            return history

        except Exception as e:
            print(f"⚠️ 업데이트 히스토리 조회 실패: {str(e)}")
            return []

    def cleanup_old_backups(self, keep_count: int = 5):
        """오래된 백업 정리"""
        try:
            backup_dirs = [d for d in self.backup_dir.iterdir()
                          if d.is_dir() and d.name.startswith('xlt_backup_')]

            # 날짜순 정렬 (최신 순)
            backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # 지정된 개수를 초과하는 백업 삭제
            for old_backup in backup_dirs[keep_count:]:
                shutil.rmtree(old_backup)
                print(f"🗑️ 오래된 백업 삭제: {old_backup.name}")

        except Exception as e:
            print(f"⚠️ 백업 정리 실패: {str(e)}")


def check_updates_on_startup():
    """시스템 시작 시 업데이트 확인"""
    updater = XLTUpdater()

    try:
        print("🔍 업데이트 확인 중...")
        update_info = updater.check_for_updates()

        if update_info.get('error'):
            print(f"⚠️ 업데이트 확인 실패: {update_info['error']}")
            return False

        if update_info['update_available']:
            behind = update_info.get('behind_commits', 0)
            remote = update_info['remote']

            print(f"🎉 새로운 업데이트 발견!")
            print(f"   현재 버전: {update_info['current']['short_hash']}")
            print(f"   최신 버전: {remote['short_hash']}")
            print(f"   뒤처진 커밋: {behind}개")
            print(f"   최신 변경: {remote['message']}")
            print(f"   웹 인터페이스에서 업데이트할 수 있습니다: http://localhost:5004")
            return True
        else:
            print("✅ 최신 버전을 사용 중입니다!")
            return False

    except Exception as e:
        print(f"⚠️ 업데이트 확인 중 오류: {str(e)}")
        return False


if __name__ == "__main__":
    # 테스트 실행
    updater = XLTUpdater()
    update_info = updater.check_for_updates()

    if update_info['update_available']:
        print("업데이트 가능!")
        print(f"현재: {update_info['current']['short_hash']}")
        print(f"최신: {update_info['remote']['short_hash']}")
    else:
        print("최신 버전 사용 중!")