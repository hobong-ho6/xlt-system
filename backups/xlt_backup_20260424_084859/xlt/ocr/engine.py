"""OCR Engine using EasyOCR for XLT system"""

import time
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np

from ..core.exceptions import OCRProcessingError
from ..translation.languages import EASYOCR_LANGUAGE_SETS
from ..utils.helpers import format_confidence, format_duration, retry_on_failure


class OCREngine:
    """EasyOCR 기반 OCR 엔진"""

    def __init__(self, config):
        self.config = config
        self.readers = {}  # 언어별 EasyOCR Reader 캐시
        self._easyocr_available = None

    def _check_easyocr_availability(self) -> bool:
        """EasyOCR 라이브러리 사용 가능 여부 확인"""
        if self._easyocr_available is not None:
            return self._easyocr_available

        try:
            import easyocr
            self._easyocr_available = True
            return True
        except ImportError:
            self._easyocr_available = False
            return False

    def _get_reader(self, reader_name: str):
        """지정된 언어 조합의 EasyOCR Reader 반환 (캐시됨)

        Args:
            reader_name: EASYOCR_LANGUAGE_SETS의 키

        Returns:
            easyocr.Reader: EasyOCR Reader 인스턴스
        """
        if not self._check_easyocr_availability():
            raise OCRProcessingError("EasyOCR 라이브러리가 설치되지 않았습니다. pip install easyocr")

        if reader_name not in self.readers:
            import easyocr

            languages = EASYOCR_LANGUAGE_SETS.get(reader_name, ['ko', 'en'])

            try:
                # GPU 사용 시도, 실패하면 CPU로 대체
                try:
                    reader = easyocr.Reader(languages, gpu=True)
                except:
                    reader = easyocr.Reader(languages, gpu=False)

                self.readers[reader_name] = reader

            except Exception as e:
                raise OCRProcessingError(f"OCR Reader 초기화 실패 ({reader_name}): {str(e)}")

        return self.readers[reader_name]

    def extract_text(self, image: Image.Image) -> List[Dict[str, Any]]:
        """이미지에서 텍스트 추출

        Args:
            image: PIL Image 객체

        Returns:
            List[Dict[str, Any]]: 추출된 텍스트 정보 목록
        """
        start_time = time.time()

        try:
            # PIL Image를 numpy 배열로 변환
            image_array = np.array(image)

            # 모든 언어 조합으로 OCR 실행
            all_results = []
            for reader_name in EASYOCR_LANGUAGE_SETS.keys():
                results = self._extract_with_reader(image_array, reader_name)
                all_results.extend(results)

            # 중복 제거 및 병합
            merged_results = self._merge_duplicate_results(all_results)

            # 신뢰도 필터링
            filtered_results = self._filter_by_confidence(merged_results)

            # Y 좌표로 정렬 (상단에서 하단으로)
            filtered_results.sort(key=lambda x: x['bbox'][0][1])  # top-left Y 좌표

            processing_time = time.time() - start_time

            # 로깅용 통계 계산
            if filtered_results:
                avg_confidence = sum(r['confidence'] for r in filtered_results) / len(filtered_results)
            else:
                avg_confidence = 0.0

            # 로거가 있으면 결과 기록
            if hasattr(self, 'logger'):
                self.logger.log_ocr_result(
                    text_count=len(filtered_results),
                    confidence_avg=avg_confidence,
                    processing_time=processing_time
                )

            return filtered_results

        except Exception as e:
            raise OCRProcessingError(f"텍스트 추출 실패: {str(e)}")

    def _extract_with_reader(self, image_array: np.ndarray, reader_name: str) -> List[Dict[str, Any]]:
        """특정 Reader로 텍스트 추출"""
        try:
            reader = self._get_reader(reader_name)

            # 재시도 로직으로 OCR 실행
            def ocr_func():
                return reader.readtext(image_array, detail=1)

            raw_results = retry_on_failure(ocr_func, max_retries=2, delay=0.5)

            # 결과를 표준 형식으로 변환
            processed_results = []
            for bbox, text, confidence in raw_results:
                if text.strip():  # 빈 텍스트 제외
                    processed_results.append({
                        'text': text.strip(),
                        'confidence': confidence,
                        'bbox': bbox,
                        'reader': reader_name
                    })

            return processed_results

        except Exception as e:
            # 특정 Reader 실패는 경고만 하고 계속 진행
            print(f"⚠️ OCR Reader '{reader_name}' 실패: {str(e)}")
            return []

    def _merge_duplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복된 텍스트 결과 병합"""
        if not results:
            return []

        # 텍스트와 위치 기준으로 그룹화
        groups = {}
        for result in results:
            text = result['text']
            bbox = result['bbox']

            # 대략적인 위치 기준으로 키 생성 (±10 픽셀 허용)
            center_x = (bbox[0][0] + bbox[2][0]) // 2
            center_y = (bbox[0][1] + bbox[2][1]) // 2
            position_key = (center_x // 20, center_y // 20)  # 20픽셀 단위로 그룹화

            group_key = (text.lower(), position_key)

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(result)

        # 각 그룹에서 가장 높은 신뢰도의 결과 선택
        merged_results = []
        for group in groups.values():
            best_result = max(group, key=lambda x: x['confidence'])
            merged_results.append(best_result)

        return merged_results

    def _filter_by_confidence(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """신뢰도 기준으로 결과 필터링"""
        threshold = self.config.ocr_confidence_threshold
        return [r for r in results if r['confidence'] >= threshold]

    def get_text_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OCR 결과 통계 정보 반환"""
        if not results:
            return {
                'total_count': 0,
                'avg_confidence': 0.0,
                'confidence_range': (0.0, 0.0),
                'readers_used': []
            }

        confidences = [r['confidence'] for r in results]
        readers_used = list(set(r['reader'] for r in results))

        return {
            'total_count': len(results),
            'avg_confidence': sum(confidences) / len(confidences),
            'confidence_range': (min(confidences), max(confidences)),
            'readers_used': readers_used,
            'confidence_distribution': {
                'high': len([c for c in confidences if c >= 0.8]),
                'medium': len([c for c in confidences if 0.5 <= c < 0.8]),
                'low': len([c for c in confidences if c < 0.5])
            }
        }

    def format_ocr_results_for_display(self, results: List[Dict[str, Any]]) -> List[str]:
        """OCR 결과를 사용자 표시용으로 포맷"""
        formatted_lines = []

        for i, result in enumerate(results, 1):
            text = result['text']
            confidence = format_confidence(result['confidence'])
            reader = result['reader']

            formatted_lines.append(f"{i:2d}. {text} ({confidence}, {reader})")

        return formatted_lines