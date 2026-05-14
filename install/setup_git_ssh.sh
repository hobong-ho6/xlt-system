#!/bin/bash

# XLT System Git SSH 설정 스크립트
# HTTPS + 토큰 → SSH 키 기반 인증으로 안전하게 전환
#
# 주요 기능:
# - 현재 Git 설정 분석
# - SSH 키 생성 및 macOS Keychain 등록
# - GitHub SSH 키 등록 안내
# - Git 원격 URL 자동 변경
# - 연결 테스트 및 검증

set -e

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
GEAR="⚙️"

echo -e "${CYAN}${SHIELD} XLT System Git SSH 설정${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}GitHub PAT를 제거하고 SSH 키 기반 안전 인증으로 전환합니다.${NC}"
echo ""

# macOS 환경 확인
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${CROSS} ${RED}이 스크립트는 macOS에서만 실행 가능합니다.${NC}"
    exit 1
fi

# Git 리포지토리 확인
if [[ ! -d ".git" ]]; then
    echo -e "${CROSS} ${RED}Git 리포지토리가 아닙니다. 프로젝트 루트에서 실행해주세요.${NC}"
    exit 1
fi

# 현재 Git 설정 분석
analyze_current_git() {
    echo -e "${BLUE}${GEAR} 현재 Git 설정 분석 중...${NC}"

    # 원격 저장소 URL 확인
    local remote_url=$(git config --get remote.origin.url 2>/dev/null || echo "")

    if [[ -z "$remote_url" ]]; then
        echo -e "${CROSS} ${RED}원격 저장소 URL을 찾을 수 없습니다.${NC}"
        exit 1
    fi

    echo -e "${BLUE}현재 원격 URL: ${YELLOW}$remote_url${NC}"

    # HTTPS + 토큰 확인
    if [[ "$remote_url" == *"github.com"* && "$remote_url" == *"ghp_"* ]]; then
        echo -e "${WARNING} ${YELLOW}GitHub PAT가 URL에 포함되어 있습니다! (보안 위험)${NC}"

        # 토큰 추출
        local github_pat=$(echo "$remote_url" | sed -n 's/.*:\\/\\/.*:\\(ghp_[^@]*\\)@.*/\\1/p')
        if [[ -n "$github_pat" ]]; then
            echo -e "${WARNING} ${YELLOW}발견된 토큰: ${github_pat:0:10}...${NC}"
            return 0  # SSH 전환 필요
        fi
    fi

    # 이미 SSH인지 확인
    if [[ "$remote_url" == git@* ]]; then
        echo -e "${CHECK} ${GREEN}이미 SSH 기반 인증을 사용 중입니다.${NC}"

        # SSH 연결 테스트
        if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
            echo -e "${CHECK} ${GREEN}SSH 인증이 정상적으로 작동합니다.${NC}"
            echo ""
            echo -e "${GREEN}추가 설정이 필요하지 않습니다! 🎉${NC}"
            exit 0
        else
            echo -e "${WARNING} ${YELLOW}SSH 키 설정이 필요합니다.${NC}"
            return 0  # SSH 키 설정 진행
        fi
    fi

    # HTTPS이지만 토큰 없음
    if [[ "$remote_url" == *"https://github.com"* ]]; then
        echo -e "${WARNING} ${YELLOW}HTTPS 인증을 사용 중입니다. SSH로 전환을 권장합니다.${NC}"
        return 0  # SSH 전환 진행
    fi

    echo -e "${CHECK} ${GREEN}현재 설정을 분석했습니다.${NC}"
    return 0
}

# GitHub 정보 추출
extract_github_info() {
    local remote_url=$(git config --get remote.origin.url)

    # SSH URL에서 정보 추출
    if [[ "$remote_url" == git@* ]]; then
        echo "$remote_url" | sed -n 's/git@github.com:\\(.*\\)\\.git/\\1/p'
        return 0
    fi

    # HTTPS URL에서 정보 추출
    if [[ "$remote_url" == *"github.com"* ]]; then
        echo "$remote_url" | sed -n 's/.*github\\.com[:\\/]\\([^\\/]*\\/[^\\/]*\\).*/\\1/p' | sed 's/\\.git$//'
        return 0
    fi

    return 1
}

