#!/bin/bash
# 修复Docker部署权限问题脚本（无需root）

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

# 获取当前用户信息
get_user_info() {
    USER_ID=$(id -u)
    GROUP_ID=$(id -g)
    USER_NAME=$(whoami)
    
    log_info "当前用户: $USER_NAME (UID: $USER_ID, GID: $GROUP_ID)"
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
    
    # 检查projects.json
    if [[ ! -f "data/projects.json" ]]; then
        echo "[]" > "data/projects.json"
        log_success "创建了空的projects.json文件"
    fi
}

# 显示权限状态
show_permissions() {
    log_info "当前权限状态:"
    echo "----------------------------------------"
    ls -la | grep -E "(data|input|output|uploads|logs)" 2>/dev/null || echo "未找到相关目录"
    echo "----------------------------------------"
}

# 检查Docker Compose配置
check_docker_compose() {
    log_info "检查Docker Compose配置..."
    
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "未找到docker-compose.yml文件"
        return 1
    fi
    
    # 检查user配置
    if grep -q "user:" docker-compose.yml; then
        local user_config=$(grep "user:" docker-compose.yml | head -1 | sed 's/.*user: *"*//' | sed 's/"*$//')
        log_info "Docker Compose用户配置: $user_config"
    else
        log_warning "Docker Compose中未配置user参数"
        log_info "建议添加: user: \"1001:1001\""
    fi
}

# 重建Docker容器
rebuild_container() {
    log_info "重建Docker容器以应用权限修复..."
    
    # 停止现有容器
    if docker-compose ps -q autoclip >/dev/null 2>&1; then
        log_info "停止现有容器..."
        docker-compose down
    fi
    
    # 清理Docker缓存
    log_info "清理Docker构建缓存..."
    docker system prune -f --volumes
    
    # 重建并启动
    log_info "重建并启动容器..."
    docker-compose up --build -d
    
    log_success "Docker容器已重建并启动"
    
    # 等待容器启动
    sleep 5
    
    # 检查容器状态
    log_info "检查容器状态..."
    docker-compose ps
}

# 验证修复结果
verify_fix() {
    log_info "验证修复结果..."
    
    # 检查容器是否运行
    if docker-compose ps -q autoclip >/dev/null 2>&1; then
        local container_id=$(docker-compose ps -q autoclip)
        
        if [[ -n "$container_id" ]]; then
            log_info "容器内部权限状态:"
            docker exec "$container_id" ls -la /app/ | head -10
            
            # 检查API健康状态
            sleep 3
            if curl -f http://localhost:8000/health >/dev/null 2>&1; then
                log_success "✓ API健康检查通过"
            else
                log_warning "API健康检查失败，可能需要更多时间启动"
            fi
        fi
    else
        log_error "容器未运行"
    fi
}

# 主函数
main() {
    log_info "开始修复Docker权限问题..."
    echo "========================================"
    
    # 获取用户信息
    get_user_info
    
    # 显示当前状态
    log_info "修复前的权限状态:"
    show_permissions
    
    # 检查Docker Compose配置
    check_docker_compose
    
    # 创建目录
    create_directories
    
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
        verify_fix
    else
        log_info "目录和配置文件已准备就绪，请手动重建容器:"
        echo "  docker-compose down"
        echo "  docker-compose up --build -d"
    fi
    
    echo "========================================"
    log_success "权限修复脚本执行完成！"
    
    echo
    log_info "如果仍有问题，请尝试:"
    echo "1. 确保Docker Compose配置了正确的user参数"
    echo "2. 检查本地目录权限是否正确"
    echo "3. 重建Docker镜像：docker-compose build --no-cache"
}

# 运行主函数
main "$@"