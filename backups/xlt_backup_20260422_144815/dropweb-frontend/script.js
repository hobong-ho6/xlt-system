// XLT System DropWeb Frontend
// 로컬 서버와 통신하여 XLT 기능을 제공

class XLTWebClient {
    constructor() {
        this.baseURL = 'http://localhost:5004';
        this.sessionId = this.generateSessionId();
        this.ocrResults = [];
        this.selectedTexts = [];

        this.init();
    }

    generateSessionId() {
        return 'web-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    async init() {
        await this.checkServerConnection();
        this.bindEvents();
    }

    // 서버 연결 상태 확인
    async checkServerConnection() {
        const statusChecking = document.getElementById('status-checking');
        const statusConnected = document.getElementById('status-connected');
        const statusDisconnected = document.getElementById('status-disconnected');
        const mainInterface = document.getElementById('main-interface');

        try {
            const response = await fetch(`${this.baseURL}/api/health`, {
                method: 'GET',
                mode: 'cors'
            });

            if (response.ok) {
                const health = await response.json();
                console.log('✅ XLT 서버 연결 성공:', health);

                statusChecking.classList.add('hidden');
                statusConnected.classList.remove('hidden');
                mainInterface.classList.remove('hidden');
            } else {
                throw new Error('Health check failed');
            }
        } catch (error) {
            console.error('❌ XLT 서버 연결 실패:', error);

            statusChecking.classList.add('hidden');
            statusDisconnected.classList.remove('hidden');
        }
    }

