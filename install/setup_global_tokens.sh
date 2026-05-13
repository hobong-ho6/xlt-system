#!/bin/bash

# XLT System 전역 토큰 설정 마법사
# macOS Keychain 기반 안전한 토큰 관리 시스템 구축
#
# 주요 기능:
# - 기존 토큰 파일 자동 감지 및 마이그레이션
# - macOS Keychain 안전 저장
# - 환경 변수 자동 설정 (~/.zshrc)
# - 토큰 유효성 검증
# - 기존 평문 토큰 파일 안전 제거

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 이모지
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
ROCKET="🚀"
KEY="🔐"
SHIELD="🛡️"
MAGIC="✨"

echo -e "${CYAN}${MAGIC} XLT System 전역 토큰 설정 마법사${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${GREEN}macOS Keychain 기반 안전한 토큰 관리 시스템을 구축합니다.${NC}"
echo -e "${GREEN}한 번 설정하면 모든 XLT 프로젝트에서 자동으로 사용 가능합니다!${NC}"
echo ""

# macOS 환경 확인
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${CROSS} ${RED}이 스크립트는 macOS에서만 실행 가능합니다.${NC}"
    exit 1
fi

# 필수 도구 확인
check_requirements() {
    echo -e "${BLUE}${SHIELD} 필수 요구사항 확인 중...${NC}"

    # security 명령어 확인
    if ! command -v security &> /dev/null; then
        echo -e "${CROSS} ${RED}macOS security 명령어를 찾을 수 없습니다.${NC}"
        exit 1
    fi

    # jq 설치 확인 (JSON 파싱용)
    if ! command -v jq &> /dev/null; then
        echo -e "${WARNING} ${YELLOW}jq가 설치되지 않았습니다. 설치하는 중...${NC}"
        if command -v brew &> /dev/null; then
            brew install jq
        else
            echo -e "${CROSS} ${RED}Homebrew가 필요합니다. 설치 후 다시 실행해주세요.${NC}"
            echo "Homebrew 설치: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    fi

    echo -e "${CHECK} ${GREEN}모든 요구사항이 충족되었습니다.${NC}"
}

# 기존 토큰 감지 함수
detect_existing_tokens() {
    echo ""
    echo -e "${BLUE}${KEY} 기존 토큰 파일 검색 중...${NC}"

    local found_tokens=()

    # Figma 토큰 확인
    if [[ -f "figma_config.json" ]]; then
        if jq -e '.access_token' figma_config.json &> /dev/null; then
            local figma_token=$(jq -r '.access_token' figma_config.json 2>/dev/null)
            if [[ -n "$figma_token" && "$figma_token" != "null" ]]; then
                echo -e "${CHECK} ${GREEN}Figma 토큰 발견: figma_config.json${NC}"
                found_tokens+=("figma:$figma_token")
            fi
        fi
    fi

    # 환경 변수에서 토큰 확인
    if [[ -n "$FIGMA_TOKEN" ]]; then
        echo -e "${CHECK} ${GREEN}Figma 토큰 발견: 환경변수 FIGMA_TOKEN${NC}"
        found_tokens+=("figma:$FIGMA_TOKEN")
    fi

    if [[ -n "$SLACK_TOKEN" ]]; then
        echo -e "${CHECK} ${GREEN}Slack 토큰 발견: 환경변수 SLACK_TOKEN${NC}"
        found_tokens+=("slack:$SLACK_TOKEN")
    fi

    if [[ -n "$GITHUB_TOKEN" ]]; then
        echo -e "${CHECK} ${GREEN}GitHub 토큰 발견: 환경변수 GITHUB_TOKEN${NC}"
        found_tokens+=("github:$GITHUB_TOKEN")
    fi

    # Git config에서 GitHub PAT 확인
    if [[ -f ".git/config" ]]; then
        local git_url=$(git config --get remote.origin.url 2>/dev/null || echo "")
        if [[ "$git_url" == *"ghp_"* ]]; then
            local github_pat=$(echo "$git_url" | sed -n 's/.*:\\/\\/.*:\\(ghp_[^@]*\\)@.*/\\1/p')
            if [[ -n "$github_pat" ]]; then
                echo -e "${WARNING} ${YELLOW}GitHub PAT 발견: .git/config (보안 위험!)${NC}"
                found_tokens+=("github:$github_pat")
            fi
        fi
    fi

    if [[ ${#found_tokens[@]} -eq 0 ]]; then
        echo -e "${WARNING} ${YELLOW}기존 토큰을 찾을 수 없습니다. 수동 입력이 필요합니다.${NC}"
    else
        echo -e "${CHECK} ${GREEN}총 ${#found_tokens[@]}개의 토큰을 발견했습니다.${NC}"
    fi

    echo "${found_tokens[@]}"
}

# 토큰 유효성 검증
validate_token() {
    local service="$1"
    local token="$2"

    case "$service" in
        "figma")
            local response=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "X-Figma-Token: $token" \
                "https://api.figma.com/v1/me" || echo "000")
            ;;
        "slack")
            local response=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: Bearer $token" \
                "https://slack.com/api/auth.test" || echo "000")
            ;;
        "github")
            local response=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: token $token" \
                "https://api.github.com/user" || echo "000")
            ;;
        *)
            echo "000"
            return 1
            ;;
    esac

    if [[ "$response" == "200" ]]; then
        return 0
    else
        return 1
    fi
}

