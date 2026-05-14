@echo off
chcp 65001 > nul
title XLT System v3.0 설치

echo 🚀 XLT System v3.0 설치를 시작합니다...
echo 📍 피그마 디자인 → 다국어 번역 자동화 도구
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  관리자 권한으로 실행하는 것을 권장합니다.
    echo    설치 중 일부 기능이 제한될 수 있습니다.
    echo.
)

:: Python 설치 확인
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo 💡 Python 3.8 이상을 설치한 후 다시 실행해주세요.
    echo    다운로드: https://python.org
    echo    설치 시 "Add Python to PATH" 체크 필수!
    pause
    exit /b 1
)

:: Python 버전 확인
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 🔍 Python 버전: %PYTHON_VERSION%

:: Python 버전 체크 (3.8 이상)
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if %errorLevel% neq 0 (
    echo ❌ Python 3.8 이상이 필요합니다. (현재: %PYTHON_VERSION%)
    pause
    exit /b 1
)

echo ✅ Python 환경이 준비되었습니다.
echo.

:: pip 업그레이드
echo 📦 pip 업그레이드 중...
python -m pip install --upgrade pip --quiet

:: 의존성 설치
echo 📚 필수 패키지 설치 중...
echo   - EasyOCR (OCR 엔진)
echo   - Google Translate (번역 엔진)
echo   - OpenPyXL (Excel 처리)
echo   - Flask (웹 서버)
echo   - Pillow (이미지 처리)

pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo ❌ 패키지 설치 중 오류가 발생했습니다.
    echo 💡 인터넷 연결을 확인하고 다시 시도해주세요.
    pause
    exit /b 1
)

echo ✅ 모든 패키지가 성공적으로 설치되었습니다.
echo.

:: 설정 파일 생성
echo ⚙️  기본 설정 생성 중...

if exist "figma_config_example.json" if not exist "figma_config.json" (
    copy "figma_config_example.json" "figma_config.json" >nul
    echo ✅ Figma 설정 파일이 생성되었습니다.
    echo    📝 figma_config.json 파일을 열어 Figma 토큰을 추가해주세요.
)

:: 폴더 생성
if not exist "output" mkdir output
if not exist "figma" mkdir figma
if not exist "logs" mkdir logs
echo ✅ 필요한 폴더들이 생성되었습니다.

:: 바로가기 생성
echo 🖥️  바로가기 생성 중...

:: 데스크톱 바로가기 (.bat 파일)
set INSTALL_DIR=%cd%
set SHORTCUT_PATH=%USERPROFILE%\Desktop\XLT System.bat

echo @echo off > "%SHORTCUT_PATH%"
echo title XLT System v3.0 >> "%SHORTCUT_PATH%"
echo cd /d "%INSTALL_DIR%" >> "%SHORTCUT_PATH%"
echo echo 🚀 XLT System 서버를 시작합니다... >> "%SHORTCUT_PATH%"
echo echo 웹 브라우저에서 http://localhost:5004 에 접속하세요. >> "%SHORTCUT_PATH%"
echo echo. >> "%SHORTCUT_PATH%"
echo start http://localhost:5004 >> "%SHORTCUT_PATH%"
echo timeout /t 3 /nobreak ^> nul >> "%SHORTCUT_PATH%"
echo python stable_web_server.py >> "%SHORTCUT_PATH%"

echo ✅ 데스크톱 바로가기가 생성되었습니다.

:: 시작 메뉴 바로가기 (선택사항)
set START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
if exist "%START_MENU%" (
    copy "%USERPROFILE%\Desktop\XLT System.bat" "%START_MENU%\XLT System.bat" >nul 2>&1
    echo ✅ 시작 메뉴 바로가기가 생성되었습니다.
)

echo.

:: 시스템 검증
echo 🔬 시스템 검증 중...

python -c "try: from xlt import XLTConfig, XLTPipeline; config = XLTConfig(); pipeline = XLTPipeline(config); print('✅ XLT 시스템 초기화 성공'); except Exception as e: print(f'❌ 초기화 실패: {e}'); exit(1)"

if %errorLevel% neq 0 (
    echo ❌ 시스템 검증에 실패했습니다.
    pause
    exit /b 1
)

echo.
echo 🎉 XLT System v3.0 설치가 완료되었습니다!
echo.
echo 📋 사용 방법:
echo   1. 서버 시작:
echo      - 데스크톱의 'XLT System.bat' 더블클릭
echo      - 또는 명령 프롬프트에서: python stable_web_server.py
echo.
echo   2. 웹 브라우저에서 접속:
echo      http://localhost:5004
echo.
echo   3. 피그마 토큰 설정 (선택사항):
echo      figma_config.json 파일 편집
echo.
echo 💡 문제 해결:
echo   - 포트 충돌 시: netstat -ano ^| findstr :5004
echo   - 서버 종료: Ctrl+C 또는 명령 프롬프트 창 닫기
echo   - 로그 확인: logs\ 폴더
echo.

:: 자동 실행 옵션
set /p choice="🔗 지금 XLT System을 시작하시겠습니까? (Y/N): "
if /i "%choice%"=="Y" (
    echo 🚀 서버를 시작합니다...
    start http://localhost:5004
    timeout /t 2 /nobreak > nul
    python stable_web_server.py
) else (
    echo 📌 나중에 데스크톱의 'XLT System.bat' 파일을 실행하세요.
)

pause