// XLT System v2.0 Web Interface JavaScript

class XLTWebInterface {
    constructor() {
        this.logInterval = null;
        this.init();
    }

    init() {
        // 시스템 상태 체크 플래그 초기화
        this.isCheckingHealth = false;

        this.setupEventListeners();
        this.initializeDefaults();
        this.setupSystemStatusMonitoring();
        this.checkSystemHealth();
        this.checkForUpdates();
    }

    initializeDefaults() {
        // XLT System v3.0 - 피그마 전용, 수동 모드 고정
        console.log('XLT System v3.0 기본값 설정 시작...');

        // 피그마 섹션만 표시
        setTimeout(() => {
            const figmaSection = document.getElementById('figma-section');
            if (figmaSection) {
                figmaSection.style.display = 'block';
            }
            console.log('피그마 섹션 표시 완료');

            // 엑셀 합치기 기본 파일명 설정
            this.setDefaultMergeFilename();

            // loading 클래스 제거
            document.body.classList.remove('loading');
            console.log('XLT System v3.0 설정 완료: 피그마 URL 전용, 수동 모드 고정');
        }, 50);
    }

    setDefaultMergeFilename() {
        const outputFilename = document.getElementById('output-filename');
        if (outputFilename && !outputFilename.value) {
            const now = new Date();
            const timestamp = now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_');
            outputFilename.placeholder = `merged_${timestamp}`;
        }
    }

    setupSystemStatusMonitoring() {
        // 시스템 상태 모니터링 초기화
        this.statusContainer = document.getElementById('status-container');
        this.statusItems = document.getElementById('status-items');
        this.statusSummary = document.getElementById('status-summary');
        this.lastCheckTime = document.getElementById('last-check-time');
        this.refreshButton = document.getElementById('refresh-status');

        // 원본 HTML 백업 (에러 상태에서 복원용)
        if (this.statusContainer) {
            this.originalStatusHTML = this.statusContainer.innerHTML;
        }

        // 새로고침 버튼 이벤트 리스너
        if (this.refreshButton) {
            this.refreshButton.addEventListener('click', () => {
                this.checkSystemHealth();
            });
        }

        // 상태 항목 클릭 이벤트 (상세 정보 토글)
        document.addEventListener('click', (e) => {
            if (e.target.closest('.status-item')) {
                const statusItem = e.target.closest('.status-item');
                const details = statusItem.querySelector('.status-details');
                if (details) {
                    const isVisible = details.style.display !== 'none';
                    details.style.display = isVisible ? 'none' : 'block';
                    statusItem.classList.toggle('clickable', !isVisible);
                }
            }
        });

        // 페이지 이벤트 기반 상태 체크 (자동 폴링 제거)
        this.setupPageEventStatusCheck();
    }

    initStatusElements() {
        // DOM 요소들을 다시 초기화 (에러 상태에서 복원 후)
        this.statusItems = document.getElementById('status-items');
        this.statusSummary = document.getElementById('status-summary');
        this.lastCheckTime = document.getElementById('last-check-time');
        this.refreshButton = document.getElementById('refresh-status');

        // 새로고침 버튼 이벤트 리스너 재등록
        if (this.refreshButton) {
            this.refreshButton.addEventListener('click', () => {
                this.checkSystemHealth();
            });
        }

        console.log('🔧 상태 UI 요소들 재초기화 완료');
    }

