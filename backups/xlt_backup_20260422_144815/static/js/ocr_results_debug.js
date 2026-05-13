// 단순화된 디버깅용 OCR 결과 JavaScript

console.log('OCR Results JavaScript 로드됨');

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 로드 완료');

    // 체크박스 찾기
    const checkboxes = document.querySelectorAll('.item-checkbox');
    console.log(`체크박스 개수: ${checkboxes.length}`);

    if (checkboxes.length === 0) {
        console.error('체크박스를 찾을 수 없습니다!');
        return;
    }

    // 선택 상태 추적 변수
    let selectedItems = [];

    // 각 체크박스에 이벤트 리스너 추가
    checkboxes.forEach((checkbox, index) => {
        console.log(`체크박스 ${index} 이벤트 리스너 추가:`, checkbox.id);

        checkbox.addEventListener('change', function() {
            console.log(`체크박스 ${this.id} 변경: ${this.checked}`);

            // 선택된 항목 다시 계산
            updateSelectedItems();
        });
    });

    // 번역 버튼 찾기
    const translateBtn = document.getElementById('translate-selected-btn');
    if (translateBtn) {
        console.log('번역 버튼 발견');

        translateBtn.addEventListener('click', function() {
            console.log('번역 버튼 클릭됨');

            if (selectedItems.length === 0) {
                console.log('선택된 항목 없음 - 알람 표시');
                alert('번역할 텍스트를 선택해주세요.');
                return;
            }

            console.log(`${selectedItems.length}개 항목 번역 시작:`, selectedItems);

            // 서버에 데이터 전송 테스트
            testServerRequest();
        });
    } else {
        console.error('번역 버튼을 찾을 수 없습니다!');
    }

    function updateSelectedItems() {
        selectedItems = [];

        document.querySelectorAll('.item-checkbox:checked').forEach(checkbox => {
            const ocrItem = checkbox.closest('.ocr-item');
            if (ocrItem) {
                const index = parseInt(ocrItem.dataset.index);
                const textInput = ocrItem.querySelector('.text-edit-input');
                const text = textInput ? textInput.value : '텍스트 없음';

                selectedItems.push({
                    index: index,
                    text: text
                });
            }
        });

        console.log(`선택된 항목 업데이트: ${selectedItems.length}개`);
        console.log('선택된 항목 상세:', selectedItems);

        // 선택 개수 표시 업데이트
        const countElement = document.getElementById('selected-count');
        if (countElement) {
            countElement.textContent = `${selectedItems.length}개`;
        }

        // 버튼 상태 업데이트
        if (translateBtn) {
            translateBtn.disabled = selectedItems.length === 0;
            if (selectedItems.length > 0) {
                translateBtn.innerHTML = `
                    <i class="fas fa-language me-2"></i>
                    ${selectedItems.length}개 항목 번역
                `;
            } else {
                translateBtn.innerHTML = `
                    <i class="fas fa-language me-2"></i>
                    선택 항목 번역
                `;
            }
        }
    }

    async function testServerRequest() {
        try {
            const sessionId = new URLSearchParams(window.location.search).get('session_id');
            const selectedIndexes = selectedItems.map(item => item.index);

            console.log('서버 전송 데이터:', {
                selected_indexes: selectedIndexes,
                session_id: sessionId
            });

            const response = await fetch('/translate-selected', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_indexes: selectedIndexes,
                    session_id: sessionId
                })
            });

            console.log('서버 응답 상태:', response.status);

            const result = await response.json();
            console.log('서버 응답 내용:', result);

            if (result.status === 'error') {
                alert(`오류: ${result.error}`);
            } else {
                alert('번역이 완료되었습니다!');
            }

        } catch (error) {
            console.error('서버 요청 오류:', error);
            alert(`네트워크 오류: ${error.message}`);
        }
    }

    // 초기 상태 업데이트
    updateSelectedItems();

    console.log('OCR Results 초기화 완료');
});