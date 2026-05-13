// XLT OCR Results Page JavaScript

class OCRResultsManager {
    constructor() {
        this.selectedItems = [];
        this.floatingPanel = document.getElementById('floating-selection-panel');
        this.isTranslating = false; // 번역 진행 중 플래그
        console.log('OCRResultsManager initialized');
        console.log('Floating panel element:', this.floatingPanel);
        this.init();

        // 디버깅: 3초 후 강제로 플로팅 패널 테스트
        setTimeout(() => {
            console.log('Testing floating panel visibility...');
            this.testFloatingPanel();
        }, 3000);
    }

    init() {
        this.debugDOMState();

        // 알림 권한 요청
        this.requestNotificationPermission();

        // 플로팅 패널 드래그 기능 초기화
        this.initDraggable();
        this.setupEventListeners();
        this.updateSelectedCount();
    }

    debugDOMState() {
        console.log('=== DOM 상태 확인 ===');

        // 체크박스 확인
        const checkboxes = document.querySelectorAll('.item-checkbox');
        console.log(`체크박스 개수: ${checkboxes.length}`);

        // OCR 아이템 확인
        const ocrItems = document.querySelectorAll('.ocr-item');
        console.log(`OCR 아이템 개수: ${ocrItems.length}`);

        // 텍스트 입력 확인
        const textInputs = document.querySelectorAll('.text-edit-input');
        console.log(`텍스트 입력 개수: ${textInputs.length}`);

        // 카운터 요소들 확인
        const elements = [
            'selected-count',
            'backup-selected-count',
            'floating-selected-count',
            'translate-selected-btn',
            'backup-translate-btn',
            'floating-translate-btn'
        ];

        elements.forEach(id => {
            const el = document.getElementById(id);
            console.log(`${id}: ${el ? '존재' : '없음'}`);
        });

        console.log('=== DOM 상태 확인 완료 ===');
    }