    setupPageEventStatusCheck() {
        // 페이지 로드 시 상태 체크
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.checkSystemHealth();
            });
        } else {
            // 이미 로드된 상태라면 즉시 실행
            this.checkSystemHealth();
        }

        // 페이지 표시 시 상태 체크 (bfcache에서 복원된 경우만)
        window.addEventListener('pageshow', (e) => {
            // bfcache에서 복원된 경우에만 체크 (중복 호출 방지)
            if (e.persisted) {
                setTimeout(() => this.checkSystemHealth(), 200);
            }
        });

        // 포커스 복원 시 체크 (debounce 적용)
        let focusTimeout = null;
        window.addEventListener('focus', () => {
            // 이전 타이머 취소 (빠른 연속 포커스 방지)
            if (focusTimeout) {
                clearTimeout(focusTimeout);
            }
            // 1초 후 실행 (debounce)
            focusTimeout = setTimeout(() => {
                this.checkSystemHealth();
                focusTimeout = null;
            }, 1000);
        });
    }

    setupEventListeners() {
        // XLT System v3.0 - 필요한 이벤트 리스너만 설정

        // 번역 시작 버튼
        const translateBtn = document.getElementById('translate-btn');
        if (translateBtn) {
            translateBtn.addEventListener('click', () => {
                this.startTranslation();
            });
        }

        // 새 번역 시작 버튼 (결과 페이지에서 생성됨)
        const newTranslationBtn = document.getElementById('new-translation-btn');
        if (newTranslationBtn) {
            newTranslationBtn.addEventListener('click', () => {
                this.resetForm();
            });
        }

        // 엑셀 번역 관련 이벤트 리스너
        this.setupExcelTranslationEvents();

        // 피그마 URL 입력 이벤트 (실시간 미리보기)
        const figmaUrlInput = document.getElementById('figma-url');
        if (figmaUrlInput) {
            let previewTimeout = null;

            figmaUrlInput.addEventListener('input', (e) => {
                // 디바운싱: 사용자가 타이핑을 멈춘 후 1초 뒤에 미리보기 요청
                clearTimeout(previewTimeout);

                const url = e.target.value.trim();
                if (!url) {
                    this.hideFigmaPreview();
                    return;
                }

                previewTimeout = setTimeout(() => {
                    this.loadFigmaPreview(url);
                }, 1000);
            });

            // 포커스를 잃었을 때도 미리보기 시도
            figmaUrlInput.addEventListener('blur', (e) => {
                const url = e.target.value.trim();
                if (url && url.includes('figma.com')) {
                    clearTimeout(previewTimeout);
                    this.loadFigmaPreview(url);
                }
            });
        }

        // 다운로드 버튼
        document.getElementById('download-btn').addEventListener('click', () => {
            this.downloadResult();
        });

        // 번역 엔진 변경 이벤트 리스너 (XLT v4.0)
        document.querySelectorAll('input[name="translation-engine"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const engine = e.target.value;
                if (engine === 'claude_integrated') {
                    this.addLog('🤖✨ Claude 통합 처리 선택: 맞춤법 교정 + 번역을 동시에 처리합니다', 'info');
                } else if (engine === 'claude') {
                    this.addLog('🤖 Claude 번역 선택: 고품질 번역을 위해 시간이 더 소요됩니다', 'info');
                } else {
                    this.addLog('🌐 Google 번역 선택: 빠르고 안정적인 번역을 제공합니다', 'info');
                }
            });
        });

        // 엑셀 합치기 이벤트 리스너들
        this.setupExcelMergeEventListeners();

        // 엑셀 검증 이벤트 리스너들
        this.setupExcelValidationEventListeners();
    }

    setupExcelMergeEventListeners() {
        // 파일 선택 이벤트
        const excelFiles = document.getElementById('excel-files');
        if (excelFiles) {
            excelFiles.addEventListener('change', (e) => this.handleExcelFilesChange(e));
        }

        // 파일 제거 버튼
        const clearFilesBtn = document.getElementById('clear-files-btn');
        if (clearFilesBtn) {
            clearFilesBtn.addEventListener('click', () => this.clearSelectedFiles());
        }

        // 엑셀 합치기 버튼
        const mergeBtn = document.getElementById('merge-excel-btn');
        if (mergeBtn) {
            mergeBtn.addEventListener('click', () => this.mergeExcelFiles());
        }

        // 합친 파일 다운로드 버튼
        const downloadMergedBtn = document.getElementById('download-merged-btn');
        if (downloadMergedBtn) {
            downloadMergedBtn.addEventListener('click', () => this.downloadMergedFile());
        }

        // 출력 파일명 입력 시 자동 생성 파일명 업데이트
        const outputFilename = document.getElementById('output-filename');
        if (outputFilename) {
            outputFilename.addEventListener('input', (e) => {
                const mergeBtn = document.getElementById('merge-excel-btn');
                if (mergeBtn && !mergeBtn.disabled) {
                    this.updateMergeButtonText();
                }
            });
        }
    }

    // setupFileDropZone 제거됨 - 파일 업로드 기능 비활성화

    // toggleInputSections 제거됨 - 입력 방식 고정
    // updateTranslationModeDescription 제거됨 - 번역 모드 고정

    updateModeDescription(mode) {
        document.getElementById('auto-description').style.display =
            mode === 'auto' ? 'block' : 'none';
        document.getElementById('manual-description').style.display =
            mode === 'manual' ? 'block' : 'none';

        // 번역 버튼 텍스트 업데이트
        const translateBtn = document.getElementById('translate-btn');
        if (mode === 'manual') {
            translateBtn.innerHTML = `
                <i class="fas fa-eye me-2"></i>
                텍스트 확인
            `;
        } else {
            translateBtn.innerHTML = `
                <i class="fas fa-play me-2"></i>
                번역 시작
            `;
        }
    }

    // handleFileSelect, showImagePreview 제거됨 - 파일 업로드 기능 비활성화

    async checkSystemHealth() {
        // 이미 실행 중이면 중복 실행 방지
        if (this.isCheckingHealth) {
            console.log('시스템 상태 체크가 이미 진행 중입니다.');
            return;
        }

        try {
            this.isCheckingHealth = true;

            // 새로고침 버튼 스피너 시작
            if (this.refreshButton) {
                this.refreshButton.disabled = true;
                this.refreshButton.classList.add('spinning');
            }

            // 로딩 상태 표시
            this.showStatusLoading();

            // 8초 타임아웃으로 요청 처리 (성능 고려)
            let timeoutId;
            let isAborted = false;

            const timeoutPromise = new Promise((_, reject) => {
                timeoutId = setTimeout(() => {
                    isAborted = true;
                    reject(new Error('요청 시간 초과 (8초)'));
                }, 8000);
            });

            const fetchPromise = fetch('/api/health').then(async (response) => {
                if (isAborted) {
                    throw new Error('요청이 중단됨');
                }

                const contentType = response.headers.get("content-type");

                let data;
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    data = await response.json();
                } else {
                    throw new Error('서버에서 JSON이 아닌 응답을 반환했습니다');
                }

                // 상태 데이터 업데이트
                this.updateSystemStatus(data);

                // 전체 시스템 상태 알림 업데이트
                this.updateSystemStatusAlert(data);

                return data;
            });

            try {
                await Promise.race([fetchPromise, timeoutPromise]);
            } catch (fetchError) {
                throw fetchError;
            } finally {
                // 타임아웃 정리
                if (timeoutId) {
                    clearTimeout(timeoutId);
                }
            }

        } catch (error) {
            console.error('System health check error:', error);

            let errorMessage = '시스템 상태를 확인할 수 없습니다';
            if (error.name === 'AbortError') {
                errorMessage = '시스템 상태 확인 시간 초과 (8초)';
            } else {
                errorMessage += ': ' + error.message;
            }

            this.showStatusError(errorMessage);
            this.showAlert('❌ ' + errorMessage, 'warning');
        } finally {
            // 새로고침 버튼 스피너 종료
            if (this.refreshButton) {
                this.refreshButton.disabled = false;
                this.refreshButton.classList.remove('spinning');
            }

            // 실행 중 플래그 해제
            this.isCheckingHealth = false;
        }
    }

    updateSystemStatus(data) {
        // 기존 에러 상태 제거 (다시 시도 후 정상 상태 복원)
        if (this.statusContainer) {
            const errorDiv = this.statusContainer.querySelector('.text-danger');
            if (errorDiv) {
                console.log('🔄 에러 상태에서 정상 상태로 복원 중...');
                // 에러 div 제거하고 원래 HTML 구조 복원
                this.statusContainer.innerHTML = this.originalStatusHTML || '';
                // 다시 DOM 요소들을 초기화
                this.initStatusElements();
            }
        }

        // 로딩 숨기고 상태 항목들 표시 (안전 체크)
        const loadingElement = document.querySelector('.status-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }

        if (this.statusItems) {
            this.statusItems.style.display = 'block';
        }

        if (this.statusSummary) {
            this.statusSummary.style.display = 'block';
        }

        // 각 컴포넌트 상태 업데이트
        const components = data.components;
        Object.keys(components).forEach(componentName => {
            this.updateComponentStatus(componentName, components[componentName]);
        });

        // 마지막 확인 시간 업데이트 (안전 체크)
        if (this.lastCheckTime && data.last_check) {
            const lastCheck = new Date(data.last_check).toLocaleTimeString('ko-KR');
            this.lastCheckTime.textContent = lastCheck;
        }

        // 전체 상태 요약 업데이트
        this.updateOverallStatus(data.overall_status, data.summary);

        // Claude CLI 상태에 따라 Claude 번역 옵션 활성화/비활성화
        this.updateClaudeTranslationOptions(data.components);
    }

    updateComponentStatus(componentName, statusData) {
        const statusItem = document.querySelector(`[data-component="${componentName}"]`);
        if (!statusItem) return;

        const icon = statusItem.querySelector('.status-icon');
        const message = statusItem.querySelector('.status-message');
        const badge = statusItem.querySelector('.status-badge');
        const details = statusItem.querySelector('.status-details');

        // 상태에 따른 클래스 및 내용 업데이트
        statusItem.setAttribute('data-status', statusData.status);

        // 아이콘 색상 업데이트
        icon.className = icon.className.replace(/\b(ok|warning|error|unknown)\b/g, '');
        icon.classList.add(statusData.status);

        // 메시지 업데이트
        message.textContent = statusData.message;

        // 배지 업데이트
        badge.className = 'badge status-badge ' + statusData.status;
        badge.textContent = statusData.status === 'ok' ? 'OK' :
                           statusData.status === 'warning' ? 'WARNING' : 'ERROR';

        // 상세 정보 업데이트
        if (details && statusData.details) {
            details.textContent = statusData.details;
            statusItem.classList.add('clickable');
        }
    }

    updateOverallStatus(overallStatus, summary) {
        // 전체 상태 요약 업데이트는 간단하게 처리
        console.log(`전체 시스템 상태: ${overallStatus} - ${summary}`);
    }

    updateClaudeTranslationOptions(components) {
        // Claude CLI 상태 확인
        const claudeStatus = components.claude;
        const claudeAvailable = claudeStatus && claudeStatus.status === 'ok';

        // Claude 관련 번역 엔진 옵션 찾기
        const claudeIntegratedRadio = document.getElementById('engine-claude-integrated');

        if (claudeIntegratedRadio) {
            claudeIntegratedRadio.disabled = !claudeAvailable;
            const claudeIntegratedLabel = claudeIntegratedRadio.closest('.form-check').querySelector('label');
            if (claudeIntegratedLabel) {
                this.updateClaudeOptionUI(claudeIntegratedLabel, claudeAvailable, claudeStatus);
            }

            // Claude 통합이 비활성화되고 현재 선택되어 있다면 Google로 전환
            if (!claudeAvailable && claudeIntegratedRadio.checked) {
                const googleRadio = document.getElementById('engine-google');
                if (googleRadio) {
                    googleRadio.checked = true;
                    this.addLog('⚠️ Claude CLI를 사용할 수 없어 Google 번역으로 전환되었습니다', 'warning');
                }
            }
        }

        // 엑셀 번역의 Claude 옵션도 업데이트
        const excelClaudeRadio = document.getElementById('excel-engine-claude-integrated');
        if (excelClaudeRadio) {
            excelClaudeRadio.disabled = !claudeAvailable;
            const excelClaudeLabel = excelClaudeRadio.closest('.form-check').querySelector('label');
            if (excelClaudeLabel) {
                this.updateClaudeOptionUI(excelClaudeLabel, claudeAvailable, claudeStatus);
            }

            // Claude 통합이 비활성화되고 현재 선택되어 있다면 Google로 전환
            if (!claudeAvailable && excelClaudeRadio.checked) {
                const excelGoogleRadio = document.getElementById('excel-engine-google');
                if (excelGoogleRadio) {
                    excelGoogleRadio.checked = true;
                    this.addLog('⚠️ Claude CLI를 사용할 수 없어 엑셀 번역도 Google로 전환되었습니다', 'warning');
                }
            }
        }

        // Claude 상태에 따른 안내 메시지
        if (!claudeAvailable && claudeStatus) {
            let statusMessage = '';
            if (claudeStatus.status === 'error') {
                statusMessage = `Claude CLI 오류: ${claudeStatus.message}`;
            } else if (claudeStatus.status === 'warning') {
                statusMessage = `Claude CLI 경고: ${claudeStatus.message}`;
            }

            if (statusMessage) {
                console.log(`Claude 번역 비활성화: ${statusMessage}`);
            }
        }
    }

    updateClaudeOptionUI(labelElement, claudeAvailable, claudeStatus) {
        // 기존 "이용불가" 배지 제거
        const existingBadge = labelElement.querySelector('.claude-unavailable-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        if (claudeAvailable) {
            // Claude 사용 가능 시 스타일 복원
            labelElement.style.opacity = '1';
            labelElement.style.textDecoration = 'none';
            labelElement.removeAttribute('title');
        } else {
            // Claude 사용 불가 시 시각적 피드백 강화
            labelElement.style.opacity = '0.4';
            labelElement.style.textDecoration = 'line-through';

            // "이용불가" 배지 추가
            const badge = document.createElement('span');
            badge.className = 'badge bg-secondary ms-2 claude-unavailable-badge';
            badge.textContent = '이용불가';
            labelElement.appendChild(badge);

            // 상세 오류 메시지를 툴팁으로 표시
            let tooltipMessage = 'Claude CLI 연결 불가';
            if (claudeStatus) {
                if (claudeStatus.message) {
                    tooltipMessage = claudeStatus.message;
                }
                if (claudeStatus.details) {
                    tooltipMessage += '\n' + claudeStatus.details;
                }
            }
            labelElement.title = tooltipMessage;
        }
    }

    setupExcelTranslationEvents() {
        // 엑셀 파일 업로드 이벤트
        const excelFileInput = document.getElementById('excel-translate-file');
        const excelTranslateBtn = document.getElementById('excel-translate-btn');

        if (excelFileInput && excelTranslateBtn) {
            excelFileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    // 파일 크기 체크 (10MB)
                    if (file.size > 10 * 1024 * 1024) {
                        alert('파일 크기가 10MB를 초과합니다.');
                        e.target.value = '';
                        excelTranslateBtn.disabled = true;
                        return;
                    }

                    // 파일 형식 체크
                    const allowedTypes = [
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
                        'application/vnd.ms-excel' // .xls
                    ];

                    if (!allowedTypes.includes(file.type)) {
                        alert('엑셀 파일만 업로드 가능합니다. (.xlsx, .xls)');
                        e.target.value = '';
                        excelTranslateBtn.disabled = true;
                        return;
                    }

                    // 업로드 성공 - 번역 버튼 활성화
                    excelTranslateBtn.disabled = false;
                    console.log(`엑셀 파일 선택됨: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
                } else {
                    excelTranslateBtn.disabled = true;
                }
            });

            // 엑셀 번역 시작 버튼
            excelTranslateBtn.addEventListener('click', () => {
                this.startExcelTranslation();
            });
        }

        // 엑셀 다운로드 버튼 (동적으로 생성됨)
        document.addEventListener('click', (e) => {
            if (e.target.id === 'excel-download-btn') {
                this.downloadTranslatedExcel();
            }
        });
    }

    async startExcelTranslation() {
        const fileInput = document.getElementById('excel-translate-file');
        const progressDiv = document.getElementById('excel-translate-progress');
        const progressBar = document.getElementById('excel-translate-progress-bar');
        const progressText = document.getElementById('excel-translate-progress-text');
        const statusText = document.getElementById('excel-translate-status');
        const translateBtn = document.getElementById('excel-translate-btn');
        const resultDiv = document.getElementById('excel-translate-result');

        const file = fileInput.files[0];
        if (!file) {
            alert('파일을 선택해주세요.');
            return;
        }

        // 선택된 번역 엔진 확인
        const selectedEngine = document.querySelector('input[name="excel-translation-engine"]:checked').value;

        try {
            // UI 상태 변경
            translateBtn.disabled = true;
            translateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>번역 중...';
            progressDiv.style.display = 'block';
            resultDiv.style.display = 'none';

            // 진행률 업데이트
            this.updateExcelProgress(10, '파일을 업로드하는 중...');

            // FormData 생성
            const formData = new FormData();
            formData.append('excel_file', file);
            formData.append('translation_engine', selectedEngine);

            // 서버로 전송
            const response = await fetch('/api/excel-translate', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.status === 'processing') {
                console.log('🚀 엑셀 번역 세션 시작:', result.session_id);

                // 진행 상태 폴링 시작
                this.startExcelProgressPolling(result.session_id);

                // 예상 시간 표시
                this.updateExcelProgress(20, `번역 처리 시작됨 (예상 시간: ${result.estimated_time})`);

            } else if (result.status === 'success') {
                // 즉시 완료된 경우 (작은 파일)
                this.updateExcelProgress(100, '번역 완료!');
                this.showExcelResult(result);

            } else {
                throw new Error(result.error || '번역 중 오류가 발생했습니다.');
            }

        } catch (error) {
            console.error('엑셀 번역 오류:', error);
            alert(`번역 중 오류가 발생했습니다: ${error.message}`);

            // UI 상태 복원
            progressDiv.style.display = 'none';
            resultDiv.style.display = 'none';
        } finally {
            // 버튼 상태 복원
            translateBtn.disabled = false;
            translateBtn.innerHTML = '<i class="fas fa-language me-2"></i>엑셀 번역 시작';
        }
    }

    updateExcelProgress(percent, message) {
        const progressBar = document.getElementById('excel-translate-progress-bar');
        const progressText = document.getElementById('excel-translate-progress-text');
        const statusText = document.getElementById('excel-translate-status');

        if (progressBar) {
            progressBar.style.width = `${percent}%`;
        }
        if (progressText) {
            progressText.textContent = `${percent}%`;
        }
        if (statusText) {
            statusText.textContent = message;
        }

        console.log(`📊 엑셀 진행률: ${percent}% - ${message}`);
    }

    startExcelProgressPolling(sessionId) {
        console.log('🔄 엑셀 진행 상태 폴링 시작:', sessionId);

        // 기존 폴링 중지
        if (this.excelProgressInterval) {
            clearInterval(this.excelProgressInterval);
        }

        // 2초마다 진행 상태 확인
        this.excelProgressInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/excel-progress/${sessionId}`);
                const data = await response.json();

                if (data.status === 'error') {
                    console.error('❌ 엑셀 진행 상태 오류:', data.error);
                    clearInterval(this.excelProgressInterval);
                    this.updateExcelProgress(0, `오류: ${data.error}`);
                    this.resetExcelUI();
                    return;
                }

                // 진행 상태 업데이트
                const progress = data.progress;
                if (progress) {
                    this.updateExcelProgress(progress.percentage, progress.message);
                }

                // 완료 확인
                if (data.status === 'completed') {
                    console.log('✅ 엑셀 번역 완료:', data.result);
                    clearInterval(this.excelProgressInterval);

                    if (data.result && data.result.status === 'success') {
                        this.updateExcelProgress(100, `번역 완료! (${data.processing_time || '완료'})`);
                        setTimeout(() => this.showExcelResult(data.result), 1000);
                    } else {
                        this.updateExcelProgress(0, `오류: ${data.result?.error || '알 수 없는 오류'}`);
                        this.resetExcelUI();
                    }
                }

            } catch (error) {
                console.error('❌ 진행 상태 확인 오류:', error);
                clearInterval(this.excelProgressInterval);
                this.updateExcelProgress(0, '진행 상태 확인 실패');
                this.resetExcelUI();
            }
        }, 2000);
    }

    showExcelResult(result) {
        console.log('📊 엑셀 결과 표시:', result);

        // 올바른 ID로 요소 찾기
        const progressDiv = document.getElementById('excel-translate-progress');
        const resultDiv = document.getElementById('excel-translate-result');

        console.log('🔍 요소 확인:', { progressDiv: !!progressDiv, resultDiv: !!resultDiv });

        // 진행률 숨기고 결과 표시
        if (progressDiv) {
            progressDiv.style.display = 'none';
            console.log('✅ 진행률 div 숨김');
        }

        if (resultDiv) {
            resultDiv.style.display = 'block';
            console.log('✅ 결과 div 표시');
        } else {
            console.error('❌ 결과 div를 찾을 수 없음');
        }

        // 다운로드 버튼에 파일명 설정
        const downloadBtn = document.getElementById('excel-download-btn');
        if (downloadBtn && result.filename) {
            downloadBtn.setAttribute('data-filename', result.filename);
            downloadBtn.innerHTML = `<i class="fas fa-download me-2"></i>번역 파일 다운로드 (${result.translation_count}개 번역됨)`;

            // 다운로드 이벤트 리스너 설정
            downloadBtn.onclick = () => this.downloadExcelFile(result.filename);

            console.log('✅ 다운로드 버튼 설정 완료:', result.filename);
        } else {
            console.error('❌ 다운로드 버튼을 찾을 수 없거나 파일명 없음:', { downloadBtn: !!downloadBtn, filename: result.filename });
        }

        // 기존 성공 메시지 요소가 있는지 확인하고 업데이트
        const alertElement = resultDiv?.querySelector('.alert');
        if (alertElement) {
            // 메시지 업데이트
            const messageElement = alertElement.querySelector('strong');
            if (messageElement) {
                messageElement.nextSibling.textContent = ` ${result.message || `${result.translation_count}개 텍스트가 성공적으로 번역되었습니다.`}`;
            }
            console.log('✅ 성공 메시지 업데이트 완료');
        }
    }

    resetExcelUI() {
        const translateBtn = document.getElementById('excel-translate-btn');
        const progressDiv = document.getElementById('excel-progress');
        const resultDiv = document.getElementById('excel-result');

        if (translateBtn) {
            translateBtn.disabled = false;
            translateBtn.innerHTML = '<i class="fas fa-language me-2"></i>엑셀 번역 시작';
        }

        if (progressDiv) progressDiv.style.display = 'none';
        if (resultDiv) resultDiv.style.display = 'none';
    }

    async downloadTranslatedExcel() {
        const downloadBtn = document.getElementById('excel-download-btn');
        const filename = downloadBtn.getAttribute('data-filename');

        if (!filename) {
            alert('다운로드할 파일이 없습니다.');
            return;
        }

        try {
            // 원래 버튼 텍스트 저장
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>다운로드 중...';
            downloadBtn.disabled = true;

            // 파일 다운로드
            const response = await fetch(`/api/download-excel/${filename}`);

            if (!response.ok) {
                throw new Error('파일 다운로드에 실패했습니다.');
            }

            // Blob으로 변환하여 다운로드
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            window.URL.revokeObjectURL(url);

            console.log(`엑셀 파일 다운로드 완료: ${filename}`);

        } catch (error) {
            console.error('다운로드 오류:', error);
            alert(`다운로드 중 오류가 발생했습니다: ${error.message}`);
        } finally {
            // 버튼 복원
            downloadBtn.innerHTML = '<i class="fas fa-download me-2"></i>번역된 엑셀 다운로드';
            downloadBtn.disabled = false;
        }
    }

    updateSystemStatusAlert(data) {
        // 기존 시스템 상태 알림 업데이트
        let alertType = 'success';
        let message = '';

        switch(data.overall_status) {
            case 'ok':
                alertType = 'success';
                message = '✅ 모든 시스템이 정상 작동 중입니다';
                break;
            case 'warning':
                alertType = 'warning';
                message = `⚠️ 일부 시스템에 경고가 있습니다: ${data.summary}`;
                break;
            case 'error':
                alertType = 'danger';
                message = `❌ 시스템 오류가 발생했습니다: ${data.summary}`;
                break;
        }

        this.showAlert(message, alertType, data.overall_status);
    }

    showStatusLoading() {
        const loadingEl = document.querySelector('.status-loading');
        if (loadingEl) loadingEl.style.display = 'block';
        if (this.statusItems) this.statusItems.style.display = 'none';
        if (this.statusSummary) this.statusSummary.style.display = 'none';
    }

    showStatusError(errorMessage) {
        const loadingEl = document.querySelector('.status-loading');
        if (loadingEl) loadingEl.style.display = 'none';
        if (this.statusItems) this.statusItems.style.display = 'none';
        if (this.statusSummary) this.statusSummary.style.display = 'none';

        // 에러 메시지 표시
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-center text-danger p-4';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
            <p class="mb-0">${errorMessage}</p>
            <button class="btn btn-sm btn-outline-danger mt-2" onclick="xlt.checkSystemHealth()">다시 시도</button>
        `;

        if (this.statusContainer) {
            this.statusContainer.innerHTML = '';
            this.statusContainer.appendChild(errorDiv);
        }
    }

    async startTranslation() {
        try {
            // XLT System v4.0 - 수동 모드 + 번역 엔진 선택
            const processingMode = 'manual';

            // 선택된 번역 엔진 가져오기
            const translationEngine = document.querySelector('input[name="translation-engine"]:checked')?.value || 'google';

            // 로그 시작
            this.clearLog();
            this.addLog('🚀 번역 작업을 시작합니다...', 'info');

            // 동적 번역 엔진 로그 메시지 (v4.0 업데이트)
            let engineName = 'Google 번역 (기본)';
            if (translationEngine === 'claude_integrated') {
                engineName = 'Claude 통합 처리 (맞춤법+번역)';
            } else if (translationEngine === 'claude') {
                engineName = 'Claude AI (고품질)';
            }

            this.addLog(`🔧 번역 엔진: ${engineName}`, 'info');

            // Claude 번역 시 추가 안내
            if (translationEngine === 'claude_integrated') {
                this.addLog('✨ Claude 통합: 추출된 텍스트에 맞춤법 교정이 미리 적용되며, 번역 시에도 통합 처리됩니다', 'info');
            } else if (translationEngine === 'claude') {
                this.addLog('⏱️ Claude 번역은 최대 3분 소요될 수 있습니다', 'warning');
            }

            this.showProgress();

            const formData = new FormData();
            formData.append('input_type', 'figma');
            formData.append('mode', processingMode);
            formData.append('translation_mode', translationEngine);

            const figmaUrlElement = document.getElementById('figma-url');
            if (!figmaUrlElement) {
                this.addLog('❌ 피그마 URL 입력 필드를 찾을 수 없습니다', 'error');
                this.showAlert('페이지를 새로고침해주세요.', 'danger');
                this.hideProgress();
                return;
            }

            const figmaUrl = figmaUrlElement.value.trim();
            if (!figmaUrl) {
                this.addLog('❌ 피그마 URL이 입력되지 않았습니다', 'error');
                this.showAlert('피그마 URL을 입력해주세요.', 'warning');
                this.hideProgress();
                return;
            }
            this.addLog(`🎨 피그마 URL 처리: ${figmaUrl.substring(0, 50)}...`, 'info');
            formData.append('figma_url', figmaUrl);

            this.addLog(`⚙️ 처리 모드: 수동 모드 (XLT System v3.0 고정)`, 'info');

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            // 응답 타입 확인
            const contentType = response.headers.get("content-type");
            let result;

            if (contentType && contentType.indexOf("application/json") !== -1) {
                // JSON 응답
                result = await response.json();
            } else {
                // HTML 또는 기타 응답 (오류 페이지)
                const textResponse = await response.text();
                console.error('Non-JSON response:', textResponse);

                // HTML 응답에서 오류 정보 추출 시도
                if (textResponse.includes('<!doctype') || textResponse.includes('<html')) {
                    this.addLog(`❌ 서버에서 HTML 오류 페이지를 반환했습니다`, 'error');
                    this.showAlert('❌ 서버 오류가 발생했습니다. 콘솔을 확인해주세요.', 'danger');
                    this.hideProgress();
                    return;
                } else {
                    // 텍스트 오류 메시지 처리
                    result = {
                        status: 'error',
                        error: textResponse || '알 수 없는 오류가 발생했습니다.'
                    };
                }
            }

            this.hideProgress();

            if (result.status === 'success') {
                // 자동 모드 완료 - 실시간 로그 시작
                if (result.session_id) {
                    // 로그 폴링 제거됨 - 서버에서 API 비지원
                    // 잠시 후 결과 표시
                    setTimeout(() => {
                        this.addLog('✅ 번역이 완료되었습니다!', 'success');
                        this.showResult(result);
                        this.stopLogPolling();
                    }, 2000);
                } else {
                    this.addLog('✅ 번역이 완료되었습니다!', 'success');
                    this.showResult(result);
                }
            } else if (result.status === 'ocr_complete') {
                // 수동 모드 - 실시간 로그 시작
                console.log('🔍 텍스트 추출 완료 - 리디렉션 정보:', result);
                console.log('🔍 리디렉션 URL:', result.redirect);

                if (result.session_id) {
                    // 로그 폴링 제거됨 - 서버에서 API 비지원
                    // 페이지 이동 로딩 표시 시작
                    this.showPageTransitionLoading(result.redirect, result.session_id);

                    // 잠시 후 페이지 이동
                    setTimeout(() => {
                        this.addLog('📝 텍스트 추출 완료, 텍스트 선택 페이지로 이동합니다', 'success');
                        if (result.redirect) {
                            console.log('🔄 페이지 이동 실행:', result.redirect);
                            this.attemptRedirect(result.redirect);
                        } else {
                            console.error('❌ redirect 값이 없습니다:', result);
                            this.showRedirectError('리다이렉션 URL이 제공되지 않았습니다');
                        }
                    }, 1500);  // 1.5초로 약간 연장
                } else {
                    this.addLog('📝 텍스트 추출 완료, 텍스트 선택 페이지로 이동합니다', 'success');

                    // 즉시 이동도 로딩 표시
                    this.showPageTransitionLoading(result.redirect, result.session_id);

                    setTimeout(() => {
                        if (result.redirect) {
                            console.log('🔄 즉시 페이지 이동 실행:', result.redirect);
                            this.attemptRedirect(result.redirect);
                        } else {
                            console.error('❌ redirect 값이 없습니다:', result);
                            this.showRedirectError('리다이렉션 URL이 제공되지 않았습니다');
                        }
                    }, 500);
                }
            } else {
                // Claude 관련 오류 특별 처리 (XLT v4.0)
                if (result.error_type === 'ClaudeNotAvailable') {
                    this.handleClaudeError(result);
                } else {
                    this.addLog(`❌ 오류 발생: ${result.error}`, 'error');
                    this.showAlert(`❌ ${result.error}`, 'danger');
                }
            }

        } catch (error) {
            this.hideProgress();
            this.addLog(`❌ 네트워크 오류: ${error.message}`, 'error');
            this.showAlert(`❌ 네트워크 오류: ${error.message}`, 'danger');
        }
    }

    showProgress() {
        document.getElementById('progress-section').style.display = 'block';
        document.getElementById('result-section').style.display = 'none';
        document.getElementById('translate-btn').disabled = true;

        // 진행 메시지 업데이트
        let step = 0;
        const messages = [
            '이미지를 업로드하고 있습니다...',
            '피그마에서 텍스트를 추출하고 있습니다...',
            '번역을 진행하고 있습니다...',
            'Excel 파일을 생성하고 있습니다...'
        ];

        const updateProgress = () => {
            if (step < messages.length) {
                document.getElementById('progress-message').textContent = messages[step];
                step++;
                setTimeout(updateProgress, 2000);
            }
        };

        updateProgress();
    }

    hideProgress() {
        document.getElementById('progress-section').style.display = 'none';
        document.getElementById('translate-btn').disabled = false;
    }

    showResult(result) {
        const resultContent = document.getElementById('result-content');
        resultContent.innerHTML = `
            <div class="result-summary">
                <div class="row">
                    <div class="col-md-6">
                        <div class="result-item">
                            <strong>소스:</strong><br>
                            <span class="text-muted">${result.source_description}</span>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="result-item">
                            <strong>번역된 항목:</strong><br>
                            <span class="badge bg-primary fs-6">${result.processed_count}개</span>
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <div class="result-item">
                        <strong>출력 파일:</strong><br>
                        <code>${result.output_file}</code>
                    </div>
                </div>
            </div>
        `;

        // 다운로드 버튼에 파일명 설정
        document.getElementById('download-btn').setAttribute('data-filename', result.output_file);

        document.getElementById('result-section').style.display = 'block';
        document.getElementById('result-section').classList.add('fade-in');
    }

    downloadResult() {
        try {
            const downloadBtn = document.getElementById('download-btn');
            if (!downloadBtn) {
                console.error('Download button not found');
                return;
            }

            const filename = downloadBtn.getAttribute('data-filename');
            if (filename) {
                window.location.href = `/download/${filename}`;
            } else {
                console.error('No filename specified for download');
            }
        } catch (error) {
            console.error('Download error:', error);
        }
    }

    handleClaudeError(result) {
        /**
         * Claude 번역기 오류 시 사용자 친화적 처리
         */
        this.addLog(`❌ Claude 번역 오류: Claude CLI가 설치되지 않았습니다`, 'error');

        // 상세 안내 모달 표시
        const modalHtml = `
            <div class="modal fade" id="claude-error-modal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title">
                                <i class="fas fa-robot me-2"></i>Claude 번역을 사용할 수 없습니다
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-lightbulb me-2"></i>
                                <strong>Claude 번역이란?</strong><br>
                                더 자연스럽고 문맥을 고려한 AI 번역을 제공합니다.
                            </div>

                            <h6><i class="fas fa-download me-2"></i>Claude CLI 설치 방법:</h6>
                            <ol>
                                <li>웹사이트 방문: <a href="https://claude.ai/download" target="_blank" class="text-primary">https://claude.ai/download</a></li>
                                <li>운영체제에 맞는 버전 다운로드</li>
                                <li>설치 후 터미널에서 확인: <code>claude --version</code></li>
                            </ol>

                            <div class="alert alert-success">
                                <i class="fas fa-magic me-2"></i>
                                <strong>지금 바로 번역하려면?</strong><br>
                                Google 번역을 선택해서 계속 진행하세요!
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" onclick="xlt.switchToGoogleTranslation()">
                                <i class="fab fa-google me-2"></i>Google 번역으로 계속하기
                            </button>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                닫기
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 기존 모달 제거 후 새로 추가
        const existingModal = document.getElementById('claude-error-modal');
        if (existingModal) {
            existingModal.remove();
        }

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('claude-error-modal'));
        modal.show();
    }

    switchToGoogleTranslation() {
        /**
         * Google 번역으로 자동 전환
         */
        const googleRadio = document.getElementById('engine-google');
        if (googleRadio) {
            googleRadio.checked = true;
            this.addLog('🌐 Google 번역으로 전환되었습니다', 'info');

            // 모달 닫기
            const modal = bootstrap.Modal.getInstance(document.getElementById('claude-error-modal'));
            if (modal) {
                modal.hide();
            }

            // 잠시 후 자동으로 번역 재시작 제안
            setTimeout(() => {
                this.showAlert('Google 번역으로 전환되었습니다. 다시 번역 시작을 클릭하세요.', 'success');
            }, 500);
        }
    }

    resetForm() {
        try {
            // 폼 리셋 - null 체크 추가
            const figmaUrlElement = document.getElementById('figma-url');
            if (figmaUrlElement) {
                figmaUrlElement.value = '';
            }

            const resultSection = document.getElementById('result-section');
            if (resultSection) {
                resultSection.style.display = 'none';
            }

            const progressSection = document.getElementById('progress-section');
            if (progressSection) {
                progressSection.style.display = 'none';
            }

            // 로그 초기화
            this.clearLog();
            this.stopLogPolling();

            // 페이지 상단으로 스크롤
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (error) {
            console.error('Reset form error:', error);
        }
    }

    // 실시간 로그 관련 메서드들
    addLog(message, type = 'info') {
        // 로그 컨테이너가 없으면 콘솔에만 출력
        if (!this.logContainer) {
            console.log(`[${type.toUpperCase()}] ${message}`);
            return;
        }

        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="timestamp">[${timestamp}]</span> ${message}
        `;

        // 환영 메시지 제거
        const welcome = this.logContainer.querySelector('.log-welcome');
        if (welcome) {
            welcome.remove();
        }

        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }

    clearLog() {
        // 로그 컨테이너가 없으면 무시
        if (!this.logContainer) {
            return;
        }

        this.logContainer.innerHTML = `
            <div class="log-welcome">
                <div class="text-center text-muted p-4">
                    <i class="fas fa-info-circle fa-2x mb-3"></i>
                    <p class="mb-0">번역 작업을 시작하면<br>실시간 처리 로그가 표시됩니다.</p>
                </div>
            </div>
        `;
    }

    startLogPolling(sessionId) {
        // 기존 폴링 중지
        this.stopLogPolling();

        // 새 폴링 시작
        this.logInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/logs/${sessionId}`);
                const contentType = response.headers.get("content-type");

                let data;
                if (contentType && contentType.indexOf("application/json") !== -1) {
                    data = await response.json();
                } else {
                    console.warn('Non-JSON response from log API');
                    return; // JSON이 아니면 이번 폴링은 스킵
                }

                if (data.status === 'success' && data.logs) {
                    data.logs.forEach(log => {
                        this.addLog(log.message, log.type);
                    });
                }

                // 작업 완료 시 폴링 중지
                if (data.completed) {
                    this.stopLogPolling();
                }
            } catch (error) {
                console.error('Log polling error:', error);
                // 연속적인 오류 발생 시 폴링 중지
                if (error.message.includes('JSON')) {
                    console.warn('JSON 파싱 오류로 인해 로그 폴링을 중지합니다');
                    this.stopLogPolling();
                }
            }
        }, 1000); // 1초마다 폴링
    }

    stopLogPolling() {
        if (this.logInterval) {
            clearInterval(this.logInterval);
            this.logInterval = null;
        }
    }

    showAlert(message, type, systemStatus = null) {
        const alertElement = document.getElementById('status-alert');
        alertElement.className = `alert alert-${type} d-flex align-items-center justify-content-between`;

        // 시스템 상태가 오류나 경고인 경우 설정 버튼 추가
        let settingsButton = '';
        if (systemStatus === 'error' || systemStatus === 'warning') {
            settingsButton = `
                <a href="/settings" class="btn btn-outline-${type === 'danger' ? 'danger' : 'warning'} btn-sm ms-3">
                    <i class="fas fa-cog me-1"></i>
                    설정 확인
                </a>
            `;
        }

        alertElement.innerHTML = `
            <div class="d-flex align-items-center flex-grow-1">
                <i class="fas fa-${type === 'success' ? 'check-circle' :
                                     type === 'danger' ? 'exclamation-circle' :
                                     type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                <span>${message}</span>
            </div>
            ${settingsButton}
        `;
    }

    // 피그마 미리보기 관련 메서드들
    async loadFigmaPreview(figmaUrl) {
        try {
            console.log('피그마 미리보기 로드 시작:', figmaUrl);

            // URL 기본 검증
            if (!figmaUrl.includes('figma.com')) {
                this.showFigmaError('올바른 Figma URL을 입력해주세요.');
                this.setFigmaInputState('error');
                return;
            }

            // 로딩 상태 표시
            this.showFigmaLoading();
            this.setFigmaInputState('loading');

            // API 요청
            const response = await fetch('/api/figma-preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    figma_url: figmaUrl
                })
            });

            const contentType = response.headers.get("content-type");
            let data;

            if (contentType && contentType.indexOf("application/json") !== -1) {
                data = await response.json();
            } else {
                throw new Error('서버에서 JSON이 아닌 응답을 반환했습니다');
            }

            if (data.status === 'success') {
                this.showFigmaImage(data.image_data, data.metadata);
                this.setFigmaInputState('success');
                console.log('피그마 미리보기 로드 성공');
            } else {
                this.showFigmaError(data.error || '이미지를 로드할 수 없습니다');
                this.setFigmaInputState('error');
                console.error('피그마 미리보기 오류:', data.error);
            }

        } catch (error) {
            console.error('피그마 미리보기 네트워크 오류:', error);
            this.showFigmaError(`네트워크 오류: ${error.message}`);
            this.setFigmaInputState('error');
        }
    }

    showFigmaLoading() {
        const previewContainer = document.getElementById('figma-preview');
        const loadingDiv = document.getElementById('figma-loading');
        const imageDiv = document.getElementById('figma-image-container');
        const errorDiv = document.getElementById('figma-error');

        // 컨테이너 표시
        previewContainer.style.display = 'block';

        // 상태 초기화
        loadingDiv.style.display = 'block';
        imageDiv.style.display = 'none';
        errorDiv.style.display = 'none';

        // 컨테이너 클래스 설정
        const container = previewContainer.querySelector('.figma-preview-container');
        container.className = 'figma-preview-container loading';
    }

    showFigmaImage(imageData, metadata) {
        const previewContainer = document.getElementById('figma-preview');
        const loadingDiv = document.getElementById('figma-loading');
        const imageDiv = document.getElementById('figma-image-container');
        const errorDiv = document.getElementById('figma-error');

        // 이미지 설정
        const imgElement = document.getElementById('figma-preview-img');
        imgElement.src = imageData;

        // 메타데이터 설정
        if (metadata) {
            document.getElementById('figma-dimensions').textContent = `${metadata.width} × ${metadata.height}`;
            document.getElementById('figma-node').textContent = metadata.node_id || 'Unknown';
        }

        // 상태 변경
        loadingDiv.style.display = 'none';
        imageDiv.style.display = 'block';
        errorDiv.style.display = 'none';

        // 컨테이너 클래스 설정
        const container = previewContainer.querySelector('.figma-preview-container');
        container.className = 'figma-preview-container success';
    }

    showFigmaError(errorMessage) {
        const previewContainer = document.getElementById('figma-preview');
        const loadingDiv = document.getElementById('figma-loading');
        const imageDiv = document.getElementById('figma-image-container');
        const errorDiv = document.getElementById('figma-error');

        // 에러 메시지 설정
        document.getElementById('figma-error-message').textContent = errorMessage;

        // 상태 변경
        loadingDiv.style.display = 'none';
        imageDiv.style.display = 'none';
        errorDiv.style.display = 'block';

        // 컨테이너 클래스 설정
        const container = previewContainer.querySelector('.figma-preview-container');
        container.className = 'figma-preview-container error';

        // 컨테이너 표시
        previewContainer.style.display = 'block';
    }

    hideFigmaPreview() {
        const previewContainer = document.getElementById('figma-preview');
        previewContainer.style.display = 'none';
        this.setFigmaInputState('normal');
    }

    setFigmaInputState(state) {
        const figmaUrlInput = document.getElementById('figma-url');

        // 이전 상태 클래스 제거
        figmaUrlInput.classList.remove('loading', 'error', 'success');

        // 새 상태 클래스 추가
        if (state === 'loading') {
            figmaUrlInput.classList.add('loading');
        } else if (state === 'error') {
            figmaUrlInput.classList.add('error');
        } else if (state === 'success') {
            figmaUrlInput.classList.add('success');
        }
    }

    // ===== 엑셀 합치기 기능 =====

    handleExcelFilesChange(e) {
        const files = Array.from(e.target.files);
        console.log(`선택된 파일 ${files.length}개:`, files.map(f => f.name));

        if (files.length === 0) {
            this.hideSelectedFilesList();
            this.updateMergeButton(false);
            return;
        }

        // 파일 검증
        const validFiles = [];
        const invalidFiles = [];

        files.forEach(file => {
            if (this.isValidExcelFile(file)) {
                validFiles.push(file);
            } else {
                invalidFiles.push(file);
            }
        });

        if (invalidFiles.length > 0) {
            this.showAlert(`올바르지 않은 파일: ${invalidFiles.map(f => f.name).join(', ')}`, 'warning');
        }

        if (validFiles.length === 0) {
            this.hideSelectedFilesList();
            this.updateMergeButton(false);
            return;
        }

        // 파일 목록 표시
        this.displaySelectedFiles(validFiles);
        this.updateMergeButton(true);
    }

    isValidExcelFile(file) {
        const validTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ];
        const validExtensions = ['.xlsx', '.xls'];

        return validTypes.includes(file.type) ||
               validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }

    displaySelectedFiles(files) {
        const container = document.getElementById('selected-files-container');
        const list = document.getElementById('selected-files-list');

        if (!container || !list) return;

        let html = '';
        files.forEach((file, index) => {
            const fileSize = this.formatFileSize(file.size);
            const fileName = file.name.length > 40 ? file.name.substring(0, 37) + '...' : file.name;

            html += `
                <div class="selected-file-item d-flex justify-content-between align-items-center py-2 border-bottom">
                    <div class="file-info">
                        <div class="fw-bold text-truncate">${fileName}</div>
                        <small class="text-muted">${fileSize}</small>
                    </div>
                    <div class="file-actions">
                        <button type="button" class="btn btn-outline-danger btn-sm" onclick="window.xltInterface.removeFile(${index})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `;
        });

        list.innerHTML = html;
        container.style.display = 'block';

        // 전역 파일 참조 저장
        window.selectedExcelFiles = files;
        window.xltInterface = this;
    }

    removeFile(index) {
        const fileInput = document.getElementById('excel-files');
        if (!fileInput || !window.selectedExcelFiles) return;

        // 파일 배열에서 제거
        const files = Array.from(window.selectedExcelFiles);
        files.splice(index, 1);

        if (files.length === 0) {
            this.clearSelectedFiles();
            return;
        }

        // 새로운 FileList 생성 (직접 조작 불가하므로 우회)
        const dt = new DataTransfer();
        files.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;

        // 화면 업데이트
        this.displaySelectedFiles(files);
    }

    clearSelectedFiles() {
        const fileInput = document.getElementById('excel-files');
        const container = document.getElementById('selected-files-container');

        if (fileInput) fileInput.value = '';
        if (container) container.style.display = 'none';

        this.updateMergeButton(false);
        window.selectedExcelFiles = null;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    updateMergeButton(hasFiles) {
        const mergeBtn = document.getElementById('merge-excel-btn');
        if (!mergeBtn) return;

        mergeBtn.disabled = !hasFiles;
        this.updateMergeButtonText();
    }

    updateMergeButtonText() {
        const mergeBtn = document.getElementById('merge-excel-btn');
        const outputFilename = document.getElementById('output-filename');

        if (!mergeBtn) return;

        const fileCount = window.selectedExcelFiles ? window.selectedExcelFiles.length : 0;
        const customName = outputFilename ? outputFilename.value.trim() : '';

        if (fileCount === 0) {
            mergeBtn.innerHTML = '<i class="fas fa-compress-arrows-alt me-2"></i>Excel 파일 합치기';
        } else if (customName) {
            mergeBtn.innerHTML = `<i class="fas fa-compress-arrows-alt me-2"></i>${fileCount}개 파일을 "${customName}.xlsx"로 합치기`;
        } else {
            mergeBtn.innerHTML = `<i class="fas fa-compress-arrows-alt me-2"></i>${fileCount}개 파일 합치기`;
        }
    }

    async mergeExcelFiles() {
        const files = window.selectedExcelFiles;
        if (!files || files.length === 0) {
            this.showAlert('선택된 파일이 없습니다.', 'warning');
            return;
        }

        // 진행 상태 표시
        this.showMergeProgress(true);

        try {
            // FormData 생성
            const formData = new FormData();

            // 파일들 추가
            files.forEach(file => {
                formData.append('files', file);
            });

            // 옵션들 추가
            const removeDuplicates = document.getElementById('remove-duplicates')?.checked ?? true;
            const sortByKey = document.getElementById('sort-by-key')?.checked ?? true;
            const outputFilename = document.getElementById('output-filename')?.value?.trim() ?? '';

            formData.append('remove_duplicates', removeDuplicates);
            formData.append('sort_by_key', sortByKey);
            formData.append('output_filename', outputFilename);

            console.log('엑셀 합치기 시작:', {
                fileCount: files.length,
                removeDuplicates,
                sortByKey,
                outputFilename
            });

            // API 호출
            const response = await fetch('/merge-excel', {
                method: 'POST',
                body: formData
            });

            // 성공 시 파일 다운로드, 실패 시 JSON 응답 처리
            if (response.ok && response.headers.get('content-type')?.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
                // 엑셀 파일 다운로드 처리
                const blob = await response.blob();
                const filename = response.headers.get('content-disposition')?.match(/filename=([^;]+)/)?.[1] || 'merged_translations.xlsx';

                const downloadUrl = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename.replace(/"/g, ''); // 따옴표 제거
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(downloadUrl);

                this.showAlert(`✅ 엑셀 파일이 성공적으로 합쳐져서 다운로드되었습니다!`, 'success');
            } else {
                // 오류 응답 JSON 처리
                const result = await response.json();
                throw new Error(result.error || '알 수 없는 오류가 발생했습니다.');
            }

        } catch (error) {
            console.error('엑셀 합치기 오류:', error);
            this.showAlert(`❌ 엑셀 합치기 실패: ${error.message}`, 'danger');
        } finally {
            this.showMergeProgress(false);
        }
    }

    showMergeProgress(show) {
        const progressDiv = document.getElementById('merge-progress');
        const mergeBtn = document.getElementById('merge-excel-btn');
        const progressText = document.getElementById('merge-progress-text');

        if (progressDiv) {
            progressDiv.style.display = show ? 'block' : 'none';
        }

        if (mergeBtn) {
            mergeBtn.disabled = show;
        }

        if (show && progressText) {
            let step = 0;
            const steps = [
                '파일을 분석하는 중...',
                '데이터를 읽는 중...',
                '중복을 확인하는 중...',
                '파일을 합치는 중...',
                '결과 파일을 생성하는 중...'
            ];

            const updateProgress = () => {
                if (step < steps.length && progressDiv.style.display !== 'none') {
                    progressText.textContent = steps[step];
                    step++;
                    setTimeout(updateProgress, 800);
                }
            };
            updateProgress();
        }
    }

    showMergeResult(result) {
        const resultDiv = document.getElementById('merge-result');
        const detailsDiv = document.getElementById('merge-result-details');
        const downloadBtn = document.getElementById('download-merged-btn');

        if (!resultDiv || !detailsDiv || !downloadBtn) return;

        // 결과 상세 정보
        let details = `
            <small class="text-muted d-block">
                • 총 ${result.total_rows}개 항목 합쳐짐<br>
                • 처리된 파일: ${result.processed_files.length}개<br>
                • 파일명: <strong>${result.output_file}</strong>
            </small>
        `;

        // 실패한 파일이 있다면 표시
        const failedFiles = result.processed_files.filter(f => f.error);
        if (failedFiles.length > 0) {
            details += `<div class="mt-2 text-warning"><small>⚠️ 처리 실패: ${failedFiles.map(f => f.filename).join(', ')}</small></div>`;
        }

        detailsDiv.innerHTML = details;

        // 다운로드 버튼에 파일명 설정
        downloadBtn.setAttribute('data-filename', result.output_file);

        // 결과 표시
        resultDiv.style.display = 'block';
        resultDiv.scrollIntoView({ behavior: 'smooth' });

        // 저장된 파일명 (다운로드용)
        this.mergedFileName = result.output_file;
    }

    downloadMergedFile() {
        const filename = this.mergedFileName;

        if (!filename) {
            this.showAlert('다운로드할 파일이 없습니다.', 'warning');
            return;
        }

        console.log(`합친 엑셀 파일 다운로드: ${filename}`);

        // 다운로드 링크 생성
        const link = document.createElement('a');
        link.href = `/download/${filename}`;
        link.download = filename;
        link.style.display = 'none';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showAlert('✅ 파일 다운로드가 시작되었습니다.', 'success');
    }

    // =====================================
    // 업데이트 관리 기능
    // =====================================

    async checkForUpdates() {
        try {
            const response = await fetch('/api/update/check');
            const data = await response.json();

            if (data.status === 'success') {
                this.handleUpdateCheckResult(data.update_info);
            } else {
                console.warn('업데이트 확인 실패:', data.error);
            }
        } catch (error) {
            console.error('업데이트 확인 오류:', error);
        }
    }

    handleUpdateCheckResult(updateInfo) {
        const updateContainer = document.getElementById('update-container');

        if (updateInfo.update_available) {
            const behind = updateInfo.behind_commits || 0;
            const latest = updateInfo.remote;

            // 업데이트 알림 표시
            this.showUpdateNotification(latest, behind);

            console.log('🎉 업데이트 발견:', {
                current: updateInfo.current.short_hash,
                latest: latest.short_hash,
                behind: behind
            });
        } else {
            console.log('✅ 최신 버전 사용 중');
            this.hideUpdateNotification();
        }
    }

    showUpdateNotification(latestVersion, behindCommits) {
        // 헤더에 업데이트 버튼 추가
        const headerControls = document.querySelector('header .d-flex .btn-settings').parentElement;

        // 기존 업데이트 버튼 제거
        const existingBtn = document.getElementById('update-btn');
        if (existingBtn) {
            existingBtn.remove();
        }

        // 새 업데이트 버튼 생성
        const updateBtn = document.createElement('button');
        updateBtn.id = 'update-btn';
        updateBtn.className = 'btn btn-warning btn-sm me-2';
        updateBtn.innerHTML = `
            <i class="fas fa-download me-1"></i>
            업데이트 (${behindCommits})
        `;
        updateBtn.title = `새 업데이트 ${behindCommits}개 발견: ${latestVersion.message}`;
        updateBtn.onclick = () => this.showUpdateModal(latestVersion, behindCommits);

        // 설정 버튼 앞에 삽입
        const settingsBtn = document.querySelector('.btn-settings');
        headerControls.insertBefore(updateBtn, settingsBtn);

        // 상태 알림도 업데이트
        const statusAlert = document.getElementById('status-alert');
        if (statusAlert) {
            statusAlert.className = 'alert alert-warning d-flex align-items-center';
            statusAlert.innerHTML = `
                <i class="fas fa-download me-2"></i>
                <span>새로운 업데이트 ${behindCommits}개가 발견되었습니다! <strong>${latestVersion.message}</strong></span>
                <button class="btn btn-sm btn-outline-warning ms-auto" onclick="xltInterface.showUpdateModal()">
                    업데이트
                </button>
            `;
        }
    }

    hideUpdateNotification() {
        // 업데이트 버튼 제거
        const updateBtn = document.getElementById('update-btn');
        if (updateBtn) {
            updateBtn.remove();
        }

        // 상태 알림을 기본 상태로 복원
        const statusAlert = document.getElementById('status-alert');
        if (statusAlert) {
            statusAlert.className = 'alert alert-success d-flex align-items-center';
            statusAlert.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                <span>XLT 시스템이 정상 작동하고 있습니다. (최신 버전)</span>
            `;
        }
    }

    getDisplayVersion(versionInfo) {
        // 버전 정보에서 사용자 친화적인 표시 형태 반환
        if (versionInfo && versionInfo.version && versionInfo.version !== 'unknown') {
            // 버전 번호가 있으면 v 프리픽스 추가
            return versionInfo.version.startsWith('v') ? versionInfo.version : `v${versionInfo.version}`;
        } else if (versionInfo && versionInfo.short_hash) {
            // 버전 번호가 없으면 커밋 해시 사용 (fallback)
            return versionInfo.short_hash;
        } else {
            // 둘 다 없으면 기본값
            return 'unknown';
        }
    }

    showUpdateModal(latestVersion = null, behindCommits = 0) {
        // 업데이트 모달 HTML 생성
        const modalHTML = `
        <div class="modal fade" id="updateModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-warning text-dark">
                        <h5 class="modal-title">
                            <i class="fas fa-download me-2"></i>
                            XLT 시스템 업데이트
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div id="update-content">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">업데이트 정보 로딩 중...</span>
                                </div>
                                <p class="mt-2">업데이트 정보를 확인하고 있습니다...</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
                        <button type="button" class="btn btn-warning" id="perform-update-btn" onclick="xltInterface.performUpdate()" disabled>
                            <i class="fas fa-download me-1"></i>
                            업데이트 실행
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;

        // 기존 모달 제거
        const existingModal = document.getElementById('updateModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 새 모달 추가
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('updateModal'));
        modal.show();

        // 업데이트 정보 로드
        this.loadUpdateInfo();
    }

    async loadUpdateInfo() {
        try {
            // 업데이트 상태 조회
            const [checkResponse, historyResponse, statusResponse] = await Promise.all([
                fetch('/api/update/check'),
                fetch('/api/update/history?limit=5'),
                fetch('/api/update/status')
            ]);

            const checkData = await checkResponse.json();
            const historyData = await historyResponse.json();
            const statusData = await statusResponse.json();

            if (checkData.status === 'success' && historyData.status === 'success' && statusData.status === 'success') {
                this.renderUpdateInfo(checkData.update_info, historyData.history, statusData);
            } else {
                throw new Error('업데이트 정보 조회 실패');
            }
        } catch (error) {
            console.error('업데이트 정보 로드 오류:', error);
            document.getElementById('update-content').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    업데이트 정보를 불러올 수 없습니다: ${error.message}
                </div>
            `;
        }
    }

    renderUpdateInfo(updateInfo, history, status) {
        const updateBtn = document.getElementById('perform-update-btn');
        let content = '';

        if (updateInfo.update_available) {
            const current = updateInfo.current;
            const remote = updateInfo.remote;
            const behind = updateInfo.behind_commits || 0;

            content = `
                <div class="alert alert-info">
                    <h6><i class="fas fa-info-circle me-2"></i>업데이트 정보</h6>
                    <div class="row">
                        <div class="col-6">
                            <strong>현재 버전:</strong><br>
                            <code>${this.getDisplayVersion(current)}</code><br>
                            <small class="text-muted">${current.message}</small>
                        </div>
                        <div class="col-6">
                            <strong>최신 버전:</strong><br>
                            <code>${this.getDisplayVersion(remote)}</code><br>
                            <small class="text-muted">${remote.message}</small>
                        </div>
                    </div>
                    <hr>
                    <p class="mb-0">
                        <strong>${behind}개의 새로운 업데이트</strong>가 있습니다.
                        ${status.has_local_changes ? '<br><span class="text-warning">⚠️ 로컬 변경사항이 감지되었습니다.</span>' : ''}
                    </p>
                </div>

                <div class="mb-3">
                    <h6><i class="fas fa-history me-2"></i>최근 업데이트 내역</h6>
                    <div class="list-group">
                        ${history.slice(0, 5).map(commit => `
                            <div class="list-group-item">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <h6 class="mb-1">${commit.message}</h6>
                                        <small class="text-muted">by ${commit.author}</small>
                                    </div>
                                    <small class="text-muted">${new Date(commit.date).toLocaleDateString()}</small>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="alert alert-warning">
                    <h6><i class="fas fa-exclamation-triangle me-2"></i>업데이트 주의사항</h6>
                    <ul class="mb-0">
                        <li>업데이트 전 자동으로 백업이 생성됩니다</li>
                        <li>업데이트 중 서버가 잠시 중단됩니다</li>
                        <li>업데이트 완료 후 서버 재시작이 필요합니다</li>
                        ${status.has_local_changes ? '<li class="text-warning">로컬 변경사항은 임시 저장됩니다</li>' : ''}
                    </ul>
                </div>
            `;

            updateBtn.disabled = false;
        } else {
            content = `
                <div class="alert alert-success">
                    <h6><i class="fas fa-check-circle me-2"></i>최신 버전 사용 중</h6>
                    <p class="mb-0">현재 XLT 시스템이 최신 버전입니다.</p>
                </div>
            `;
            updateBtn.disabled = true;
        }

        document.getElementById('update-content').innerHTML = content;
    }

    async performUpdate() {
        const updateBtn = document.getElementById('perform-update-btn');
        const originalText = updateBtn.innerHTML;

        try {
            // 업데이트 버튼 비활성화
            updateBtn.disabled = true;
            updateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> 업데이트 중...';

            // 업데이트 실행
            const response = await fetch('/api/update/perform', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    create_backup: true
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                // 성공 메시지 표시
                document.getElementById('update-content').innerHTML = `
                    <div class="alert alert-success">
                        <h6><i class="fas fa-check-circle me-2"></i>업데이트 완료!</h6>
                        <p>${result.message}</p>
                        ${result.backup_path ? `<p><small class="text-muted">백업 위치: ${result.backup_path}</small></p>` : ''}
                        <div class="mt-3">
                            <h6>업데이트 로그:</h6>
                            <pre class="bg-light p-2 rounded">${result.update_log.join('\n')}</pre>
                        </div>
                    </div>
                `;

                // 버튼 변경
                updateBtn.innerHTML = '<i class="fas fa-refresh me-1"></i> 페이지 새로고침';
                updateBtn.onclick = () => window.location.reload();
                updateBtn.disabled = false;

                // 자동 새로고침 (5초 후)
                setTimeout(() => {
                    window.location.reload();
                }, 5000);

            } else {
                throw new Error(result.error || '업데이트 실행 실패');
            }

        } catch (error) {
            console.error('업데이트 실행 오류:', error);

            document.getElementById('update-content').innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fas fa-exclamation-circle me-2"></i>업데이트 실패</h6>
                    <p>${error.message}</p>
                    <p class="mb-0"><small class="text-muted">백업에서 복원이 필요할 수 있습니다.</small></p>
                </div>
            `;

            // 버튼 복원
            updateBtn.innerHTML = originalText;
            updateBtn.disabled = false;
        }
    }

    // 페이지 전환 로딩 표시
    showPageTransitionLoading(redirectUrl = null, sessionId = null) {
        // 기존 오버레이가 있다면 제거
        const existingOverlay = document.getElementById('page-transition-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        // 전체 화면 로딩 오버레이 생성
        const overlay = document.createElement('div');
        overlay.id = 'page-transition-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            backdrop-filter: blur(3px);
            animation: fadeIn 0.3s ease-in-out;
        `;

        // 로딩 스피너
        const spinner = document.createElement('div');
        spinner.style.cssText = `
            width: 60px;
            height: 60px;
            border: 4px solid rgba(255, 255, 255, 0.2);
            border-left: 4px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        `;

        // 로딩 메시지
        const message = document.createElement('div');
        message.style.cssText = `
            color: white;
            font-size: 18px;
            font-weight: 500;
            text-align: center;
            margin-bottom: 10px;
        `;
        message.innerHTML = '<i class="fas fa-arrow-right me-2"></i>텍스트 선택 페이지로 이동 중...';

        // 진행률 바
        const progressContainer = document.createElement('div');
        progressContainer.style.cssText = `
            width: 300px;
            height: 4px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 15px;
        `;

        const progressBar = document.createElement('div');
        progressBar.style.cssText = `
            width: 0%;
            height: 100%;
            background: #007bff;
            border-radius: 2px;
            transition: width 0.3s ease;
        `;

        progressContainer.appendChild(progressBar);

        // 요소들 조립
        overlay.appendChild(spinner);
        overlay.appendChild(message);
        overlay.appendChild(progressContainer);

        // 리다이렉션 정보 저장 (에러 시 사용)
        if (redirectUrl) overlay.setAttribute('data-redirect-url', redirectUrl);
        if (sessionId) overlay.setAttribute('data-session-id', sessionId);

        // 페이지에 추가
        document.body.appendChild(overlay);

        // CSS 애니메이션 정의 (한 번만 추가)
        if (!document.getElementById('page-transition-styles')) {
            const style = document.createElement('style');
            style.id = 'page-transition-styles';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }

        // 진행률 바 애니메이션
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15 + 5; // 5-20% 씩 증가
            if (progress > 90) progress = 90; // 90%까지만
            progressBar.style.width = progress + '%';
        }, 200);

        // 페이지 이동 전 정리를 위해 interval을 저장
        overlay.progressInterval = progressInterval;

        console.log('🎬 페이지 전환 로딩 오버레이 표시 완료');
    }

    // 리다이렉션 시도 (에러 핸들링 포함)
    async attemptRedirect(redirectUrl) {
        try {
            console.log('🔄 리다이렉션 시도 중:', redirectUrl);

            // 세션 ID 추출
            const urlParams = new URLSearchParams(redirectUrl.split('?')[1]);
            const sessionId = urlParams.get('session_id');

            if (sessionId) {
                console.log('🔍 세션 유효성 검증 중:', sessionId);

                // 세션 검증
                const response = await fetch('/api/session/validate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({session_id: sessionId})
                });

                if (response.ok) {
                    const validation = await response.json();
                    console.log('✅ 세션 유효성 확인됨:', validation);
                } else {
                    const error = await response.json();
                    console.error('❌ 세션 무효:', error);
                    this.showRedirectError(`세션이 만료되었거나 찾을 수 없습니다: ${error.error}`);
                    return;
                }
            }

            // 5초 타임아웃 설정
            const redirectTimeout = setTimeout(() => {
                console.error('⚠️ 리다이렉션 타임아웃 (5초 초과)');
                this.showRedirectError('페이지 로딩이 너무 오래 걸리고 있습니다');
            }, 5000);

            // 페이지 이동 실행
            window.location.href = redirectUrl;

            // 성공 시 타임아웃 제거
            clearTimeout(redirectTimeout);

        } catch (error) {
            console.error('❌ 리다이렉션 실패:', error);
            this.showRedirectError('페이지 이동 중 오류가 발생했습니다: ' + error.message);
        }
    }

    // 리다이렉션 실패 시 수동 옵션 표시
    showRedirectError(errorMessage) {
        const overlay = document.getElementById('page-transition-overlay');
        if (!overlay) return;

        // 기존 진행률 바 애니메이션 정리
        if (overlay.progressInterval) {
            clearInterval(overlay.progressInterval);
        }

        // 오버레이 내용 변경
        overlay.innerHTML = `
            <div style="color: #dc3545; font-size: 20px; margin-bottom: 20px;">
                <i class="fas fa-exclamation-triangle me-2"></i>페이지 이동 실패
            </div>
            <div style="color: white; font-size: 16px; text-align: center; margin-bottom: 30px; line-height: 1.5;">
                ${errorMessage}<br>
                아래 버튼을 클릭하여 수동으로 계속하세요.
            </div>
            <div style="display: flex; gap: 15px; flex-direction: column; align-items: center;">
                <button id="manual-continue-btn" style="
                    background: #007bff;
                    border: none;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 16px;
                    cursor: pointer;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    transition: background-color 0.2s;
                ">
                    <i class="fas fa-arrow-right me-2"></i>텍스트 선택 페이지로 이동
                </button>
                <button id="restart-btn" style="
                    background: #6c757d;
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-size: 14px;
                    cursor: pointer;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                ">
                    <i class="fas fa-home me-2"></i>홈으로 돌아가기
                </button>
            </div>
        `;

        // 버튼 이벤트 리스너 추가
        const continueBtn = document.getElementById('manual-continue-btn');
        const restartBtn = document.getElementById('restart-btn');

        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                // 세션 ID가 있으면 OCR 결과 페이지로, 없으면 홈으로
                const sessionId = overlay.getAttribute('data-session-id');
                if (sessionId) {
                    window.location.href = `/ocr_results?session_id=${sessionId}`;
                } else {
                    const redirectUrl = overlay.getAttribute('data-redirect-url');
                    if (redirectUrl) {
                        window.location.href = redirectUrl;
                    } else {
                        window.location.href = '/';
                    }
                }
            });
        }

        if (restartBtn) {
            restartBtn.addEventListener('click', () => {
                window.location.href = '/';
            });
        }

        console.log('🚨 리다이렉션 에러 화면 표시 완료');
    }
    // =============================================================================
    // 엑셀 검증 관련 메서드들 (Claude AI 기반)
    // =============================================================================

    setupExcelValidationEventListeners() {
        console.log('🔍 엑셀 검증 이벤트 리스너 설정 중...');

        // 엑셀 검증 폼 이벤트
        const validationForm = document.getElementById('excel-validation-form');
        if (validationForm) {
            validationForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startExcelValidation();
            });
        }

        // Claude AI 자동 교정 버튼 이벤트
        const autoCorrectionBtn = document.getElementById('start-auto-correction');
        if (autoCorrectionBtn) {
            autoCorrectionBtn.addEventListener('click', () => {
                this.startAutoCorrection();
            });
        }

        // 교정된 엑셀 다운로드 버튼 이벤트
        const downloadCorrectedBtn = document.getElementById('download-corrected-excel');
        if (downloadCorrectedBtn) {
            downloadCorrectedBtn.addEventListener('click', () => {
                this.downloadCorrectedExcel();
            });
        }

        console.log('✅ 엑셀 검증 이벤트 리스너 설정 완료');
    }

    async startExcelValidation() {
        try {
            console.log('🔍 엑셀 검증 시작');

            // 파일 확인
            const fileInput = document.getElementById('validation-file');
            if (!fileInput.files || !fileInput.files[0]) {
                this.showAlert('파일을 선택해주세요.', 'warning');
                return;
            }

            const file = fileInput.files[0];

            // 파일 형식 검증
            if (!file.name.toLowerCase().match(/\.(xlsx|xls)$/)) {
                this.showAlert('엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.', 'error');
                return;
            }

            // UI 상태 변경
            this.hideAllValidationSections();
            this.showValidationProgress();

            // 폼 데이터 생성
            const formData = new FormData();
            formData.append('file', file);

            // API 호출
            const response = await fetch('/api/excel-validate', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.currentValidationSessionId = result.session_id;
                console.log(`✅ 검증 시작됨: ${result.session_id}`);

                // 진행 상태 모니터링 시작
                this.startValidationProgressMonitoring();

                this.showAlert(`엑셀 검증이 시작되었습니다: ${file.name}`, 'success');
            } else {
                throw new Error(result.error || '검증 시작 실패');
            }

        } catch (error) {
            console.error('❌ 엑셀 검증 시작 오류:', error);
            this.showAlert(`검증 시작 오류: ${error.message}`, 'error');
            this.hideValidationProgress();
        }
    }

    startValidationProgressMonitoring() {
        if (!this.currentValidationSessionId) return;

        console.log('📊 검증 진행 상태 모니터링 시작');

        // 기존 타이머 정리
        if (this.validationProgressTimer) {
            clearInterval(this.validationProgressTimer);
        }

        // 진행 상태 확인 (2초마다)
        this.validationProgressTimer = setInterval(async () => {
            try {
                const response = await fetch(`/api/excel-validate-progress/${this.currentValidationSessionId}`);
                const result = await response.json();

                if (result.status === 'completed') {
                    clearInterval(this.validationProgressTimer);
                    this.hideValidationProgress();
                    this.showValidationResults(result.result);
                } else if (result.status === 'error') {
                    clearInterval(this.validationProgressTimer);
                    this.hideValidationProgress();
                    this.showAlert(`검증 오류: ${result.error || '알 수 없는 오류'}`, 'error');
                }

                // 진행률 업데이트 (현재는 단순 애니메이션)
                this.updateValidationProgress();

            } catch (error) {
                console.error('❌ 검증 진행 상태 확인 오류:', error);
            }
        }, 2000);
    }

    showValidationResults(validationResult) {
        try {
            console.log('📋 검증 결과 표시:', validationResult);

            const resultsSection = document.getElementById('validation-results');
            const summaryDiv = document.getElementById('validation-summary');
            const detailsDiv = document.getElementById('validation-details');
            const correctionSection = document.getElementById('auto-correction-section');

            if (!resultsSection || !summaryDiv || !detailsDiv) {
                console.error('❌ 검증 결과 UI 요소를 찾을 수 없음');
                return;
            }

            // 요약 정보 생성
            const summary = validationResult.validation_summary || {};
            const totalIssues = summary.total_issues || 0;

            summaryDiv.innerHTML = `
                <div class="row text-center">
                    <div class="col-md-2">
                        <div class="card border-primary">
                            <div class="card-body">
                                <h5 class="text-primary">${validationResult.total_rows || 0}</h5>
                                <small>전체 행</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="card border-${totalIssues > 0 ? 'danger' : 'success'}">
                            <div class="card-body">
                                <h5 class="text-${totalIssues > 0 ? 'danger' : 'success'}">${totalIssues}</h5>
                                <small>총 문제</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="card border-warning">
                            <div class="card-body">
                                <h5 class="text-warning">${summary.spelling_errors || 0}</h5>
                                <small>맞춤법</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="card border-info">
                            <div class="card-body">
                                <h5 class="text-info">${summary.terminology_errors || 0}</h5>
                                <small>용어집</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="card border-secondary">
                            <div class="card-body">
                                <h5 class="text-secondary">${summary.language_mismatches || 0}</h5>
                                <small>언어불일치</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="card border-dark">
                            <div class="card-body">
                                <h5 class="text-dark">${summary.completeness_issues || 0}</h5>
                                <small>빈필드</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 상세 결과 생성
            const detailedResults = validationResult.detailed_results || {};
            let detailsHtml = '';

            // 각 검증 결과별 상세 정보
            Object.entries(detailedResults).forEach(([key, data]) => {
                const issues = data.issues || [];
                if (issues.length > 0) {
                    const sectionTitle = this.getValidationSectionTitle(key);
                    const sectionIcon = this.getValidationSectionIcon(key);

                    detailsHtml += `
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${key}">
                                    ${sectionIcon} ${sectionTitle} (${issues.length}개)
                                </button>
                            </h2>
                            <div id="${key}" class="accordion-collapse collapse">
                                <div class="accordion-body">
                                    ${this.generateIssuesList(issues, key)}
                                </div>
                            </div>
                        </div>
                    `;
                }
            });

            if (detailsHtml) {
                detailsDiv.innerHTML = `
                    <h6>검증 상세 결과:</h6>
                    <div class="accordion">${detailsHtml}</div>
                `;
            } else {
                detailsDiv.innerHTML = '<div class="alert alert-success"><i class="fas fa-check me-2"></i>모든 검증을 통과했습니다!</div>';
            }

            // 자동 교정 섹션 표시/숨김
            if (validationResult.has_issues && totalIssues > 0) {
                correctionSection.style.display = 'block';
            } else {
                correctionSection.style.display = 'none';
            }

            // 결과 섹션 표시
            resultsSection.style.display = 'block';

        } catch (error) {
            console.error('❌ 검증 결과 표시 오류:', error);
            this.showAlert('검증 결과 표시 중 오류가 발생했습니다.', 'error');
        }
    }

    async startAutoCorrection() {
        try {
            if (!this.currentValidationSessionId) {
                this.showAlert('검증 세션을 찾을 수 없습니다.', 'error');
                return;
            }

            console.log('🔧 Claude AI 자동 교정 시작');

            // UI 상태 변경
            const correctionSection = document.getElementById('auto-correction-section');
            if (correctionSection) correctionSection.style.display = 'none';

            this.showCorrectionProgress();

            // API 호출
            const response = await fetch(`/api/excel-auto-correct/${this.currentValidationSessionId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.currentCorrectionSessionId = result.correction_session_id;
                console.log(`✅ 교정 시작됨: ${result.correction_session_id}`);

                // 교정 진행 상태 모니터링 시작
                this.startCorrectionProgressMonitoring();

                this.showAlert('Claude AI 자동 교정이 시작되었습니다.', 'success');
            } else {
                throw new Error(result.error || '교정 시작 실패');
            }

        } catch (error) {
            console.error('❌ 자동 교정 시작 오류:', error);
            this.showAlert(`교정 시작 오류: ${error.message}`, 'error');
            this.hideCorrectionProgress();
        }
    }

    startCorrectionProgressMonitoring() {
        if (!this.currentCorrectionSessionId) return;

        console.log('🔧 교정 진행 상태 모니터링 시작');

        // 기존 타이머 정리
        if (this.correctionProgressTimer) {
            clearInterval(this.correctionProgressTimer);
        }

        // 진행 상태 확인 (3초마다)
        this.correctionProgressTimer = setInterval(async () => {
            try {
                const response = await fetch(`/api/excel-correction-progress/${this.currentCorrectionSessionId}`);
                const result = await response.json();

                if (result.status === 'completed') {
                    clearInterval(this.correctionProgressTimer);
                    this.hideCorrectionProgress();
                    this.showCorrectionResults(result.result);
                } else if (result.status === 'error') {
                    clearInterval(this.correctionProgressTimer);
                    this.hideCorrectionProgress();
                    this.showAlert(`교정 오류: ${result.error || '알 수 없는 오류'}`, 'error');
                }

                // 세부 진행률 업데이트
                const progress = result.progress || {};
                this.updateCorrectionProgress(progress);

            } catch (error) {
                console.error('❌ 교정 진행 상태 확인 오류:', error);
            }
        }, 3000);
    }

    showCorrectionResults(correctionResult) {
        try {
            console.log('🎉 교정 결과 표시:', correctionResult);

            const resultsSection = document.getElementById('correction-results');
            const summaryDiv = document.getElementById('correction-summary');

            if (!resultsSection || !summaryDiv) {
                console.error('❌ 교정 결과 UI 요소를 찾을 수 없음');
                return;
            }

            // 교정 요약 정보 생성
            const summary = correctionResult.correction_summary || {};
            const processingTime = correctionResult.processing_time || 0;

            summaryDiv.innerHTML = `
                <div class="row text-center mb-4">
                    <div class="col-md-3">
                        <div class="card border-info">
                            <div class="card-body">
                                <h5 class="text-info">${summary.total_items_processed || 0}</h5>
                                <small>처리 항목</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-success">
                            <div class="card-body">
                                <h5 class="text-success">${summary.successfully_corrected || 0}</h5>
                                <small>교정 완료</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-warning">
                            <div class="card-body">
                                <h5 class="text-warning">${Math.round((summary.improvement_rate || 0) * 100)}%</h5>
                                <small>개선율</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card border-secondary">
                            <div class="card-body">
                                <h5 class="text-secondary">${processingTime.toFixed(1)}초</h5>
                                <small>처리 시간</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    Claude AI가 <strong>${summary.successfully_corrected || 0}개</strong> 항목을 성공적으로 교정했습니다!
                </div>
            `;

            // 교정 완료 섹션 표시
            resultsSection.style.display = 'block';

        } catch (error) {
            console.error('❌ 교정 결과 표시 오류:', error);
            this.showAlert('교정 결과 표시 중 오류가 발생했습니다.', 'error');
        }
    }

    async downloadCorrectedExcel() {
        try {
            if (!this.currentCorrectionSessionId) {
                this.showAlert('교정 세션을 찾을 수 없습니다.', 'error');
                return;
            }

            console.log('📥 교정된 엑셀 파일 다운로드 시작');

            // 다운로드 링크로 리다이렉트
            window.location.href = `/api/download-corrected-excel/${this.currentCorrectionSessionId}`;

        } catch (error) {
            console.error('❌ 교정된 엑셀 다운로드 오류:', error);
            this.showAlert(`다운로드 오류: ${error.message}`, 'error');
        }
    }

    // UI 헬퍼 메서드들
    hideAllValidationSections() {
        const sections = ['validation-progress', 'validation-results', 'correction-progress', 'correction-results'];
        sections.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });
    }

    showValidationProgress() {
        const element = document.getElementById('validation-progress');
        if (element) element.style.display = 'block';
    }

    hideValidationProgress() {
        const element = document.getElementById('validation-progress');
        if (element) element.style.display = 'none';
    }

    updateValidationProgress() {
        // 간단한 애니메이션 (실제 진행률 정보가 없으므로)
        const progressBar = document.querySelector('#validation-progress .progress-bar');
        if (progressBar) {
            const currentWidth = parseInt(progressBar.style.width) || 0;
            const newWidth = Math.min(currentWidth + 10, 90);
            progressBar.style.width = `${newWidth}%`;
        }
    }

    showCorrectionProgress() {
        const element = document.getElementById('correction-progress');
        if (element) element.style.display = 'block';
    }

    hideCorrectionProgress() {
        const element = document.getElementById('correction-progress');
        if (element) element.style.display = 'none';
    }

    updateCorrectionProgress(progressData) {
        const progressBar = document.getElementById('correction-progress-bar');
        const statusText = document.getElementById('correction-status-text');
        const progressText = document.getElementById('correction-progress-text');

        if (progressData.progress !== undefined && progressBar) {
            progressBar.style.width = `${progressData.progress}%`;
        }

        if (progressData.current_step && statusText) {
            statusText.textContent = progressData.current_step;
        }

        if (progressData.progress !== undefined && progressText) {
            progressText.textContent = `${progressData.progress}%`;
        }
    }

    getValidationSectionTitle(key) {
        const titles = {
            'spelling_validation': '맞춤법/띄어쓰기 오류',
            'terminology_validation': '용어집 불일치',
            'language_validation': '언어 불일치',
            'multilingual_validation': '다국어 용어 오류',
            'completeness_validation': '데이터 완성도'
        };
        return titles[key] || key;
    }

    getValidationSectionIcon(key) {
        const icons = {
            'spelling_validation': '<i class="fas fa-spell-check text-warning"></i>',
            'terminology_validation': '<i class="fas fa-book text-info"></i>',
            'language_validation': '<i class="fas fa-language text-secondary"></i>',
            'multilingual_validation': '<i class="fas fa-globe text-primary"></i>',
            'completeness_validation': '<i class="fas fa-exclamation-triangle text-dark"></i>'
        };
        return icons[key] || '<i class="fas fa-question-circle"></i>';
    }

    generateIssuesList(issues, sectionKey) {
        if (!Array.isArray(issues) || issues.length === 0) {
            return '<div class="text-muted">문제가 없습니다.</div>';
        }

        let html = '<div class="list-group">';

        issues.slice(0, 10).forEach((issue, index) => { // 최대 10개까지만 표시
            let issueHtml = '<div class="list-group-item">';

            switch (sectionKey) {
                case 'spelling_validation':
                    issueHtml += `
                        <strong>텍스트:</strong> ${issue.text || 'N/A'}<br>
                        <strong>오류 유형:</strong> ${issue.error_type || 'N/A'}<br>
                        <strong>문제:</strong> ${issue.error || 'N/A'}<br>
                        <strong>제안:</strong> <span class="text-success">${issue.suggestion || 'N/A'}</span>
                    `;
                    break;
                case 'terminology_validation':
                    issueHtml += `
                        <strong>텍스트:</strong> ${issue.text || 'N/A'}<br>
                        <strong>잘못된 용어:</strong> <span class="text-danger">${issue.wrong_term || 'N/A'}</span><br>
                        <strong>올바른 용어:</strong> <span class="text-success">${issue.suggested_term || 'N/A'}</span><br>
                        <strong>이유:</strong> ${issue.reason || 'N/A'}
                    `;
                    break;
                default:
                    issueHtml += `<pre>${JSON.stringify(issue, null, 2)}</pre>`;
            }

            issueHtml += '</div>';
            html += issueHtml;
        });

        if (issues.length > 10) {
            html += `<div class="list-group-item text-muted text-center">... 그 외 ${issues.length - 10}개 항목</div>`;
        }

        html += '</div>';
        return html;
    }

}

// 페이지 로드 시 초기화
let xltInterface = null;
document.addEventListener('DOMContentLoaded', () => {
    xltInterface = new XLTWebInterface();
    // 전역 변수로 설정하여 HTML에서 접근 가능하도록 함
    window.xlt = xltInterface;
});

// 전역 에러 핸들링
window.addEventListener('error', (e) => {
    console.error('JavaScript Error:', e.error);
});

// 서비스 워커 등록 (선택사항 - PWA 기능)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // 향후 PWA 기능 추가 시 사용
    });
}