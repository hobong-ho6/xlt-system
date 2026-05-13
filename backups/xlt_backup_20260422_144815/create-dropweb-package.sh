#!/bin/bash

# XLT System DropWeb 패키지 생성 스크립트
# DropWeb 정적 호스팅에 업로드할 ZIP 파일을 생성합니다.

echo "🚀 XLT System DropWeb 패키지 생성을 시작합니다..."

# 변수 설정
FRONTEND_DIR="dropweb-frontend"
OUTPUT_DIR="dropweb-package"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PACKAGE_NAME="xlt-system-web-${TIMESTAMP}.zip"

# 기존 패키지 디렉토리 정리
if [ -d "$OUTPUT_DIR" ]; then
    echo "📁 기존 패키지 디렉토리를 정리합니다..."
    rm -rf "$OUTPUT_DIR"
fi

# 패키지 디렉토리 생성
mkdir -p "$OUTPUT_DIR"

# 필수 파일 복사
echo "📋 DropWeb 업로드 체크리스트 확인 중..."

# 체크리스트 확인
echo "✅ 체크리스트:"

# 1. index.html 존재 확인
if [ -f "$FRONTEND_DIR/index.html" ]; then
    echo "  ✅ index.html 존재"
    cp "$FRONTEND_DIR/index.html" "$OUTPUT_DIR/"
else
    echo "  ❌ index.html 없음 - 필수 파일입니다!"
    exit 1
fi

# 2. JavaScript 파일 복사
if [ -f "$FRONTEND_DIR/script.js" ]; then
    echo "  ✅ script.js 존재"
    cp "$FRONTEND_DIR/script.js" "$OUTPUT_DIR/"
else
    echo "  ⚠️  script.js 없음"
fi

# 3. CSS 파일 복사
if [ -f "$FRONTEND_DIR/style.css" ]; then
    echo "  ✅ style.css 존재"
    cp "$FRONTEND_DIR/style.css" "$OUTPUT_DIR/"
else
    echo "  ⚠️  style.css 없음"
fi

# 4. 문서 파일 복사
if [ -f "$FRONTEND_DIR/service-spec.md" ]; then
    echo "  ✅ service-spec.md 존재"
    cp "$FRONTEND_DIR/service-spec.md" "$OUTPUT_DIR/"
fi

if [ -f "$FRONTEND_DIR/README.md" ]; then
    echo "  ✅ README.md 존재"
    cp "$FRONTEND_DIR/README.md" "$OUTPUT_DIR/"
fi

# 5. 상대 경로 검사
echo "🔍 상대 경로 검사 중..."
relative_path_issues=$(grep -r "href=\"/\|src=\"/\|url(/\|action=\"/" "$OUTPUT_DIR" 2>/dev/null || true)

if [ -n "$relative_path_issues" ]; then
    echo "  ⚠️  절대 경로 발견 - 상대 경로로 수정 필요:"
    echo "$relative_path_issues"
    echo ""
    echo "  💡 수정 방법:"
    echo "     href=\"/\" → href=\"./\""
    echo "     src=\"/style.css\" → src=\"style.css\""
    echo "     url(/assets/) → url(assets/)"
else
    echo "  ✅ 모든 경로가 상대 경로입니다"
fi

# 6. 허용되지 않는 파일 형식 검사
echo "📄 파일 형식 검사 중..."
forbidden_files=$(find "$OUTPUT_DIR" -type f ! -name "*.html" ! -name "*.css" ! -name "*.js" ! -name "*.json" ! -name "*.txt" ! -name "*.md" ! -name "*.png" ! -name "*.jpg" ! -name "*.jpeg" ! -name "*.gif" ! -name "*.svg" ! -name "*.ico" ! -name "*.webp" ! -name "*.woff" ! -name "*.woff2" ! -name "*.ttf" ! -name "*.eot" ! -name "*.otf" ! -name "*.map" ! -name "*.xml" ! -name "*.webmanifest" 2>/dev/null || true)

if [ -n "$forbidden_files" ]; then
    echo "  ⚠️  허용되지 않는 파일 형식 발견:"
    echo "$forbidden_files"
    echo "  💡 .php, .py, .sh, .exe 등은 DropWeb에서 지원하지 않습니다"
else
    echo "  ✅ 모든 파일이 허용된 형식입니다"
fi

# ZIP 파일 생성
echo "📦 ZIP 패키지 생성 중..."
cd "$OUTPUT_DIR"
zip -r "../$PACKAGE_NAME" . > /dev/null 2>&1
cd ..

# 파일 크기 확인
package_size=$(du -h "$PACKAGE_NAME" | cut -f1)
package_size_bytes=$(stat -f%z "$PACKAGE_NAME" 2>/dev/null || stat -c%s "$PACKAGE_NAME" 2>/dev/null)
max_size_bytes=$((150 * 1024 * 1024))  # 150MB

echo "📊 패키지 정보:"
echo "  파일명: $PACKAGE_NAME"
echo "  크기: $package_size"

if [ "$package_size_bytes" -gt "$max_size_bytes" ]; then
    echo "  ⚠️  파일 크기가 150MB를 초과합니다! ($package_size)"
    echo "  💡 이미지나 불필요한 파일을 제거해주세요"
else
    echo "  ✅ 파일 크기가 적절합니다 (150MB 제한)"
fi

# 최종 체크리스트 출력
echo ""
echo "🎯 DropWeb 업로드 최종 체크리스트:"
echo "  📁 ZIP 파일: $PACKAGE_NAME"
echo "  📋 업로드 전 확인사항:"
echo "     ☑️ index.html이 ZIP 내부 루트에 있는가?"
echo "     ☑️ 모든 경로가 상대 경로인가?"
echo "     ☑️ 파일 크기가 150MB 이하인가?"
echo "     ☑️ 허용되지 않는 파일 형식이 없는가?"
echo ""

# 사용자 안내
echo "📚 다음 단계:"
echo "  1. 로컬 XLT 서버가 실행 중인지 확인:"
echo "     python3 stable_web_server.py"
echo ""
echo "  2. DropWeb에 업로드:"
echo "     - DropWeb 관리 페이지 접속"
echo "     - '$PACKAGE_NAME' 파일 업로드"
echo "     - 배포 완료 후 웹사이트 테스트"
echo ""
echo "  3. 테스트 방법:"
echo "     - 웹사이트 접속 → 연결 상태 확인"
echo "     - 피그마 URL로 OCR 테스트"
echo "     - 번역 및 Excel 다운로드 테스트"
echo ""

# 정리
rm -rf "$OUTPUT_DIR"

echo "✅ DropWeb 패키지 생성이 완료되었습니다!"
echo "📦 파일: $PACKAGE_NAME"