#!/bin/bash

# AutoClip Docker 工具函数库
# 提供所有Docker脚本共享的功能函数
# 
# 使用方法:
# source "$(dirname "$0")/docker-utils.sh"

# ==================== 全局变量 ====================

# 脚本根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# 确保脚本在项目根目录执行
cd "$PROJECT_ROOT" || {
    echo "❌ 无法切换到项目根目录: $PROJECT_ROOT"
    exit 1
}

# ==================== 颜色定义 ====================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ==================== 日志函数 ====================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_debug() {
    if [ "${DEBUG:-false}" = "true" ]; then
        echo -e "${PURPLE}🔍 DEBUG: $1${NC}"
    fi
}

log_step() {
    echo -e "${CYAN}🔄 $1${NC}"
}

# 带时间戳的日志
log_timestamp() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO") log_info "[$timestamp] $message" ;;
        "SUCCESS") log_success "[$timestamp] $message" ;;
        "WARNING") log_warning "[$timestamp] $message" ;;
        "ERROR") log_error "[$timestamp] $message" ;;
        "DEBUG") log_debug "[$timestamp] $message" ;;
        *) echo -e "[$timestamp] $message" ;;
    esac
}

# ==================== Docker 检测函数 ====================

# 检测 Docker Compose 版本并返回描述信息
get_docker_compose_info() {
    if command -v docker-compose &> /dev/null; then
        local version=$(docker-compose --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
        echo "docker-compose (v${version:-unknown})"
        return 0
    elif docker compose version &> /dev/null 2>&1; then
        local version=$(docker compose version --short 2>/dev/null || echo "unknown")
        echo "docker compose (v$version)"
        return 0
    else
        return 1
    fi
}

# 获取实际的 Docker Compose 命令
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        return 1
    fi
}

# 检查 Docker 是否安装和运行
check_docker_status() {
    local quiet="${1:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "检查 Docker 状态..."
    fi
    
    # 检查 Docker 命令是否存在
    if ! command -v docker &> /dev/null; then
        if [ "$quiet" = "false" ]; then
            log_error "Docker 未安装"
            log_info "安装指南: https://docs.docker.com/get-docker/"
        fi
        return 1
    fi
    
    # 检查 Docker 服务是否运行
    if ! docker info &> /dev/null 2>&1; then
        if [ "$quiet" = "false" ]; then
            log_error "Docker 服务未运行，请启动 Docker 服务"
        fi
        return 1
    fi
    
    if [ "$quiet" = "false" ]; then
        local docker_version=$(docker --version 2>/dev/null || echo "Unknown version")
        log_success "Docker 已安装并运行: $docker_version"
    fi
    
    return 0
}

# 检查 Docker Compose 是否可用
check_docker_compose_status() {
    local quiet="${1:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "检查 Docker Compose 状态..."
    fi
    
    local compose_info
    compose_info=$(get_docker_compose_info)
    if [ $? -ne 0 ]; then
        if [ "$quiet" = "false" ]; then
            log_error "Docker Compose 未安装或无法访问"
            log_info "安装指南: https://docs.docker.com/compose/install/"
        fi
        return 1
    fi
    
    if [ "$quiet" = "false" ]; then
        log_success "Docker Compose 可用: $compose_info"
    fi
    
    # 设置全局变量
    export DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    return 0
}

# ==================== 环境管理函数 ====================

# 加载环境变量
load_environment() {
    local env_file="${1:-.env}"
    local quiet="${2:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "加载环境配置..."
    fi
    
    if [ -f "$env_file" ]; then
        # 安全地加载环境变量
        set -a
        source "$env_file"
        set +a
        
        if [ "$quiet" = "false" ]; then
            log_success "环境变量已加载: $env_file"
        fi
        return 0
    else
        if [ "$quiet" = "false" ]; then
            log_warning "环境文件不存在: $env_file"
        fi
        return 1
    fi
}

# 检查环境变量文件
check_environment_file() {
    local required="${1:-true}"
    local quiet="${2:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "检查环境配置..."
    fi
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            if [ "$quiet" = "false" ]; then
                log_warning "未找到 .env 文件，但找到 env.example"
                log_info "建议运行: cp env.example .env 并编辑配置"
            fi
            
            if [ "$required" = "true" ]; then
                return 1
            fi
        else
            if [ "$quiet" = "false" ]; then
                log_error ".env 和 env.example 文件都不存在"
                log_info "请创建 .env 文件并配置必要的环境变量"
            fi
            return 1
        fi
    else
        if [ "$quiet" = "false" ]; then
            log_success ".env 文件存在"
        fi
    fi
    
    return 0
}

