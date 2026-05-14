#!/usr/bin/env python3
"""
XLT System 자가 치유 헬스 체크 시스템
"""

import json
import subprocess
import time
import requests
import os
import signal
import sys
from pathlib import Path

class XLTHealthChecker:
    def __init__(self):
        self.config_file = Path(__file__).parent / "self_healing_config.json"
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            self.config = {"self_healing": {"enabled": False}}

    def check_server_health(self):
        """서버 상태 확인"""
        try:
            response = requests.get("http://localhost:5004/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def check_process_running(self):
        """프로세스 실행 상태 확인"""
        try:
            result = subprocess.run(['pgrep', '-f', 'stable_web_server.py'],
                                  capture_output=True, text=True)
            return result.returncode == 0 and result.stdout.strip()
        except:
            return False

    def auto_restart_server(self):
        """서버 자동 재시작"""
        try:
            print("🔄 서버 자동 재시작 시도...")

            # 기존 프로세스 정리
            subprocess.run(['pkill', '-f', 'stable_web_server.py'], stderr=subprocess.DEVNULL)
            time.sleep(3)

            # 새 서버 시작
            subprocess.Popen(['python3', 'stable_web_server.py'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5)

            # 재시작 확인
            if self.check_server_health():
                print("✅ 서버 자동 재시작 성공")
                return True
            else:
                print("❌ 서버 재시작 실패")
                return False

        except Exception as e:
            print(f"❌ 자동 재시작 오류: {e}")
            return False

    def run_health_check(self):
        """헬스 체크 실행"""
        if not self.config.get("self_healing", {}).get("enabled", False):
            return True

        print("🔍 XLT System 헬스 체크 실행 중...")

        # 프로세스 확인
        if not self.check_process_running():
            print("⚠️ 서버 프로세스가 실행되지 않음")
            if self.auto_restart_server():
                return True
            else:
                return False

        # 서버 응답 확인
        if not self.check_server_health():
            print("⚠️ 서버 응답 실패")
            if self.auto_restart_server():
                return True
            else:
                return False

        print("✅ 시스템 정상")
        return True

if __name__ == "__main__":
    checker = XLTHealthChecker()
    success = checker.run_health_check()
    sys.exit(0 if success else 1)
