#!/bin/bash
# 修复Docker部署权限问题脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以root身份运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要以root身份运行以修复权限问题"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 创建必要目录
create_directories() {
    log_info "创建必要的目录..."
    
    local dirs=("data" "input" "output" "uploads" "logs")
    local created=0
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
            ((created++))
        fi
    done
    
    if [[ $created -gt 0 ]]; then
        log_success "创建了 $created 个目录"
    else
        log_info "所有必要目录都已存在"
    fi
}

# 设置正确的权限
fix_permissions() {
    log_info "修复目录权限..."
    
    # 获取当前用户的UID（运行docker-compose的用户）
    local current_user=$(logname 2>/dev/null || echo $SUDO_USER)
    local current_uid=$(id -u "$current_user" 2>/dev/null || echo "1000")
    local current_gid=$(id -g "$current_user" 2>/dev/null || echo "1000")
    
    log_info "当前用户: $current_user (UID: $current_uid, GID: $current_gid)"
    
    # 需要修复权限的目录
    local dirs=("data" "input" "output" "uploads" "logs")
    
    for dir in "${dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            log_info "修复 $dir 目录权限..."
            # 设置为10001:10001（与Docker容器中的appuser一致）
            chown -R 10001:10001 "$dir"
            chmod -R 755 "$dir"
            log_success "✓ $dir 权限已修复"
        else
            log_warning "目录 $dir 不存在，跳过"
        fi
    done
}

# 创建或修复配置文件
fix_config_files() {
    log_info "检查配置文件..."
    
    # 检查data/settings.json
    if [[ ! -f "data/settings.json" ]] && [[ -f "data/settings.example.json" ]]; then
        cp "data/settings.example.json" "data/settings.json"
        log_success "创建了默认配置文件: data/settings.json"
    fi
    
    # 检查bilibili_cookies.txt
    if [[ ! -f "data/bilibili_cookies.txt" ]]; then
        touch "data/bilibili_cookies.txt"
        log_success "创建了空的bilibili cookies文件"
    fi
    
    # 设置配置文件权限
    if [[ -f "data/settings.json" ]]; then
        chown 10001:10001 "data/settings.json"
        chmod 644 "data/settings.json"
        log_success "✓ data/settings.json 权限已修复"
    fi
    
    if [[ -f "data/bilibili_cookies.txt" ]]; then
        chown 10001:10001 "data/bilibili_cookies.txt"
        chmod 644 "data/bilibili_cookies.txt"
        log_success "✓ data/bilibili_cookies.txt 权限已修复"
    fi
}

# 显示权限状态
show_permissions() {
    log_info "当前权限状态:"
    echo "----------------------------------------"
    ls -la | grep -E "(data|input|output|uploads|logs)" || true
    echo "----------------------------------------"
}

# 重建Docker容器
rebuild_container() {
    log_info "重建Docker容器以应用权限修复..."
    
    # 停止现有容器
    if docker-compose ps -q autoclip >/dev/null 2>&1; then
        log_info "停止现有容器..."
        docker-compose down
    fi
    
    # 重建并启动
    log_info "重建并启动容器..."
    docker-compose up --build -d
    
    log_success "Docker容器已重建并启动"
}

# 主函数
main() {
    log_info "开始修复Docker权限问题..."
    echo "========================================"
    
    # 检查root权限
    check_root
    
    # 显示当前状态
    log_info "修复前的权限状态:"
    show_permissions
    
    # 创建目录
    create_directories
    
    # 修复权限
    fix_permissions
    
    # 修复配置文件
    fix_config_files
    
    # 显示修复后状态
    log_info "修复后的权限状态:"
    show_permissions
    
    # 询问是否重建容器
    echo
    read -p "是否要重建Docker容器以应用修复？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rebuild_container
    else
        log_info "权限已修复，请手动重建容器以应用更改:"
        echo "  docker-compose down"
        echo "  docker-compose up --build -d"
    fi
    
    echo "========================================"
    log_success "权限修复完成！"
}

# 运行主函数
main "$@"