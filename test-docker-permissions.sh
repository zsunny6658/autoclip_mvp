#!/bin/bash
# 测试Docker权限修复效果

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

# 检查容器是否运行
check_container() {
    log_info "检查容器状态..."
    
    local container_id=$(docker-compose ps -q autoclip 2>/dev/null || echo "")
    
    if [[ -z "$container_id" ]]; then
        log_error "容器未运行，请先启动容器"
        echo "运行: docker-compose up -d"
        return 1
    fi
    
    log_success "容器正在运行: $container_id"
    return 0
}

# 检查容器内权限
check_container_permissions() {
    log_info "检查容器内权限..."
    
    local container_id=$(docker-compose ps -q autoclip)
    
    echo "容器内文件权限状态:"
    echo "----------------------------------------"
    docker exec "$container_id" ls -la /app/ | head -15
    echo "----------------------------------------"
    
    # 检查关键目录权限
    local dirs=("data" "input" "output" "uploads" "logs")
    local errors=0
    
    for dir in "${dirs[@]}"; do
        local owner=$(docker exec "$container_id" stat -c "%U:%G" "/app/$dir" 2>/dev/null || echo "unknown")
        if [[ "$owner" == "appuser:appuser" ]]; then
            log_success "✓ $dir 目录权限正确: $owner"
        else
            log_error "✗ $dir 目录权限错误: $owner (应为 appuser:appuser, UID 10001:10001)"
            ((errors++))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        log_success "所有目录权限都正确！"
        return 0
    else
        log_error "发现 $errors 个权限问题"
        return 1
    fi
}

# 测试文件创建权限
test_file_creation() {
    log_info "测试文件创建权限..."
    
    local container_id=$(docker-compose ps -q autoclip)
    local test_file="/app/data/permission_test_$(date +%s).txt"
    
    # 尝试在容器内创建文件
    if docker exec "$container_id" sh -c "echo 'Permission test' > '$test_file'" 2>/dev/null; then
        log_success "✓ 可以在data目录创建文件"
        
        # 清理测试文件
        docker exec "$container_id" rm -f "$test_file" 2>/dev/null || true
    else
        log_error "✗ 无法在data目录创建文件"
        return 1
    fi
}

# 测试API健康状态
test_api_health() {
    log_info "测试API健康状态..."
    
    # 等待服务启动
    sleep 3
    
    # 检查健康端点
    if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
        log_success "✓ API健康检查通过"
    else
        log_warning "API健康检查失败，服务可能还在启动中"
        
        # 尝试基本端点
        if curl -f -s http://localhost:8000/ >/dev/null 2>&1; then
            log_success "✓ 基本API端点可访问"
        else
            log_error "✗ API端点无法访问"
            return 1
        fi
    fi
}

# 显示容器日志
show_container_logs() {
    log_info "最近的容器日志："
    echo "----------------------------------------"
    docker-compose logs --tail=20 autoclip 2>/dev/null || echo "无法获取日志"
    echo "----------------------------------------"
}

# 主函数
main() {
    echo "========================================"
    log_info "开始验证Docker权限修复效果"
    echo "========================================"
    
    # 检查容器状态
    if ! check_container; then
        exit 1
    fi
    
    # 检查权限
    local permission_ok=true
    if ! check_container_permissions; then
        permission_ok=false
    fi
    
    # 测试文件创建
    local file_creation_ok=true
    if ! test_file_creation; then
        file_creation_ok=false
    fi
    
    # 测试API
    local api_ok=true
    if ! test_api_health; then
        api_ok=false
    fi
    
    # 显示日志
    show_container_logs
    
    # 总结结果
    echo "========================================"
    log_info "验证结果总结："
    
    if [[ "$permission_ok" == "true" ]]; then
        log_success "✓ 目录权限检查通过"
    else
        log_error "✗ 目录权限检查失败"
    fi
    
    if [[ "$file_creation_ok" == "true" ]]; then
        log_success "✓ 文件创建权限测试通过"
    else
        log_error "✗ 文件创建权限测试失败"
    fi
    
    if [[ "$api_ok" == "true" ]]; then
        log_success "✓ API服务测试通过"
    else
        log_error "✗ API服务测试失败"
    fi
    
    if [[ "$permission_ok" == "true" && "$file_creation_ok" == "true" && "$api_ok" == "true" ]]; then
        echo "========================================"
        log_success "🎉 所有测试都通过！权限问题已解决！"
    else
        echo "========================================"
        log_error "发现问题，需要进一步调试"
        echo
        log_info "建议操作："
        echo "1. 检查Dockerfile中的用户配置"
        echo "2. 确认docker-compose.yml中的user参数"
        echo "3. 重建容器：docker-compose down && docker-compose up --build -d"
        echo "4. 检查本地目录权限：ls -la"
    fi
    
    echo "========================================"
}

# 运行主函数
main "$@"