# 验证API密钥配置
validate_api_keys() {
    local required="${1:-true}"
    local quiet="${2:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "验证 API 密钥..."
    fi
    
    # 先加载环境变量
    if ! load_environment ".env" true; then
        if [ "$required" = "true" ]; then
            if [ "$quiet" = "false" ]; then
                log_error "无法加载环境变量文件"
            fi
            return 1
        fi
    fi
    
    # 检查 API 密钥
    if [ -z "${DASHSCOPE_API_KEY:-}" ] && [ -z "${SILICONFLOW_API_KEY:-}" ]; then
        if [ "$quiet" = "false" ]; then
            if [ "$required" = "true" ]; then
                log_error "API 密钥未配置"
                log_info "需要设置 DASHSCOPE_API_KEY 或 SILICONFLOW_API_KEY"
            else
                log_warning "API 密钥未配置"
            fi
        fi
        
        if [ "$required" = "true" ]; then
            return 1
        fi
    else
        if [ "$quiet" = "false" ]; then
            log_success "API 密钥已配置"
        fi
    fi
    
    return 0
}

# 自动设置环境变量文件
setup_environment_file() {
    local force="${1:-false}"
    
    log_step "设置环境变量文件..."
    
    if [ ! -f ".env" ] || [ "$force" = "true" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            log_success "已创建 .env 文件（从 env.example）"
            log_info "请编辑 .env 文件并配置必要的环境变量"
            return 0
        else
            log_error "env.example 文件不存在，无法自动创建 .env"
            return 1
        fi
    else
        log_info ".env 文件已存在，跳过创建"
        return 0
    fi
}

# ==================== 文件和目录检查函数 ====================

# 检查必需文件
check_required_files() {
    local files_array=("$@")
    local missing_files=()
    local quiet="${QUIET_MODE:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "检查必需文件..."
    fi
    
    for file in "${files_array[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
            if [ "$quiet" = "false" ]; then
                log_error "缺少文件: $file"
            fi
        else
            if [ "$quiet" = "false" ]; then
                log_success "文件存在: $file"
            fi
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        if [ "$quiet" = "false" ]; then
            log_success "所有必需文件存在"
        fi
        return 0
    else
        if [ "$quiet" = "false" ]; then
            log_error "缺少 ${#missing_files[@]} 个必需文件"
        fi
        return 1
    fi
}

# 检查目录结构
check_directory_structure() {
    local dirs_array=("$@")
    local missing_dirs=()
    local quiet="${QUIET_MODE:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "检查目录结构..."
    fi
    
    for dir in "${dirs_array[@]}"; do
        if [ ! -d "$dir" ]; then
            missing_dirs+=("$dir")
            if [ "$quiet" = "false" ]; then
                log_error "缺少目录: $dir"
            fi
        else
            if [ "$quiet" = "false" ]; then
                log_success "目录存在: $dir"
            fi
        fi
    done
    
    if [ ${#missing_dirs[@]} -eq 0 ]; then
        if [ "$quiet" = "false" ]; then
            log_success "所有目录存在"
        fi
        return 0
    else
        if [ "$quiet" = "false" ]; then
            log_error "缺少 ${#missing_dirs[@]} 个目录"
        fi
        return 1
    fi
}

# 创建项目目录
create_project_directories() {
    local custom_dirs=("$@")
    local quiet="${QUIET_MODE:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "创建项目目录..."
    fi
    
    # 默认目录
    local default_dirs=(
        "${UPLOADS_DIR:-./uploads}"
        "${OUTPUT_DIR:-./output}/clips"
        "${OUTPUT_DIR:-./output}/collections"
        "${OUTPUT_DIR:-./output}/metadata"
        "${DATA_DIR:-./data}"
        "${INPUT_DIR:-./input}"
        "./logs"
    )
    
    # 合并自定义目录
    local all_dirs=("${default_dirs[@]}")
    if [ ${#custom_dirs[@]} -gt 0 ]; then
        all_dirs+=("${custom_dirs[@]}")
    fi
    
    # 创建目录
    for dir in "${all_dirs[@]}"; do
        if mkdir -p "$dir" 2>/dev/null; then
            chmod 755 "$dir" 2>/dev/null || true
            if [ "$quiet" = "false" ]; then
                log_success "创建目录: $dir"
            fi
        else
            if [ "$quiet" = "false" ]; then
                log_error "创建目录失败: $dir"
            fi
            return 1
        fi
    done
    
    if [ "$quiet" = "false" ]; then
        log_success "目录创建完成"
    fi
    return 0
}

# ==================== Docker Compose 操作函数 ====================

# 验证 Docker Compose 文件语法
validate_compose_files() {
    local files_array=("$@")
    local quiet="${QUIET_MODE:-false}"
    local compose_cmd="${DOCKER_COMPOSE_CMD}"
    
    if [ -z "$compose_cmd" ]; then
        compose_cmd=$(get_docker_compose_cmd)
        if [ $? -ne 0 ]; then
            if [ "$quiet" = "false" ]; then
                log_error "Docker Compose 不可用"
            fi
            return 1
        fi
    fi
    
    if [ "$quiet" = "false" ]; then
        log_step "验证 Docker Compose 文件语法..."
    fi
    
    for file in "${files_array[@]}"; do
        if [ ! -f "$file" ]; then
            if [ "$quiet" = "false" ]; then
                log_warning "跳过不存在的文件: $file"
            fi
            continue
        fi
        
        if $compose_cmd -f "$file" config >/dev/null 2>&1; then
            if [ "$quiet" = "false" ]; then
                log_success "$file 语法正确"
            fi
        else
            if [ "$quiet" = "false" ]; then
                log_error "$file 语法错误"
                log_info "错误详情:"
                $compose_cmd -f "$file" config 2>&1 | head -10
            fi
            return 1
        fi
    done
    
    return 0
}

# 停止容器
stop_containers() {
    local compose_file="${1:-docker-compose.yml}"
    local timeout="${2:-30}"
    local quiet="${QUIET_MODE:-false}"
    local compose_cmd="${DOCKER_COMPOSE_CMD}"
    
    if [ -z "$compose_cmd" ]; then
        compose_cmd=$(get_docker_compose_cmd)
        if [ $? -ne 0 ]; then
            if [ "$quiet" = "false" ]; then
                log_error "Docker Compose 不可用"
            fi
            return 1
        fi
    fi
    
    if [ "$quiet" = "false" ]; then
        log_step "停止容器..."
    fi
    
    # 检查是否有运行的容器
    if $compose_cmd -f "$compose_file" ps -q 2>/dev/null | grep -q .; then
        if timeout "$timeout" $compose_cmd -f "$compose_file" down 2>/dev/null; then
            if [ "$quiet" = "false" ]; then
                log_success "容器已停止"
            fi
        else
            if [ "$quiet" = "false" ]; then
                log_warning "停止容器超时，强制停止"
            fi
            $compose_cmd -f "$compose_file" kill 2>/dev/null || true
            $compose_cmd -f "$compose_file" down 2>/dev/null || true
        fi
    else
        if [ "$quiet" = "false" ]; then
            log_info "没有运行中的容器"
        fi
    fi
    
    return 0
}

# 构建镜像
build_images() {
    local compose_file="${1:-docker-compose.yml}"
    local no_cache="${2:-false}"
    local quiet="${QUIET_MODE:-false}"
    local compose_cmd="${DOCKER_COMPOSE_CMD}"
    
    if [ -z "$compose_cmd" ]; then
        compose_cmd=$(get_docker_compose_cmd)
        if [ $? -ne 0 ]; then
            if [ "$quiet" = "false" ]; then
                log_error "Docker Compose 不可用"
            fi
            return 1
        fi
    fi
    
    if [ "$quiet" = "false" ]; then
        log_step "构建 Docker 镜像..."
    fi
    
    local build_args=""
    if [ "$no_cache" = "true" ]; then
        build_args="--no-cache"
    fi
    
    if $compose_cmd -f "$compose_file" build $build_args; then
        if [ "$quiet" = "false" ]; then
            log_success "镜像构建成功"
        fi
        return 0
    else
        if [ "$quiet" = "false" ]; then
            log_error "镜像构建失败"
        fi
        return 1
    fi
}

# 启动服务
start_services() {
    local compose_file="${1:-docker-compose.yml}"
    local detach="${2:-true}"
    local quiet="${QUIET_MODE:-false}"
    local compose_cmd="${DOCKER_COMPOSE_CMD}"
    
    if [ -z "$compose_cmd" ]; then
        compose_cmd=$(get_docker_compose_cmd)
        if [ $? -ne 0 ]; then
            if [ "$quiet" = "false" ]; then
                log_error "Docker Compose 不可用"
            fi
            return 1
        fi
    fi
    
    if [ "$quiet" = "false" ]; then
        log_step "启动服务..."
    fi
    
    local up_args=""
    if [ "$detach" = "true" ]; then
        up_args="-d"
    fi
    
    if $compose_cmd -f "$compose_file" up $up_args; then
        if [ "$quiet" = "false" ]; then
            log_success "服务启动成功"
        fi
        return 0
    else
        if [ "$quiet" = "false" ]; then
            log_error "服务启动失败"
        fi
        return 1
    fi
}

# 检查容器状态
check_container_status() {
    local compose_file="${1:-docker-compose.yml}"
    local quiet="${QUIET_MODE:-false}"
    local compose_cmd="${DOCKER_COMPOSE_CMD}"
    
    if [ -z "$compose_cmd" ]; then
        compose_cmd=$(get_docker_compose_cmd)
        if [ $? -ne 0 ]; then
            if [ "$quiet" = "false" ]; then
                log_error "Docker Compose 不可用"
            fi
            return 1
        fi
    fi
    
    if [ "$quiet" = "false" ]; then
        log_step "检查容器状态..."
    fi
    
    local status_output
    status_output=$($compose_cmd -f "$compose_file" ps 2>/dev/null)
    
    if echo "$status_output" | grep -q "Up"; then
        if [ "$quiet" = "false" ]; then
            log_success "容器运行正常"
            echo "$status_output"
        fi
        return 0
    else
        if [ "$quiet" = "false" ]; then
            log_error "容器未正常运行"
            if [ -n "$status_output" ]; then
                echo "$status_output"
            fi
        fi
        return 1
    fi
}

# ==================== 健康检查函数 ====================

# 检查HTTP端点
check_http_endpoint() {
    local url="$1"
    local timeout="${2:-10}"
    local quiet="${3:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "检查端点: $url"
    fi
    
    if curl -f -s --max-time "$timeout" "$url" >/dev/null 2>&1; then
        if [ "$quiet" = "false" ]; then
            log_success "端点响应正常: $url"
        fi
        return 0
    else
        if [ "$quiet" = "false" ]; then
            log_error "端点无响应: $url"
        fi
        return 1
    fi
}

# 等待服务就绪
wait_for_service() {
    local url="$1"
    local max_attempts="${2:-30}"
    local sleep_interval="${3:-2}"
    local quiet="${4:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "等待服务就绪: $url"
    fi
    
    local attempt=1
    while [ $attempt -le $max_attempts ]; do
        if check_http_endpoint "$url" 5 true; then
            if [ "$quiet" = "false" ]; then
                echo  # 换行
                log_success "服务已就绪！"
            fi
            return 0
        fi
        
        if [ "$quiet" = "false" ]; then
            printf "."
        fi
        sleep "$sleep_interval"
        attempt=$((attempt + 1))
    done
    
    if [ "$quiet" = "false" ]; then
        echo  # 换行
        log_warning "服务启动超时"
    fi
    return 1
}

# 检查系统资源
check_system_resources() {
    local quiet="${1:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "检查系统资源..."
    fi
    
    # 检查内存
    if command -v free >/dev/null 2>&1; then
        local available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}' 2>/dev/null || echo "Unknown")
        if [ "$quiet" = "false" ]; then
            log_info "可用内存: ${available_memory}GB"
        fi
    fi
    
    # 检查磁盘空间
    local available_disk=$(df -h . | awk 'NR==2 {print $4}' 2>/dev/null || echo "Unknown")
    if [ "$quiet" = "false" ]; then
        log_info "可用磁盘空间: $available_disk"
    fi
    
    # 检查磁盘使用率
    local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//' 2>/dev/null || echo "0")
    if [ "$disk_usage" -gt 90 ]; then
        if [ "$quiet" = "false" ]; then
            log_warning "磁盘使用率过高: ${disk_usage}%"
        fi
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        if [ "$quiet" = "false" ]; then
            log_warning "磁盘使用率较高: ${disk_usage}%"
        fi
    fi
    
    return 0
}

# 检查端口占用
check_port_usage() {
    local ports_array=("$@")
    local quiet="${QUIET_MODE:-false}"
    local occupied_ports=()
    
    if [ "$quiet" = "false" ]; then
        log_step "检查端口占用..."
    fi
    
    for port in "${ports_array[@]}"; do
        if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
            occupied_ports+=("$port")
            if [ "$quiet" = "false" ]; then
                log_warning "端口 $port 已被占用"
            fi
        else
            if [ "$quiet" = "false" ]; then
                log_success "端口 $port 可用"
            fi
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        return 1
    else
        return 0
    fi
}

# ==================== 工具函数 ====================

# 显示分隔线
show_separator() {
    local char="${1:-=}"
    local length="${2:-50}"
    local message="$3"
    
    if [ -n "$message" ]; then
        local padding=$(( (length - ${#message} - 2) / 2 ))
        printf "%*s%s %s %s\n" $padding "" "$char" "$message" "$(printf "%*s" $padding "" | tr ' ' "$char")"
    else
        printf "%*s\n" $length "" | tr ' ' "$char"
    fi
}

# 确认提示
confirm_action() {
    local message="$1"
    local default="${2:-n}"
    
    local prompt="$message"
    if [ "$default" = "y" ]; then
        prompt="$prompt (Y/n): "
    else
        prompt="$prompt (y/N): "
    fi
    
    read -p "$prompt" -n 1 -r
    echo
    
    if [ "$default" = "y" ]; then
        [[ $REPLY =~ ^[Nn]$ ]] && return 1 || return 0
    else
        [[ $REPLY =~ ^[Yy]$ ]] && return 0 || return 1
    fi
}

# 清理函数
cleanup_temp_files() {
    local quiet="${1:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_step "清理临时文件..."
    fi
    
    # 清理Docker相关临时文件
    docker system prune -f >/dev/null 2>&1 || true
    
    # 清理项目临时文件
    find . -name "*.tmp" -type f -delete 2>/dev/null || true
    find . -name ".DS_Store" -type f -delete 2>/dev/null || true
    
    if [ "$quiet" = "false" ]; then
        log_success "临时文件清理完成"
    fi
}

# 错误处理
handle_error() {
    local exit_code=$?
    local line_number=$1
    local command="$2"
    
    if [ $exit_code -ne 0 ]; then
        log_error "命令执行失败 (退出码: $exit_code)"
        log_error "行号: $line_number"
        log_error "命令: $command"
        
        # 清理并退出
        cleanup_temp_files true
        exit $exit_code
    fi
}

# 设置错误陷阱
set_error_trap() {
    set -eE
    trap 'handle_error $LINENO "$BASH_COMMAND"' ERR
}

# ==================== 初始化函数 ====================

# 初始化工具库
init_docker_utils() {
    local quiet="${1:-false}"
    
    if [ "$quiet" = "false" ]; then
        log_info "初始化 Docker 工具库..."
    fi
    
    # 设置全局变量
    export DOCKER_UTILS_LOADED="true"
    export DOCKER_UTILS_VERSION="1.0.0"
    
    # 检查基本依赖
    if ! check_docker_status true; then
        if [ "$quiet" = "false" ]; then
            log_error "Docker 环境检查失败"
        fi
        return 1
    fi
    
    if ! check_docker_compose_status true; then
        if [ "$quiet" = "false" ]; then
            log_error "Docker Compose 环境检查失败"
        fi
        return 1
    fi
    
    if [ "$quiet" = "false" ]; then
        log_success "Docker 工具库初始化完成"
    fi
    
    return 0
}

# ==================== 版本信息 ====================

show_docker_utils_info() {
    echo "AutoClip Docker 工具库 v${DOCKER_UTILS_VERSION:-1.0.0}"
    echo "提供 Docker 脚本共享功能"
    echo ""
    echo "主要功能:"
    echo "  - Docker 环境检测和管理"
    echo "  - 环境变量配置管理"
    echo "  - 容器生命周期管理"
    echo "  - 健康检查和监控"
    echo "  - 统一的日志和错误处理"
}

# ==================== 导出检查 ====================

# 检查是否在脚本中被正确导入
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    log_error "此文件应该通过 source 命令导入，不能直接执行"
    log_info "正确用法: source \"$(dirname \"\$0\")/docker-utils.sh\""
    exit 1
fi