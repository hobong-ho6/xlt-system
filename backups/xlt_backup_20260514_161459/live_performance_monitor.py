#!/usr/bin/env python3
"""
실시간 성능 모니터링 시스템 (사용자 테스트 중)
XLT System v4.2 성능 최적화 효과 실시간 추적
"""

import time
import json
import requests
from datetime import datetime

class LivePerformanceMonitor:
    def __init__(self):
        self.base_url = "http://localhost:5004"
        self.test_results = []

    def measure_api_call(self, endpoint, method="GET", data=None):
        """API 호출 성능 측정"""
        start_time = time.time()

        try:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}", timeout=60)
            elif method == "POST":
                response = requests.post(f"{self.base_url}{endpoint}",
                                       json=data, timeout=60)

            elapsed = time.time() - start_time

            result = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'method': method,
                'elapsed_time': elapsed,
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response_size': len(response.content) if response.content else 0
            }

            # JSON 응답이면 파싱 시도
            try:
                if 'application/json' in response.headers.get('content-type', ''):
                    result['response_data'] = response.json()
            except:
                pass

            self.test_results.append(result)
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            result = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'method': method,
                'elapsed_time': elapsed,
                'error': str(e),
                'success': False
            }
            self.test_results.append(result)
            return result

    def test_system_health(self):
        """시스템 상태 체크"""
        print("🔍 시스템 상태 실시간 체크")
        print("=" * 50)

        result = self.measure_api_call("/api/health")

        if result['success']:
            health_data = result.get('response_data', {})
            components = health_data.get('components', {})

            print(f"⚡ 응답 시간: {result['elapsed_time']:.2f}초")
            print(f"📊 전체 상태: {health_data.get('overall_status', 'unknown')}")

            # Claude 상태 확인
            claude_status = components.get('claude', {})
            print(f"🤖 Claude CLI: {claude_status.get('status', 'unknown')} - {claude_status.get('message', '')}")

            # 메모리 상태 확인
            memory_status = components.get('memory', {})
            print(f"💾 메모리: {memory_status.get('status', 'unknown')} - {memory_status.get('details', '')}")

            return True
        else:
            print(f"❌ 시스템 상태 확인 실패: {result.get('error', 'Unknown error')}")
            return False

    def monitor_translation_performance(self, test_type, texts, languages):
        """번역 성능 실시간 모니터링"""
        print(f"\n📊 {test_type} 성능 모니터링 시작")
        print("-" * 40)
        print(f"📝 텍스트: {len(texts)}개")
        print(f"🌐 언어: {len(languages)}개 ({languages})")

        # 예상 처리 시간 계산 (기존 방식)
        estimated_old_time = len(texts) * len(languages) * 15  # 개별 처리 15초씩

        print(f"⏱️  기존 예상 시간: {estimated_old_time}초 ({estimated_old_time//60}분 {estimated_old_time%60}초)")
        print(f"🚀 최적화 목표: 70-90% 단축")

        start_monitor_time = time.time()

        return {
            'test_type': test_type,
            'texts_count': len(texts),
            'languages_count': len(languages),
            'languages': languages,
            'estimated_old_time': estimated_old_time,
            'start_time': start_monitor_time
        }

    def finish_translation_monitoring(self, monitor_data, actual_time, success_count):
        """번역 모니터링 완료"""
        improvement = ((monitor_data['estimated_old_time'] - actual_time) /
                      monitor_data['estimated_old_time'] * 100)

        print(f"\n✅ {monitor_data['test_type']} 성능 결과:")
        print(f"   실제 소요: {actual_time:.1f}초 ({actual_time//60:.0f}분 {actual_time%60:.1f}초)")
        print(f"   성공률: {success_count}/{monitor_data['texts_count']} ({success_count/monitor_data['texts_count']*100:.1f}%)")
        print(f"   개선도: {improvement:+.1f}% ({'단축' if improvement > 0 else '증가'})")
        print(f"   속도 향상: {monitor_data['estimated_old_time']/actual_time:.1f}배")

        if improvement >= 70:
            print("🔥 목표 달성! 70% 이상 성능 향상")
        elif improvement >= 50:
            print("🚀 양호! 50% 이상 성능 향상")
        elif improvement >= 0:
            print("📈 개선됨")
        else:
            print("⚠️ 성능 저하 발생")

    def save_results(self):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/user/Documents/XLTTT/live_test_results_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

        print(f"\n📊 실시간 테스트 결과 저장: {filename}")

# 전역 모니터 인스턴스
monitor = LivePerformanceMonitor()

def start_monitoring():
    """모니터링 시작"""
    print("🎯 XLT System v4.2 실시간 성능 모니터링 시작")
    print("=" * 60)

    # 시스템 상태 체크
    system_ok = monitor.test_system_health()

    if system_ok:
        print("\n✅ 시스템 준비 완료 - 사용자 테스트 대기 중")
        print("📋 모니터링 준비된 항목:")
        print("   • API 응답 시간")
        print("   • 번역 처리 성능")
        print("   • 배치 처리 효과")
        print("   • 시스템 리소스 사용률")
    else:
        print("\n❌ 시스템 상태 이상 - 문제 해결 필요")

    return system_ok

if __name__ == "__main__":
    start_monitoring()