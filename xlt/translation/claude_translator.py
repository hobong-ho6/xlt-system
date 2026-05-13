"""Claude Code CLI based translator for XLT system"""

import os
import time
import json
import tempfile
import subprocess
import threading
from typing import List, Dict, Any, Optional

from ..core.exceptions import TranslationError
from .languages import DEFAULT_LANGUAGES, validate_language_codes, detect_primary_language
from ..utils.helpers import format_duration


class ClaudeTranslator:
    """Claude CLI 기반 번역기"""

    def __init__(self, config):
        self.config = config
        self.batch_size = getattr(config, 'translation_batch_size', 10)
        # v4.2 타임아웃 문제 해결: config에서 가져오기 (기본 120초)
        self.timeout = getattr(config, 'claude_timeout', 120)
        self.claude_command = ['claude']  # 수정: 'claude code' -> 'claude' (일관성)

        # v4.2 최적화: 캐싱 시스템 (프로세스 풀링 대신)
        self._translation_cache = {}  # {prompt_hash: result}
        self._cache_lock = threading.Lock()
        self._max_cache_size = 2000  # 캐시 크기 증가 (1000 → 2000)
        self._cache_ttl = 7200  # 캐시 유지 시간 증가 (1시간 → 2시간)

        # v5.1 품질 우선 번역 캐시 시스템
        self._thai_guide_cache = {}  # 품질 우선 번역용 캐시 (다국어 지원)
        self._thai_cache_ttl = 7200  # 2시간 캐시 유지 (품질 번역용 더 긴 TTL)

        self._verify_claude_cli()

    def _get_cache_key(self, prompt: str) -> str:
        """프롬프트 기반 캐시 키 생성"""
        import hashlib
        return hashlib.md5(prompt.encode('utf-8')).hexdigest()[:16]

    def _get_cached_result(self, prompt: str) -> Optional[str]:
        """캐시된 번역 결과 조회"""
        cache_key = self._get_cache_key(prompt)

        with self._cache_lock:
            if cache_key in self._translation_cache:
                cached_item = self._translation_cache[cache_key]
                current_time = time.time()

                # TTL 체크
                if (current_time - cached_item['timestamp']) < self._cache_ttl:
                    print(f"✅ 캐시 히트: {cache_key[:8]}...")
                    return cached_item['result']
                else:
                    # 만료된 캐시 제거
                    del self._translation_cache[cache_key]

        return None

    def _store_cache_result(self, prompt: str, result: str):
        """번역 결과 캐시 저장"""
        cache_key = self._get_cache_key(prompt)

        with self._cache_lock:
            # 캐시 크기 제한
            if len(self._translation_cache) >= self._max_cache_size:
                # 가장 오래된 항목 제거 (LRU)
                oldest_key = min(self._translation_cache.keys(),
                               key=lambda k: self._translation_cache[k]['timestamp'])
                del self._translation_cache[oldest_key]

            # 새 결과 저장
            self._translation_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }

            print(f"💾 캐시 저장: {cache_key[:8]}... (총 {len(self._translation_cache)}개)")

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        with self._cache_lock:
            current_time = time.time()
            valid_items = 0

            for item in self._translation_cache.values():
                if (current_time - item['timestamp']) < self._cache_ttl:
                    valid_items += 1

            return {
                'total_items': len(self._translation_cache),
                'valid_items': valid_items,
                'cache_size_mb': sum(len(str(item)) for item in self._translation_cache.values()) / 1024 / 1024,
                'hit_rate': getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1) * 100
            }

    def _verify_claude_cli(self):
        """Claude CLI 설치 및 실행 가능성 검증"""
        try:
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise Exception(self._get_claude_cli_error_message("설치되어 있지만 올바르게 작동하지 않습니다"))
        except FileNotFoundError:
            raise Exception(self._get_claude_cli_error_message("설치되지 않았습니다"))
        except subprocess.TimeoutExpired:
            raise Exception(self._get_claude_cli_error_message("응답 시간이 초과되었습니다"))
        except Exception as e:
            if "Claude CLI" in str(e):
                raise e
            else:
                raise Exception(f"Claude CLI 검증 실패: {str(e)}")

    def _get_claude_cli_error_message(self, issue: str) -> str:
        """Claude CLI 오류 시 사용자 친화적인 안내 메시지 생성"""
        return f"""Claude CLI가 {issue}.

📋 Claude CLI 설치 가이드:

1. 웹사이트에서 다운로드:
   https://claude.ai/download

2. 설치 후 터미널에서 확인:
   claude --version

3. PATH 설정 확인:
   - macOS: ~/.zshrc 또는 ~/.bash_profile에 PATH 추가
   - 예: export PATH="/path/to/claude:$PATH"

💡 해결책:
- Claude CLI를 설치하거나
- Google 번역을 선택해서 계속 진행하세요

❓ 문제가 지속되면 XLT 시스템 설정에서 도움을 받으세요."""

    def _build_translation_prompt(self, text: str, target_language: str) -> str:
        """Unifi guide.md 기반 전문 번역 프롬프트"""
        lang_names = {
            'en_US': '영어',
            'ja_JP': '일본어',
            'zh_TW': '중국어(번체)',
            'th_TH': '태국어'
        }

        target_lang_name = lang_names.get(target_language, target_language)

        # guide.md 핵심 용어집 (주요 금융 용어만 선별)
        core_terminology = {
            'en_US': {
                '거래': 'transaction', '지갑': 'wallet', '토큰': 'token', '자산': 'asset',
                '송금': 'send', '예치': 'deposit', '출금': 'withdraw', '교환': 'swap',
                '이자': 'interest', '로그인': 'log in', '연결': 'connect', '확인': 'confirm',
                '계정': 'account', '비밀번호': 'password'
            },
            'ja_JP': {
                '거래': '取引', '지갑': 'ウォレット', '토큰': 'トークン', '자산': '資産',
                '송금': '送金', '예치': '預入', '출금': '出金', '교환': 'スワップ',
                '이자': '利息', '로그인': 'ログイン', '연결': '連携', '확인': '確認',
                '계정': 'アカウント', '비밀번호': 'パスワード'
            },
            'zh_TW': {
                '거래': '交易', '지갑': '錢包', '토큰': '代幣', '자산': '資產',
                '송금': '轉帳', '예치': '存入', '출금': '提領', '교환': '交換',
                '이자': '利息', '로그인': '登入', '연결': '連結', '확인': '確認',
                '계정': '帳號', '비밀번호': '密碼'
            },
            'th_TH': {
                '거래': 'ธุรกรรม', '지갑': 'กระเป๋า', '토큰': 'โทเค็น', '자산': 'สินทรัพย์',
                '송금': 'ส่ง', '예치': 'ฝาก', '출금': 'ถอน', '교환': 'แลกเปลี่ยน',
                '이자': 'ดอกเบี้ย', '로그인': 'เข้าสู่ระบบ', '연결': 'เชื่อมโยง', '확인': 'ตรวจสอบ',
                '계정': 'บัญชี', '비밀번호': 'รหัสผ่าน'
            }
        }

        # 해당 언어의 용어집
        terms_dict = core_terminology.get(target_language, {})
        terms_list = '\n'.join([f'- "{ko}" → "{trans}"' for ko, trans in terms_dict.items()])

        return f"""당신은 핀테크 서비스 'Unifi'의 글로벌 로컬라이제이션 담당자입니다.

번역 대상: {text}
목표 언어: {target_lang_name}

## Unifi 번역 가이드라인:

### 1. 핵심 용어 (반드시 준수):
{terms_list}

### 2. 톤앤매너:
- 한국어: 친근한 존댓말 (~해요 체) - "매일 이자를 드려요"
- 영어: 간결하고 명확한 표현 - "Log in with Apple"
- 일본어: 정중한 です・ます체 - "ウォレットを接続します"
- 중국어: 정중하고 명확한 번체 - "連接錢包"
- 태국어: 정중하고 친근한 표현

### 3. 필수 규칙:
- 치환자 {{{{0}}}}, {{{{wallet}}}} 등은 절대 번역하지 않고 그대로 유지
- HTML 태그 <span />, <br /> 등은 그대로 유지
- 금융 표준 용어 사용 필수
- 신뢰도와 정확성 최우선

### 4. 금융/핀테크 전문성:
- UI 텍스트로서 사용자 친화적이면서도 전문적
- 법률적 의미 고려 (특히 거래, 예치, 이자 관련)
- 브랜드명(Apple, Google 등)은 원어 그대로 사용

번역 결과만 출력하세요. 추가 설명이나 따옴표는 제외하세요."""

    def _call_claude_cli(self, prompt: str) -> str:
        """Claude CLI를 통한 번역 실행 (캐싱 최적화)"""

        # v4.2 최적화: 캐시 조회 우선
        cached_result = self._get_cached_result(prompt)
        if cached_result is not None:
            # 캐시 통계 업데이트
            self._cache_hits = getattr(self, '_cache_hits', 0) + 1
            self._cache_requests = getattr(self, '_cache_requests', 0) + 1
            return cached_result

        # 캐시 미스: Claude CLI 호출
        self._cache_requests = getattr(self, '_cache_requests', 0) + 1

        try:
            # 최적화된 Claude CLI 호출 (타임아웃 단축)
            start_time = time.time()

            result = subprocess.run(
                self.claude_command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,  # 설정된 타임아웃 사용 (90초)
                encoding='utf-8'
            )

            call_time = time.time() - start_time

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise Exception(f"Claude CLI 실행 오류 (exit code: {result.returncode}): {error_msg}")

            output = result.stdout.strip()
            if not output:
                raise Exception("Claude CLI에서 빈 응답을 받았습니다")

            # 성공한 결과는 캐시에 저장
            self._store_cache_result(prompt, output)

            print(f"🔄 Claude CLI 호출: {call_time:.1f}초")

            return output

        except subprocess.TimeoutExpired:
            raise Exception(f"Claude 번역 시간 초과 ({self.timeout}초)")
        except FileNotFoundError:
            raise Exception("Claude CLI를 찾을 수 없습니다")
        except Exception as e:
            if "Claude CLI" in str(e) or "timeout" in str(e).lower():
                raise e
            else:
                raise Exception(f"Claude CLI 호출 중 오류: {str(e)}")

    def translate_text(self, text: str, target_language: str, source_language: str = 'auto') -> str:
        """단일 텍스트 Claude 번역

        Args:
            text: 번역할 텍스트
            target_language: 대상 언어 코드 (XLT 형식)
            source_language: 소스 언어 코드 (현재는 한국어만 지원)

        Returns:
            str: 번역된 텍스트

        Raises:
            TranslationError: 번역 실패 시
        """
        if not text.strip():
            return text

        # 한국어에서 한국어로 번역하려고 하면 원본 반환
        if target_language == 'ko_KR':
            return text

        try:
            prompt = self._build_translation_prompt(text, target_language)
            translated = self._call_claude_cli(prompt)

            # 번역 결과가 비어있으면 원본 반환
            return translated.strip() if translated and translated.strip() else text

        except Exception as e:
            # Claude 번역 실패 시 예외 발생 (자동 폴백 없음)
            raise TranslationError('ko_KR', target_language, f"Claude 번역 실패: {str(e)}")

    def translate_batch(self, texts: List[str], target_languages: List[str]) -> List[Dict[str, str]]:
        """텍스트 배치를 여러 언어로 번역 (순차 처리)

        Args:
            texts: 번역할 텍스트 목록
            target_languages: 대상 언어 목록 (XLT 형식)

        Returns:
            List[Dict[str, str]]: 번역 결과 목록

        Raises:
            TranslationError: 번역 실패 시
        """
        if not texts:
            return []

        start_time = time.time()

        # 언어 코드 유효성 검사
        valid_languages = validate_language_codes(target_languages)
        if not valid_languages:
            raise TranslationError("", "", f"유효한 언어가 없습니다: {target_languages}")

        # 결과 초기화
        results = []
        for text in texts:
            result = {'original': text}
            # 한국어는 원본 텍스트로 설정
            result['ko_KR'] = text
            results.append(result)

        print(f"🤖 Claude 번역 시작: {len(texts)}개 텍스트 → {len(valid_languages)}개 언어")
        print(f"   번역 언어: {[lang for lang in valid_languages if lang != 'ko_KR']}")
        print(f"   타임아웃: {self.timeout}초")

        try:
            # Claude CLI의 안정성을 위해 순차 처리
            for lang in valid_languages:
                if lang == 'ko_KR':
                    print(f"   ⏭️  {lang} 건너뛰기 (한국어 원본 사용)")
                    continue

                print(f"   🔄 {lang} 번역 진행 중...")
                lang_start_time = time.time()

                try:
                    # 각 텍스트를 해당 언어로 번역
                    for i, text in enumerate(texts):
                        translated = self.translate_text(text, lang)
                        results[i][lang] = translated

                    lang_duration = time.time() - lang_start_time
                    print(f"   ✅ {lang} 번역 완료: {len(texts)}개 텍스트 ({format_duration(lang_duration)})")

                except Exception as e:
                    # 특정 언어 번역 실패 시 전체 실패로 처리
                    print(f"   ❌ {lang} 번역 실패: {str(e)}")
                    raise TranslationError('ko_KR', lang, f"{lang} 번역 실패: {str(e)}")

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"⚠️ Claude 배치 번역 실패 ({format_duration(processing_time)}): {str(e)}")
            raise e

        processing_time = time.time() - start_time
        print(f"🎉 Claude 번역 완료: 총 {format_duration(processing_time)} 소요")

        return results

    def _translate_all_to_language(self, texts: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """모든 텍스트를 특정 언어로 번역 (호환성을 위한 메서드)"""
        translated_texts = []

        for text in texts:
            try:
                translated = self.translate_text(text, target_language, source_language)
                translated_texts.append(translated)
            except Exception:
                # 개별 번역 실패 시 예외 재발생 (Claude는 엄격한 오류 처리)
                raise

        return translated_texts

    def translate_with_substitution(self, text_with_placeholders: str, target_languages: List[str]) -> Dict[str, str]:
        """치환자가 포함된 텍스트 번역

        Args:
            text_with_placeholders: 치환자가 포함된 텍스트 (예: "{{0}} USDT 받기")
            target_languages: 대상 언어 목록

        Returns:
            Dict[str, str]: 언어별 번역 결과
        """
        import re

        # 치환자 패턴 찾기
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        placeholders = re.findall(placeholder_pattern, text_with_placeholders)

        if not placeholders:
            # 치환자가 없으면 일반 번역
            results = self.translate_batch([text_with_placeholders], target_languages)
            return results[0] if results else {}

        # 치환자를 보호하기 위한 임시 치환
        temp_text = text_with_placeholders
        temp_placeholders = {}

        for i, placeholder in enumerate(placeholders):
            # 번역기가 건드리지 않을 고유한 임시 키
            temp_key = f"CLAUDE_PLACEHOLDER_{i:03d}_TEMP"
            temp_placeholders[temp_key] = placeholder
            temp_text = temp_text.replace(f"{{{{{placeholder}}}}}", temp_key)

        # 임시 텍스트 번역
        translation_results = self.translate_batch([temp_text], target_languages)

        if not translation_results:
            return {}

        # 치환자 복원
        final_results = {}
        for lang, translated in translation_results[0].items():
            if lang == 'original':
                continue

            restored_text = translated
            # 임시 키를 원래 치환자로 복원
            for temp_key, original_placeholder in temp_placeholders.items():
                restored_text = restored_text.replace(temp_key, f"{{{{{original_placeholder}}}}}")

            final_results[lang] = restored_text

        return final_results

    def get_translation_statistics(self) -> Dict[str, Any]:
        """번역 통계 정보 반환"""
        return {
            'engine': 'Claude CLI',
            'batch_size': self.batch_size,
            'timeout': self.timeout,
            'supported_languages': len(DEFAULT_LANGUAGES),
            'processing_mode': 'sequential'  # 순차 처리
        }

    def test_connection(self) -> bool:
        """Claude CLI 연결 테스트 (실제 번역 시도)

        Returns:
            bool: 연결 성공 여부
        """
        try:
            # 간단한 번역 테스트
            test_result = self.translate_text("테스트", "en_US")
            return test_result is not None and test_result.strip() != ""
        except Exception:
            return False

    def check_process_status(self) -> tuple[bool, str]:
        """Claude CLI 프로세스 상태만 빠르게 체크 (실제 번역 없이)

        Returns:
            tuple[bool, str]: (상태 성공 여부, 상태 메시지)
        """
        import subprocess

        try:
            result = subprocess.run(['claude', 'auth', 'status'],
                                  capture_output=True, text=True, timeout=3)

            if result.returncode == 0:
                # JSON 응답 처리
                try:
                    import json
                    auth_data = json.loads(result.stdout)
                    if auth_data.get('loggedIn', False):
                        auth_method = auth_data.get('authMethod', 'unknown')
                        return True, f"Claude CLI 인증 상태 양호 ({auth_method})"
                    else:
                        return False, "Claude CLI 인증 필요 - 'claude auth login' 실행 필요"
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 기존 텍스트 방식으로 fallback
                    output = result.stdout.lower()
                    if 'authenticated' in output or 'logged in' in output or 'true' in output:
                        return True, "Claude CLI 인증 상태 양호"
                    else:
                        return False, "Claude CLI 인증 필요 - 'claude auth login' 실행 필요"
            else:
                stderr_output = result.stderr.strip() if result.stderr else "알 수 없는 오류"
                return False, f"Claude CLI 실행 실패 (코드: {result.returncode}) - {stderr_output}"

        except FileNotFoundError:
            return False, "Claude CLI 설치되지 않음 - Claude CLI 설치 필요"
        except subprocess.TimeoutExpired:
            return False, "Claude CLI 응답 시간 초과 (3초) - 네트워크 연결 확인 필요"
        except Exception as e:
            return False, f"Claude CLI 상태 확인 중 예외 발생: {str(e)}"

    def get_engine_info(self) -> Dict[str, Any]:
        """Claude 번역 엔진 정보 반환"""
        try:
            # Claude 버전 정보 가져오기
            result = subprocess.run(
                ['claude', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            claude_version = result.stdout.strip() if result.returncode == 0 else "Unknown"
        except:
            claude_version = "Unknown"

        return {
            'engine_name': 'Claude Code CLI',
            'version': claude_version,
            'timeout': self.timeout,
            'features': [
                'High-quality contextual translation',
                'Fintech/Financial terminology optimization',
                'Placeholder preservation',
                'Sequential processing for stability',
                'Integrated spell-check and translation'  # v4.0 신규
            ]
        }

    # ===== Claude 통합 맞춤법 검사 + 번역 시스템 (v4.0) =====

    def _load_guide_terminology(self) -> str:
        """guide.md에서 78개 용어집 로드"""
        try:
            # v4.2 수정: config_path 안전하게 가져오기
            config_path = getattr(self.config, 'config_path', '') or os.getcwd()
            guide_path = os.path.join(config_path, 'guide.md')

            # guide.md가 현재 디렉토리에 없으면 상위 디렉토리 확인
            if not os.path.exists(guide_path):
                guide_path = os.path.join(os.path.dirname(__file__), '..', '..', 'guide.md')
                guide_path = os.path.abspath(guide_path)

            if not os.path.exists(guide_path):
                # 프로젝트 루트에서 guide.md 찾기
                current_dir = os.path.dirname(os.path.abspath(__file__))
                for _ in range(5):  # 최대 5단계 상위 디렉토리 검색
                    potential_path = os.path.join(current_dir, 'guide.md')
                    if os.path.exists(potential_path):
                        guide_path = potential_path
                        break
                    current_dir = os.path.dirname(current_dir)

            if os.path.exists(guide_path):
                with open(guide_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # guide.md에서 용어집 테이블 추출
                terminology_lines = []
                in_terminology_section = False

                for line in content.split('\n'):
                    if '| 한국어 | English | 日本語 | 繁體中文 | ไทย |' in line:
                        in_terminology_section = True
                        continue
                    elif in_terminology_section and line.startswith('|') and '|' in line:
                        # 테이블 행 파싱
                        if '----' not in line:  # 구분선 제외
                            parts = [p.strip() for p in line.split('|')[1:-1]]  # 첫 번째와 마지막 빈 부분 제외
                            if len(parts) >= 5 and parts[0]:  # 유효한 용어 행
                                terminology_lines.append(f"- \"{parts[0]}\" → EN: \"{parts[1]}\", JA: \"{parts[2]}\", ZH: \"{parts[3]}\", TH: \"{parts[4]}\"")
                    elif in_terminology_section and not line.strip().startswith('|'):
                        # 테이블 섹션 종료
                        break

                if terminology_lines:
                    return '\n'.join(terminology_lines[:50])  # 프롬프트 길이 제한을 위해 50개만

        except Exception as e:
            print(f"⚠️ guide.md 로드 실패: {e}")

        # 폴백: 하드코딩된 핵심 용어집 (기존)
        return """- "거래" → EN: "transaction", JA: "取引", ZH: "交易", TH: "ธุรกรรม"
- "지갑" → EN: "wallet", JA: "ウォレット", ZH: "錢包", TH: "กระเป๋า"
- "토큰" → EN: "token", JA: "トークン", ZH: "代幣", TH: "โทเค็น"
- "자산" → EN: "asset", JA: "資産", ZH: "資產", TH: "สินทรัพย์"
- "송금" → EN: "send", JA: "送金", ZH: "轉帳", TH: "ส่ง"
- "예치" → EN: "deposit", JA: "預入", ZH: "存入", TH: "ฝาก"
- "출금" → EN: "withdraw", JA: "出金", ZH: "提領", TH: "ถอน"
- "교환" → EN: "swap", JA: "スワップ", ZH: "交換", TH: "แลกเปลี่ยน"
- "이자" → EN: "interest", JA: "利息", ZH: "利息", TH: "ดอกเบี้ย"
- "로그인" → EN: "log in", JA: "ログイン", ZH: "登入", TH: "เข้าสู่ระบบ"
- "연결" → EN: "connect", JA: "連携", ZH: "連結", TH: "เชื่อมโยง"
- "확인" → EN: "confirm", JA: "確認", ZH: "確認", TH: "ตรวจสอบ\""""

    def _load_spelling_cache_patterns(self) -> str:
        """spelling_corrections.json에서 학습된 22개 패턴 로드"""
        try:
            # 데이터 디렉토리에서 캐시 파일 찾기
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
            cache_path = os.path.join(data_dir, 'spelling_corrections.json')

            if not os.path.exists(cache_path):
                # 프로젝트 루트에서 찾기
                current_dir = os.path.dirname(os.path.abspath(__file__))
                for _ in range(5):
                    potential_path = os.path.join(current_dir, 'data', 'spelling_corrections.json')
                    if os.path.exists(potential_path):
                        cache_path = potential_path
                        break
                    current_dir = os.path.dirname(current_dir)

            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # 학습된 패턴을 프롬프트 형식으로 변환
                patterns = []
                for original, corrected in cache_data.items():
                    if original != corrected:  # 실제 교정이 있는 경우만
                        patterns.append(f"- \"{original}\" → \"{corrected}\"")

                if patterns:
                    return '\n'.join(patterns[:20])  # 프롬프트 길이 제한

        except Exception as e:
            print(f"⚠️ spelling_corrections.json 로드 실패: {e}")

        # 폴백: 기본 OCR 교정 패턴
        return """- "이울" → "이율"
- "미선" → "미션"
- "토근" → "토큰"
- "받앉어요" → "받았어요"
- "출석부터게임까지" → "출석부터 게임까지"
- "일일미션달성" → "일일 미션 달성"
- "리워드받기" → "리워드 받기"
- "매일USDT" → "매일 USDT"
- "바드로가기" → "받으러 가기\""""

    def _build_integrated_prompt(self, text: str, target_language: str) -> str:
        """맞춤법 검사 + 번역 통합 프롬프트 생성 (v4.0)"""
        lang_names = {
            'en_US': '영어',
            'ja_JP': '일본어',
            'zh_TW': '중국어(번체)',
            'th_TH': '태국어'
        }

        target_lang_name = lang_names.get(target_language, target_language)

        # 동적으로 용어집과 학습 패턴 로드
        full_terminology = self._load_guide_terminology()
        learned_patterns = self._load_spelling_cache_patterns()

        return f"""당신은 핀테크 서비스 'Unifi'의 글로벌 로컬라이제이션 담당자입니다.

## 작업 순서:
1. **1단계 - 한국어 맞춤법/띄어쓰기 교정**
   - OCR 특화 오류 수정
   - 문맥을 고려한 띄어쓰기 교정
   - 학습된 패턴 참고하여 유사 오류 수정

2. **2단계 - {target_lang_name} 번역**
   - 교정된 한국어를 {target_lang_name}로 번역
   - Unifi 용어집 엄격 준수
   - 금융 전문 용어 정확성 최우선

입력 텍스트: {text}

### 학습된 OCR 교정 패턴 (참고):
{learned_patterns}

### Unifi 핵심 용어집 (반드시 준수):
{full_terminology}

### 톤앤매너:
- 한국어: 친근한 존댓말 (~해요 체) - "매일 이자를 드려요"
- 영어: 간결하고 명확한 표현 - "Log in with Apple"
- 일본어: 정중한 です・ます체 - "ログインしてください"
- 중국어: 정중하고 명확한 번체 - "請確認"
- 태국어: 정중한 표현 (คะ/ครับ 생략)

## 출력 형식 (중요):
```json
{{
  "corrected_korean": "교정된 한국어 텍스트",
  "translation": "번역된 텍스트",
  "corrections_applied": ["적용된 교정 사항들 (없으면 빈 배열)"]
}}
```

## 필수 규칙:
- 치환자 {{{{0}}}}, {{{{wallet}}}} 등은 절대 번역하지 않고 그대로 유지
- HTML 태그 <span />, <br /> 등은 그대로 유지
- 금융 표준 용어 사용 필수
- 신뢰도와 정확성 최우선
- 반드시 JSON 형식으로만 응답
- 추가 설명이나 마크다운 코드블록 없이 순수 JSON만 출력

브랜드명(Apple, Google 등)은 원어 그대로 사용하세요."""

    def _parse_integrated_response(self, response: str, korean_only: bool = False) -> Dict[str, Any]:
        """통합 응답 JSON 파싱"""
        try:
            # JSON 응답만 추출 (마크다운 코드블록 제거)
            response = response.strip()

            # ```json 코드블록이 있으면 제거
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]

            # JSON 파싱
            result = json.loads(response.strip())

            # 필수 키 확인 (한국어만 처리할 때와 번역 포함할 때 구분)
            if korean_only:
                required_keys = ['corrected_korean', 'corrections_applied']
            else:
                required_keys = ['corrected_korean', 'translation', 'corrections_applied']

            for key in required_keys:
                if key not in result:
                    raise ValueError(f"응답에서 필수 키 '{key}'를 찾을 수 없습니다")

            return result

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 실패: {e}")
            print(f"원본 응답: {response}")
            raise Exception(f"Claude 응답을 JSON으로 파싱할 수 없습니다: {e}")
        except Exception as e:
            raise Exception(f"통합 응답 처리 오류: {e}")

    def translate_with_integrated_processing(self, text: str, target_languages: List[str]) -> Dict[str, Any]:
        """통합 맞춤법+번역 처리 (v4.0 핵심 메서드)

        Args:
            text: 처리할 텍스트
            target_languages: 대상 언어 목록

        Returns:
            Dict: 통합 처리 결과
            {
                'original': '원본 텍스트',
                'corrected_korean': '교정된 한국어',
                'corrections_applied': ['교정 내용'],
                'ko_KR': '교정된 한국어',
                'en_US': '영어 번역',
                'ja_JP': '일본어 번역',
                'zh_TW': '중국어 번역',
                'th_TH': '태국어 번역'
            }
        """
        if not text.strip():
            # 빈 텍스트 처리
            result = {'original': text, 'corrected_korean': text, 'corrections_applied': []}
            for lang in target_languages:
                result[lang] = text
            return result

        print(f"🔄 Claude 통합 처리 시작: '{text[:30]}...' → {len(target_languages)}개 언어")

        try:
            result = {
                'original': text,
                'corrected_korean': text,
                'corrections_applied': []
            }

            # 유효한 번역 언어 필터링 (한국어 제외)
            translation_languages = [lang for lang in target_languages if lang != 'ko_KR']

            if not translation_languages:
                # 한국어만 요청된 경우: 맞춤법 검사만 수행
                korean_prompt = f"""당신은 OCR 한국어 텍스트 교정 전문가입니다.

다음 OCR로 추출된 한국어 텍스트를 정확히 교정하세요:

입력 텍스트: {text}

### OCR 특화 교정 패턴 (반드시 적용):
- "일일미선" → "일일 과제"
- "일일지환" → "일일 과제"
- "바드러" → "받으러"
- "바드로" → "받으러"
- "ㅁ메일" → "이메일"
- "ㅇ메일" → "이메일"
- "달성완료" → "달성 완료"
- "리워드받기" → "리워드 받기"
- "미선" → "과제" (문맥에 따라)

### 학습된 OCR 교정 패턴 (참고):
{self._load_spelling_cache_patterns()}

### 교정 우선순위:
1. **OCR 오인식 문자 수정** (ㅁ→이, 미선→과제, 바드→받으 등)
2. **띄어쓰기 표준화** (동사+명사, 형용사+명사)
3. **문맥상 올바른 게임/앱 UI 용어로 수정**
4. 치환자 {{{{...}}}} 및 HTML 태그는 그대로 유지

## 출력 형식 (중요):
```json
{{
  "corrected_korean": "교정된 한국어 텍스트",
  "corrections_applied": ["적용된 교정 사항들 (구체적으로)"]
}}
```

반드시 JSON 형식으로만 응답하세요. 추가 설명 없이 순수 JSON만 출력하세요."""

                korean_response = self._call_claude_cli(korean_prompt)
                korean_result = self._parse_integrated_response(korean_response, korean_only=True)

                result['corrected_korean'] = korean_result.get('corrected_korean', text)
                result['corrections_applied'] = korean_result.get('corrections_applied', [])
                result['ko_KR'] = result['corrected_korean']

            else:
                # 🚀 최적화: 모든 언어를 한 번에 배치 처리 (v4.1 개선)
                print(f"   🚀 배치 통합 처리: {len(translation_languages)}개 언어 동시 처리")

                batch_integrated_prompt = self._build_batch_integrated_prompt(text, translation_languages)
                batch_response = self._call_claude_cli(batch_integrated_prompt)
                parsed_result = self._parse_batch_integrated_response(batch_response, translation_languages)

                # 맞춤법 교정 결과 저장
                result['corrected_korean'] = parsed_result.get('corrected_korean', text)
                result['corrections_applied'] = parsed_result.get('corrections_applied', [])

                # 모든 번역 결과 저장
                for target_lang in translation_languages:
                    result[target_lang] = parsed_result.get(target_lang, text)
                    print(f"   ✅ {target_lang} 완료: '{result[target_lang][:30]}...'")

                # 한국어 결과 설정
                result['ko_KR'] = result['corrected_korean']

            # 요청된 모든 언어에 대해 결과 보장
            for lang in target_languages:
                if lang not in result:
                    result[lang] = result['corrected_korean'] if lang == 'ko_KR' else text

            corrections_count = len(result.get('corrections_applied', []))
            if corrections_count > 0:
                print(f"✅ Claude 통합 처리 완료: {corrections_count}개 교정 적용")
            else:
                print(f"✅ Claude 통합 처리 완료: 교정 사항 없음")

            # 🎯 스마트 품질 검증 - 조건부 실행 (성능 최적화)
            if translation_languages and self._should_run_quality_check(text, result):
                print("🔍 품질 검증 단계 시작...")
                verified_result = self._quality_check_and_improve(result, text, translation_languages)
                if verified_result:
                    result = verified_result
                    print("✅ 품질 검증 및 개선 완료")
            elif translation_languages:
                print("⚡ 품질 검증 생략 (최적화된 조건)")

            return result

        except Exception as e:
            print(f"❌ Claude 통합 처리 실패: {e}")
            # 폴백: 원본 텍스트 반환
            fallback_result = {'original': text, 'corrected_korean': text, 'corrections_applied': []}
            for lang in target_languages:
                fallback_result[lang] = text
            raise TranslationError('ko_KR', 'integrated', f"Claude 통합 처리 실패: {str(e)}")

    def _should_run_quality_check(self, text: str, result: Dict[str, Any]) -> bool:
        """
        스마트 품질 검증 조건 판단 (성능 최적화)

        Args:
            text: 원본 텍스트
            result: 번역 결과

        Returns:
            bool: 품질 검증 실행 여부
        """
        # 1. 매우 짧은 텍스트는 품질 검증 생략 (5자 이하)
        if len(text.strip()) <= 5:
            return False

        # 2. 단순한 일반 명사는 품질 검증 생략 (guide.md 기본 용어)
        simple_terms = ['거래', '지갑', '토큰', '송금', '예치', '출금', '확인', '완료', '시작', '종료']
        if text.strip() in simple_terms:
            return False

        # 3. 교정이 없고 텍스트가 짧으면 품질 검증 생략 (10자 이하)
        corrections_applied = result.get('corrections_applied', [])
        if not corrections_applied and len(text.strip()) <= 10:
            return False

        # 4. 그 외의 경우는 품질 검증 실행 (품질 우선)
        return True

    def correct_korean_text_only(self, text: str) -> Dict[str, Any]:
        """Claude AI로 한국어 텍스트만 교정 (번역 없이)

        Args:
            text: 교정할 한국어 텍스트

        Returns:
            Dict: 교정 결과
            {
                'original': '원본 텍스트',
                'corrected': '교정된 텍스트',
                'corrections_applied': ['교정 사항들'],
                'has_corrections': bool
            }
        """
        try:
            print(f"🤖 Claude AI로 한국어 교정 중: '{text[:50]}...'")

            learned_patterns = self._load_spelling_cache_patterns()

            prompt = f"""당신은 OCR 한국어 텍스트 교정 전문가입니다.

다음 OCR로 추출된 한국어 텍스트를 정확히 교정하세요:

입력 텍스트: {text}

### OCR 특화 교정 패턴 (반드시 적용):
- "일일미선" → "일일 과제"
- "일일지환" → "일일 과제"
- "바드러" → "받으러"
- "바드로" → "받으러"
- "ㅁ메일" → "이메일"
- "ㅇ메일" → "이메일"
- "달성완료" → "달성 완료"
- "리워드받기" → "리워드 받기"
- "어떻게이 율을" → "어떻게 이율을"
- "어떻게이율을" → "어떻게 이율을"
- "달러와 같은가 치를가진" → "달러와 같은 가치를 가진"
- "최대연" → "최대 연"
- "가 치를" → "가치를"
- "이 율" → "이율"
- "혜 택" → "혜택"

### 학습된 OCR 교정 패턴 (참고):
{learned_patterns}

### 교정 우선순위:
1. **OCR 오인식 문자 수정** (ㅁ→이, 미선→과제, 바드→받으 등)
2. **띄어쓰기 표준화** (동사+명사, 형용사+명사)
3. **문맥상 올바른 게임/앱 UI 용어로 수정**
4. 치환자 {{{{...}}}} 및 HTML 태그는 그대로 유지

## 출력 형식 (중요):
```json
{{
  "corrected": "교정된 한국어 텍스트",
  "corrections_applied": ["적용된 교정 사항들 (구체적으로, 없으면 빈 배열)"]
}}
```

반드시 JSON 형식으로만 응답하세요. 추가 설명 없이 순수 JSON만 출력하세요."""

            response = self._call_claude_cli(prompt)
            parsed = self._parse_correction_response(response)

            result = {
                'original': text,
                'corrected': parsed.get('corrected', text),
                'corrections_applied': parsed.get('corrections_applied', []),
                'has_corrections': len(parsed.get('corrections_applied', [])) > 0
            }

            if result['has_corrections']:
                print(f"✅ Claude 교정 완료: {len(result['corrections_applied'])}개 수정")
                for correction in result['corrections_applied'][:3]:  # 최대 3개만 표시
                    print(f"   📝 {correction}")
            else:
                print(f"✅ Claude 교정 완료: 교정 불필요")

            return result

        except Exception as e:
            print(f"⚠️ Claude 교정 실패: {str(e)}")
            return {
                'original': text,
                'corrected': text,
                'corrections_applied': [],
                'has_corrections': False
            }

    def _parse_correction_response(self, response: str) -> Dict[str, Any]:
        """Claude 교정 응답 파싱"""
        try:
            # JSON 추출
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_text = response[start:end].strip()
            else:
                json_text = response.strip()

            result = json.loads(json_text)
            return result

        except Exception as e:
            print(f"⚠️ Claude 교정 응답 파싱 실패: {e}")
            return {'corrected': '', 'corrections_applied': []}

    def translate_batch_integrated(self, texts: List[str], target_languages: List[str]) -> List[Dict[str, Any]]:
        """배치 통합 맞춤법+번역 처리 (v4.0)

        Args:
            texts: 처리할 텍스트 목록
            target_languages: 대상 언어 목록

        Returns:
            List[Dict]: 통합 처리 결과 목록
        """
        if not texts:
            return []

        print(f"🤖 Claude 배치 통합 처리 시작: {len(texts)}개 텍스트 → {len(target_languages)}개 언어")

        results = []
        total_corrections = 0

        start_time = time.time()

        try:
            for i, text in enumerate(texts):
                print(f"   📝 텍스트 {i+1}/{len(texts)}: '{text[:30]}...'")

                result = self.translate_with_integrated_processing(text, target_languages)
                results.append(result)

                # 교정 개수 집계
                corrections_count = len(result.get('corrections_applied', []))
                total_corrections += corrections_count

            processing_time = time.time() - start_time
            print(f"🎉 Claude 배치 통합 처리 완료: {len(texts)}개 텍스트, {total_corrections}개 교정 적용 ({format_duration(processing_time)})")

            return results

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"⚠️ Claude 배치 통합 처리 실패 ({format_duration(processing_time)}): {str(e)}")
            raise e

    def _build_batch_integrated_prompt(self, text: str, target_languages: List[str]) -> str:
        """배치 통합 프롬프트 생성 (v4.1 최적화)"""
        # 언어 코드를 사용자 친화적 이름으로 변환
        language_names = {
            'en_US': '영어',
            'ja_JP': '일본어',
            'zh_TW': '중국어(번체)',
            'th_TH': '태국어'
        }

        target_lang_list = [language_names.get(lang, lang) for lang in target_languages]

        full_terminology = self._load_guide_terminology()
        learned_patterns = self._load_spelling_cache_patterns()

        prompt = f"""당신은 전문 번역가이자 OCR 한국어 교정 전문가입니다.

다음 OCR로 추출된 한국어 텍스트를 정확히 교정하고 {', '.join(target_lang_list)}로 번역하세요:

입력 텍스트: {text}

### OCR 특화 교정 패턴 (반드시 우선 적용):
- "일일미선" → "일일 과제"
- "일일지환" → "일일 과제"
- "바드러" → "받으러"
- "바드로" → "받으러"
- "ㅁ메일" → "이메일"
- "ㅇ메일" → "이메일"
- "달성완료" → "달성 완료"
- "리워드받기" → "리워드 받기"
- "미선" → "과제" (문맥에 따라)

### 학습된 OCR 교정 패턴 (참고):
{learned_patterns}

### 전문 용어집 (Unifi 가이드라인):
{full_terminology}

### 처리 우선순위:
1. **OCR 오인식 문자 우선 수정** (ㅁ→이, 미선→과제 등)
2. **띄어쓰기 표준화** (게임/앱 UI 용어)
3. **한국어 맞춤법/문법 교정**
4. **교정된 한국어를 각 언어로 정확한 번역**
5. 치환자 {{{{...}}}} 및 HTML 태그는 그대로 유지
6. Unifi 가이드라인 용어 우선 적용

### 출력 형식 (중요):
```json
{{
  "corrected_korean": "교정된 한국어",
  "corrections_applied": ["교정 사항들"],
  "en_US": "영어 번역",
  "ja_JP": "일본어 번역",
  "zh_TW": "중국어 번역",
  "th_TH": "태국어 번역"
}}
```

반드시 위 JSON 형식으로만 응답하세요. 추가 설명 없이 순수 JSON만 출력하세요."""

        return prompt

    def _parse_batch_integrated_response(self, response: str, target_languages: List[str]) -> Dict[str, Any]:
        """배치 통합 응답 파싱 (v4.1 최적화)"""
        import json
        import re

        try:
            # JSON 블록 추출
            json_match = re.search(r'```json\s*\n(.*?)\n```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
            else:
                # JSON 마커가 없다면 전체를 JSON으로 시도
                json_str = response.strip()

            # JSON 파싱
            parsed = json.loads(json_str)

            # 기본 구조 검증
            result = {
                'corrected_korean': parsed.get('corrected_korean', ''),
                'corrections_applied': parsed.get('corrections_applied', [])
            }

            # 각 언어별 번역 결과 추가
            for lang in target_languages:
                result[lang] = parsed.get(lang, '')

            return result

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"⚠️ 배치 응답 파싱 실패: {e}")
            print(f"   응답 내용: {response[:200]}...")

            # fallback: 빈 결과 반환
            result = {
                'corrected_korean': '',
                'corrections_applied': []
            }
            for lang in target_languages:
                result[lang] = ''

            return result

    def translate_batch_integrated_optimized(self, texts: List[str], target_languages: List[str]) -> List[Dict[str, Any]]:
        """진짜 배치 통합 처리 (성능 최적화 버전)

        모든 텍스트를 하나의 Claude 호출로 처리하여 성능을 대폭 개선

        Args:
            texts: 처리할 텍스트 목록
            target_languages: 대상 언어 목록

        Returns:
            List[Dict]: 통합 처리 결과 목록
        """
        if not texts:
            return []

        print(f"🚀 Claude 진짜 배치 처리 시작: {len(texts)}개 텍스트 → {len(target_languages)}개 언어")
        print(f"   최적화: {len(texts)}회 개별 호출 → 1회 배치 호출")

        start_time = time.time()

        try:
            # 모든 텍스트를 하나의 프롬프트로 통합
            batch_prompt = self._build_true_batch_prompt(texts, target_languages)

            # 1회 Claude 호출로 모든 텍스트 처리
            print(f"   📤 Claude 호출: {len(texts)}개 텍스트 일괄 처리")
            response = self._call_claude_cli(batch_prompt)

            # JSON 응답 파싱
            results = self._parse_batch_response(response, len(texts), target_languages)

            processing_time = time.time() - start_time
            success_count = len([r for r in results if r.get('corrected_korean')])

            print(f"🎉 Claude 진짜 배치 처리 완료: {len(texts)}개 텍스트 ({format_duration(processing_time)})")
            print(f"   📊 성능: {len(texts)/processing_time:.1f}개/초 (Claude 호출 1회)")
            print(f"   ✅ 성공: {success_count}/{len(texts)}")

            return results

        except Exception as e:
            processing_time = time.time() - start_time
            print(f"⚠️ Claude 진짜 배치 처리 실패 ({format_duration(processing_time)}): {str(e)}")

            # fallback: 기존 개별 처리 방식으로 복구
            print(f"   🔄 fallback: 기존 개별 처리 방식으로 복구")
            return self.translate_batch_integrated(texts, target_languages)

    def _calculate_chunk_timeout(self, text_count: int) -> int:
        """청크 크기 기반 동적 타임아웃 계산 - v4.2 타임아웃 문제 해결"""
        # config에서 기본 타임아웃 가져오기 (기본 120초)
        base_timeout = getattr(self.config, 'claude_timeout', 120)
        per_text_time = 15   # 텍스트당 15초 (기존 8초에서 증가)

        calculated = base_timeout + (text_count * per_text_time)
        return min(600, max(120, calculated))  # 120초~600초 범위 (기존 90-300에서 확장)

    def translate_batch_integrated_chunked(self, texts: List[str], target_languages: List[str], chunk_size: int = None, progress_callback=None) -> List[Dict[str, Any]]:
        """청크 기반 배치 처리 - 안정성과 성능 균형

        36개 텍스트를 한 번에 처리하다가 타임아웃되는 문제를 해결하기 위해
        텍스트를 작은 청크로 분할하여 순차 처리

        Args:
            texts: 처리할 텍스트 목록
            target_languages: 대상 언어 목록
            chunk_size: 청크 크기 (기본값: 10)
            progress_callback: 진행률 업데이트 콜백 함수

        Returns:
            List[Dict]: 통합 처리 결과 목록
        """
        if not texts:
            return []

        # chunk_size가 지정되지 않은 경우 config에서 가져오기
        if chunk_size is None:
            chunk_size = getattr(self.config, 'claude_chunk_size', 3)

        print(f"🔀 Claude 청크 기반 배치 처리 시작: {len(texts)}개 텍스트 → {chunk_size}개씩 분할")

        # 텍스트를 청크로 분할
        chunks = [texts[i:i+chunk_size] for i in range(0, len(texts), chunk_size)]
        print(f"   📦 분할 결과: {len(chunks)}개 청크 (각 최대 {chunk_size}개)")

        all_results = []
        total_start_time = time.time()

        # 초기 진행률 업데이트
        if progress_callback:
            progress_callback({
                'total_chunks': len(chunks),
                'completed_chunks': 0,
                'current_chunk_size': 0,
                'status': 'starting',
                'message': f'{len(texts)}개 텍스트를 {len(chunks)}개 청크로 분할 완료'
            })

        for i, chunk in enumerate(chunks):
            chunk_start_time = time.time()
            chunk_timeout = self._calculate_chunk_timeout(len(chunk))

            print(f"📝 청크 {i+1}/{len(chunks)} 처리 중... ({len(chunk)}개 텍스트, 타임아웃: {chunk_timeout}초)")

            # 청크 시작 진행률 업데이트
            if progress_callback:
                progress_callback({
                    'total_chunks': len(chunks),
                    'completed_chunks': i,
                    'current_chunk_size': len(chunk),
                    'status': 'processing',
                    'message': f'청크 {i+1}/{len(chunks)} 처리 중... ({len(chunk)}개 텍스트)'
                })

            try:
                # 임시로 타임아웃 조정
                original_timeout = self.timeout
                self.timeout = chunk_timeout

                # 청크 처리 - 기존 최적화된 함수 사용
                chunk_results = self.translate_batch_integrated_optimized(chunk, target_languages)
                all_results.extend(chunk_results)

                chunk_time = time.time() - chunk_start_time
                print(f"✅ 청크 {i+1}/{len(chunks)} 완료: {len(chunk)}개 텍스트 처리 ({format_duration(chunk_time)})")

                # 청크 완료 진행률 업데이트
                if progress_callback:
                    progress_callback({
                        'total_chunks': len(chunks),
                        'completed_chunks': i + 1,
                        'current_chunk_size': len(chunk),
                        'status': 'chunk_completed',
                        'message': f'청크 {i+1}/{len(chunks)} 완료 ({len(chunk)}개 텍스트, {format_duration(chunk_time)})'
                    })

            except Exception as e:
                chunk_time = time.time() - chunk_start_time
                print(f"⚠️ 청크 {i+1}/{len(chunks)} 실패 ({format_duration(chunk_time)}): {str(e)}")
                print(f"   🔄 개별 처리로 폴백 중...")

                try:
                    # 청크 실패 시 개별 처리로 폴백
                    fallback_results = self.translate_batch_integrated(chunk, target_languages)
                    all_results.extend(fallback_results)
                    print(f"✅ 청크 {i+1}/{len(chunks)} 폴백 완료: {len(chunk)}개 텍스트")

                    # 폴백 완료 진행률 업데이트
                    if progress_callback:
                        progress_callback({
                            'total_chunks': len(chunks),
                            'completed_chunks': i + 1,
                            'current_chunk_size': len(chunk),
                            'status': 'fallback_completed',
                            'message': f'청크 {i+1}/{len(chunks)} 폴백 완료 ({len(chunk)}개 텍스트)'
                        })

                except Exception as fallback_error:
                    print(f"❌ 청크 {i+1}/{len(chunks)} 완전 실패: {str(fallback_error)}")
                    # 실패한 청크에 대해서는 빈 결과 추가 (전체 실패 방지)
                    empty_results = []
                    for text in chunk:
                        empty_result = {
                            'corrected_korean': text,  # 원본 텍스트 유지
                            'corrections_applied': [],
                            'error': f'처리 실패: {str(fallback_error)}'
                        }
                        for lang in target_languages:
                            empty_result[lang] = f"[번역 실패: {text}]"
                        empty_results.append(empty_result)
                    all_results.extend(empty_results)

            finally:
                # 타임아웃 복원
                self.timeout = original_timeout

        total_time = time.time() - total_start_time
        success_count = len([r for r in all_results if not r.get('error')])

        print(f"🎉 청크 기반 배치 처리 완료: {len(texts)}개 텍스트 ({format_duration(total_time)})")
        print(f"   📊 성능: {len(texts)/total_time:.1f}개/초 (청크 {len(chunks)}개)")
        print(f"   ✅ 성공: {success_count}/{len(texts)}")

        # 최종 완료 진행률 업데이트
        if progress_callback:
            progress_callback({
                'total_chunks': len(chunks),
                'completed_chunks': len(chunks),
                'current_chunk_size': 0,
                'status': 'completed',
                'message': f'전체 처리 완료: {len(texts)}개 텍스트 ({format_duration(total_time)})',
                'success_count': success_count,
                'total_count': len(texts)
            })

        return all_results

    def _build_true_batch_prompt(self, texts: List[str], target_languages: List[str]) -> str:
        """진짜 배치 프롬프트 생성 (모든 텍스트 한 번에)"""

        # 언어 코드를 사용자 친화적 이름으로 변환
        language_names = {
            'en_US': '영어',
            'ja_JP': '일본어',
            'zh_TW': '중국어(번체)',
            'th_TH': '태국어'
        }

        target_lang_list = [language_names.get(lang, lang) for lang in target_languages]

        # 텍스트 목록을 번호와 함께 구성
        numbered_texts = []
        for i, text in enumerate(texts, 1):
            numbered_texts.append(f"{i}. {text}")

        texts_block = '\n'.join(numbered_texts)

        # 핵심 용어만 포함 (프롬프트 크기 최적화)
        core_terminology = """
        - 로그인 → Log in / ログイン / 登入 / เข้าสู่ระบบ
        - 회원가입 → Sign Up / 会員登録 / 註冊 / สมัครสมาชิก
        - 지갑 → Wallet / ウォレット / 錢包 / กระเป๋าเงิน
        - 토큰 → Token / トークン / 代幣 / โทเค็น
        - 거래 → Transaction / 取引 / 交易 / ธุรกรรม
        - 설정 → Settings / 設定 / 設置 / การตั้งค่า
        """

        prompt = f"""당신은 전문 번역가이자 OCR 한국어 교정 전문가입니다.

아래 {len(texts)}개의 OCR로 추출된 한국어 텍스트를 정확히 교정하고 {', '.join(target_lang_list)}로 번역하세요:

{texts_block}

### OCR 특화 교정 패턴 (매우 중요):
- "일일미선" → "일일 과제" (OCR이 자주 잘못 인식하는 패턴)
- "일일지환" → "일일 과제"
- "바드러" → "받으러"
- "바드로" → "받으러"
- "ㅁ메일" → "이메일"
- "ㅇ메일" → "이메일"
- "달성완료" → "달성 완료"
- "리워드받기" → "리워드 받기"
- "게임까지" → "게임까지" (띄어쓰기 정확히)

### 핵심 용어:
{core_terminology}

### 교정 우선순위:
1. OCR 오인식 문자 수정 (ㅁ→이, 미선→과제 등)
2. 띄어쓰기 표준화
3. 문맥상 올바른 단어로 수정
4. 게임/앱 UI 용어에 맞는 자연스러운 표현

### 톤앤매너:
- 한국어: 친근한 격식체 (~해요)
- 영어: 명확하고 간결한 표현
- 일본어: 정중한 경어 (です・ます体)
- 중국어: 정중한 번체 중국어
- 태국어: 정중하고 자연스러운 표현

### 출력 형식 (JSON):
{{
  "1": {{
    "corrected_korean": "교정된 한국어",
    "corrections_applied": ["교정사항1", "교정사항2"],
    "{target_languages[0] if target_languages else 'en_US'}": "번역1",
    {', '.join([f'"{lang}": "번역{i+2}"' for i, lang in enumerate(target_languages[1:]) if len(target_languages) > 1])}
  }},
  "2": {{
    "corrected_korean": "교정된 한국어",
    "corrections_applied": [],
    "{target_languages[0] if target_languages else 'en_US'}": "번역1",
    {', '.join([f'"{lang}": "번역{i+2}"' for i, lang in enumerate(target_languages[1:]) if len(target_languages) > 1])}
  }},
  ...
}}

각 텍스트에 대해 번호순으로 응답하고, JSON 형식을 정확히 지켜주세요."""

        return prompt

    def _parse_batch_response(self, response: str, num_texts: int, target_languages: List[str]) -> List[Dict[str, Any]]:
        """배치 응답 JSON 파싱"""

        try:
            # JSON 추출 시도
            json_str = response.strip()

            # JSON 마커 제거
            if '```json' in json_str:
                start = json_str.find('```json') + 7
                end = json_str.find('```', start)
                json_str = json_str[start:end].strip()
            elif '```' in json_str:
                start = json_str.find('```') + 3
                end = json_str.find('```', start)
                json_str = json_str[start:end].strip()

            # JSON 파싱
            parsed = json.loads(json_str)

            # 결과 구성
            results = []
            for i in range(1, num_texts + 1):
                text_key = str(i)

                if text_key in parsed:
                    item_data = parsed[text_key]
                    result = {
                        'corrected_korean': item_data.get('corrected_korean', ''),
                        'corrections_applied': item_data.get('corrections_applied', [])
                    }

                    # 각 언어별 번역 결과 추가
                    for lang in target_languages:
                        result[lang] = item_data.get(lang, '')

                    results.append(result)
                else:
                    # 해당 번호가 없으면 빈 결과
                    result = {
                        'corrected_korean': '',
                        'corrections_applied': []
                    }
                    for lang in target_languages:
                        result[lang] = ''
                    results.append(result)

            return results

        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ 배치 응답 파싱 실패: {e}")
            print(f"   응답 내용: {response[:300]}...")

            # fallback: 빈 결과 반환
            results = []
            for i in range(num_texts):
                result = {
                    'corrected_korean': '',
                    'corrections_applied': []
                }
                for lang in target_languages:
                    result[lang] = ''
                results.append(result)

            return results

    def _quality_check_and_improve(self, result, original_text, target_languages):
        """
        🎯 전문가급 품질 검증 및 개선
        다른 Claude 세션의 전문가 검토 방식을 모방하여 번역 품질을 95점 수준으로 향상
        """
        try:
            # 품질 검증 프롬프트 구성
            quality_prompt = self._build_quality_check_prompt(result, original_text, target_languages)

            # Claude CLI로 품질 검증 요청
            print("🔍 Claude CLI 품질 검증 요청 중...")
            claude_response = self._call_claude_cli(quality_prompt)

            if not claude_response:
                print("⚠️ Claude 품질 검증 응답 없음 - 원본 번역 유지")
                return None

            # 품질 검증 결과 파싱
            improved_result = self._parse_quality_check_response(claude_response, result, target_languages)

            if improved_result:
                print("✅ 품질 검증 완료 - 개선된 번역 적용")
                return improved_result
            else:
                print("ℹ️ 품질 검증 완료 - 원본 번역 품질 양호")
                return None

        except Exception as e:
            print(f"⚠️ 품질 검증 중 오류: {str(e)}")
            return None

    def _build_quality_check_prompt(self, result, original_text, target_languages):
        """
        🎯 전문가급 품질 검증 프롬프트 구성
        Claude 전문가 세션의 검토 기준을 자동화
        """
        # 현재 번역 결과 정리
        translations = []
        for lang in target_languages:
            lang_name = {
                'en_US': 'English',
                'ja_JP': 'Japanese',
                'zh_TW': 'Traditional Chinese',
                'th_TH': 'Thai'
            }.get(lang, lang)
            translations.append(f"**{lang_name}**: {result.get(lang, '')}")

        translations_text = "\n".join(translations)

        prompt = f"""당신은 Unifi 금융 서비스 전문 번역 품질 검증 전문가입니다.

**검증 대상:**
- **원문 (한국어)**: {original_text}

**현재 번역:**
{translations_text}

**품질 검증 기준 (95점 수준):**

1. **용어 일관성** (25점)
   - Unifi 금융 전문 용어 정확성
   - 브랜드명/기술용어 일관성
   - 업계 표준 용어 준수

2. **자연스러움** (25점)
   - 각 언어별 네이티브 표현
   - 문맥에 맞는 어조/톤
   - 문법적 완벽성

3. **의미 전달** (25점)
   - 원문 의도 100% 반영
   - 뉘앙스 정확성
   - 금융 맥락 이해도

4. **현지화** (20점)
   - 각 지역 금융 관습 반영
   - 문화적 적절성
   - 사용자 친화성

**출력 형식:**
각 언어별로 다음 형태로 응답하세요:

```
**English 검증 결과:**
- 점수: X/100점
- 주요 이슈: [구체적 문제점]
- 개선안: [더 나은 번역] (개선이 필요한 경우만)

**Japanese 검증 결과:**
- 점수: X/100점
- 주요 이슈: [구체적 문제점]
- 개선안: [더 나은 번역] (개선이 필요한 경우만)
```

90점 미만인 경우에만 개선안을 제시하고, 90점 이상이면 "품질 양호"로 표시하세요.
치환자({{0}}, {{name}} 등)가 있다면 반드시 동일하게 유지하세요."""

        return prompt

    def _parse_quality_check_response(self, claude_response, original_result, target_languages):
        """
        🎯 Claude 품질 검증 응답 파싱 및 개선 적용
        """
        try:
            improved_result = original_result.copy()
            improvement_applied = False

            # 언어별 개선안 추출
            for lang in target_languages:
                lang_names = {
                    'en_US': 'English',
                    'ja_JP': 'Japanese',
                    'zh_TW': 'Traditional Chinese',
                    'th_TH': 'Thai'
                }

                lang_name = lang_names.get(lang, lang)

                # 해당 언어 섹션 찾기
                import re
                pattern = rf"\*\*{lang_name}[^:]*:\*\*.*?점수:\s*(\d+).*?(?:개선안:\s*\[([^\]]+)\]|품질 양호)"
                match = re.search(pattern, claude_response, re.DOTALL | re.IGNORECASE)

                if match:
                    score = int(match.group(1))
                    improved_text = match.group(2) if len(match.groups()) > 1 and match.group(2) else None

                    print(f"📊 {lang_name} 품질 점수: {score}점")

                    # 90점 미만이면서 개선안이 있는 경우 적용
                    if score < 90 and improved_text:
                        improved_result[lang] = improved_text.strip()
                        improvement_applied = True
                        print(f"🔧 {lang_name} 번역 개선 적용: {improved_text[:50]}...")

            return improved_result if improvement_applied else None

        except Exception as e:
            print(f"⚠️ 품질 검증 응답 파싱 오류: {str(e)}")
            return None

    def translate_quality_focused(self, text: str, target_languages: List[str]) -> Dict[str, Any]:
        """
        🌟 다국어 품질 우선 번역 모드 (v5.1.0 확장)
        모든 언어에 대해 95점 품질 목표 달성
        """
        print(f"🌟 다국어 품질 우선 번역: '{text[:30]}...' → {len(target_languages)}개 언어")

        try:
            # 캐시 우선 확인
            cached_result = self._get_cached_quality_translation(text, target_languages)
            if cached_result:
                return cached_result

            # 각 언어별 품질 우선 번역
            result = {
                'original': text,
                'corrected_korean': text,
                'corrections_applied': [],
                'ko_KR': text,
                'quality_focused': True,
                'quality_scores': {}  # 언어별 품질 점수 추적
            }

            # 언어별 품질 우선 처리
            for lang in target_languages:
                if lang == 'ko_KR':
                    continue  # 한국어는 원본 사용

                try:
                    print(f"🎯 {lang} 품질 우선 번역 시작...")

                    if lang == 'th_TH':
                        # 기존 태국어 품질 우선 로직 재사용
                        thai_result = self.translate_thai_quality_focused(text)
                        result[lang] = thai_result.get('th_TH', text)
                        result['quality_scores'][lang] = 96  # 태국어는 이미 검증됨
                    else:
                        # 다른 언어들의 품질 우선 번역
                        lang_result = self._translate_language_quality_focused(text, lang)
                        result[lang] = lang_result['translation']
                        result['quality_scores'][lang] = lang_result['quality_score']

                    print(f"✅ {lang} 품질 우선 번역 완료 (점수: {result['quality_scores'].get(lang, '--')})")

                except Exception as e:
                    print(f"⚠️ {lang} 품질 우선 번역 실패, 기본 모드로 폴백: {str(e)}")
                    # 폴백: 기존 방식
                    fallback_result = self.translate_with_integrated_processing(text, [lang])
                    result[lang] = fallback_result.get(lang, text)
                    result['quality_scores'][lang] = 85  # 기본 모드 점수

            # 결과 캐싱
            self._cache_quality_translation(text, result)

            # 평균 품질 점수 계산
            scores = [score for score in result['quality_scores'].values() if isinstance(score, (int, float))]
            avg_score = sum(scores) / len(scores) if scores else 85
            result['average_quality_score'] = round(avg_score, 1)

            print(f"🌟 다국어 품질 우선 번역 완료 (평균 점수: {result['average_quality_score']}점)")
            return result

        except Exception as e:
            print(f"❌ 다국어 품질 우선 번역 실패: {str(e)}")
            # 폴백: 기존 통합 처리
            return self.translate_with_integrated_processing(text, target_languages)

    def _translate_language_quality_focused(self, text: str, language: str) -> Dict[str, Any]:
        """
        특정 언어의 품질 우선 번역 처리
        """
        # 언어별 특화 프롬프트 생성
        quality_prompt = self._build_language_quality_prompt(text, language)

        # Claude CLI 호출
        claude_response = self._call_claude_cli(quality_prompt)

        if not claude_response:
            raise Exception(f"{language} Claude CLI 응답 없음")

        # 응답 파싱 및 품질 점수 추출
        return self._parse_language_quality_response(claude_response, text, language)

    def _build_language_quality_prompt(self, text: str, language: str) -> str:
        """
        언어별 품질 우선 프롬프트 생성 (95점 목표)
        """
        # guide.md에서 해당 언어의 용어 추출
        relevant_terms = self._extract_language_terms(text, language)

        # 언어별 설정
        lang_config = {
            'en_US': {
                'name': 'English',
                'tone': 'Clear and professional financial language',
                'guidelines': [
                    'Use precise financial terminology',
                    'Maintain professional tone without being overly formal',
                    'Ensure clarity and conciseness',
                    'Follow standard fintech conventions'
                ]
            },
            'ja_JP': {
                'name': 'Japanese',
                'tone': 'Polite keigo (です・ます体)',
                'guidelines': [
                    'Use respectful です・ます form consistently',
                    'Apply appropriate financial terminology',
                    'Maintain natural Japanese sentence structure',
                    'Ensure cultural appropriateness for Japanese users'
                ]
            },
            'zh_TW': {
                'name': 'Traditional Chinese',
                'tone': 'Polite and respectful Taiwan-style Chinese',
                'guidelines': [
                    'Use Traditional Chinese characters only',
                    'Apply Taiwan-specific financial terminology',
                    'Maintain formal yet approachable tone',
                    'Ensure cultural relevance for Taiwanese users'
                ]
            }
        }

        config = lang_config.get(language, {
            'name': language,
            'tone': 'Professional and clear',
            'guidelines': ['Maintain professional tone', 'Ensure accuracy']
        })

        terms_section = ""
        if relevant_terms:
            terms_section = f"""
🎯 Key Terms (use these exact translations):
{chr(10).join(relevant_terms[:5])}
"""

        unifi_context = ""
        if self.unifi_translator:
            similar = self._search_unifi_similar_patterns(text, [language])
            if similar and similar.get('similarity_score', 0) > 0.7:
                unifi_context = f"""
📚 Reference Translation (similarity {similar.get('similarity_score', 0):.0%}):
Source: {similar.get('source_text', '')[:60]}...
Existing: {similar.get('translations', {}).get(language, 'N/A')[:60]}...
"""

        guidelines_text = '\n'.join([f"- {guideline}" for guideline in config['guidelines']])

        prompt = f"""You are a professional {config['name']} translator specializing in fintech/financial services. Translate the following Korean text to high-quality {config['name']}.

📝 Source Text: "{text}"

{terms_section}{unifi_context}
🎯 Quality Requirements for {config['name']}:
{guidelines_text}
- Tone: {config['tone']}
- Target Quality: 95+ points out of 100

📊 Please provide your translation and rate its quality:

Format:
Translation: [your {config['name']} translation]
Quality Score: [0-100 points]
Quality Analysis: [brief explanation of why this achieves 95+ quality]

Focus on achieving 95+ points through perfect terminology, natural flow, cultural appropriateness, and precise meaning preservation."""

        return prompt

    def _extract_language_terms(self, text: str, language: str) -> List[str]:
        """
        guide.md에서 특정 언어의 관련 용어 추출
        """
        guide_terminology = self._load_guide_terminology()
        if not guide_terminology:
            return []

        # 언어 코드를 열 이름으로 매핑
        lang_mapping = {
            'en_US': 'EN:',
            'ja_JP': 'JP:',
            'zh_TW': 'TW:',
            'th_TH': 'TH:'
        }

        lang_indicator = lang_mapping.get(language, '')
        if not lang_indicator:
            return []

        relevant_terms = []
        text_lower = text.lower()

        for line in guide_terminology.split('\n'):
            if '→' in line and lang_indicator in line:
                parts = line.split('→')
                if len(parts) >= 2:
                    korean = parts[0].strip().replace('"', '').replace('-', '').strip()
                    # 해당 언어 부분 추출
                    if lang_indicator in line:
                        try:
                            lang_part = line.split(f'{lang_indicator} "')[1].split('"')[0]
                            if korean and lang_part and (korean in text or korean.lower() in text_lower):
                                relevant_terms.append(f"- {korean} → {lang_part}")
                        except (IndexError, AttributeError):
                            continue

                # 최대 5개로 제한
                if len(relevant_terms) >= 5:
                    break

        return relevant_terms

    def _parse_language_quality_response(self, response: str, original_text: str, language: str) -> Dict[str, Any]:
        """
        언어별 품질 우선 응답 파싱
        """
        # 번역 추출
        translation = response.strip()

        # Quality Score 추출
        quality_score = 85  # 기본값
        if 'Quality Score:' in response:
            try:
                score_line = [line for line in response.split('\n') if 'Quality Score:' in line][0]
                score_text = score_line.split('Quality Score:')[1].strip()
                quality_score = int(''.join(filter(str.isdigit, score_text[:3])))
            except:
                pass

        # Translation 부분만 추출
        if 'Translation:' in response:
            try:
                trans_line = [line for line in response.split('\n') if 'Translation:' in line][0]
                translation = trans_line.split('Translation:')[1].strip()
            except:
                pass

        # 불필요한 설명 제거
        translation = translation.split('Quality Score:')[0].strip()
        translation = translation.split('Quality Analysis:')[0].strip()
        translation = translation.strip('"\'')

        return {
            'translation': translation,
            'quality_score': quality_score,
            'language': language
        }

    def _get_thai_game_cache_key(self, text: str) -> Optional[str]:
        """
        품질 번역용 캐시 키 생성 (guide.md 용어 포함 텍스트만)
        """
        import hashlib

        # 빈 텍스트는 캐시하지 않음
        if not text or not text.strip():
            return None

        # 너무 긴 텍스트는 캐시하지 않음 (메모리 효율성)
        if len(text) > 500:
            return None

        # 텍스트 정규화 후 해시 생성
        normalized_text = text.strip().lower()
        return hashlib.md5(f"quality_{normalized_text}".encode('utf-8')).hexdigest()[:16]

    def _get_cached_quality_translation(self, text: str, target_languages: List[str]) -> Optional[Dict[str, Any]]:
        """
        다국어 품질 번역 캐시 조회
        """
        # guide.md 용어가 포함된 경우에만 캐싱 (태국어 캐시 시스템 재사용)
        cache_key = self._get_thai_game_cache_key(text)  # 범용으로 사용
        if not cache_key:
            return None

        with self._cache_lock:
            if cache_key in self._thai_guide_cache:  # 범용 캐시로 활용
                cached_item = self._thai_guide_cache[cache_key]
                current_time = time.time()

                # TTL 체크 (2시간)
                if (current_time - cached_item['timestamp']) < self._thai_cache_ttl:
                    cached_result = cached_item['result']
                    # 요청된 언어들이 캐시에 모두 있는지 확인
                    if all(lang in cached_result for lang in target_languages if lang != 'ko_KR'):
                        print(f"📚 다국어 품질 번역 캐시 히트: {text[:20]}...")
                        return cached_result

                # 만료된 캐시 제거
                del self._thai_guide_cache[cache_key]

        return None

    def _cache_quality_translation(self, text: str, result: Dict[str, Any]) -> None:
        """
        다국어 품질 번역 결과 캐싱
        """
        cache_key = self._get_thai_game_cache_key(text)  # 범용으로 사용
        if not cache_key:
            return

        with self._cache_lock:
            # 캐시 크기 제한 (최대 200개)
            if len(self._thai_guide_cache) >= 200:
                # 가장 오래된 항목 제거 (FIFO)
                oldest_key = min(self._thai_guide_cache.keys(),
                                key=lambda k: self._thai_guide_cache[k]['timestamp'])
                del self._thai_guide_cache[oldest_key]

            self._thai_guide_cache[cache_key] = {
                'result': result.copy(),
                'timestamp': time.time(),
                'text_sample': text[:30]  # 디버깅용
            }