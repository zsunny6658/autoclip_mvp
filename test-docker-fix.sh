#!/bin/bash

# AutoClip Docker 修复测试脚本
# 用于测试和验证 Docker 构建修复是否成功

set -e

echo "🔧 AutoClip Docker 修复测试脚本"
echo "=================================="

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

# 检查 Docker 状态
check_docker() {
    log_info "检查 Docker 服务状态..."
    if ! docker --version > /dev/null 2>&1; then
        log_error "Docker 未安装或未启动"
        exit 1
    fi
    log_success "Docker 服务正常"
}

# 检查 Docker Compose
check_docker_compose() {
    log_info "检查 Docker Compose..."
    if docker-compose --version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version > /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        log_error "Docker Compose 未安装"
        exit 1
    fi
    log_success "Docker Compose 可用: $DOCKER_COMPOSE_CMD"
}

# 清理旧的构建缓存
cleanup_cache() {
    log_info "清理 Docker 构建缓存..."
    docker builder prune -f > /dev/null 2>&1 || true
    log_success "缓存清理完成"
}

# 测试 Dockerfile 语法
test_dockerfile() {
    log_info "测试 Dockerfile 语法..."
    if docker build --dry-run . > /dev/null 2>&1; then
        log_success "Dockerfile 语法正确"
    else
        log_error "Dockerfile 语法错误"
        return 1
    fi
}

# 测试网络连接
test_network() {
    log_info "测试网络连接..."
    if curl -s --connect-timeout 5 https://registry-1.docker.io > /dev/null; then
        log_success "Docker Hub 连接正常"
    else
        log_warning "Docker Hub 连接异常，可能影响镜像下载"
    fi
    
    if curl -s --connect-timeout 5 https://dl-cdn.alpinelinux.org > /dev/null; then
        log_success "Alpine 仓库连接正常"
    else
        log_warning "Alpine 仓库连接异常，可能影响包下载"
    fi
}

# 构建前端镜像（仅前端阶段）
build_frontend() {
    log_info "测试前端构建阶段..."
    if docker build --target frontend-builder -t autoclip:frontend-test . > build_frontend.log 2>&1; then
        log_success "前端构建阶段成功"
        return 0
    else
        log_error "前端构建阶段失败"
        echo "错误日志："
        tail -n 20 build_frontend.log
        return 1
    fi
}

# 构建完整镜像
build_full() {
    log_info "测试完整镜像构建..."
    if docker build -t autoclip:test . > build_full.log 2>&1; then
        log_success "完整镜像构建成功"
        return 0
    else
        log_error "完整镜像构建失败"
        echo "错误日志："
        tail -n 30 build_full.log
        return 1
    fi
}

# 清理测试镜像
cleanup_test_images() {
    log_info "清理测试镜像..."
    docker rmi autoclip:frontend-test > /dev/null 2>&1 || true
    docker rmi autoclip:test > /dev/null 2>&1 || true
    log_success "测试镜像清理完成"
}

# 主流程
main() {
    echo
    log_info "开始 Docker 修复验证流程..."
    echo
    
    # 基础检查
    check_docker
    check_docker_compose
    test_network
    echo
    
    # 清理缓存
    cleanup_cache
    echo
    
    # 语法检查
    test_dockerfile
    echo
    
    # 分阶段测试构建
    log_info "开始分阶段构建测试..."
    
    if build_frontend; then
        echo
        if build_full; then
            echo
            log_success "🎉 所有测试通过！Docker 修复成功！"
            echo
            log_info "接下来你可以运行："
            echo "  $DOCKER_COMPOSE_CMD up -d"
            echo
        else
            log_error "完整构建失败，检查 build_full.log 获取详细信息"
            exit 1
        fi
    else
        log_error "前端构建失败，检查 build_frontend.log 获取详细信息"
        exit 1
    fi
    
    # 清理
    cleanup_test_images
    
    echo
    log_success "修复验证完成！"
}

# 执行主流程
main "$@"