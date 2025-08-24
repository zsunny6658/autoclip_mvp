#!/bin/bash

# 权限修复脚本
# 修复AutoClip Docker部署中的文件权限问题

set -e

echo "🔧 AutoClip 权限修复脚本"
echo "=========================="

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

# 获取当前用户信息
CURRENT_USER=$(whoami)
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

log_info "当前用户: $CURRENT_USER (UID: $CURRENT_UID, GID: $CURRENT_GID)"

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    local dirs=(
        "data"
        "uploads"
        "output"
        "output/clips"
        "output/collections"
        "output/metadata"
        "input"
        "logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "✓ 创建目录: $dir"
        else
            log_info "✓ 目录已存在: $dir"
        fi
    done
}

# 设置目录权限
set_permissions() {
    log_info "设置目录权限..."
    
    # 设置目录为755（rwxr-xr-x）
    local dirs=(
        "data"
        "uploads"
        "output"
        "input"
        "logs"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            chmod 755 "$dir"
            log_success "✓ 设置目录权限: $dir (755)"
        fi
    done
    
    # 递归设置子目录权限
    find output -type d -exec chmod 755 {} \; 2>/dev/null || true
    find uploads -type d -exec chmod 755 {} \; 2>/dev/null || true
    
    log_success "目录权限设置完成"
}

# 创建示例配置文件
create_config_files() {
    log_info "创建配置文件..."
    
    # 创建 settings.json
    if [ ! -f "data/settings.json" ]; then
        if [ -f "data/settings.example.json" ]; then
            cp "data/settings.example.json" "data/settings.json"
            log_success "✓ 从示例创建 settings.json"
        else
            cat > "data/settings.json" << 'EOF'
{
  "dashscope_api_key": "",
  "siliconflow_api_key": "",
  "api_provider": "dashscope",
  "model_name": "qwen-plus",
  "siliconflow_model": "Qwen/Qwen2.5-72B-Instruct",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
EOF
            log_success "✓ 创建默认 settings.json"
        fi
    else
        log_info "✓ settings.json 已存在"
    fi
    
    # 创建 projects.json
    if [ ! -f "data/projects.json" ]; then
        echo "[]" > "data/projects.json"
        log_success "✓ 创建空 projects.json"
    else
        log_info "✓ projects.json 已存在"
    fi
    
    # 设置文件权限为644（rw-r--r--）
    chmod 644 data/settings.json data/projects.json 2>/dev/null || true
    log_success "配置文件权限设置完成"
}

# 验证权限
verify_permissions() {
    log_info "验证权限设置..."
    
    local error_count=0
    
    # 检查目录权限
    local dirs=("data" "uploads" "output" "input" "logs")
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            if [ -r "$dir" ] && [ -w "$dir" ] && [ -x "$dir" ]; then
                log_success "✓ $dir 权限正常"
            else
                log_error "✗ $dir 权限不足"
                ((error_count++))
            fi
        fi
    done
    
    # 检查配置文件权限
    local files=("data/settings.json" "data/projects.json")
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            if [ -r "$file" ] && [ -w "$file" ]; then
                log_success "✓ $file 权限正常"
            else
                log_error "✗ $file 权限不足"
                ((error_count++))
            fi
        fi
    done
    
    if [ $error_count -eq 0 ]; then
        log_success "所有权限验证通过！"
        return 0
    else
        log_error "发现 $error_count 个权限问题"
        return 1
    fi
}

# 显示系统信息
show_system_info() {
    log_info "系统信息："
    echo "操作系统: $(uname -s)"
    echo "内核版本: $(uname -r)"
    echo "当前用户: $CURRENT_USER"
    echo "UID/GID: $CURRENT_UID/$CURRENT_GID"
    echo "工作目录: $(pwd)"
    echo ""
}

# 主流程
main() {
    echo
    log_info "开始权限修复流程..."
    echo
    
    show_system_info
    
    create_directories
    echo
    
    set_permissions
    echo
    
    create_config_files
    echo
    
    if verify_permissions; then
        echo
        log_success "🎉 权限修复完成！"
        echo
        log_info "接下来可以重新构建Docker容器："
        echo "  docker-compose down"
        echo "  docker-compose build --no-cache"
        echo "  docker-compose up -d"
        echo
    else
        echo
        log_error "❌ 权限修复失败，请检查系统权限"
        exit 1
    fi
}

# 执行主流程
main "$@"