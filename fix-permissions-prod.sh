#!/bin/bash

# 生产环境权限修复脚本
# 修复AutoClip生产环境Docker部署中的文件权限问题

set -e

echo "🔧 AutoClip 生产环境权限修复脚本"
echo "===================================="

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

# 生产环境路径配置
PROD_BASE_DIR="${DATA_DIR:-/var/lib/autoclip}"
PROD_LOG_DIR="${LOG_DIR:-/var/log/autoclip}"

# 检查是否为root用户
check_permissions() {
    if [ "$CURRENT_UID" -ne 0 ] && [ ! -w "/var/lib" ] 2>/dev/null; then
        log_warning "当前用户可能没有足够权限创建生产环境目录"
        log_warning "建议使用sudo运行此脚本或在具有相应权限的环境中运行"
        echo ""
        echo "选项1: 使用sudo权限运行"
        echo "  sudo ./fix-permissions-prod.sh"
        echo ""
        echo "选项2: 使用当前目录作为开发环境"
        echo "  ./fix-permissions.sh"
        echo ""
        read -p "是否继续在当前目录创建开发环境配置? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "退出脚本"
            exit 0
        fi
        # 使用当前目录作为开发环境
        PROD_BASE_DIR="."
        PROD_LOG_DIR="./logs"
    fi
}