# SSH 키 생성
generate_ssh_key() {
    echo ""
    echo -e "${BLUE}${KEY} SSH 키 생성 중...${NC}"

    local ssh_dir="$HOME/.ssh"
    local key_name="id_ed25519_xlt"
    local key_path="$ssh_dir/$key_name"

    # .ssh 디렉토리 생성
    mkdir -p "$ssh_dir"
    chmod 700 "$ssh_dir"

    # 기존 키 확인
    if [[ -f "$key_path" ]]; then
        echo -e "${WARNING} ${YELLOW}기존 SSH 키가 발견되었습니다: $key_path${NC}"

        read -p "기존 키를 사용하시겠습니까? (Y/n): " -n 1 -r
        echo ""

        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${CHECK} ${GREEN}기존 SSH 키를 사용합니다.${NC}"
            return 0
        fi

        # 백업 생성
        local backup_key="${key_path}.backup_$(date +%s)"
        cp "$key_path" "$backup_key"
        cp "${key_path}.pub" "${backup_key}.pub"
        echo -e "${CHECK} ${GREEN}기존 키를 $backup_key 로 백업했습니다.${NC}"
    fi

    # 사용자 이메일 확인
    local git_email=$(git config user.email || echo "")
    if [[ -z "$git_email" ]]; then
        echo -e "${WARNING} ${YELLOW}Git 이메일이 설정되지 않았습니다.${NC}"
        read -p "SSH 키에 사용할 이메일을 입력하세요: " git_email

        # Git 전역 설정에 이메일 저장
        git config --global user.email "$git_email"
        echo -e "${CHECK} ${GREEN}Git 이메일이 설정되었습니다: $git_email${NC}"
    fi

    echo -e "${BLUE}SSH 키 생성 중... (ed25519 방식)${NC}"

    # SSH 키 생성 (패스워드 없음)
    ssh-keygen -t ed25519 -C "$git_email" -f "$key_path" -N ""

    if [[ $? -eq 0 ]]; then
        echo -e "${CHECK} ${GREEN}SSH 키가 성공적으로 생성되었습니다.${NC}"
        echo -e "${BLUE}공개 키 위치: ${key_path}.pub${NC}"
        echo -e "${BLUE}개인 키 위치: ${key_path}${NC}"
    else
        echo -e "${CROSS} ${RED}SSH 키 생성에 실패했습니다.${NC}"
        exit 1
    fi

    # 키 권한 설정
    chmod 600 "$key_path"
    chmod 644 "${key_path}.pub"

    echo -e "${CHECK} ${GREEN}SSH 키 권한이 설정되었습니다.${NC}"
}

# SSH 키를 macOS Keychain에 등록
register_ssh_key() {
    echo ""
    echo -e "${BLUE}${SHIELD} SSH 키를 macOS Keychain에 등록 중...${NC}"

    local key_path="$HOME/.ssh/id_ed25519_xlt"

    # SSH agent에 키 추가
    ssh-add --apple-use-keychain "$key_path"

    if [[ $? -eq 0 ]]; then
        echo -e "${CHECK} ${GREEN}SSH 키가 Keychain에 등록되었습니다.${NC}"
    else
        echo -e "${WARNING} ${YELLOW}SSH 키 Keychain 등록에 실패했습니다.${NC}"
        echo -e "${YELLOW}수동으로 등록하려면: ssh-add --apple-use-keychain $key_path${NC}"
    fi

    # SSH config 설정
    local ssh_config="$HOME/.ssh/config"

    # 기존 XLT 설정 제거
    if [[ -f "$ssh_config" ]]; then
        # 백업 생성
        local backup_config="${ssh_config}.backup_$(date +%s)"
        cp "$ssh_config" "$backup_config"
        echo -e "${CHECK} ${GREEN}SSH config를 $backup_config 로 백업했습니다.${NC}"

        # XLT 관련 기존 설정 제거
        sed -i '' '/Host.*github.com.*xlt/,+5d' "$ssh_config" 2>/dev/null || true
    else
        touch "$ssh_config"
        chmod 600 "$ssh_config"
    fi

    # 새 SSH config 추가
    cat >> "$ssh_config" << EOF

# XLT System GitHub SSH 설정
Host github.com-xlt
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_xlt
    AddKeysToAgent yes
    UseKeychain yes

# GitHub 기본 설정 (XLT 키 사용)
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_xlt
    AddKeysToAgent yes
    UseKeychain yes

EOF

    echo -e "${CHECK} ${GREEN}SSH config가 업데이트되었습니다.${NC}"
}