# Keychain에 토큰 저장
store_token_keychain() {
    local service="$1"
    local token="$2"

    local account="xlt_${service}"
    local service_name="XLT_${service^^}_TOKEN"

    # 기존 토큰 삭제 (있는 경우)
    security delete-generic-password -a "$account" -s "$service_name" 2>/dev/null || true

    # 새 토큰 저장
    if security add-generic-password -a "$account" -s "$service_name" -w "$token" -U 2>/dev/null; then
        echo -e "${CHECK} ${GREEN}${service^} 토큰이 Keychain에 안전하게 저장되었습니다.${NC}"
        return 0
    else
        echo -e "${CROSS} ${RED}${service^} 토큰 저장 실패${NC}"
        return 1
    fi
}

# 토큰 마이그레이션
migrate_tokens() {
    local found_tokens=("$@")

    if [[ ${#found_tokens[@]} -eq 0 ]]; then
        return 0
    fi

    echo ""
    echo -e "${BLUE}${ROCKET} 토큰 마이그레이션 시작...${NC}"

    for token_info in "${found_tokens[@]}"; do
        local service=$(echo "$token_info" | cut -d':' -f1)
        local token=$(echo "$token_info" | cut -d':' -f2-)

        echo ""
        echo -e "${CYAN}${service^} 토큰 처리 중...${NC}"

        # 토큰 유효성 검증
        if validate_token "$service" "$token"; then
            echo -e "${CHECK} ${GREEN}토큰 유효성 검증 성공${NC}"

            # Keychain에 저장
            if store_token_keychain "$service" "$token"; then
                echo -e "${CHECK} ${GREEN}${service^} 토큰 마이그레이션 완료${NC}"
            else
                echo -e "${CROSS} ${RED}${service^} 토큰 마이그레이션 실패${NC}"
            fi
        else
            echo -e "${WARNING} ${YELLOW}토큰 유효성 검증 실패. 건너뜁니다.${NC}"
        fi
    done
}

# 수동 토큰 입력
manual_token_input() {
    local services=("figma" "slack" "github")

    echo ""
    echo -e "${BLUE}${KEY} 수동 토큰 입력${NC}"
    echo -e "${YELLOW}각 서비스의 토큰을 입력하세요. (건너뛰려면 Enter)${NC}"

    for service in "${services[@]}"; do
        # 이미 Keychain에 있는지 확인
        local existing_token=$(security find-generic-password -a "xlt_$service" -s "XLT_${service^^}_TOKEN" -w 2>/dev/null || echo "")

        if [[ -n "$existing_token" ]]; then
            echo -e "${CHECK} ${GREEN}${service^} 토큰이 이미 Keychain에 있습니다.${NC}"
            continue
        fi

        echo ""
        echo -e "${CYAN}${service^} 토큰을 입력하세요:${NC}"

        case "$service" in
            "figma")
                echo -e "${YELLOW}Figma → Settings → Personal Access Tokens에서 생성${NC}"
                echo -e "${YELLOW}형식: figd_...${NC}"
                ;;
            "slack")
                echo -e "${YELLOW}Slack App → OAuth & Permissions → Bot User OAuth Token${NC}"
                echo -e "${YELLOW}형식: xoxb-...${NC}"
                ;;
            "github")
                echo -e "${YELLOW}GitHub → Settings → Developer settings → Personal access tokens${NC}"
                echo -e "${YELLOW}형식: ghp_... (classic) 또는 github_pat_...${NC}"
                ;;
        esac

        read -s -p "토큰: " token
        echo ""

        if [[ -n "$token" ]]; then
            echo -e "${BLUE}토큰 유효성 검증 중...${NC}"

            if validate_token "$service" "$token"; then
                echo -e "${CHECK} ${GREEN}토큰 유효성 검증 성공${NC}"

                if store_token_keychain "$service" "$token"; then
                    echo -e "${CHECK} ${GREEN}${service^} 토큰 설정 완료${NC}"
                fi
            else
                echo -e "${CROSS} ${RED}토큰 유효성 검증 실패. 다시 확인해주세요.${NC}"
            fi
        else
            echo -e "${WARNING} ${YELLOW}${service^} 토큰을 건너뜁니다.${NC}"
        fi
    done
}