# 创建生产环境目录结构
create_prod_directories() {
    log_info "创建生产环境目录结构..."
    
    local dirs=(
        "$PROD_BASE_DIR/data"
        "$PROD_BASE_DIR/uploads"
        "$PROD_BASE_DIR/output"
        "$PROD_BASE_DIR/output/clips"
        "$PROD_BASE_DIR/output/collections"
        "$PROD_BASE_DIR/output/metadata"
        "$PROD_BASE_DIR/input"
        "$PROD_LOG_DIR"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            if mkdir -p "$dir" 2>/dev/null; then
                log_success "✓ 创建目录: $dir"
            else
                log_error "✗ 无法创建目录: $dir"
                return 1
            fi
        else
            log_info "✓ 目录已存在: $dir"
        fi
    done
}

# 设置生产环境权限
set_prod_permissions() {
    log_info "设置生产环境权限..."
    
    # 设置目录权限为755（rwxr-xr-x）
    local dirs=(
        "$PROD_BASE_DIR/data"
        "$PROD_BASE_DIR/uploads"
        "$PROD_BASE_DIR/output"
        "$PROD_BASE_DIR/input"
        "$PROD_LOG_DIR"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            if chmod 755 "$dir" 2>/dev/null; then
                log_success "✓ 设置目录权限: $dir (755)"
            else
                log_warning "⚠ 无法设置目录权限: $dir"
            fi
        fi
    done
    
    # 递归设置子目录权限
    find "$PROD_BASE_DIR/output" -type d -exec chmod 755 {} \; 2>/dev/null || true
    find "$PROD_BASE_DIR/uploads" -type d -exec chmod 755 {} \; 2>/dev/null || true
    
    log_success "生产环境权限设置完成"
}

# 创建生产环境配置文件
create_prod_config_files() {
    log_info "创建生产环境配置文件..."
    
    # 创建 settings.json
    local settings_file="$PROD_BASE_DIR/data/settings.json"
    if [ ! -f "$settings_file" ]; then
        cat > "$settings_file" << 'EOF'
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
        log_success "✓ 创建生产环境 settings.json"
    else
        log_info "✓ 生产环境 settings.json 已存在"
    fi
    
    # 创建 projects.json
    local projects_file="$PROD_BASE_DIR/data/projects.json"
    if [ ! -f "$projects_file" ]; then
        echo "[]" > "$projects_file"
        log_success "✓ 创建生产环境 projects.json"
    else
        log_info "✓ 生产环境 projects.json 已存在"
    fi
    
    # 设置文件权限为644（rw-r--r--）
    chmod 644 "$settings_file" "$projects_file" 2>/dev/null || true
    log_success "生产环境配置文件权限设置完成"
}

# 创建生产环境变量文件
create_prod_env_file() {
    log_info "创建生产环境变量文件..."
    
    if [ ! -f ".env.prod" ]; then
        cat > ".env.prod" << EOF
# 生产环境配置

# API配置（必须配置）
DASHSCOPE_API_KEY=your_dashscope_api_key
SILICONFLOW_API_KEY=your_siliconflow_api_key
API_PROVIDER=dashscope
MODEL_NAME=qwen-plus
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct

# 服务器配置
PROD_PORT=80
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# 生产环境目录配置
DATA_DIR=$PROD_BASE_DIR/data
UPLOADS_DIR=$PROD_BASE_DIR/uploads
OUTPUT_DIR=$PROD_BASE_DIR/output
INPUT_DIR=$PROD_BASE_DIR/input
LOG_DIR=$PROD_LOG_DIR

# 资源限制
MEMORY_LIMIT_PROD=4G
CPU_LIMIT_PROD=2.0
MEMORY_RESERVATION_PROD=1G
CPU_RESERVATION_PROD=0.5

# 处理参数
MAX_CONCURRENT_TASKS=6
VIDEO_PROCESSING_TIMEOUT=7200
MAX_UPLOAD_SIZE=4096

# Docker配置
DOCKER_IMAGE_TAG=autoclip:prod
CONTAINER_PREFIX=autoclip
EOF
        log_success "✓ 创建生产环境配置文件 .env.prod"
        log_warning "⚠ 请编辑 .env.prod 文件并配置正确的API密钥"
    else
        log_info "✓ 生产环境配置文件 .env.prod 已存在"
    fi
}

# 验证生产环境配置
verify_prod_setup() {
    log_info "验证生产环境配置..."
    
    local error_count=0
    
    # 检查目录权限
    local dirs=("$PROD_BASE_DIR/data" "$PROD_BASE_DIR/uploads" "$PROD_BASE_DIR/output" "$PROD_BASE_DIR/input" "$PROD_LOG_DIR")
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
    local files=("$PROD_BASE_DIR/data/settings.json" "$PROD_BASE_DIR/data/projects.json")
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
        log_success "生产环境配置验证通过！"
        return 0
    else
        log_error "发现 $error_count 个问题"
        return 1
    fi
}

# 显示部署指令
show_deployment_instructions() {
    echo
    log_info "生产环境部署指令："
    echo "1. 配置环境变量："
    echo "   cp .env.prod .env"
    echo "   # 编辑 .env 文件并配置正确的API密钥"
    echo ""
    # 检测 Docker Compose 命令
    local compose_cmd="docker-compose"
    if ! command -v docker-compose &> /dev/null; then
        if docker compose version &> /dev/null 2>&1; then
            compose_cmd="docker compose"
        fi
    fi
    
    echo "2. 构建生产环境镜像："
    echo "   $compose_cmd -f docker-compose.prod.yml build --no-cache"
    echo ""
    echo "3. 启动生产环境服务："
    echo "   $compose_cmd -f docker-compose.prod.yml up -d"
    echo ""
    echo "4. 查看服务状态："
    echo "   $compose_cmd -f docker-compose.prod.yml ps"
    echo "   $compose_cmd -f docker-compose.prod.yml logs -f"
    echo ""
}

# 主流程
main() {
    echo
    log_info "开始生产环境权限修复流程..."
    echo
    
    check_permissions
    echo
    
    create_prod_directories
    echo
    
    set_prod_permissions
    echo
    
    create_prod_config_files
    echo
    
    create_prod_env_file
    echo
    
    if verify_prod_setup; then
        echo
        log_success "🎉 生产环境权限修复完成！"
        show_deployment_instructions
    else
        echo
        log_error "❌ 生产环境配置失败，请检查权限"
        exit 1
    fi
}

# 执行主流程
main "$@"