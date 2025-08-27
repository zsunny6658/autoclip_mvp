#!/bin/bash

# AutoClip 权限工具函数库
# 提供所有脚本共享的权限修复功能

# ==================== 颜色定义 ====================
if [[ -z "${RED:-}" ]]; then RED='\033[0;31m'; fi
if [[ -z "${GREEN:-}" ]]; then GREEN='\033[0;32m'; fi
if [[ -z "${YELLOW:-}" ]]; then YELLOW='\033[1;33m'; fi
if [[ -z "${BLUE:-}" ]]; then BLUE='\033[0;34m'; fi
if [[ -z "${NC:-}" ]]; then NC='\033[0m'; fi

# ==================== 日志函数 ====================
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

# ==================== 权限修复函数 ====================

# 修复开发环境权限
fix_dev_permissions() {
    log_info "修复开发环境权限..."
    
    # 获取当前用户信息
    local current_user=$(whoami)
    local current_uid=$(id -u)
    local current_gid=$(id -g)
    
    log_info "当前用户: $current_user (UID: $current_uid, GID: $current_gid)"
    
    # 创建必要目录
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
            if mkdir -p "$dir" 2>/dev/null; then
                log_success "✓ 创建目录: $dir"
            else
                log_warning "无法创建目录: $dir"
            fi
        else
            log_info "✓ 目录已存在: $dir"
        fi
    done
    
    # 设置目录权限
    log_info "设置目录权限..."
    
    # 设置目录为755（rwxr-xr-x）
    local perm_dirs=(
        "data"
        "uploads"
        "output"
        "input"
        "logs"
    )
    
    for dir in "${perm_dirs[@]}"; do
        if [ -d "$dir" ]; then
            if chmod 755 "$dir" 2>/dev/null; then
                log_success "✓ 设置目录权限: $dir (755)"
            else
                log_warning "无法设置权限: $dir"
            fi
        fi
    done
    
    # 递归设置子目录权限
    find output -type d -exec chmod 755 {} \; 2>/dev/null || true
    find uploads -type d -exec chmod 755 {} \; 2>/dev/null || true
    
    # 创建示例配置文件
    log_info "创建配置文件..."
    
    # 创建 settings.json
    if [ ! -f "data/settings.json" ]; then
        if [ -f "data/settings.example.json" ]; then
            if cp "data/settings.example.json" "data/settings.json" 2>/dev/null; then
                log_success "✓ 从示例创建 settings.json"
            else
                log_warning "无法创建 settings.json"
            fi
        else
            # 创建默认配置
            if cat > "data/settings.json" << 'EOF' 2>/dev/null; then
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
            else
                log_warning "无法创建 settings.json"
            fi
        fi
    else
        log_info "✓ settings.json 已存在"
    fi
    
    # 创建 projects.json
    if [ ! -f "data/projects.json" ]; then
        if echo "[]" > "data/projects.json" 2>/dev/null; then
            log_success "✓ 创建空 projects.json"
        else
            log_warning "无法创建 projects.json"
        fi
    else
        log_info "✓ projects.json 已存在"
    fi
    
    # 设置文件权限为644（rw-r--r--）
    if chmod 644 data/settings.json data/projects.json 2>/dev/null; then
        log_success "配置文件权限设置完成"
    else
        log_warning "无法设置配置文件权限"
    fi
    
    # 设置容器用户权限（与Docker容器中的appuser一致）
    log_info "设置容器用户权限..."
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            # 设置为10001:10001（与Docker容器中的appuser一致）
            if chown -R 10001:10001 "$dir" 2>/dev/null; then
                if chmod -R 755 "$dir" 2>/dev/null; then
                    log_success "✓ $dir 权限已设置为容器用户 (10001:10001)"
                fi
            else
                log_warning "无法设置容器用户权限: $dir"
            fi
        fi
    done
    
    log_success "开发环境权限修复完成"
}