# 환경 변수 설정
setup_environment() {
    echo ""
    echo -e "${BLUE}${ROCKET} 환경 변수 설정 중...${NC}"

    # 사용자 셸 확인
    local user_shell=$(basename "$SHELL")
    local rc_file=""

    case "$user_shell" in
        "zsh")
            rc_file="$HOME/.zshrc"
            ;;
        "bash")
            rc_file="$HOME/.bash_profile"
            ;;
        *)
            rc_file="$HOME/.profile"
            ;;
    esac

    echo -e "${BLUE}셸: $user_shell, 설정 파일: $rc_file${NC}"

    # 기존 XLT 설정 제거
    if [[ -f "$rc_file" ]]; then
        # XLT 관련 기존 설정 백업 및 제거
        local backup_file="${rc_file}.xlt_backup_$(date +%s)"
        cp "$rc_file" "$backup_file"
        echo -e "${CHECK} ${GREEN}기존 설정을 $backup_file 에 백업했습니다.${NC}"

        # XLT 관련 기존 줄 제거
        sed -i '' '/# XLT System/d' "$rc_file" 2>/dev/null || true
        sed -i '' '/export FIGMA_TOKEN=/d' "$rc_file" 2>/dev/null || true
        sed -i '' '/export SLACK_TOKEN=/d' "$rc_file" 2>/dev/null || true
        sed -i '' '/export GITHUB_TOKEN=/d' "$rc_file" 2>/dev/null || true
        sed -i '' '/ssh-add.*xlt/d' "$rc_file" 2>/dev/null || true
    fi

    # 새 환경 변수 설정 추가
    cat >> "$rc_file" << 'EOF'

# XLT System 토큰 자동 로드 (from Keychain)
# 생성 시간: $(date)

# Figma 토큰
export FIGMA_TOKEN=$(security find-generic-password -a "xlt_figma" -s "XLT_FIGMA_TOKEN" -w 2>/dev/null)

# Slack 토큰
export SLACK_TOKEN=$(security find-generic-password -a "xlt_slack" -s "XLT_SLACK_TOKEN" -w 2>/dev/null)

# GitHub 토큰 (SSH 사용 권장하지만 일부 도구에서 필요)
export GITHUB_TOKEN=$(security find-generic-password -a "xlt_github" -s "XLT_GITHUB_TOKEN" -w 2>/dev/null)

# XLT SSH 키 자동 추가 (GitHub 인증용)
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_xlt 2>/dev/null

