// XLT System v2.0 Web Interface JavaScript

class XLTWebInterface {
    constructor() {
        this.logInterval = null;
        this.init();
    }

    init() {
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

        // 자동 갱신 타이머 설정 (30초마다)
        this.statusTimer = setInterval(() => {
            this.checkSystemHealth();
        }, 30000);
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

        // 엑셀 합치기 이벤트 리스너들
        this.setupExcelMergeEventListeners();
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
                OCR 결과 확인
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
        try {
            // 새로고침 버튼 스피너 시작
            if (this.refreshButton) {
                this.refreshButton.disabled = true;
                this.refreshButton.classList.add('spinning');
            }

            // 로딩 상태 표시
            this.showStatusLoading();

            const response = await fetch('/api/health');
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

        } catch (error) {
            console.error('System health check error:', error);
            this.showStatusError('시스템 상태를 확인할 수 없습니다: ' + error.message);
            this.showAlert('❌ 시스템 상태를 확인할 수 없습니다.', 'warning');
        } finally {
            // 새로고침 버튼 스피너 종료
            if (this.refreshButton) {
                this.refreshButton.disabled = false;
                this.refreshButton.classList.remove('spinning');
            }
        }
    }

    updateSystemStatus(data) {
        // 로딩 숨기고 상태 항목들 표시
        document.querySelector('.status-loading').style.display = 'none';
        this.statusItems.style.display = 'block';
        this.statusSummary.style.display = 'block';

        // 각 컴포넌트 상태 업데이트
        const components = data.components;
        Object.keys(components).forEach(componentName => {
            this.updateComponentStatus(componentName, components[componentName]);
        });

        // 마지막 확인 시간 업데이트
        const lastCheck = new Date(data.last_check).toLocaleTimeString('ko-KR');
        this.lastCheckTime.textContent = lastCheck;

        // 전체 상태 요약 업데이트
        this.updateOverallStatus(data.overall_status, data.summary);
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
        document.querySelector('.status-loading').style.display = 'block';
        this.statusItems.style.display = 'none';
        this.statusSummary.style.display = 'none';
    }

    showStatusError(errorMessage) {
        document.querySelector('.status-loading').style.display = 'none';
        this.statusItems.style.display = 'none';
        this.statusSummary.style.display = 'none';

        // 에러 메시지 표시
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-center text-danger p-4';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
            <p class="mb-0">${errorMessage}</p>
            <button class="btn btn-sm btn-outline-danger mt-2" onclick="xlt.checkSystemHealth()">다시 시도</button>
        `;

        this.statusContainer.innerHTML = '';
        this.statusContainer.appendChild(errorDiv);
    }

    async startTranslation() {
        try {
            // XLT System v3.0 - 수동 모드 고정
            const processingMode = 'manual';

            // 로그 시작
            this.clearLog();
            this.addLog('🚀 번역 작업을 시작합니다...', 'info');
            this.addLog('🔧 번역 엔진: Google 번역 (전용)', 'info');

            this.showProgress();

            const formData = new FormData();
            formData.append('input_type', 'figma');
            formData.append('mode', processingMode);
            formData.append('translation_mode', 'google');

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
                    this.startLogPolling(result.session_id);
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
                if (result.session_id) {
                    this.startLogPolling(result.session_id);
                    // 잠시 후 페이지 이동
                    setTimeout(() => {
                        this.addLog('📝 OCR 처리 완료, 텍스트 선택 페이지로 이동합니다', 'success');
                        window.location.href = result.redirect;
                    }, 1000);
                } else {
                    this.addLog('📝 OCR 처리 완료, 텍스트 선택 페이지로 이동합니다', 'success');
                    window.location.href = result.redirect;
                }
            } else {
                this.addLog(`❌ 오류 발생: ${result.error}`, 'error');
                this.showAlert(`❌ ${result.error}`, 'danger');
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
            'OCR로 텍스트를 추출하고 있습니다...',
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
                            <code>${current.short_hash}</code><br>
                            <small class="text-muted">${current.message}</small>
                        </div>
                        <div class="col-6">
                            <strong>최신 버전:</strong><br>
                            <code>${remote.short_hash}</code><br>
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
}

// 페이지 로드 시 초기화
let xltInterface = null;
document.addEventListener('DOMContentLoaded', () => {
    xltInterface = new XLTWebInterface();
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