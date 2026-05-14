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

    def get_current_version(self) -> Optional[Dict[str, str]]:
        """현재 로컬 버전 정보 조회"""
        try:
            os.chdir(self.project_root)

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
                'branch': self._get_current_branch()
            }
        except Exception as e:
            print(f"⚠️ 현재 버전 정보 조회 실패: {str(e)}")
            return None

    def get_remote_version(self) -> Optional[Dict[str, str]]:
        """GitHub 원격 저장소 최신 버전 정보 조회"""
        try:
            # GitHub API로 최신 커밋 정보 조회
            response = requests.get(f"{self.api_url}/commits/main", timeout=10)
            response.raise_for_status()

            commit_data = response.json()

            return {
                'hash': commit_data['sha'],
                'short_hash': commit_data['sha'][:7],
                'message': commit_data['commit']['message'].split('\n')[0],
                'date': commit_data['commit']['committer']['date'],
                'author': commit_data['commit']['author']['name'],
                'url': commit_data['html_url']
            }
        except Exception as e:
            print(f"⚠️ 원격 버전 정보 조회 실패: {str(e)}")
            return None

    def check_for_updates(self) -> Dict[str, any]:
        """업데이트 확인"""
        current = self.get_current_version()
        remote = self.get_remote_version()

        if not current or not remote:
            return {
                'update_available': False,
                'error': '버전 정보 조회 실패',
                'current': current,
                'remote': remote
            }

        update_available = current['hash'] != remote['hash']

        result = {
            'update_available': update_available,
            'current': current,
            'remote': remote,
            'behind_commits': 0
        }

        if update_available:
            # 뒤처진 커밋 수 계산
            result['behind_commits'] = self._count_behind_commits()

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
        """업데이트 실행"""
        update_log = []

        try:
            os.chdir(self.project_root)

            # 1. 백업 생성
            backup_path = None
            if create_backup:
                backup_path = self.create_backup()
                update_log.append(f"백업 생성: {backup_path}")

            # 2. 로컬 변경사항 확인
            if self.has_local_changes():
                # 로컬 변경사항 임시 저장
                subprocess.run(['git', 'stash', 'push', '-m', f'Auto-stash before update {datetime.now()}'],
                              capture_output=True, check=True)
                update_log.append("로컬 변경사항 임시 저장")

            # 3. 원격 저장소에서 최신 버전 가져오기
            subprocess.run(['git', 'fetch', 'origin', 'main'],
                          capture_output=True, check=True)
            update_log.append("원격 저장소 정보 업데이트")

            # 4. 메인 브랜치로 체크아웃
            subprocess.run(['git', 'checkout', 'main'],
                          capture_output=True, check=True)
            update_log.append("메인 브랜치 체크아웃")

            # 5. 최신 코드로 업데이트
            result = subprocess.run(['git', 'pull', 'origin', 'main'],
                                  capture_output=True, text=True, check=True)
            update_log.append("최신 코드 다운로드 완료")

            # 6. 의존성 업데이트 확인
            if (self.project_root / "requirements.txt").exists():
                try:
                    subprocess.run(['pip', 'install', '-r', 'requirements.txt'],
                                  capture_output=True, check=True)
                    update_log.append("의존성 패키지 업데이트 완료")
                except:
                    update_log.append("⚠️ 의존성 업데이트 실패 (수동 확인 필요)")

            return {
                'success': True,
                'backup_path': backup_path,
                'update_log': update_log,
                'message': '업데이트가 성공적으로 완료되었습니다!'
            }

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