EOF

    echo -e "${CHECK} ${GREEN}환경 변수 설정이 $rc_file 에 추가되었습니다.${NC}"

    # 현재 세션에 즉시 적용
    echo -e "${BLUE}현재 세션에 환경 변수 적용 중...${NC}"
    export FIGMA_TOKEN=$(security find-generic-password -a "xlt_figma" -s "XLT_FIGMA_TOKEN" -w 2>/dev/null)
    export SLACK_TOKEN=$(security find-generic-password -a "xlt_slack" -s "XLT_SLACK_TOKEN" -w 2>/dev/null)
    export GITHUB_TOKEN=$(security find-generic-password -a "xlt_github" -s "XLT_GITHUB_TOKEN" -w 2>/dev/null)

    echo -e "${CHECK} ${GREEN}환경 변수 설정 완료${NC}"
}

# 토큰 파일 정리
cleanup_token_files() {
    echo ""
    echo -e "${BLUE}${SHIELD} 보안을 위한 토큰 파일 정리...${NC}"

    local files_to_remove=()

    # figma_config.json 확인
    if [[ -f "figma_config.json" ]]; then
        if jq -e '.access_token' figma_config.json &> /dev/null; then
            files_to_remove+=("figma_config.json")
        fi
    fi

    # slack_config.json 확인
    if [[ -f "slack_config.json" ]]; then
        if jq -e '.bot_token // .access_token' slack_config.json &> /dev/null; then
            files_to_remove+=("slack_config.json")
        fi
    fi

    if [[ ${#files_to_remove[@]} -gt 0 ]]; then
        echo -e "${WARNING} ${YELLOW}다음 파일에 토큰이 평문으로 저장되어 있습니다:${NC}"
        for file in "${files_to_remove[@]}"; do
            echo -e "  • $file"
        done

        echo ""
        read -p "이 파일들을 안전하게 삭제하시겠습니까? (y/N): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for file in "${files_to_remove[@]}"; do
                # 백업 생성
                local backup_file="${file}.backup_$(date +%s)"
                cp "$file" "$backup_file"
                echo -e "${CHECK} ${GREEN}$file → $backup_file 백업 생성${NC}"

                # 안전 삭제 (macOS)
                rm -P "$file" 2>/dev/null || rm -f "$file"
                echo -e "${CHECK} ${GREEN}$file 안전 삭제 완료${NC}"
            done
        else
            echo -e "${WARNING} ${YELLOW}토큰 파일이 유지됩니다. 수동으로 삭제하거나 .gitignore에 추가하세요.${NC}"
        fi
    else
        echo -e "${CHECK} ${GREEN}정리할 토큰 파일이 없습니다.${NC}"
    fi
}

# .gitignore 업데이트
update_gitignore() {
    echo ""
    echo -e "${BLUE}${SHIELD} .gitignore 보안 강화...${NC}"

    if [[ -f ".gitignore" ]]; then
        # XLT 관련 기존 패턴 제거
        local backup_file=".gitignore.backup_$(date +%s)"
        cp ".gitignore" "$backup_file"
    else
        touch ".gitignore"
    fi

    # 보안 패턴 추가
    cat >> ".gitignore" << 'EOF'

# XLT System 보안 - 토큰 및 자격증명 완전 차단
figma_config.json
slack_config.json
github_config.json
*.token
.env
.env.*
!.env.example
credentials.json
auth.json

# Git 자격증명
.git-credentials
.gitconfig.local

# SSH 키 (절대 커밋 금지)
id_*
id_*.pub
*.key
*.pem
*.p12

EOF

    echo -e "${CHECK} ${GREEN}.gitignore에 보안 패턴이 추가되었습니다.${NC}"
}

# 설정 검증
verify_setup() {
    echo ""
    echo -e "${BLUE}${ROCKET} 설정 검증 중...${NC}"

    local services=("figma" "slack" "github")
    local success_count=0

    for service in "${services[@]}"; do
        local token=$(security find-generic-password -a "xlt_$service" -s "XLT_${service^^}_TOKEN" -w 2>/dev/null || echo "")
        local env_token=""

        case "$service" in
            "figma") env_token="$FIGMA_TOKEN" ;;
            "slack") env_token="$SLACK_TOKEN" ;;
            "github") env_token="$GITHUB_TOKEN" ;;
        esac

        if [[ -n "$token" ]]; then
            echo -e "${CHECK} ${GREEN}${service^}: Keychain 저장 ✓${NC}"

            if [[ -n "$env_token" ]]; then
                echo -e "    ${GREEN}환경변수 로드 ✓${NC}"
            else
                echo -e "    ${YELLOW}환경변수 미로드 (터미널 재시작 필요)${NC}"
            fi

            ((success_count++))
        else
            echo -e "${WARNING} ${YELLOW}${service^}: 설정되지 않음${NC}"
        fi
    done

    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${GREEN}설정 완료: $success_count/3 서비스${NC}"

    if [[ $success_count -eq 3 ]]; then
        echo -e "${CHECK} ${GREEN}모든 토큰이 성공적으로 설정되었습니다!${NC}"
    elif [[ $success_count -gt 0 ]]; then
        echo -e "${WARNING} ${YELLOW}일부 토큰이 설정되었습니다. 필요에 따라 나머지를 추가하세요.${NC}"
    else
        echo -e "${CROSS} ${RED}토큰이 설정되지 않았습니다. 수동으로 추가해주세요.${NC}"
    fi
}