# 修复生产环境权限
fix_prod_permissions() {
    log_info "修复生产环境权限..."
    
    # 获取当前用户信息
    local current_user=$(whoami)
    local current_uid=$(id -u)
    local current_gid=$(id -g)
    
    log_info "当前用户: $current_user (UID: $current_uid, GID: $current_gid)"
    
    # 生产环境使用绝对路径
    local prod_dirs=(
        "${UPLOADS_DIR:-/var/lib/autoclip/uploads}"
        "${OUTPUT_DIR:-/var/lib/autoclip/output}"
        "${OUTPUT_DIR:-/var/lib/autoclip/output}/clips"
        "${OUTPUT_DIR:-/var/lib/autoclip/output}/collections"
        "${OUTPUT_DIR:-/var/lib/autoclip/output}/metadata"
        "${DATA_DIR:-/var/lib/autoclip/data}"
        "${INPUT_DIR:-/var/lib/autoclip/input}"
        "${LOG_DIR:-/var/log/autoclip}"
    )
    
    # 创建必要目录
    for dir in "${prod_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            # 尝试创建目录（可能需要sudo）
            if mkdir -p "$dir" 2>/dev/null; then
                log_success "✓ 创建目录: $dir"
            else
                log_warning "无法创建目录: $dir，可能需要管理员权限"
            fi
        else
            log_info "✓ 目录已存在: $dir"
        fi
    done
    
    # 设置目录权限
    log_info "设置生产环境目录权限..."
    
    for dir in "${prod_dirs[@]}"; do
        if [ -d "$dir" ]; then
            # 设置目录为755（rwxr-xr-x）
            if chmod 755 "$dir" 2>/dev/null; then
                log_success "✓ 设置目录权限: $dir (755)"
            else
                log_warning "无法设置权限: $dir，可能需要管理员权限"
            fi
            
            # 设置所有者为当前用户（如果可能）
            if chown "$current_user:$current_user" "$dir" 2>/dev/null; then
                log_success "✓ 设置目录所有者: $dir ($current_user:$current_user)"
            else
                log_warning "无法设置所有者: $dir，可能需要管理员权限"
            fi
        fi
    done
    
    # 创建示例配置文件
    log_info "创建生产环境配置文件..."
    
    local data_dir="${DATA_DIR:-/var/lib/autoclip/data}"
    mkdir -p "$data_dir" 2>/dev/null || true
    
    # 创建 settings.json
    local settings_file="$data_dir/settings.json"
    if [ ! -f "$settings_file" ]; then
        if [ -f "data/settings.example.json" ]; then
            if cp "data/settings.example.json" "$settings_file" 2>/dev/null; then
                chmod 644 "$settings_file"
                log_success "✓ 从示例创建 settings.json"
            else
                log_warning "无法创建 settings.json，可能需要管理员权限"
            fi
        else
            # 创建默认配置
            if cat > "$settings_file" << 'EOF' 2>/dev/null; then
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
                chmod 644 "$settings_file"
                log_success "✓ 创建默认 settings.json"
            else
                log_warning "无法创建 settings.json，可能需要管理员权限"
            fi
        fi
    else
        log_info "✓ settings.json 已存在"
    fi
    
    # 创建 projects.json
    local projects_file="$data_dir/projects.json"
    if [ ! -f "$projects_file" ]; then
        if echo "[]" > "$projects_file" 2>/dev/null; then
            chmod 644 "$projects_file"
            log_success "✓ 创建空 projects.json"
        else
            log_warning "无法创建 projects.json，可能需要管理员权限"
        fi
    else
        log_info "✓ projects.json 已存在"
    fi
    
    # 设置容器用户权限（与Docker容器中的appuser一致）
    log_info "设置容器用户权限..."
    for dir in "${prod_dirs[@]}"; do
        if [ -d "$dir" ]; then
            # 设置为10001:10001（与Docker容器中的appuser一致）
            if chown -R 10001:10001 "$dir" 2>/dev/null; then
                if chmod -R 755 "$dir" 2>/dev/null; then
                    log_success "✓ $dir 权限已设置为容器用户 (10001:10001)"
                fi
            else
                log_warning "无法设置容器用户权限: $dir，可能需要管理员权限"
            fi
        fi
    done
    
    log_success "生产环境权限修复完成"
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