# GitHub에 SSH 공개 키 등록 안내
guide_github_setup() {
    echo ""
    echo -e "${BLUE}${KEY} GitHub SSH 키 등록 안내${NC}"
    echo -e "${YELLOW}========================================${NC}"

    local public_key=$(cat "$HOME/.ssh/id_ed25519_xlt.pub")

    echo -e "${CYAN}다음 단계를 따라 GitHub에 SSH 키를 등록하세요:${NC}"
    echo ""
    echo -e "${YELLOW}1. GitHub 웹사이트에 로그인${NC}"
    echo -e "   https://github.com"
    echo ""
    echo -e "${YELLOW}2. Settings → SSH and GPG keys 페이지로 이동${NC}"
    echo -e "   https://github.com/settings/keys"
    echo ""
    echo -e "${YELLOW}3. 'New SSH key' 버튼 클릭${NC}"
    echo ""
    echo -e "${YELLOW}4. 다음 정보 입력:${NC}"
    echo -e "   • Title: XLT System (macOS)"
    echo -e "   • Key: 아래 공개 키 복사"
    echo ""
    echo -e "${CYAN}--- 공개 키 (복사하세요) ---${NC}"
    echo -e "${GREEN}$public_key${NC}"
    echo -e "${CYAN}--- 여기까지 복사 ---${NC}"
    echo ""
    echo -e "${YELLOW}5. 'Add SSH key' 버튼 클릭${NC}"
    echo ""

    # 클립보드에 복사 (macOS)
    echo "$public_key" | pbcopy
    echo -e "${CHECK} ${GREEN}공개 키가 클립보드에 복사되었습니다!${NC}"
    echo ""

    read -p "GitHub에 SSH 키를 등록했으면 Enter를 누르세요..." -r
}

# Git 원격 URL 변경
update_git_remote() {
    echo ""
    echo -e "${BLUE}${GEAR} Git 원격 URL 업데이트 중...${NC}"

    local repo_info=$(extract_github_info)
    if [[ -z "$repo_info" ]]; then
        echo -e "${CROSS} ${RED}GitHub 리포지토리 정보를 추출할 수 없습니다.${NC}"
        exit 1
    fi

    local new_ssh_url="git@github.com:${repo_info}.git"
    echo -e "${BLUE}새 SSH URL: ${GREEN}$new_ssh_url${NC}"

    # 기존 URL 백업
    local current_url=$(git config --get remote.origin.url)
    echo -e "${BLUE}기존 URL: ${YELLOW}$current_url${NC}"

    # URL 변경
    git remote set-url origin "$new_ssh_url"

    if [[ $? -eq 0 ]]; then
        echo -e "${CHECK} ${GREEN}Git 원격 URL이 SSH로 변경되었습니다.${NC}"
    else
        echo -e "${CROSS} ${RED}Git 원격 URL 변경에 실패했습니다.${NC}"
        exit 1
    fi
}

# SSH 연결 테스트
test_ssh_connection() {
    echo ""
    echo -e "${BLUE}${ROCKET} SSH 연결 테스트 중...${NC}"

    # GitHub SSH 연결 테스트
    local test_result=$(ssh -T git@github.com 2>&1)

    if echo "$test_result" | grep -q "successfully authenticated"; then
        local username=$(echo "$test_result" | sed -n 's/.*Hi \\([^!]*\\)!.*/\\1/p')
        echo -e "${CHECK} ${GREEN}SSH 인증 성공! GitHub 사용자: $username${NC}"
        return 0
    else
        echo -e "${CROSS} ${RED}SSH 인증 실패${NC}"
        echo -e "${YELLOW}오류 내용:${NC}"
        echo "$test_result"
        echo ""
        echo -e "${YELLOW}해결 방법:${NC}"
        echo -e "1. GitHub에 SSH 키가 올바르게 등록되었는지 확인"
        echo -e "2. SSH 키 파일 권한 확인: chmod 600 ~/.ssh/id_ed25519_xlt"
        echo -e "3. SSH agent 재시작: ssh-add -D && ssh-add --apple-use-keychain ~/.ssh/id_ed25519_xlt"
        return 1
    fi
}