# Python 테스트 실행
test_python_integration() {
    echo ""
    echo -e "${BLUE}${ROCKET} Python 통합 테스트...${NC}"

    # Python에서 토큰 조회 테스트
    cat > /tmp/test_xlt_tokens.py << 'EOF'
import sys
import os

# XLT 경로 추가
sys.path.insert(0, os.getcwd())

try:
    from xlt.core.config import XLTConfig

    config = XLTConfig()

    services = ['figma', 'slack', 'github']
    success = 0

    print("🧪 Python 토큰 조회 테스트")
    print("=" * 40)

    for service in services:
        token = config.get_token(service)
        if token:
            print(f"✅ {service.title()}: 토큰 로드 성공")
            success += 1
        else:
            print(f"⚠️  {service.title()}: 토큰 없음")

    print(f"\\n결과: {success}/{len(services)} 서비스 성공")

    if success > 0:
        print("\\n🎉 XLT System이 토큰을 성공적으로 인식합니다!")

except ImportError as e:
    print(f"❌ XLT 모듈 import 실패: {e}")
except Exception as e:
    print(f"❌ 테스트 실패: {e}")
EOF

    python3 /tmp/test_xlt_tokens.py
    rm -f /tmp/test_xlt_tokens.py
}

# 메인 실행 함수
main() {
    # 요구사항 확인
    check_requirements

    # 기존 토큰 감지
    local found_tokens=($(detect_existing_tokens))

    # 토큰 마이그레이션
    if [[ ${#found_tokens[@]} -gt 0 ]]; then
        migrate_tokens "${found_tokens[@]}"
    fi

    # 수동 토큰 입력
    manual_token_input

    # 환경 변수 설정
    setup_environment

    # 토큰 파일 정리
    cleanup_token_files

    # .gitignore 업데이트
    update_gitignore

    # 설정 검증
    verify_setup

    # Python 통합 테스트
    test_python_integration

    # 완료 메시지
    echo ""
    echo -e "${GREEN}${MAGIC}================================${NC}"
    echo -e "${GREEN}${CHECK} XLT 전역 토큰 설정 완료!${NC}"
    echo -e "${GREEN}${MAGIC}================================${NC}"
    echo ""
    echo -e "${CYAN}다음 단계:${NC}"
    echo -e "${YELLOW}1. 터미널을 재시작하거나 다음 명령어를 실행하세요:${NC}"
    echo -e "   source ~/.zshrc"
    echo ""
    echo -e "${YELLOW}2. 다른 프로젝트에서 토큰 사용:${NC}"
    echo -e "   export된 환경변수를 통해 자동으로 사용됩니다."
    echo ""
    echo -e "${YELLOW}3. Git SSH 설정 (보안 강화):${NC}"
    echo -e "   bash install/setup_git_ssh.sh"
    echo ""
    echo -e "${GREEN}${ROCKET} 이제 모든 XLT 프로젝트에서 동일한 토큰을 사용할 수 있습니다!${NC}"
}

# 스크립트 실행
main "$@"