    // 이벤트 바인딩
    bindEvents() {
        const processBtn = document.getElementById('process-btn');
        const figmaUrlInput = document.getElementById('figma-url');
        const selectAllBtn = document.getElementById('select-all-btn');
        const translateBtn = document.getElementById('translate-btn');

        // 피그마 URL 처리
        processBtn.addEventListener('click', () => this.processFigmaURL());

        // Enter 키로 처리 실행
        figmaUrlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.processFigmaURL();
            }
        });

        // 전체 선택/해제
        selectAllBtn.addEventListener('click', () => this.toggleSelectAll());

        // 번역 시작
        translateBtn.addEventListener('click', () => this.startTranslation());
    }

    // 피그마 URL 처리
    async processFigmaURL() {
        const figmaUrlInput = document.getElementById('figma-url');
        const processBtn = document.getElementById('process-btn');
        const processingSection = document.getElementById('processing-section');
        const processingMessage = document.getElementById('processing-message');
        const resultsSection = document.getElementById('results-section');

        const figmaUrl = figmaUrlInput.value.trim();
        if (!figmaUrl) {
            alert('피그마 URL을 입력해주세요.');
            return;
        }

        if (!figmaUrl.includes('figma.com')) {
            alert('올바른 피그마 URL을 입력해주세요.');
            return;
        }

        try {
            // UI 상태 변경
            processBtn.disabled = true;
            processingSection.classList.remove('hidden');
            resultsSection.classList.add('hidden');

            processingMessage.textContent = '피그마 이미지를 다운로드하고 있습니다...';

            // OCR 처리 요청
            const formData = new FormData();
            formData.append('figma_url', figmaUrl);
            formData.append('session_id', this.sessionId);

            const response = await fetch(`${this.baseURL}/upload`, {
                method: 'POST',
                body: formData,
                mode: 'cors'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.status === 'success') {
                processingMessage.textContent = '텍스트를 추출하고 있습니다...';

                // 텍스트 선택 페이지 로드
                await this.loadOCRResults();

                processingSection.classList.add('hidden');
                resultsSection.classList.remove('hidden');
            } else {
                throw new Error(result.error || '처리 중 오류가 발생했습니다.');
            }

        } catch (error) {
            console.error('❌ 피그마 URL 처리 오류:', error);
            alert(`처리 중 오류가 발생했습니다: ${error.message}`);

            processingSection.classList.add('hidden');
        } finally {
            processBtn.disabled = false;
        }
    }

    // OCR 결과 로드
    async loadOCRResults() {
        try {
            const response = await fetch(`${this.baseURL}/select_texts?session_id=${this.sessionId}`, {
                method: 'GET',
                mode: 'cors'
            });

            const html = await response.text();

            // HTML에서 OCR 결과 파싱 (간단한 방법)
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const ocrItems = doc.querySelectorAll('.ocr-item');

            this.ocrResults = Array.from(ocrItems).map((item, index) => ({
                index: index,
                text: item.querySelector('.ocr-text')?.textContent || '',
                x: parseInt(item.dataset.x) || 0,
                y: parseInt(item.dataset.y) || 0
            }));

            this.displayOCRResults();

        } catch (error) {
            console.error('❌ OCR 결과 로드 오류:', error);
            alert('OCR 결과를 불러올 수 없습니다.');
        }
    }

    // OCR 결과 표시
    displayOCRResults() {
        const ocrResultsContainer = document.getElementById('ocr-results');

        ocrResultsContainer.innerHTML = this.ocrResults.map((item, index) => `
            <div class="flex items-center p-3 border rounded-lg hover:bg-gray-50">
                <input
                    type="checkbox"
                    id="text-${index}"
                    class="mr-3 text-selection-checkbox"
                    data-index="${index}"
                >
                <label for="text-${index}" class="flex-1 cursor-pointer">
                    <span class="font-mono text-sm text-gray-500 mr-3">[${item.x}, ${item.y}]</span>
                    <span class="text-gray-900">${this.escapeHtml(item.text)}</span>
                </label>
            </div>
        `).join('');
    }

    // HTML 이스케이프
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 전체 선택/해제
    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.text-selection-checkbox');
        const selectAllBtn = document.getElementById('select-all-btn');

        const allChecked = Array.from(checkboxes).every(cb => cb.checked);

        checkboxes.forEach(cb => {
            cb.checked = !allChecked;
        });

        selectAllBtn.textContent = allChecked ? '전체 선택' : '전체 해제';
    }

    // 번역 시작
    async startTranslation() {
        const checkboxes = document.querySelectorAll('.text-selection-checkbox:checked');

        if (checkboxes.length === 0) {
            alert('번역할 텍스트를 선택해주세요.');
            return;
        }

        const selectedIndices = Array.from(checkboxes).map(cb => parseInt(cb.dataset.index));
        const selectedTexts = selectedIndices.map(index => this.ocrResults[index].text);

        try {
            const translateBtn = document.getElementById('translate-btn');
            translateBtn.disabled = true;
            translateBtn.textContent = '번역 중...';

            // 번역 요청
            const response = await fetch(`${this.baseURL}/translate-selected`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    selected_indices: selectedIndices,
                    selected_texts: selectedTexts,
                    xlt_keys: selectedTexts.map((text, i) => `item_${i + 1}`)
                }),
                mode: 'cors'
            });

            const result = await response.json();

            if (result.status === 'success') {
                // 번역 미리보기 표시
                this.showTranslationPreview(result);
            } else {
                throw new Error(result.error || '번역 중 오류가 발생했습니다.');
            }

        } catch (error) {
            console.error('❌ 번역 오류:', error);
            alert(`번역 중 오류가 발생했습니다: ${error.message}`);
        } finally {
            const translateBtn = document.getElementById('translate-btn');
            translateBtn.disabled = false;
            translateBtn.textContent = '번역 시작';
        }
    }

    // 번역 미리보기 표시
    showTranslationPreview(result) {
        // 새 창이나 모달로 번역 결과 표시
        const previewWindow = window.open('', 'translation-preview', 'width=800,height=600');

        const previewHTML = `
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>번역 미리보기</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-50 p-6">
                <div class="max-w-4xl mx-auto">
                    <h1 class="text-2xl font-bold mb-6">번역 미리보기</h1>

                    ${result.data.translations.map((item, index) => `
                        <div class="bg-white rounded-lg shadow p-6 mb-4">
                            <h3 class="text-lg font-semibold mb-4">📝 항목 ${index + 1}: ${item.key || `item_${index + 1}`}</h3>

                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">원본 텍스트</label>
                                    <div class="p-3 bg-gray-50 rounded border">${this.escapeHtml(item.original || '')}</div>
                                </div>
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">처리된 텍스트</label>
                                    <div class="p-3 bg-gray-50 rounded border">${this.escapeHtml(item.processed || item.original || '')}</div>
                                </div>
                            </div>

                            <div>
                                <h4 class="text-md font-medium mb-3">🌐 번역 결과</h4>
                                <div class="space-y-2">
                                    <div class="flex"><span class="w-16 text-gray-600">🇰🇷 한국어:</span><span>${this.escapeHtml(item.ko_KR || '')}</span></div>
                                    <div class="flex"><span class="w-16 text-gray-600">🇺🇸 영어:</span><span>${this.escapeHtml(item.en_US || '')}</span></div>
                                    <div class="flex"><span class="w-16 text-gray-600">🇯🇵 일본어:</span><span>${this.escapeHtml(item.ja_JP || '')}</span></div>
                                    <div class="flex"><span class="w-16 text-gray-600">🇹🇼 중국어:</span><span>${this.escapeHtml(item.zh_TW || '')}</span></div>
                                    <div class="flex"><span class="w-16 text-gray-600">🇹🇭 태국어:</span><span>${this.escapeHtml(item.th_TH || '')}</span></div>
                                </div>
                            </div>
                        </div>
                    `).join('')}

                    <div class="flex justify-center mt-6">
                        <button
                            onclick="downloadExcel('${result.data.filename || 'translation_result'}')"
                            class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 text-lg"
                        >
                            📊 Excel 파일 다운로드
                        </button>
                    </div>
                </div>

                <script>
                    async function downloadExcel(filename) {
                        try {
                            const response = await fetch('http://localhost:5004/download-excel', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ filename: filename })
                            });

                            if (response.ok) {
                                const blob = await response.blob();
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = filename + '.xlsx';
                                a.click();
                                window.URL.revokeObjectURL(url);
                            } else {
                                alert('Excel 파일 다운로드에 실패했습니다.');
                            }
                        } catch (error) {
                            console.error('다운로드 오류:', error);
                            alert('Excel 파일 다운로드 중 오류가 발생했습니다.');
                        }
                    }
                </script>
            </body>
            </html>
        `;

        previewWindow.document.write(previewHTML);
        previewWindow.document.close();
    }
}

// DOM 로드 후 XLT 클라이언트 초기화
document.addEventListener('DOMContentLoaded', () => {
    new XLTWebClient();
});