# Git 작업 테스트
test_git_operations() {
    echo ""
    echo -e "${BLUE}${ROCKET} Git 작업 테스트 중...${NC}"

    # fetch 테스트
    echo -e "${BLUE}원격 저장소에서 fetch 중...${NC}"

    if git fetch origin 2>/dev/null; then
        echo -e "${CHECK} ${GREEN}git fetch 성공${NC}"
    else
        echo -e "${CROSS} ${RED}git fetch 실패${NC}"
        return 1
    fi

    # 현재 브랜치 확인
    local current_branch=$(git branch --show-current)
    echo -e "${BLUE}현재 브랜치: $current_branch${NC}"

    # pull 테스트 (변경사항이 있는 경우만)
    local remote_hash=$(git rev-parse origin/$current_branch 2>/dev/null || echo "")
    local local_hash=$(git rev-parse HEAD)

    if [[ -n "$remote_hash" && "$remote_hash" != "$local_hash" ]]; then
        echo -e "${BLUE}원격 변경사항 동기화 중...${NC}"
        if git pull origin "$current_branch" 2>/dev/null; then
            echo -e "${CHECK} ${GREEN}git pull 성공${NC}"
        else
            echo -e "${WARNING} ${YELLOW}git pull 실패 (conflict 가능성)${NC}"
        fi
    else
        echo -e "${CHECK} ${GREEN}로컬과 원격이 동기화되어 있습니다.${NC}"
    fi

    return 0
}

# 기존 토큰 정리
cleanup_git_tokens() {
    echo ""
    echo -e "${BLUE}${SHIELD} Git 설정 정리 중...${NC}"

    # .git/config에서 토큰 흔적 제거 확인
    if grep -q "ghp_" .git/config 2>/dev/null; then
        echo -e "${WARNING} ${YELLOW}Git config에서 토큰 흔적이 제거되었는지 확인 중...${NC}"

        local current_url=$(git config --get remote.origin.url)
        if [[ "$current_url" == git@* ]]; then
            echo -e "${CHECK} ${GREEN}토큰이 성공적으로 제거되었습니다.${NC}"
        else
            echo -e "${WARNING} ${YELLOW}토큰이 아직 남아있을 수 있습니다.${NC}"
        fi
    fi

    # Git credential helper 확인
    local cred_helper=$(git config --global credential.helper 2>/dev/null || echo "")
    if [[ "$cred_helper" == "osxkeychain" ]]; then
        echo -e "${CHECK} ${GREEN}Git credential helper가 osxkeychain으로 설정되어 있습니다.${NC}"

        # GitHub 자격증명 제거 (HTTPS 토큰)
        security delete-generic-password -s "github.com" 2>/dev/null || true
        echo -e "${CHECK} ${GREEN}기존 GitHub HTTPS 자격증명을 정리했습니다.${NC}"
    fi
}

# 설정 완료 안내
show_completion_guide() {
    echo ""
    echo -e "${GREEN}${CHECK}================================${NC}"
    echo -e "${GREEN}${CHECK} SSH 설정 완료! 🎉${NC}"
    echo -e "${GREEN}${CHECK}================================${NC}"
    echo ""

    echo -e "${CYAN}설정 요약:${NC}"
    echo -e "• SSH 키: ~/.ssh/id_ed25519_xlt"
    echo -e "• macOS Keychain: 자동 관리"
    echo -e "• Git 원격: SSH 기반 인증"
    echo -e "• 보안: GitHub PAT 제거됨"
    echo ""

    echo -e "${CYAN}이제 다음 Git 작업들이 SSH로 안전하게 수행됩니다:${NC}"
    echo -e "• git clone"
    echo -e "• git fetch / git pull"
    echo -e "• git push"
    echo ""

    echo -e "${YELLOW}참고사항:${NC}"
    echo -e "• SSH 키는 만료되지 않습니다"
    echo -e "• macOS 로그인 시 자동으로 로드됩니다"
    echo -e "• 다른 프로젝트에서도 동일한 키를 사용할 수 있습니다"
    echo ""

    echo -e "${GREEN}${ROCKET} 안전한 Git 인증이 완료되었습니다!${NC}"
}

# 메인 실행 함수
main() {
    # 현재 Git 설정 분석
    analyze_current_git

    # SSH 키 생성
    generate_ssh_key

    # SSH 키를 Keychain에 등록
    register_ssh_key

    # GitHub SSH 키 등록 안내
    guide_github_setup

    # SSH 연결 테스트
    if ! test_ssh_connection; then
        echo -e "${CROSS} ${RED}SSH 설정을 완료한 후 다시 실행해주세요.${NC}"
        exit 1
    fi

    # Git 원격 URL 변경
    update_git_remote

    # Git 작업 테스트
    test_git_operations

    # 기존 토큰 정리
    cleanup_git_tokens

    # 완료 안내
    show_completion_guide
}

# 스크립트 실행
main "$@"