    setupEventListeners() {
        // 체크박스 변경 이벤트 - 강화된 이벤트 처리
        const checkboxes = document.querySelectorAll('.item-checkbox');
        console.log(`Found ${checkboxes.length} checkboxes`); // 디버깅

        if (checkboxes.length === 0) {
            console.warn('No checkboxes found! Trying alternative selectors...');
            // 대체 선택자들 시도
            const altCheckboxes = document.querySelectorAll('input[type="checkbox"]');
            console.log(`Alternative checkboxes found: ${altCheckboxes.length}`);
        }

        checkboxes.forEach((checkbox, index) => {
            console.log(`Setting up checkbox ${index}:`, checkbox);

            // 여러 이벤트로 확실하게 처리
            ['change', 'click', 'input'].forEach(eventType => {
                checkbox.addEventListener(eventType, (e) => {
                    console.log(`Checkbox ${eventType} event triggered on checkbox ${index}:`, e.target.checked);
                    this.handleSelectionChange();
                });
            });
        });

        // 이벤트 위임 방식도 추가 (동적 생성된 체크박스 대응)
        document.addEventListener('change', (e) => {
            if (e.target.matches('.item-checkbox')) {
                console.log('Event delegation: checkbox changed', e.target.checked);
                this.handleSelectionChange();
            }
        });

        // 플로팅 패널 버튼들을 위한 이벤트 위임
        document.addEventListener('click', (e) => {
            // 플로팅 번역 버튼 클릭 (이벤트 위임만 사용 - setupFloatingPanelEvents에서 중복 등록하지 않음)
            if (e.target.matches('#floating-translate-btn') ||
                e.target.closest('#floating-translate-btn')) {
                e.preventDefault();
                e.stopPropagation();
                console.log('플로팅 번역 버튼 클릭!');

                if (this.selectedItems.length > 0) {
                    console.log('번역 시작...');
                    this.translateSelected();
                } else {
                    console.error('선택된 항목이 없음!');
                    alert('번역할 텍스트를 선택해주세요.');
                }
                return;
            }

            // 플로팅 전체 선택 버튼
            if (e.target.matches('#floating-select-all') ||
                e.target.closest('#floating-select-all')) {
                e.preventDefault();
                console.log('플로팅 전체 선택 버튼 클릭');
                this.selectAllFiltered();
                return;
            }

            // 플로팅 선택 해제 버튼
            if (e.target.matches('#floating-clear-selection') ||
                e.target.closest('#floating-clear-selection')) {
                e.preventDefault();
                console.log('플로팅 선택 해제 버튼 클릭');
                this.clearSelection();
                return;
            }
        });

        // 텍스트 수정 이벤트
        document.querySelectorAll('.text-edit-input').forEach(input => {
            input.addEventListener('input', () => {
                this.handleTextChange(input);
            });
        });

        // v3.3: 맞춤법 검사 버튼 이벤트 (이벤트 위임)
        document.addEventListener('click', async (e) => {
            if (e.target.matches('.spell-check-btn') ||
                e.target.closest('.spell-check-btn')) {
                e.preventDefault();

                // v4.0: Claude 통합 모드에서는 맞춤법 검사 비활성화
                if (window.xlTTranslationMode === 'claude_integrated') {
                    this.showAlert('Claude 통합 모드에서는 이미 맞춤법 교정이 적용되어 있습니다. ✨', 'info');
                    return;
                }

                const btn = e.target.closest('.spell-check-btn') || e.target;
                const inputField = btn.closest('.d-flex').querySelector('.text-edit-input');

                if (inputField) {
                    await this.checkSpelling(inputField, btn);
                }
            }
        });

        // 버튼 이벤트들 (null 체크 추가)
        const translateBtn = document.getElementById('translate-selected-btn');
        if (translateBtn) {
            translateBtn.addEventListener('click', () => {
                this.translateSelected();
            });
        }

        const selectAllBtn = document.getElementById('select-all-filtered');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                this.selectAllFiltered();
            });
        }

        const clearBtn = document.getElementById('clear-selection');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearSelection();
            });
        }

        // 다운로드 버튼 (결과 후)
        const downloadBtn = document.getElementById('download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                console.log('📥 다운로드 버튼 클릭 감지됨');
                this.downloadResult();
            });
            console.log('다운로드 버튼 이벤트 리스너 등록 완료');
        } else {
            console.warn('⚠️ download-btn 요소를 찾을 수 없어 이벤트 리스너를 등록하지 못했습니다.');
        }

        // 새번역 버튼
        document.getElementById('new-translation-btn').addEventListener('click', () => {
            this.disableBeforeUnloadWarning();
        });

        // 백업 선택 요약 버튼들 (즉시 사용 가능)
        this.setupBackupSelectionEvents();

        // 번역 가이드 보기 버튼 (이벤트 위임 방식)
        // 직접 이벤트 등록
        const viewGuideBtn = document.getElementById('view-guide-btn');
        if (viewGuideBtn) {
            console.log('✅ view-guide-btn 요소 발견:', viewGuideBtn);
            viewGuideBtn.addEventListener('click', (e) => {
                console.log('🖱️ 번역 가이드 버튼 클릭됨 (직접 이벤트)!', e);
                this.showTranslationGuide();
            });
            console.log('✅ 번역 가이드 버튼 이벤트 리스너 등록 완료');
        } else {
            console.error('❌ view-guide-btn 요소를 찾을 수 없습니다!');
        }

        // 이벤트 위임으로도 등록 (백업)
        document.addEventListener('click', (e) => {
            if (e.target.id === 'view-guide-btn' || e.target.closest('#view-guide-btn')) {
                console.log('🖱️ 번역 가이드 버튼 클릭됨 (이벤트 위임)!', e);
                e.preventDefault();
                e.stopPropagation();
                this.showTranslationGuide();
            }
        });

        // 플로팅 패널 이벤트들 - DOM 로드 후 설정
        setTimeout(() => {
            this.setupFloatingPanelEvents();
        }, 500); // 0.5초 후 이벤트 설정
    }

    setupFloatingPanelEvents() {
        console.log('setupFloatingPanelEvents 시작');

        // 플로팅 패널 닫기 버튼
        const closeBtn = document.getElementById('close-panel-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                console.log('플로팅 패널 닫기 버튼 클릭');
                this.hideFloatingPanel();
            });
            console.log('닫기 버튼 이벤트 설정 완료');
        } else {
            console.warn('close-panel-btn 요소를 찾을 수 없음');
        }

        // 플로팅 번역 버튼 - 이벤트 위임에서 이미 처리하므로 여기서는 등록하지 않음
        const translateBtn = document.getElementById('floating-translate-btn');
        if (translateBtn) {
            console.log('플로팅 번역 버튼 발견 (이벤트는 위임 방식으로 처리됨)');
        } else {
            console.error('floating-translate-btn 요소를 찾을 수 없음!');
        }

        // 플로팅 전체 선택 버튼
        const selectAllBtn = document.getElementById('floating-select-all');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                console.log('플로팅 전체 선택 버튼 클릭');
                this.selectAllFiltered();
            });
            console.log('전체 선택 버튼 이벤트 설정 완료');
        } else {
            console.warn('floating-select-all 요소를 찾을 수 없음');
        }

        // 플로팅 선택 해제 버튼
        const clearBtn = document.getElementById('floating-clear-selection');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                console.log('플로팅 선택 해제 버튼 클릭');
                this.clearSelection();
            });
            console.log('선택 해제 버튼 이벤트 설정 완료');
        } else {
            console.warn('floating-clear-selection 요소를 찾을 수 없음');
        }

        // 스크롤 이벤트로 패널 최적화
        window.addEventListener('scroll', () => {
            if (this.selectedItems.length > 0) {
                this.optimizeFloatingPanelForScroll();
            }
        });

        console.log('setupFloatingPanelEvents 완료');

    }

    setupBackupSelectionEvents() {
        // 백업 번역 버튼
        document.getElementById('backup-translate-btn').addEventListener('click', () => {
            this.translateSelected();
        });

        // 백업 전체 선택 버튼
        document.getElementById('backup-select-all').addEventListener('click', () => {
            this.selectAllFiltered();
        });

        // 백업 선택 해제 버튼
        document.getElementById('backup-clear-selection').addEventListener('click', () => {
            this.clearSelection();
        });

        // 자동 치환 체크박스 동기화 (존재하는 경우에만)
        const backupAutoPlaceholder = document.getElementById('backup-auto-placeholder');
        const floatingAutoPlaceholder = document.getElementById('floating-auto-placeholder');
        if (backupAutoPlaceholder && floatingAutoPlaceholder) {
            backupAutoPlaceholder.addEventListener('change', (e) => {
                floatingAutoPlaceholder.checked = e.target.checked;
            });
        }

        // OCR 아이템 클릭으로 선택
        document.querySelectorAll('.ocr-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.type !== 'checkbox' && e.target.type !== 'text') {
                    const checkbox = item.querySelector('.item-checkbox');
                    checkbox.checked = !checkbox.checked;
                    this.handleSelectionChange();
                }
            });
        });
    }

    handleSelectionChange() {
        console.log('Selection changed'); // 디버깅
        this.updateSelectedItems();
        this.updateSelectedCount();
        this.updateTranslateButton(); // 이미 백업/플로팅 버튼도 처리함
        this.updateItemStyles();
        this.updateFloatingPanel();
        console.log(`Selected items count: ${this.selectedItems.length}`); // 디버깅
        console.log('Floating panel update called'); // 플로팅 패널 디버깅
    }

    updateSelectedItems() {
        console.log('=== updateSelectedItems 시작 ===');
        this.selectedItems = [];

        // 모든 체크박스 확인
        const allCheckboxes = document.querySelectorAll('.item-checkbox');
        const checkedCheckboxes = document.querySelectorAll('.item-checkbox:checked');

        console.log(`전체 체크박스: ${allCheckboxes.length}개`);
        console.log(`체크된 체크박스: ${checkedCheckboxes.length}개`);

        checkedCheckboxes.forEach((checkbox, idx) => {
            console.log(`처리 중인 체크박스 ${idx}:`, checkbox);

            const ocrItem = checkbox.closest('.ocr-item');
            console.log(`OCR 아이템:`, ocrItem);

            if (!ocrItem) {
                console.error(`OCR 아이템을 찾을 수 없음!`);
                return;
            }

            const index = parseInt(ocrItem.dataset.index);
            const sourceType = ocrItem.dataset.source;
            const textInput = ocrItem.querySelector('.text-edit-input');

            console.log(`인덱스: ${index}, 소스타입: ${sourceType}`);
            console.log(`텍스트 입력:`, textInput);

            if (textInput) {
                const item = {
                    index: index,
                    text: textInput.value.trim(),
                    source_type: sourceType,
                    element: ocrItem
                };

                console.log(`추가될 아이템:`, item);
                this.selectedItems.push(item);
            } else {
                console.error('텍스트 입력을 찾을 수 없음!');
            }
        });

        console.log(`최종 selectedItems:`, this.selectedItems);
        console.log('=== updateSelectedItems 완료 ===');
    }

    updateSelectedCount() {
        const count = this.selectedItems.length;
        console.log(`선택 카운트 업데이트: ${count}개`);

        // 기존 카운터 (있다면)
        const selectedCountEl = document.getElementById('selected-count');
        if (selectedCountEl) {
            selectedCountEl.textContent = `${count}개`;
            console.log('기존 selected-count 업데이트됨');
        }

        // 백업 카운터
        const backupCountEl = document.getElementById('backup-selected-count');
        if (backupCountEl) {
            backupCountEl.textContent = `${count}개`;
            console.log('backup-selected-count 업데이트됨');
        }

        // 플로팅 카운터
        const floatingCountEl = document.getElementById('floating-selected-count');
        if (floatingCountEl) {
            floatingCountEl.textContent = `${count}개`;
            console.log('floating-selected-count 업데이트됨');
        }
    }

    updateTranslateButton() {
        console.log('updateTranslateButton 호출됨');

        // 기존 번역 버튼 (있다면)
        const button = document.getElementById('translate-selected-btn');
        if (button) {
            button.disabled = this.selectedItems.length === 0;

            if (this.selectedItems.length > 0) {
                button.innerHTML = `
                    <i class="fas fa-language me-2"></i>
                    ${this.selectedItems.length}개 항목 번역
                `;
            } else {
                button.innerHTML = `
                    <i class="fas fa-language me-2"></i>
                    선택 항목 번역
                `;
            }
            console.log('기존 번역 버튼 업데이트됨');
        }

        // 백업 번역 버튼
        const backupButton = document.getElementById('backup-translate-btn');
        const backupText = document.getElementById('backup-translate-text');

        if (backupButton && backupText) {
            backupButton.disabled = this.selectedItems.length === 0;

            if (this.selectedItems.length > 0) {
                backupText.textContent = `${this.selectedItems.length}개 항목 번역`;
            } else {
                backupText.textContent = '선택 항목 번역';
            }
            console.log('백업 번역 버튼 업데이트됨');
        }

        // 플로팅 번역 버튼
        const floatingButton = document.getElementById('floating-translate-btn');
        const floatingText = document.getElementById('floating-translate-text');

        if (floatingButton && floatingText) {
            floatingButton.disabled = this.selectedItems.length === 0;

            if (this.selectedItems.length > 0) {
                floatingText.textContent = `${this.selectedItems.length}개 항목 번역`;
            } else {
                floatingText.textContent = '선택 항목 번역';
            }
            console.log('플로팅 번역 버튼 업데이트됨');
        }
    }

    updateItemStyles() {
        document.querySelectorAll('.ocr-item').forEach(item => {
            const checkbox = item.querySelector('.item-checkbox');
            if (checkbox.checked) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
    }

    handleTextChange(input) {
        // 실시간 텍스트 변경 처리 (필요시 추가 로직)
        this.updateSelectedItems();
    }

    selectAllFiltered() {
        document.querySelectorAll('#filtered-results .item-checkbox').forEach(checkbox => {
            checkbox.checked = true;
        });
        this.handleSelectionChange();

        // 의미있는 텍스트 탭으로 이동
        const filteredTab = document.getElementById('filtered-tab');
        const tab = new bootstrap.Tab(filteredTab);
        tab.show();
    }

    clearSelection() {
        document.querySelectorAll('.item-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        this.handleSelectionChange();
    }

    async translateSelected() {
        console.log('translateSelected called, selectedItems:', this.selectedItems);

        // 중복 호출 방지
        if (this.isTranslating) {
            console.log('번역이 이미 진행 중입니다. 중복 호출 무시.');
            return;
        }

        if (this.selectedItems.length === 0) {
            console.log('No items selected');
            alert('번역할 텍스트를 선택해주세요.');
            return;
        }

        this.isTranslating = true; // 번역 시작

        // 빈 텍스트 확인
        const validItems = this.selectedItems.filter(item => item.text.length > 0);
        console.log('Valid items after filtering:', validItems);

        if (validItems.length === 0) {
            alert('유효한 텍스트가 없습니다. 텍스트를 입력해주세요.');
            return;
        }

        try {
            // 1단계: 즉시 로딩 표시
            const selectedIndexes = validItems.map(item => item.index);
            const selectedTexts = validItems.map(item => item.text); // v3.2: 사용자가 수정한 텍스트 전송
            const sessionId = new URLSearchParams(window.location.search).get('session_id');

            // 즉시 로딩 인디케이터 표시
            const loadingModal = this.showLoadingModal('치환자 패턴 확인 중...');

            console.log('Checking placeholders with user-edited texts...');
            const placeholderResponse = await fetch('/check-placeholders', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_indexes: selectedIndexes,
                    selected_texts: selectedTexts, // v3.2: 사용자 수정 텍스트 포함
                    session_id: sessionId
                })
            });

            const placeholderResult = await placeholderResponse.json();

            // 로딩 모달 숨기기
            this.hideLoadingModal(loadingModal);

            if (placeholderResult.status !== 'success') {
                this.showAlert(placeholderResult.error, 'danger');
                return;
            }

            // 2단계: 치환자가 있으면 사용자가 개별 선택
            let finalTexts = validItems.map(item => item.text); // 기본값은 원본 텍스트

            if (placeholderResult.has_placeholders) {
                // 항상 모달을 보여서 개별 선택 가능하도록 함
                console.log('치환자 패턴 발견, 사용자 선택 모달 표시');
                const userChoice = await this.showPlaceholderModal(placeholderResult.placeholder_suggestions, validItems);
                if (userChoice.cancelled) {
                    return; // 사용자가 취소
                }
                finalTexts = userChoice.finalTexts;
            } else {
                console.log('치환자 패턴 없음, 원본 텍스트로 진행');
            }

            // 3단계: XLT Key 설정
            console.log('=== XLT Key 설정 단계 ===');
            console.log('Selected indexes:', selectedIndexes);
            console.log('Session ID:', sessionId);
            console.log('Final texts:', finalTexts);

            const keySetupResponse = await fetch('/set-xlt-keys', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    selected_indexes: selectedIndexes,
                    session_id: sessionId,
                    final_texts: finalTexts
                })
            });

            const keySetupResult = await keySetupResponse.json();
            if (keySetupResult.status !== 'success') {
                this.showAlert(keySetupResult.error, 'danger');
                return;
            }

            // 4단계: XLT Key 편집 모달
            const xltKeys = await this.showXltKeyModal(keySetupResult.key_setup_data);
            if (!xltKeys) {
                return; // 사용자가 취소
            }

            // 5단계: 번역 실행 (개별 XLT Key 포함)
            console.log('=== 번역 시작 (개별 XLT Key) ===');
            console.log('XLT Keys:', xltKeys);

            this.showProgress();
            console.log('Progress shown');

            console.log('Sending translate request with XLT keys...');
            const response = await fetch('/translate-selected', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    xlt_keys: xltKeys
                })
            });

            console.log('Translate response received, status:', response.status);

            // JSON 응답 처리
            const result = await response.json();
            console.log('Translate result:', result);

            this.hideProgress();
            console.log('Progress hidden');

            if (result.status === 'success') {
                // 번역 성공 시 beforeunload 경고 비활성화 및 플로팅 패널 숨김
                this.disableBeforeUnloadWarning();
                this.hideFloatingPanel();

                // 번역 미리보기 표시 (Excel 다운로드 버튼 포함)
                this.showTranslationPreview(result);
            } else {
                this.showAlert(result.error, 'danger');
            }

        } catch (error) {
            // 로딩 모달이 열려있다면 닫기
            if (typeof loadingModal !== 'undefined' && loadingModal) {
                this.hideLoadingModal(loadingModal);
            }

            this.hideProgress();
            this.showAlert(`네트워크 오류: ${error.message}`, 'danger');
        } finally {
            this.isTranslating = false; // 번역 완료/오류 시 플래그 해제
        }
    }

    async showKeyPrefixModal(sessionId, translationResult) {
        console.log('showKeyPrefixModal called');

        // Bootstrap 모달 인스턴스 가져오기/생성
        const modalElement = document.getElementById('keyPrefixModal');
        if (!modalElement) {
            console.error('Key prefix 모달 요소를 찾을 수 없습니다');
            // 모달 없으면 바로 Excel 생성 (기본값 사용)
            this.generateExcel(sessionId, '', translationResult);
            return;
        }

        const modal = new bootstrap.Modal(modalElement);
        const inputElement = document.getElementById('keyPrefixInput');
        const skipButton = document.getElementById('skipKeyPrefix');
        const applyButton = document.getElementById('applyKeyPrefix');

        // 입력 필드 초기화
        if (inputElement) {
            inputElement.value = '';
        }

        // 모달 정리 이벤트 리스너 추가 (aria-hidden 문제 해결)
        modalElement.addEventListener('hidden.bs.modal', function cleanupModal() {
            console.log('Key prefix 모달 정리 시작');

            // Remove aria-hidden from all elements except modal
            document.querySelectorAll('[aria-hidden="true"]').forEach(el => {
                if (el.id !== 'keyPrefixModal') {
                    el.removeAttribute('aria-hidden');
                }
            });

            // Remove modal-open class
            document.body.classList.remove('modal-open');

            // Remove backdrop
            document.querySelector('.modal-backdrop')?.remove();

            // Clear body styles
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';

            console.log('Key prefix 모달 정리 완료');

            // Remove this event listener after first execution
            modalElement.removeEventListener('hidden.bs.modal', cleanupModal);
        });

        // 이벤트 리스너 제거 (중복 방지)
        const newSkipButton = skipButton.cloneNode(true);
        const newApplyButton = applyButton.cloneNode(true);
        skipButton.parentNode.replaceChild(newSkipButton, skipButton);
        applyButton.parentNode.replaceChild(newApplyButton, applyButton);

        // 건너뛰기 버튼
        newSkipButton.addEventListener('click', async () => {
            console.log('Key prefix 건너뛰기');
            modal.hide();
            await this.generateExcel(sessionId, '', translationResult);
        });

        // 적용하기 버튼
        newApplyButton.addEventListener('click', async () => {
            const keyPrefix = inputElement ? inputElement.value.trim() : '';
            console.log('Key prefix 적용:', keyPrefix);

            if (!keyPrefix) {
                alert('Key prefix를 입력해주세요. 또는 "건너뛰기"를 선택하세요.');
                return;
            }

            modal.hide();
            await this.generateExcel(sessionId, keyPrefix, translationResult);
        });

        // Enter 키 처리
        if (inputElement) {
            const enterHandler = (e) => {
                if (e.key === 'Enter') {
                    newApplyButton.click();
                }
            };
            inputElement.addEventListener('keypress', enterHandler);
        }

        // 모달 표시 후 입력 필드에 포커스
        modal.show();
        modalElement.addEventListener('shown.bs.modal', () => {
            if (inputElement) {
                inputElement.focus();
            }
        }, { once: true });
    }

    async generateExcel(sessionId, keyPrefix, translationResult) {
        try {
            console.log('generateExcel called with keyPrefix:', keyPrefix);
            console.log('translationResult:', translationResult);

            // Progress 표시
            this.showProgress();
            console.log('Progress shown');

            const response = await fetch('/generate-excel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    key_prefix: keyPrefix
                })
            });

            console.log('generateExcel response received, status:', response.status);

            // Excel 파일인지 JSON인지 확인
            const contentType = response.headers.get('content-type');
            console.log('Response content type:', contentType);

            if (contentType && contentType.includes('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) {
                // Excel 파일 다운로드 처리
                console.log('Excel file detected, handling download...');
                this.hideProgress();

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;

                // 파일명 생성 (Content-Disposition에서 추출하거나 기본값 사용)
                const contentDisposition = response.headers.get('content-disposition');
                let filename = 'translation_result.xlsx';
                if (contentDisposition && contentDisposition.includes('filename=')) {
                    const match = contentDisposition.match(/filename=([^;]+)/);
                    if (match) {
                        filename = match[1].replace(/"/g, '');
                    }
                }

                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                console.log(`✅ Excel 파일 다운로드 완료: ${filename}`);

                // 번역 성공 시 beforeunload 경고 비활성화 및 플로팅 패널 숨김
                this.disableBeforeUnloadWarning();
                this.hideFloatingPanel();

                // 성공 메시지 표시
                this.showAlert(`번역 완료! Excel 파일이 다운로드되었습니다.`, 'success');

                return; // 함수 종료
            }

            // JSON 응답 처리 (오류 응답인 경우)
            const result = await response.json();
            console.log('generateExcel JSON result:', result);

            this.hideProgress();
            console.log('Progress hidden');

            if (result.status === 'success') {
                // 이 경우는 발생하지 않아야 함 (Excel 파일이 직접 반환되어야 함)
                console.warn('Unexpected JSON success response from /generate-excel');
                this.showAlert('Excel 생성은 완료되었지만 다운로드에 문제가 있습니다.', 'warning');
            } else {
                console.error('Excel generation failed:', result.error);
                this.showAlert(result.error, 'danger');
            }

        } catch (error) {
            console.error('generateExcel error:', error);
            this.hideProgress();
            this.showAlert(`Excel 생성 오류: ${error.message}`, 'danger');
        }
    }

    showTranslationPreview(result) {
        console.log('showTranslationPreview called with:', result);

        const { preview_data, session_id } = result;

        if (!preview_data || preview_data.length === 0) {
            this.showAlert('번역 미리보기 데이터가 없습니다.', 'warning');
            return;
        }

        // 기존 미리보기 모달이 있으면 제거
        const existingModal = document.getElementById('translationPreviewModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 언어별 라벨
        const languageLabels = {
            'ko_KR': '🇰🇷 한국어',
            'en_US': '🇺🇸 영어',
            'ja_JP': '🇯🇵 일본어',
            'zh_TW': '🇹🇼 중국어',
            'th_TH': '🇹🇭 태국어'
        };

        // 미리보기 내용 생성
        let previewContent = '<div class="translation-preview-content">';

        preview_data.forEach((item, index) => {
            previewContent += `
                <div class="preview-item card mb-4">
                    <div class="card-header bg-primary text-white">
                        <h6 class="mb-0">📝 항목 ${index + 1}: ${item.xlt_key}</h6>
                    </div>
                    <div class="card-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <div class="mb-2">
                                    <span class="badge bg-secondary">원본 텍스트</span>
                                </div>
                                <div class="p-2 border rounded bg-light">
                                    ${item.original_text}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-2">
                                    <span class="badge bg-info">치환자 적용 결과</span>
                                </div>
                                <div class="p-2 border rounded bg-light">
                                    ${item.processed_text}
                                </div>
                            </div>
                        </div>

                        <div class="translations-section">
                            <h6 class="mb-3">🌐 번역 결과</h6>
                            <div class="row">
            `;

            // 각 언어별 번역 결과 표시
            Object.keys(languageLabels).forEach(lang => {
                const translation = item.translations[lang] || item.processed_text; // 번역이 없으면 원본 사용
                previewContent += `
                    <div class="col-md-6 mb-3">
                        <div class="translation-item">
                            <div class="mb-1">
                                <span class="badge bg-success">${languageLabels[lang]}</span>
                            </div>
                            <div class="p-2 border rounded">
                                ${translation}
                            </div>
                        </div>
                    </div>
                `;
            });

            previewContent += `
                        </div>
                    </div>
                </div>
            </div>
            `;
        });

        previewContent += '</div>';

        // 미리보기 모달 생성
        const modal = document.createElement('div');
        modal.id = 'translationPreviewModal';
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title">📋 번역 결과 미리보기</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body" style="max-height: 70vh; overflow-y: auto;">
                        ${previewContent}

                        <div class="alert alert-info mt-4">
                            <i class="bi bi-info-circle"></i>
                            <strong>안내:</strong> 번역 결과를 확인하신 후 Excel 파일로 다운로드할 수 있습니다.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">닫기</button>
                        <button type="button" class="btn btn-success btn-lg" id="downloadExcelBtn">
                            <i class="bi bi-download"></i> Excel 파일 다운로드
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const bsModal = new bootstrap.Modal(modal);

        // Excel 다운로드 버튼 이벤트
        document.getElementById('downloadExcelBtn').addEventListener('click', async () => {
            try {
                console.log('Excel download button clicked');

                // 다운로드 버튼 비활성화 및 로딩 표시
                const downloadBtn = document.getElementById('downloadExcelBtn');
                const originalText = downloadBtn.innerHTML;
                downloadBtn.disabled = true;
                downloadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Excel 생성 중...';

                const response = await fetch('/download-excel', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: session_id
                    })
                });

                if (response.ok) {
                    // Excel 파일 다운로드
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;

                    // Content-Disposition 헤더에서 파일명 추출
                    const disposition = response.headers.get('Content-Disposition');
                    let filename = 'translation_result.xlsx';
                    if (disposition) {
                        const match = disposition.match(/filename="?([^";]+)"?/);
                        if (match) {
                            filename = match[1];
                        }
                    }

                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);

                    // 모달 닫기
                    bsModal.hide();

                    this.showAlert('Excel 파일이 성공적으로 다운로드되었습니다!', 'success');
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Excel 다운로드 실패');
                }

                // 버튼 상태 복원
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = originalText;

            } catch (error) {
                console.error('Excel download error:', error);
                this.showAlert(`Excel 다운로드 오류: ${error.message}`, 'danger');

                // 버튼 상태 복원
                const downloadBtn = document.getElementById('downloadExcelBtn');
                if (downloadBtn) {
                    downloadBtn.disabled = false;
                    downloadBtn.innerHTML = '<i class="bi bi-download"></i> Excel 파일 다운로드';
                }
            }
        });

        // 모달 표시
        bsModal.show();

        console.log('Translation preview modal displayed');

        // v3.3: 학습 리포트 표시 (모달이 닫힌 후)
        modal.addEventListener('hidden.bs.modal', () => {
            if (result.learned_count && result.learned_count > 0) {
                this.showLearningReport(result.learned_count, result.learned_corrections);
            }
        });
    }

    // v3.3: 맞춤법/띄어쓰기 학습 결과 리포트 표시
    showLearningReport(learnedCount, learnedCorrections) {
        const reportSection = document.getElementById('learning-report-section');
        const reportContent = document.getElementById('learning-report-content');

        if (!reportSection || !reportContent) {
            return;
        }

        // 학습 내역 테이블 생성
        let tableHTML = `
            <div class="alert alert-success mb-3">
                <i class="fas fa-check-circle me-2"></i>
                <strong>${learnedCount}개</strong>의 맞춤법/띄어쓰기 교정 내용이 학습되었습니다.
            </div>
            <table class="table table-bordered table-hover">
                <thead class="table-light">
                    <tr>
                        <th style="width: 5%">#</th>
                        <th style="width: 45%">OCR 원본</th>
                        <th style="width: 5%">→</th>
                        <th style="width: 45%">사용자 수정</th>
                    </tr>
                </thead>
                <tbody>
        `;

        learnedCorrections.forEach((correction, index) => {
            tableHTML += `
                <tr>
                    <td class="text-center"><span class="badge bg-primary">${index + 1}</span></td>
                    <td class="text-muted">${this.escapeHtml(correction.original)}</td>
                    <td class="text-center"><i class="fas fa-arrow-right text-success"></i></td>
                    <td class="fw-bold text-primary">${this.escapeHtml(correction.corrected)}</td>
                </tr>
            `;
        });

        tableHTML += `
                </tbody>
            </table>
            <p class="text-muted mt-3 mb-0">
                <i class="fas fa-lightbulb me-1"></i>
                이 학습 내용은 <code>data/spelling_corrections.json</code>에 저장되어 다음 번역 시 자동으로 적용됩니다.
            </p>
        `;

        reportContent.innerHTML = tableHTML;
        reportSection.style.display = 'block';

        // 학습 리포트로 스크롤
        setTimeout(() => {
            reportSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
    }

    // HTML 이스케이프 헬퍼 함수
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // applyAutoPlaceholders 함수 제거됨 - 개별 선택 방식으로 변경

    async showXltKeyModal(keySetupData) {
        return new Promise((resolve) => {
            let resolved = false;
            console.log('XLT Key modal: Creating modal for key setup:', keySetupData);

            // 모달 HTML 생성
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'xltKeyModal';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('aria-labelledby', 'xltKeyModalLabel');
            modal.setAttribute('aria-hidden', 'true');

            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="xltKeyModalLabel">
                                <i class="fas fa-key me-2"></i>XLT Key 설정
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle me-2"></i>
                                각 문구에 대해 개별 XLT Key를 설정하세요. Key는 Excel 파일에서 해당 항목을 식별하는 데 사용됩니다.
                            </div>
                            <div class="card mb-3 bg-light">
                                <div class="card-body">
                                    <h6 class="card-title">🔧 키 생성 방식 선택 (v3.3)</h6>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="radio" name="keyMode" id="keyModeAuto" value="auto" checked>
                                                <label class="form-check-label" for="keyModeAuto">
                                                    <strong>지능형 키</strong>
                                                    <small class="d-block text-muted">텍스트 내용 분석 (예: login_confirm_001)</small>
                                                </label>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="form-check">
                                                <input class="form-check-input" type="radio" name="keyMode" id="keyModePrefix" value="prefix">
                                                <label class="form-check-label" for="keyModePrefix">
                                                    <strong>단순 prefix + 번호</strong>
                                                    <small class="d-block text-muted">사용자 정의 (예: MY_KEY_001)</small>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                    <div id="prefixInputContainer" class="mt-3" style="display:none;">
                                        <label class="form-label fw-bold">Prefix 입력:</label>
                                        <input type="text" class="form-control" id="customPrefix" placeholder="예: MY_KEY, BUTTON_LABEL" maxlength="30">
                                        <small class="text-muted">영문, 숫자, 밑줄(_)만 사용 가능</small>
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3 text-center">
                                <button type="button" class="btn btn-outline-primary" id="auto-generate-keys">
                                    <i class="fas fa-magic me-2"></i>자동 생성
                                </button>
                                <small class="text-muted d-block mt-1">선택한 방식으로 XLT Key를 자동 생성합니다</small>
                            </div>
                            <div class="row">
                                <div class="col-12">
                                    ${keySetupData.map((item, index) => `
                                        <div class="card mb-3">
                                            <div class="card-body">
                                                <div class="row align-items-center">
                                                    <div class="col-md-6">
                                                        <label class="form-label fw-bold">문구 ${index + 1}:</label>
                                                        <div class="text-muted small mb-2">${item.text}</div>
                                                    </div>
                                                    <div class="col-md-6">
                                                        <label class="form-label">XLT Key:</label>
                                                        <input type="text" class="form-control xlt-key-input"
                                                               value=""
                                                               data-index="${item.index}"
                                                               placeholder="예: menu_login, btn_submit">
                                                        <div class="form-text">
                                                            영문, 숫자, 밑줄(_)만 사용 가능
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" id="cancel-xlt-keys">취소</button>
                            <button type="button" class="btn btn-primary" id="apply-xlt-keys">
                                <i class="fas fa-check me-2"></i>XLT Key 설정 완료
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            const bsModal = new bootstrap.Modal(modal);

            // v3.3: 키 생성 모드 선택 시 prefix 입력 필드 표시/숨김
            const keyModeRadios = modal.querySelectorAll('input[name="keyMode"]');
            const prefixContainer = modal.querySelector('#prefixInputContainer');
            keyModeRadios.forEach(radio => {
                radio.addEventListener('change', (e) => {
                    if (e.target.value === 'prefix') {
                        prefixContainer.style.display = 'block';
                    } else {
                        prefixContainer.style.display = 'none';
                    }
                });
            });

            // 자동 생성 버튼 이벤트
            document.getElementById('auto-generate-keys').addEventListener('click', () => {
                console.log('Auto-generating XLT keys...');
                const keyInputs = modal.querySelectorAll('.xlt-key-input');
                const usedKeys = new Set();

                // v3.3: 선택된 키 생성 모드 확인
                const selectedMode = modal.querySelector('input[name="keyMode"]:checked').value;
                const customPrefix = modal.querySelector('#customPrefix').value.trim();

                if (selectedMode === 'prefix') {
                    // 단순 prefix + 번호 모드
                    if (!customPrefix) {
                        alert('Prefix를 입력해주세요.');
                        modal.querySelector('#customPrefix').focus();
                        return;
                    }
                    if (!/^[a-zA-Z0-9_]+$/.test(customPrefix)) {
                        alert('Prefix는 영문, 숫자, 밑줄(_)만 사용 가능합니다.');
                        modal.querySelector('#customPrefix').focus();
                        return;
                    }

                    keyInputs.forEach((input, index) => {
                        const autoKey = `${customPrefix}_${String(index + 1).padStart(3, '0')}`;
                        input.value = autoKey;
                        usedKeys.add(autoKey);
                        input.classList.remove('is-invalid');
                        console.log(`Auto-generated simple key [${index}]: "${autoKey}"`);
                    });
                } else {
                    // 지능형 키 생성 모드 (기존)
                    keyInputs.forEach((input, index) => {
                        const textContent = keySetupData[index].text;
                        const autoKey = this.generateXltKey(textContent, usedKeys);
                        input.value = autoKey;
                        usedKeys.add(autoKey);
                        input.classList.remove('is-invalid');
                        console.log(`Auto-generated smart key [${index}]: "${textContent.substring(0, 30)}..." → "${autoKey}"`);
                    });
                }
            });

            // 적용 버튼 이벤트
            document.getElementById('apply-xlt-keys').addEventListener('click', () => {
                if (resolved) return;

                const keyInputs = modal.querySelectorAll('.xlt-key-input');
                const xltKeys = [];
                let hasError = false;

                // 먼저 빈 필드에 자동 키 생성 (기존 키와 중복되지 않도록)
                const usedKeys = new Set();
                keyInputs.forEach(input => {
                    const key = input.value.trim();
                    if (key) {
                        usedKeys.add(key);
                    }
                });

                keyInputs.forEach((input, index) => {
                    let key = input.value.trim();

                    // 빈 필드는 자동 생성
                    if (!key) {
                        const textContent = keySetupData[index].text;
                        key = this.generateXltKey(textContent, usedKeys);
                        input.value = key;
                        usedKeys.add(key);
                        console.log(`Auto-generated key for empty field [${index}]: "${key}"`);
                    }

                    // Key 유효성 검증 (영문, 숫자, 밑줄만 허용)
                    if (!/^[a-zA-Z0-9_]+$/.test(key)) {
                        hasError = true;
                        input.classList.add('is-invalid');
                        return;
                    }

                    input.classList.remove('is-invalid');
                    xltKeys.push(key);
                });

                if (hasError) {
                    alert('유효하지 않은 XLT Key가 있습니다. 영문, 숫자, 밑줄(_)만 사용해주세요.');
                    return;
                }

                // 중복 Key 확인
                const uniqueKeys = new Set(xltKeys);
                if (uniqueKeys.size !== xltKeys.length) {
                    alert('중복된 XLT Key가 있습니다. 각 Key는 고유해야 합니다.');
                    return;
                }

                console.log('XLT Keys applied:', xltKeys);
                resolved = true;
                bsModal.hide();
                setTimeout(() => modal.remove(), 300);
                resolve(xltKeys);
            });

            // 취소 버튼 이벤트
            document.getElementById('cancel-xlt-keys').addEventListener('click', () => {
                if (resolved) return;
                console.log('XLT Key modal: Cancel button clicked');
                resolved = true;
                bsModal.hide();
                setTimeout(() => modal.remove(), 300);
                resolve(null);
            });

            // X 버튼이나 backdrop 클릭으로 닫을 때도 취소 처리
            modal.addEventListener('hidden.bs.modal', () => {
                if (!resolved) {
                    console.log('XLT Key modal: Closed without button click');
                    resolved = true;
                    resolve(null);
                }
                setTimeout(() => modal.remove(), 300);
            });

            bsModal.show();
            console.log('XLT Key modal shown');
        });
    }

    async showPlaceholderModal(suggestions, validItems) {
        return new Promise((resolve) => {
            // 성능 최적화: 상세 로그 축소
            console.log(`showPlaceholderModal: ${suggestions.length}개 제안, ${validItems.length}개 아이템`);

            // 성능 최적화: 배열로 모달 내용 생성 (문자열 연결보다 빠름)
            const modalParts = [
                '<div class="placeholder-suggestions">',
                '<h5>🔧 치환자 적용 선택</h5>',
                '<p>치환 가능한 패턴을 발견했습니다. 치환자를 적용할 텍스트를 개별적으로 선택하세요.</p>',
                '<div class="mb-3 border-bottom pb-2">',
                '<button type="button" class="btn btn-sm btn-outline-primary me-2" id="select-all-placeholders">전체 선택</button>',
                '<button type="button" class="btn btn-sm btn-outline-secondary" id="select-none-placeholders">전체 해제</button>',
                '</div>'
            ];

            // 치환자 항목들을 배치로 처리 (성능 최적화)
            suggestions.forEach((suggestion, idx) => {
                const checkboxId = `apply_placeholder_${idx}`;

                // 텍스트 길이 제한으로 성능 최적화
                const truncatedOriginal = suggestion.original_text.length > 100
                    ? suggestion.original_text.substring(0, 100) + '...'
                    : suggestion.original_text;

                modalParts.push(
                    `<div class="suggestion-item mb-3 p-3 border rounded" data-index="${suggestion.index}">`,
                    `<div class="form-check mb-3">`,
                    `<input class="form-check-input placeholder-checkbox" type="checkbox" id="${checkboxId}" data-index="${idx}" checked>`,
                    `<label class="form-check-label fw-bold" for="${checkboxId}">치환자 적용하기</label>`,
                    `</div>`,
                    `<div class="text-preview">`,
                    `<div class="mb-2"><span class="badge bg-secondary">원본</span> ${truncatedOriginal}</div>`
                );

                if (suggestion.suggestions && suggestion.suggestions.length > 0) {
                    const s = suggestion.suggestions[0];
                    const truncatedPlaceholder = s.with_placeholders.length > 100
                        ? s.with_placeholders.substring(0, 100) + '...'
                        : s.with_placeholders;

                    modalParts.push(
                        `<div class="mb-2">`,
                        `<span class="badge bg-primary">치환자 적용 결과</span> ${truncatedPlaceholder}`,
                        `<br><small class="text-muted">패턴: ${s.patterns.map(p => `${p.type}(${p.matched})`).join(', ')}</small>`,
                        `</div>`,
                        `<div class="mb-3">`,
                        `<label class="form-label fw-bold">🖊️ 치환자 적용된 텍스트 편집:</label>`,
                        `<input type="text" class="form-control placeholder-text-edit" id="edit_text_${idx}" value="${s.with_placeholders}" placeholder="치환자가 적용된 텍스트를 수정하세요">`,
                        `<small class="text-muted">치환자 {{0}}, {{1}} 등을 유지하면서 텍스트를 수정할 수 있습니다.</small>`,
                        `</div>`
                    );
                } else {
                    modalParts.push(
                        `<div class="mb-3">`,
                        `<label class="form-label fw-bold">🖊️ 텍스트 편집:</label>`,
                        `<input type="text" class="form-control placeholder-text-edit" id="edit_text_${idx}" value="${suggestion.original_text}" placeholder="텍스트를 수정하세요">`,
                        `<small class="text-muted">텍스트를 수정할 수 있습니다.</small>`,
                        `</div>`
                    );
                }

                modalParts.push('</div></div>');
            });

            modalParts.push('</div>');
            const modalContent = modalParts.join('');

            // 기존 모달이 있으면 제거
            const existingModal = document.getElementById('placeholderModal');
            if (existingModal) {
                existingModal.remove();
            }

            // 모달 생성 (성능 최적화: fade 제거하여 즉시 표시)
            const modal = document.createElement('div');
            modal.id = 'placeholderModal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">치환자 적용 확인</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${modalContent}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="cancel-placeholder">취소</button>
                            <button type="button" class="btn btn-primary" id="apply-placeholder">적용하고 번역하기</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            const bsModal = new bootstrap.Modal(modal);

            let resolved = false; // Promise가 이미 resolve되었는지 추적

            // 전체 선택/해제 버튼 이벤트
            document.getElementById('select-all-placeholders').addEventListener('click', () => {
                document.querySelectorAll('.placeholder-checkbox').forEach(checkbox => {
                    checkbox.checked = true;
                });
            });

            document.getElementById('select-none-placeholders').addEventListener('click', () => {
                document.querySelectorAll('.placeholder-checkbox').forEach(checkbox => {
                    checkbox.checked = false;
                });
            });

            // 성능 최적화: 이벤트 위임으로 텍스트 편집 이벤트 처리
            modal.addEventListener('focus', (e) => {
                if (e.target.classList.contains('placeholder-text-edit')) {
                    console.log(`치환자 적용된 텍스트 편집 시작: ${e.target.value.substring(0, 30)}...`);
                }
            }, true);

            modal.addEventListener('input', (e) => {
                if (e.target.classList.contains('placeholder-text-edit')) {
                    const editedText = e.target.value.trim();

                    // 치환자 패턴 유효성 검사 (최소화)
                    if (editedText.includes('{{')) {
                        const placeholderPattern = /\{\{\d+\}\}/g;
                        const placeholders = editedText.match(placeholderPattern);
                        if (placeholders && placeholders.length > 0) {
                            console.log(`치환자 유지됨: ${placeholders.length}개`);
                        }
                    }
                }
            });

            // 적용 버튼 이벤트
            document.getElementById('apply-placeholder').addEventListener('click', () => {
                if (resolved) return;
                console.log('Placeholder modal: Apply button clicked');

                const finalTexts = [];

                // 모든 선택된 텍스트를 처리 (치환자 제안이 있는 것과 없는 것 모두)
                validItems.forEach((item) => {
                    // 이 텍스트에 대한 치환자 제안 찾기
                    const suggestionIndex = suggestions.findIndex(s => s.original_text === item.text);

                    if (suggestionIndex !== -1) {
                        // 치환자 제안이 있는 텍스트
                        const suggestion = suggestions[suggestionIndex];
                        const checkbox = document.getElementById(`apply_placeholder_${suggestionIndex}`);
                        const textInput = document.getElementById(`edit_text_${suggestionIndex}`);
                        const shouldApplyPlaceholder = checkbox && checkbox.checked;

                        if (shouldApplyPlaceholder && textInput) {
                            // 치환자 적용 선택됨: 편집된 치환자 텍스트 사용
                            const editedPlaceholderText = textInput.value.trim();
                            finalTexts.push(editedPlaceholderText);
                            console.log(`Using edited placeholder text: "${suggestion.original_text}" → "${editedPlaceholderText}"`);
                        } else {
                            // 치환자 적용 안함: 원본 텍스트 사용
                            finalTexts.push(suggestion.original_text);
                            console.log(`Using original text: "${suggestion.original_text}"`);
                        }
                    } else {
                        // 치환자 제안이 없는 텍스트: 원본 텍스트 그대로 사용
                        finalTexts.push(item.text);
                        console.log(`No placeholder suggestion, using original: "${item.text}"`);
                    }
                });

                console.log('Final texts after placeholder selection with editing:', finalTexts);
                resolved = true;
                bsModal.hide();
                setTimeout(() => modal.remove(), 100); // 300ms → 100ms로 단축
                resolve({ cancelled: false, finalTexts });
            });

            document.getElementById('cancel-placeholder').addEventListener('click', () => {
                if (resolved) return;
                console.log('Placeholder modal: Cancel button clicked');
                resolved = true;
                bsModal.hide();
                setTimeout(() => modal.remove(), 100); // 300ms → 100ms로 단축
                resolve({ cancelled: true });
            });

            // X 버튼이나 backdrop 클릭으로 닫을 때도 취소 처리
            modal.addEventListener('hidden.bs.modal', () => {
                if (!resolved) {
                    console.log('Placeholder modal: Closed without button click (X or backdrop)');
                    resolved = true;
                    resolve({ cancelled: true });
                }
                setTimeout(() => modal.remove(), 100); // 300ms → 100ms로 단축
            });

            bsModal.show();
            console.log('Placeholder modal shown');
        });
    }

    showProgress() {
        const progressSection = document.getElementById('progress-section');
        if (progressSection) {
            progressSection.style.display = 'block';
        }

        const resultSection = document.getElementById('result-section');
        if (resultSection) {
            resultSection.style.display = 'none';
        }

        // 진행 상세 정보 표시
        const progressDetails = document.getElementById('progress-details');
        if (progressDetails) {
            progressDetails.style.display = 'block';
        }

        // 실시간 로그 영역 표시
        const translationLogsSection = document.getElementById('translation-logs-section');
        if (translationLogsSection) {
            translationLogsSection.style.display = 'block';
        }

        // 모든 번역 버튼들을 비활성화
        const backupBtn = document.getElementById('backup-translate-btn');
        if (backupBtn) backupBtn.disabled = true;

        const floatingBtn = document.getElementById('floating-translate-btn');
        if (floatingBtn) floatingBtn.disabled = true;

        // 페이지 하단으로 스크롤
        if (progressSection) {
            progressSection.scrollIntoView({ behavior: 'smooth' });
        }

        // 번역 진행 상황 폴링 시작
        this.startProgressPolling();
    }

    startProgressPolling() {
        const sessionId = new URLSearchParams(window.location.search).get('session_id');
        if (!sessionId) {
            console.log('세션 ID가 없어 진행 상황 폴링을 시작할 수 없습니다.');
            return;
        }

        // 진행 상황 상세 정보 표시
        const progressDetails = document.getElementById('progress-details');
        if (progressDetails) {
            progressDetails.style.display = 'block';
        }

        // 적응형 폴링 설정 (성능 최적화)
        let pollInterval = 300; // 초기: 0.3초 (빠른 시작)
        let pollCount = 0;

        const poll = async () => {
            try {
                const response = await fetch(`/api/translation-progress/${sessionId}`);
                const data = await response.json();

                if (data.status === 'success' && data.progress) {
                    this.updateProgressUI(data.progress);

                    // 번역 완료 시 폴링 중지
                    if (data.progress.status === 'completed' || data.progress.status === 'failed') {
                        this.stopProgressPolling();
                        return;
                    }
                }

                pollCount++;
                // 점진적으로 폴링 간격 증가 (서버 부하 감소)
                if (pollCount > 5) {
                    pollInterval = Math.min(pollInterval * 1.3, 2000); // 최대 2초
                }

                this.progressPollingInterval = setTimeout(poll, pollInterval);
            } catch (error) {
                console.error('진행 상황 조회 오류:', error);
                // 오류 시 더 느린 간격으로 재시도
                this.progressPollingInterval = setTimeout(poll, Math.max(pollInterval * 2, 3000));
            }
        };

        // 첫 번째 호출
        poll();
    }

    stopProgressPolling() {
        if (this.progressPollingInterval) {
            clearTimeout(this.progressPollingInterval);
            this.progressPollingInterval = null;
        }
    }

    updateProgressUI(progress) {
        const progressTitle = document.getElementById('progress-title');
        const progressMessage = document.getElementById('progress-message');
        const progressBar = document.getElementById('translation-progress-bar');
        const progressPercentage = document.getElementById('progress-percentage');
        const progressStatus = document.getElementById('progress-status');

        // 메시지 업데이트
        if (progressMessage && progress.message) {
            progressMessage.textContent = progress.message;
        }

        // 진행률 계산
        if (progress.total_languages && progress.completed_languages) {
            const percentage = Math.round((progress.completed_languages.length / progress.total_languages) * 100);

            if (progressBar) {
                progressBar.style.width = `${percentage}%`;
                progressBar.setAttribute('aria-valuenow', percentage);
            }

            if (progressPercentage) {
                progressPercentage.textContent = `${percentage}%`;
            }

            // 상태 메시지 (예상 시간 포함)
            if (progressStatus) {
                const completedCount = progress.completed_languages.length;
                const totalCount = progress.total_languages;

                let statusText = `${completedCount}/${totalCount} 언어 번역 완료`;

                // 예상 완료 시간 표시
                if (progress.estimated_time) {
                    statusText += ` (예상 시간: ${progress.estimated_time})`;
                }

                // 경과 시간 표시
                if (progress.start_time) {
                    const elapsed = Math.floor((Date.now() - new Date(progress.start_time * 1000)) / 1000);
                    const elapsedMinutes = Math.floor(elapsed / 60);
                    const elapsedSeconds = elapsed % 60;

                    if (elapsedMinutes > 0) {
                        statusText += ` • 경과: ${elapsedMinutes}분 ${elapsedSeconds}초`;
                    } else {
                        statusText += ` • 경과: ${elapsedSeconds}초`;
                    }
                }

                progressStatus.textContent = statusText;
            }
        }

        // 완료 상태
        if (progress.status === 'completed') {
            if (progressTitle) {
                progressTitle.innerHTML = '<i class="fas fa-check-circle text-success"></i> 번역 완료!';
            }
            if (progressBar) {
                progressBar.classList.remove('progress-bar-animated');
                progressBar.classList.add('bg-success');
            }

            // 브라우저 알림 전송
            this.sendNotification('XLT 번역 완료', `번역이 성공적으로 완료되었습니다!`);

            // 완료 시 폴링 중지
            this.stopProgressPolling();
        } else if (progress.status === 'failed') {
            // 실패 알림
            this.sendNotification('XLT 번역 실패', `번역 중 오류가 발생했습니다: ${progress.message || '알 수 없는 오류'}`);
            this.stopProgressPolling();
        }

        // XLT System v3.0: 로깅 기능 비활성화
        // this.updateTranslationLogs();
    }

    // 실시간 로그 업데이트 메소드 - DISABLED (로깅 시스템 비활성화)
    async updateTranslationLogs() {
        // XLT System v3.0: 로깅 기능 비활성화 - 아무 작업도 하지 않음
        return;
    }

    // XLT System v3.0: 로깅 헬퍼 메서드 비활성화
    // getLogTypeClass(type) { ... }
    // getLogIcon(message) { ... }

    // 세션 ID 가져오기 헬퍼 메소드
    getSessionId() {
        return new URLSearchParams(window.location.search).get('session_id');
    }

    // 빠른 로딩 모달 표시 (성능 최적화)
    showLoadingModal(message = '처리 중...') {
        // 기존 로딩 모달 제거
        const existingModal = document.getElementById('quickLoadingModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 간단한 로딩 모달 생성
        const modal = document.createElement('div');
        modal.id = 'quickLoadingModal';
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
        modal.innerHTML = `
            <div class="modal-dialog modal-sm modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-body text-center py-4">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <div class="fw-bold">${message}</div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        console.log(`⏳ 빠른 로딩 모달 표시: ${message}`);
        return modal;
    }

    // 빠른 로딩 모달 숨김
    hideLoadingModal(modal) {
        if (modal && modal.parentNode) {
            modal.remove();
            console.log('✅ 빠른 로딩 모달 숨김');
        }
    }

    // XLT Key 자동 생성 헬퍼 메소드
    generateXltKey(textContent, usedKeys) {
        // 한국어 텍스트를 영문 키로 변환
        let baseKey = '';

        // 1. 영문/숫자만 추출
        const alphanumeric = textContent.match(/[a-zA-Z0-9]+/g);
        if (alphanumeric && alphanumeric.length > 0) {
            baseKey = alphanumeric.join('_').toLowerCase();
        }

        // 2. 영문이 없으면 한국어 의미 기반 키워드 매핑
        if (!baseKey) {
            const koreanKeywords = {
                '로그인': 'login', '회원가입': 'signup', '비밀번호': 'password',
                '확인': 'confirm', '취소': 'cancel', '저장': 'save', '삭제': 'delete',
                '편집': 'edit', '수정': 'modify', '추가': 'add', '제거': 'remove',
                '검색': 'search', '찾기': 'find', '목록': 'list', '상세': 'detail',
                '설정': 'settings', '프로필': 'profile', '계정': 'account',
                '지갑': 'wallet', '토큰': 'token', '거래': 'trade', '송금': 'transfer',
                '미션': 'mission', '보상': 'reward', '레벨': 'level', '포인트': 'point',
                '메뉴': 'menu', '버튼': 'button', '링크': 'link', '페이지': 'page',
                '홈': 'home', '뒤로': 'back', '다음': 'next', '이전': 'prev',
                '완료': 'complete', '시작': 'start', '끝': 'end', '종료': 'finish'
            };

            for (const [korean, english] of Object.entries(koreanKeywords)) {
                if (textContent.includes(korean)) {
                    baseKey = baseKey ? `${baseKey}_${english}` : english;
                }
            }
        }

        // 3. 여전히 키가 없으면 기본값 사용
        if (!baseKey) {
            baseKey = 'text_item';
        }

        // 4. 길이 제한 (30자)
        if (baseKey.length > 30) {
            baseKey = baseKey.substring(0, 30);
        }

        // 5. 중복 방지를 위한 숫자 접미사 추가
        let finalKey = baseKey;
        let counter = 1;
        while (usedKeys.has(finalKey)) {
            finalKey = `${baseKey}_${counter}`;
            counter++;
            // 무한루프 방지
            if (counter > 999) {
                finalKey = `${baseKey}_${Date.now()}`;
                break;
            }
        }

        return finalKey;
    }

    // 플로팅 패널 드래그 기능 초기화
    initDraggable() {
        const floatingPanel = document.getElementById('floating-selection-panel');
        const draggableHandle = floatingPanel?.querySelector('.draggable-handle');

        if (!floatingPanel || !draggableHandle) {
            console.log('드래그 가능한 요소를 찾을 수 없습니다.');
            return;
        }

        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        let xOffset = 0;
        let yOffset = 0;

        // 마우스 이벤트
        draggableHandle.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);

        // 터치 이벤트 (모바일 지원)
        draggableHandle.addEventListener('touchstart', dragStart);
        document.addEventListener('touchmove', drag);
        document.addEventListener('touchend', dragEnd);

        function dragStart(e) {
            if (e.type === "touchstart") {
                initialX = e.touches[0].clientX - xOffset;
                initialY = e.touches[0].clientY - yOffset;
            } else {
                initialX = e.clientX - xOffset;
                initialY = e.clientY - yOffset;
            }

            if (e.target === draggableHandle || draggableHandle.contains(e.target)) {
                isDragging = true;
                floatingPanel.classList.add('dragging'); // 드래그 상태 클래스 추가
                e.preventDefault(); // 기본 동작 방지
            }
        }

        function drag(e) {
            if (isDragging) {
                e.preventDefault();

                if (e.type === "touchmove") {
                    currentX = e.touches[0].clientX - initialX;
                    currentY = e.touches[0].clientY - initialY;
                } else {
                    currentX = e.clientX - initialX;
                    currentY = e.clientY - initialY;
                }

                xOffset = currentX;
                yOffset = currentY;

                // 화면 경계 제한
                const rect = floatingPanel.getBoundingClientRect();
                const maxX = window.innerWidth - rect.width;
                const maxY = window.innerHeight - rect.height;

                xOffset = Math.max(0, Math.min(maxX, xOffset));
                yOffset = Math.max(0, Math.min(maxY, yOffset));

                floatingPanel.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
            }
        }

        function dragEnd(e) {
            if (isDragging) {
                isDragging = false;
                floatingPanel.classList.remove('dragging'); // 드래그 상태 클래스 제거

                // 위치 저장 (로컬 스토리지)
                localStorage.setItem('floatingPanelPosition', JSON.stringify({ x: xOffset, y: yOffset }));

                console.log('패널 위치 저장됨:', { x: xOffset, y: yOffset });
            }
        }

        // 저장된 위치 복원
        const savedPosition = localStorage.getItem('floatingPanelPosition');
        if (savedPosition) {
            const { x, y } = JSON.parse(savedPosition);
            xOffset = x;
            yOffset = y;
            floatingPanel.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
        }

        console.log('플로팅 패널 드래그 기능 초기화 완료');
    }

    // 브라우저 알림 전송
    async sendNotification(title, message) {
        try {
            // 알림 권한 확인 및 요청
            if (Notification.permission === 'default') {
                const permission = await Notification.requestPermission();
                if (permission !== 'granted') {
                    console.log('알림 권한이 거부되었습니다.');
                    return;
                }
            } else if (Notification.permission === 'denied') {
                console.log('알림 권한이 차단되었습니다.');
                return;
            }

            // 알림 생성 및 전송
            if (Notification.permission === 'granted') {
                const notification = new Notification(title, {
                    body: message,
                    icon: '/static/favicon.ico', // 아이콘이 있다면
                    badge: '/static/favicon.ico',
                    tag: 'xlt-translation', // 중복 알림 방지
                    requireInteraction: false, // 자동으로 사라지게
                    silent: false // 사운드 재생
                });

                // 3초 후 자동 닫기
                setTimeout(() => {
                    notification.close();
                }, 3000);

                // 알림 클릭 시 창 포커스
                notification.onclick = () => {
                    window.focus();
                    notification.close();
                };

                console.log('브라우저 알림 전송 완료:', title);
            }
        } catch (error) {
            console.error('브라우저 알림 전송 실패:', error);
        }
    }

    // 페이지 로드 시 알림 권한 요청
    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('알림 권한이 허용되었습니다.');
                } else {
                    console.log('알림 권한이 거부되었습니다.');
                }
            });
        }
    }

    hideProgress() {
        console.log('hideProgress called');

        // 진행 상황 폴링 중지
        this.stopProgressPolling();

        const progressSection = document.getElementById('progress-section');
        console.log('progress-section element:', progressSection);
        if (progressSection) {
            progressSection.style.display = 'none';
            console.log('progress-section hidden');
        }

        // 진행 상황 상세 정보 숨김
        const progressDetails = document.getElementById('progress-details');
        if (progressDetails) {
            progressDetails.style.display = 'none';
        }

        // 모든 번역 버튼들을 활성화
        const backupBtn = document.getElementById('backup-translate-btn');
        if (backupBtn) backupBtn.disabled = false;

        const floatingBtn = document.getElementById('floating-translate-btn');
        if (floatingBtn) floatingBtn.disabled = false;
        console.log('hideProgress completed');
    }

    showResult(result) {
        console.log('showResult called with:', result);
        const resultContent = document.getElementById('result-content');
        console.log('result-content element:', resultContent);

        // 번역 결과 표시
        let translationsHtml = '';
        if (result.translations && result.translations.length > 0) {
            translationsHtml = `
                <div class="translation-results">
                    <h6 class="mb-3">번역 결과 미리보기: <span class="badge bg-primary">${result.translations.length}개 항목</span></h6>
                    <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                        <table class="table table-sm table-bordered table-hover">
                            <thead>
                                <tr>
                                    <th>원본</th>
                                    <th>처리된 텍스트</th>
                                    <th>한국어</th>
                                    <th>영어</th>
                                    <th>일본어</th>
                                    <th>중국어(번체)</th>
                                    <th>태국어</th>
                                </tr>
                            </thead>
                            <tbody>
            `;

            // 전체 리스트 표시 (5개 제한 제거)
            result.translations.forEach(item => {
                translationsHtml += `
                    <tr>
                        <td class="text-muted small">${this.truncateText(item.original_text, 20)}</td>
                        <td class="fw-bold">${this.truncateText(item.processed_text, 25)}</td>
                        <td>${this.truncateText(item.translations.ko_KR || '', 20)}</td>
                        <td>${this.truncateText(item.translations.en_US || '', 20)}</td>
                        <td>${this.truncateText(item.translations.ja_JP || '', 20)}</td>
                        <td>${this.truncateText(item.translations.zh_TW || '', 20)}</td>
                        <td>${this.truncateText(item.translations.th_TH || '', 20)}</td>
                    </tr>
                `;
            });

            translationsHtml += '</tbody></table></div>';

            if (result.translations.length > 5) {
                translationsHtml += `<p class="text-muted small">... 및 ${result.translations.length - 5}개 추가 항목</p>`;
            }
            translationsHtml += '</div>';
        }

        resultContent.innerHTML = `
            <div class="result-summary">
                <div class="row">
                    <div class="col-md-4">
                        <div class="result-item">
                            <strong>선택된 항목:</strong><br>
                            <span class="badge bg-primary fs-6">${result.processed_count}개</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="result-item">
                            <strong>번역 언어:</strong><br>
                            <span class="text-muted">5개 언어</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="result-item">
                            <strong>처리 시간:</strong><br>
                            <span class="text-muted">방금 전</span>
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <div class="result-item">
                        <strong>출력 파일:</strong><br>
                        <code>${result.output_file}</code>
                    </div>
                </div>
                ${translationsHtml}
            </div>
        `;

        // 다운로드 버튼에 파일명 설정
        const downloadBtn = document.getElementById('download-btn');
        if (downloadBtn && result.output_file) {
            downloadBtn.setAttribute('data-filename', result.output_file);
            console.log(`📎 다운로드 버튼에 파일명 설정: ${result.output_file}`);
        } else {
            console.error('❌ 다운로드 버튼 또는 출력 파일명을 찾을 수 없습니다:', {
                downloadBtn: !!downloadBtn,
                outputFile: result.output_file
            });
        }

        const resultSection = document.getElementById('result-section');
        console.log('result-section element:', resultSection);
        if (resultSection) {
            resultSection.style.display = 'block';
            console.log('result-section display set to block');
            resultSection.scrollIntoView({ behavior: 'smooth' });
            console.log('scrollIntoView called');
        } else {
            console.error('❌ result-section element not found!');
        }
    }

    downloadResult() {
        console.log('📥 downloadResult 함수 호출됨');

        const downloadBtn = document.getElementById('download-btn');
        console.log('다운로드 버튼:', downloadBtn);

        const filename = downloadBtn ? downloadBtn.getAttribute('data-filename') : null;
        console.log('파일명 속성:', filename);

        if (filename) {
            console.log(`📥 파일 다운로드 시작: ${filename}`);

            // 임시로 beforeunload 경고 비활성화
            window.onbeforeunload = null;

            // <a> 태그를 이용한 파일 다운로드 (페이지 이동 없이)
            const link = document.createElement('a');
            link.href = `/download/${filename}`;
            link.download = filename;
            link.style.display = 'none';

            console.log('다운로드 링크 생성:', link.href);

            document.body.appendChild(link);
            link.click();
            console.log('다운로드 링크 클릭됨');

            document.body.removeChild(link);

            // 다운로드 후 beforeunload 경고 재활성화 (다음 선택 시를 위해)
            setTimeout(() => {
                this.setupBeforeUnloadWarning();
            }, 100);
        } else {
            console.error('❌ 파일명을 찾을 수 없습니다. data-filename 속성이 설정되지 않았을 수 있습니다.');
            alert('다운로드할 파일명을 찾을 수 없습니다. 다시 번역을 실행해주세요.');
        }
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // 다운로드 테스트 함수 (개발자 도구에서 호출 가능)
    testDownload() {
        console.log('🧪 다운로드 테스트 시작');

        // 가장 최근 Excel 파일 다운로드 시도
        const testFilename = 'Manual selection - 20260417_222746_20260417_222746.xlsx';

        console.log(`테스트 파일: ${testFilename}`);

        // 직접 다운로드 링크 생성
        const link = document.createElement('a');
        link.href = `/download/${testFilename}`;
        link.download = testFilename;
        link.style.display = 'none';

        console.log('테스트 링크:', link.href);

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        console.log('✅ 테스트 다운로드 링크 클릭 완료');
    }

    setupBeforeUnloadWarning() {
        window.addEventListener('beforeunload', (e) => {
            const selectedCount = document.querySelectorAll('.item-checkbox:checked').length;
            const resultVisible = document.getElementById('result-section').style.display !== 'none';

            // 선택된 항목이 있고 번역 결과가 아직 표시되지 않은 경우에만 경고
            if (selectedCount > 0 && !resultVisible) {
                e.preventDefault();
                e.returnValue = '선택된 항목이 있습니다. 페이지를 나가시겠습니까?';
            }
        });
    }

    disableBeforeUnloadWarning() {
        window.onbeforeunload = null;
    }

    // 디버깅: 플로팅 패널 테스트
    testFloatingPanel() {
        console.log('=== Floating Panel Test ===');
        const panel = document.getElementById('floating-selection-panel');
        console.log('Panel found by ID:', !!panel);

        if (panel) {
            console.log('Panel current state:', {
                display: panel.style.display,
                classList: Array.from(panel.classList),
                offsetWidth: panel.offsetWidth,
                offsetHeight: panel.offsetHeight
            });

            // 강제로 표시해보기
            panel.style.display = 'block';
            panel.classList.remove('hidden');
            console.log('Forced panel visible');
        } else {
            console.error('Floating panel element not found in DOM!');
            console.log('Available elements with ID:',
                Array.from(document.querySelectorAll('[id]')).map(el => el.id)
            );
        }
    }

    // 플로팅 패널 업데이트
    updateFloatingPanel() {
        try {
            console.log('updateFloatingPanel called, selectedItems:', this.selectedItems.length);
            console.log('floatingPanel element:', this.floatingPanel);

            if (!this.floatingPanel) {
                console.warn('플로팅 패널 요소가 없어서 업데이트 건너뛰기');
                return;
            }

            if (this.selectedItems.length > 0) {
                console.log('Showing floating panel');
                this.showFloatingPanel();
            } else {
                console.log('Hiding floating panel');
                this.hideFloatingPanel();
            }
        } catch (e) {
            console.error('updateFloatingPanel 오류:', e);
            // 오류가 발생해도 계속 진행할 수 있도록
        }
    }

    showFloatingPanel() {
        console.log('showFloatingPanel called');

        if (!this.floatingPanel) {
            console.error('Floating panel element not found!');
            return;
        }

        try {
            // 요소들 존재 확인 (안전하게)
            const countElement = document.getElementById('floating-selected-count');
            const translateBtn = document.getElementById('floating-translate-btn');
            const translateText = document.getElementById('floating-translate-text');

            console.log('Elements found:', {
                count: !!countElement,
                btn: !!translateBtn,
                text: !!translateText,
                panel: !!this.floatingPanel
            });

            // 선택된 항목 수 업데이트 (안전하게)
            if (countElement) {
                try {
                    countElement.textContent = `${this.selectedItems.length}개`;
                    console.log('플로팅 카운트 업데이트 완료');
                } catch (e) {
                    console.error('플로팅 카운트 업데이트 실패:', e);
                }
            } else {
                console.warn('floating-selected-count 요소를 찾을 수 없음');
            }

            // 번역 버튼 텍스트 업데이트 (안전하게)
            if (translateBtn) {
                try {
                    translateBtn.disabled = this.selectedItems.length === 0;
                    console.log('플로팅 번역 버튼 상태 업데이트 완료');
                } catch (e) {
                    console.error('플로팅 번역 버튼 상태 업데이트 실패:', e);
                }
            } else {
                console.warn('floating-translate-btn 요소를 찾을 수 없음');
            }

            if (translateText) {
                try {
                    if (this.selectedItems.length > 0) {
                        translateText.textContent = `${this.selectedItems.length}개 항목 번역`;
                    } else {
                        translateText.textContent = '선택 항목 번역';
                    }
                    console.log('플로팅 번역 텍스트 업데이트 완료');
                } catch (e) {
                    console.error('플로팅 번역 텍스트 업데이트 실패:', e);
                }
            } else {
                console.warn('floating-translate-text 요소를 찾을 수 없음');
            }

            // 패널 표시 - 강력한 설정 (안전하게)
            try {
                console.log('Setting panel display to block');
                this.floatingPanel.style.cssText = 'display: block !important;';
                this.floatingPanel.classList.remove('hidden');
                this.floatingPanel.classList.add('show');

                // 추가 보장
                this.floatingPanel.style.visibility = 'visible';
                this.floatingPanel.style.opacity = '1';

                console.log('Panel after show:', {
                    display: this.floatingPanel.style.display,
                    classList: Array.from(this.floatingPanel.classList)
                });

                // 애니메이션 클래스 정리
                setTimeout(() => {
                    try {
                        this.floatingPanel.classList.remove('show');
                    } catch (e) {
                        console.error('애니메이션 정리 실패:', e);
                    }
                }, 300);

                console.log('플로팅 패널 표시 완료');
            } catch (e) {
                console.error('플로팅 패널 표시 실패:', e);
            }

        } catch (e) {
            console.error('showFloatingPanel 전체 오류:', e);
        }
    }

    hideFloatingPanel() {
        console.log('hideFloatingPanel called');
        if (!this.floatingPanel) return;

        this.floatingPanel.classList.add('hidden');
        setTimeout(() => {
            if (this.floatingPanel.classList.contains('hidden')) {
                this.floatingPanel.style.cssText = 'display: none !important;';
                this.floatingPanel.style.visibility = 'hidden';
                this.floatingPanel.style.opacity = '0';
            }
        }, 300);
    }

    // 백업 선택 요약 업데이트
    updateBackupSelection() {
        // 선택된 항목 수 업데이트
        const countElement = document.getElementById('backup-selected-count');
        if (countElement) {
            countElement.textContent = `${this.selectedItems.length}개`;
        }

        // 백업 번역 버튼 업데이트
        const translateBtn = document.getElementById('backup-translate-btn');
        const translateText = document.getElementById('backup-translate-text');

        if (translateBtn && translateText) {
            if (this.selectedItems.length > 0) {
                translateBtn.disabled = false;
                translateText.textContent = `${this.selectedItems.length}개 항목 번역`;
            } else {
                translateBtn.disabled = true;
                translateText.textContent = '선택 항목 번역';
            }
        }
    }

    optimizeFloatingPanelForScroll() {
        if (window.scrollY > 100) {
            this.floatingPanel.classList.add('scrolled');
        } else {
            this.floatingPanel.classList.remove('scrolled');
        }
    }

    showAlert(message, type) {
        // 임시 알림 표시
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 400px;';
        alertDiv.innerHTML = `
            <i class="fas fa-${type === 'danger' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        // 5초 후 자동 제거
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }

    async showTranslationGuide() {
        console.log('🔍 번역 가이드 모달 표시 시작');

        const modalElement = document.getElementById('guideModal');
        const loadingDiv = document.getElementById('guide-loading');
        const contentDiv = document.getElementById('guide-content');
        const errorDiv = document.getElementById('guide-error');

        console.log('📍 요소 확인:', {
            modalElement: modalElement,
            loadingDiv: loadingDiv,
            contentDiv: contentDiv,
            errorDiv: errorDiv
        });

        if (!modalElement) {
            console.error('❌ guideModal 요소를 찾을 수 없습니다!');
            alert('번역 가이드 모달을 찾을 수 없습니다.');
            return;
        }

        console.log('✅ 모달 요소 발견:', modalElement);
        console.log('   - 클래스:', modalElement.className);
        console.log('   - 스타일:', modalElement.style.display);
        console.log('   - 부모:', modalElement.parentElement);

        // Bootstrap 확인
        if (typeof bootstrap === 'undefined') {
            console.error('❌ Bootstrap이 로드되지 않았습니다!');
            alert('Bootstrap 라이브러리를 찾을 수 없습니다.');
            return;
        }
        console.log('✅ Bootstrap 로드됨:', typeof bootstrap);

        // 초기 상태: 로딩 표시
        if (loadingDiv) {
            loadingDiv.style.display = 'block';
            console.log('✅ 로딩 표시 설정');
        }
        if (contentDiv) {
            contentDiv.style.display = 'none';
            console.log('✅ 콘텐츠 숨김 설정');
        }
        if (errorDiv) {
            errorDiv.style.display = 'none';
            console.log('✅ 에러 숨김 설정');
        }

        // 모달 열기
        try {
            const modal = new bootstrap.Modal(modalElement, {
                backdrop: true,
                keyboard: true,
                focus: true
            });
            console.log('✅ Bootstrap Modal 인스턴스 생성:', modal);

            // 모달 닫힐 때 이벤트 리스너 (aria-hidden 정리)
            modalElement.addEventListener('hidden.bs.modal', function cleanupModal() {
                console.log('🧹 모달 닫힘 - 정리 작업 시작');

                // aria-hidden 속성 제거
                const elementsWithAriaHidden = document.querySelectorAll('[aria-hidden="true"]');
                elementsWithAriaHidden.forEach(el => {
                    if (el.id !== 'guideModal') { // 모달 자체는 제외
                        el.removeAttribute('aria-hidden');
                        console.log('  - aria-hidden 제거:', el.tagName, el.id || el.className);
                    }
                });

                // body의 modal-open 클래스 제거 확인
                if (document.body.classList.contains('modal-open')) {
                    document.body.classList.remove('modal-open');
                    console.log('  - body modal-open 클래스 제거');
                }

                // backdrop 제거 확인
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                    console.log('  - backdrop 제거');
                }

                // body 스타일 정리
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
                console.log('  - body 스타일 정리 완료');

                console.log('✅ 모달 정리 완료');

                // 이벤트 리스너 제거 (한 번만 실행)
                modalElement.removeEventListener('hidden.bs.modal', cleanupModal);
            });

            modal.show();
            console.log('✅ 모달 show() 호출 완료');

            // 모달 상태 확인
            setTimeout(() => {
                console.log('📍 모달 상태 확인:');
                console.log('   - display:', modalElement.style.display);
                console.log('   - class:', modalElement.className);
                console.log('   - aria-modal:', modalElement.getAttribute('aria-modal'));
            }, 500);
        } catch (error) {
            console.error('❌ 모달 표시 중 오류:', error);
            alert('모달을 표시하는 중 오류가 발생했습니다: ' + error.message);
            return;
        }

        try {
            // API에서 가이드 로드
            const response = await fetch('/api/translation-guide');
            const result = await response.json();

            if (result.status === 'success') {
                // 마크다운을 HTML로 변환 (간단한 변환)
                const htmlContent = this.convertMarkdownToHTML(result.content);
                contentDiv.innerHTML = htmlContent;

                // 로딩 숨기고 콘텐츠 표시
                loadingDiv.style.display = 'none';
                contentDiv.style.display = 'block';

                console.log('번역 가이드 로드 완료');
            } else {
                throw new Error(result.error || '가이드를 불러올 수 없습니다.');
            }
        } catch (error) {
            console.error('가이드 로드 오류:', error);

            // 오류 표시
            loadingDiv.style.display = 'none';
            errorDiv.style.display = 'block';
            document.getElementById('guide-error-message').textContent =
                `가이드를 불러오는 중 오류가 발생했습니다: ${error.message}`;
        }
    }

    convertMarkdownToHTML(markdown) {
        // 간단한 마크다운 to HTML 변환
        let html = markdown;

        // 코드 블록 (```)
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang}">${this.escapeHtml(code)}</code></pre>`;
        });

        // 인라인 코드 (`)
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // 헤더
        html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');

        // 굵은 글씨 (**)
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // 기울임 (*)
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // 링크
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // 순서 없는 목록
        html = html.replace(/^\- (.*$)/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

        // 순서 있는 목록
        html = html.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');

        // 수평선
        html = html.replace(/^---$/gm, '<hr>');

        // 단락
        html = html.replace(/\n\n/g, '</p><p>');
        html = '<p>' + html + '</p>';

        // 빈 단락 제거
        html = html.replace(/<p><\/p>/g, '');
        html = html.replace(/<p>\s*<\/p>/g, '');

        // 테이블 처리 (간단한 변환)
        html = html.replace(/\|(.*)\|/g, (match, content) => {
            const cells = content.split('|').map(cell => cell.trim());
            const cellTags = cells.map(cell => {
                // 헤더인지 구분 (이전 줄에 ---가 있으면 헤더)
                return `<td>${cell}</td>`;
            }).join('');
            return `<tr>${cellTags}</tr>`;
        });
        html = html.replace(/(<tr>.*<\/tr>\n?)+/g, '<table class="table table-bordered">$&</table>');

        return html;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // v3.3: 맞춤법 검사 기능 (v4.0: Claude 통합 모드 지원)
    async checkSpelling(inputField, btn) {
        // v4.0: Claude 통합 모드에서는 맞춤법 검사 방지
        if (window.xlTTranslationMode === 'claude_integrated') {
            this.showAlert('🤖✨ Claude 통합 모드: 이미 맞춤법 교정이 적용되어 있습니다!', 'info');
            return;
        }

        const originalText = inputField.value.trim();

        if (!originalText) {
            alert('검사할 텍스트를 입력해주세요.');
            return;
        }

        // 버튼 비활성화 및 로딩 표시
        const originalBtnContent = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch('/api/spell-check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: originalText
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                const correctedText = result.corrected_text;

                if (correctedText !== originalText) {
                    // 교정된 텍스트로 업데이트
                    inputField.value = correctedText;

                    // 시각적 피드백
                    inputField.style.backgroundColor = '#d4edda';
                    setTimeout(() => {
                        inputField.style.backgroundColor = '';
                    }, 1500);

                    // 알림 표시
                    this.showAlert(`✅ 맞춤법 교정 완료: "${originalText.substring(0, 20)}..." → "${correctedText.substring(0, 20)}..."`, 'success');

                    // 선택된 항목이면 selectedItems 업데이트
                    const ocrItem = inputField.closest('.ocr-item');
                    if (ocrItem) {
                        const checkbox = ocrItem.querySelector('.item-checkbox');
                        if (checkbox && checkbox.checked) {
                            this.handleSelectionChange();
                        }
                    }
                } else {
                    this.showAlert('교정할 내용이 없습니다. 맞춤법이 정확합니다.', 'info');
                }
            } else {
                throw new Error(result.error || '맞춤법 검사 실패');
            }
        } catch (error) {
            console.error('맞춤법 검사 오류:', error);
            this.showAlert(`맞춤법 검사 중 오류가 발생했습니다: ${error.message}`, 'danger');
        } finally {
            // 버튼 복구
            btn.disabled = false;
            btn.innerHTML = originalBtnContent;
        }
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    console.log('Available elements:', document.querySelectorAll('[id]').length);

    // 약간의 딜레이 후 초기화 (DOM이 완전히 준비된 후)
    setTimeout(() => {
        console.log('Initializing OCRResultsManager...');
        window.ocrManager = new OCRResultsManager();

        // 전역 테스트 함수들 추가
        window.testShowFloatingPanel = () => {
            console.log('Manual test: showing floating panel');
            const panel = document.getElementById('floating-selection-panel');
            if (panel) {
                panel.style.cssText = 'display: block !important;';
                panel.classList.remove('hidden');
                console.log('Panel should be visible now');
            } else {
                console.error('Panel not found!');
            }
        };

        window.testHideFloatingPanel = () => {
            console.log('Manual test: hiding floating panel');
            const panel = document.getElementById('floating-selection-panel');
            if (panel) {
                panel.style.cssText = 'display: none !important;';
                panel.classList.add('hidden');
                console.log('Panel should be hidden now');
            }
        };

        window.forceShowPanel = () => {
            if (window.ocrManager) {
                window.ocrManager.selectedItems = [{text: 'test'}]; // 가짜 데이터
                window.ocrManager.updateFloatingPanel();
            }
        };

        // 선택 테스트 함수들 추가
        window.testSelection = () => {
            console.log('=== 선택 테스트 시작 ===');
            if (window.ocrManager) {
                window.ocrManager.debugDOMState();
                window.ocrManager.updateSelectedItems();
                window.ocrManager.updateSelectedCount();
                console.log('현재 선택된 항목:', window.ocrManager.selectedItems);
            }
        };

        window.forceSelectFirst = () => {
            console.log('첫 번째 체크박스 강제 체크');
            const firstCheckbox = document.querySelector('.item-checkbox');
            if (firstCheckbox) {
                firstCheckbox.checked = true;
                console.log('첫 번째 체크박스 체크됨');
                if (window.ocrManager) {
                    window.ocrManager.handleSelectionChange();
                }
            } else {
                console.error('체크박스를 찾을 수 없음!');
            }
        };

        window.checkAllCheckboxes = () => {
            console.log('모든 체크박스 체크');
            const checkboxes = document.querySelectorAll('.item-checkbox');
            checkboxes.forEach((cb, i) => {
                cb.checked = true;
                console.log(`체크박스 ${i} 체크됨`);
            });
            if (window.ocrManager) {
                window.ocrManager.handleSelectionChange();
            }
        };

        // 플로팅 패널 요소들 직접 확인
        window.checkFloatingElements = () => {
            console.log('=== 플로팅 패널 요소 확인 ===');
            const elements = {
                panel: document.getElementById('floating-selection-panel'),
                count: document.getElementById('floating-selected-count'),
                btn: document.getElementById('floating-translate-btn'),
                text: document.getElementById('floating-translate-text')
            };

            Object.entries(elements).forEach(([name, el]) => {
                console.log(`${name}:`, el ? '존재' : '없음', el);
            });

            // 직접 업데이트 시도
            if (elements.count) {
                elements.count.textContent = '5개';
                console.log('카운트 직접 업데이트 완료');
            }

            if (elements.btn) {
                elements.btn.disabled = false;
                console.log('버튼 직접 활성화 완료');
            }

            if (elements.text) {
                elements.text.textContent = '5개 항목 번역';
                console.log('텍스트 직접 업데이트 완료');
            }

            console.log('=== 플로팅 패널 요소 확인 완료 ===');
        };

        // 오류 없이 번역 실행
        window.safeTranslate = () => {
            console.log('안전한 번역 실행');
            if (window.ocrManager && window.ocrManager.selectedItems.length > 0) {
                window.ocrManager.translateSelected();
            } else {
                console.log('선택된 항목이 없거나 OCR 매니저가 없음');
            }
        };

        // 플로팅 번역 버튼 강제 클릭
        window.clickFloatingTranslate = () => {
            console.log('플로팅 번역 버튼 강제 클릭');
            const btn = document.getElementById('floating-translate-btn');
            if (btn) {
                console.log('버튼 찾음, 클릭 실행');
                btn.click();
            } else {
                console.error('플로팅 번역 버튼을 찾을 수 없음!');
            }
        };

        // 전체 플로우 테스트
        window.testFullFlow = () => {
            console.log('=== 전체 플로우 테스트 시작 ===');

            // 1단계: 체크박스 선택
            const checkboxes = document.querySelectorAll('.item-checkbox');
            if (checkboxes.length > 0) {
                checkboxes[0].checked = true;
                checkboxes[1] && (checkboxes[1].checked = true);
                checkboxes[2] && (checkboxes[2].checked = true);
                console.log('✅ 1단계: 3개 체크박스 선택 완료');

                // 2단계: 선택 변경 이벤트 트리거
                if (window.ocrManager) {
                    window.ocrManager.handleSelectionChange();
                    console.log('✅ 2단계: 선택 변경 이벤트 트리거 완료');

                    // 3단계: 선택된 항목 확인
                    console.log(`✅ 3단계: 선택된 항목 ${window.ocrManager.selectedItems.length}개`);

                    // 4단계: 번역 실행
                    setTimeout(() => {
                        console.log('✅ 4단계: 번역 실행');
                        window.ocrManager.translateSelected();
                    }, 1000);
                }
            } else {
                console.error('❌ 체크박스를 찾을 수 없음!');
            }

            console.log('=== 전체 플로우 테스트 완료 ===');
        };

    }, 100);

    // 번역 가이드 테스트 함수 추가
    window.testGuideModal = function() {
        console.log('=== 번역 가이드 모달 테스트 ===');

        // 1. 모달 요소 확인
        const modal = document.getElementById('guideModal');
        console.log('1. 모달 요소:', modal);

        // 2. 버튼 요소 확인
        const btn = document.getElementById('view-guide-btn');
        console.log('2. 버튼 요소:', btn);

        // 3. Bootstrap 확인
        console.log('3. Bootstrap:', typeof bootstrap !== 'undefined' ? '✅ 로드됨' : '❌ 없음');

        // 4. 모달 직접 열기 시도
        if (modal && typeof bootstrap !== 'undefined') {
            console.log('4. 모달 직접 열기 시도...');
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
            console.log('✅ 모달 show() 호출 완료');
        }

        console.log('=== 테스트 완료 ===');
    };

    // 가이드 로드 테스트
    window.testGuideAPI = async function() {
        console.log('=== API 테스트 시작 ===');
        try {
            const response = await fetch('/api/translation-guide');
            const result = await response.json();
            console.log('API 응답:', result.status);
            console.log('가이드 크기:', result.size);
            console.log('내용 미리보기:', result.content.substring(0, 100));
        } catch (error) {
            console.error('API 오류:', error);
        }
    };
});

// 키보드 단축키
document.addEventListener('keydown', (e) => {
    // Ctrl+A: 모든 필터링된 텍스트 선택
    if (e.ctrlKey && e.key === 'a') {
        e.preventDefault();
        document.getElementById('select-all-filtered').click();
    }

    // Ctrl+Enter: 번역 시작
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('translate-selected-btn').click();
    }
});

// 페이지 로드 시 beforeunload 경고 설정
document.addEventListener('DOMContentLoaded', () => {
    // OCRResultsManager는 이미 위에서 초기화됨
    // beforeunload 경고 설정
    const setupWarning = () => {
        window.addEventListener('beforeunload', (e) => {
            const selectedCount = document.querySelectorAll('.item-checkbox:checked').length;
            const resultVisible = document.getElementById('result-section').style.display !== 'none';

            // 선택된 항목이 있고 번역 결과가 아직 표시되지 않은 경우에만 경고
            if (selectedCount > 0 && !resultVisible) {
                e.preventDefault();
                e.returnValue = '선택된 항목이 있습니다. 페이지를 나가시겠습니까?';
            }
        });
    };
    setupWarning();
});