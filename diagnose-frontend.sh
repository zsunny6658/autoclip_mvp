#!/bin/bash

# 前端文件诊断脚本
# 用于诊断Docker部署中前端文件缺失的问题

set -e

echo "🔍 前端文件诊断脚本"
echo "========================"

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

# 检查本地前端构建
check_local_frontend() {
    log_info "检查本地前端构建..."
    
    if [ -d "frontend/dist" ]; then
        log_success "✓ frontend/dist 目录存在"
        echo "内容:"
        ls -la frontend/dist/ || echo "无法列出内容"
        
        if [ -f "frontend/dist/index.html" ]; then
            log_success "✓ index.html 存在"
            echo "文件大小: $(stat -c%s frontend/dist/index.html 2>/dev/null || stat -f%z frontend/dist/index.html 2>/dev/null || echo '未知') bytes"
        else
            log_error "✗ index.html 不存在"
        fi
        
        if [ -d "frontend/dist/assets" ]; then
            log_success "✓ assets 目录存在"
            echo "assets 内容:"
            ls -la frontend/dist/assets/ | head -10 || echo "无法列出assets内容"
        else
            log_warning "⚠ assets 目录不存在"
        fi
    else
        log_error "✗ frontend/dist 目录不存在"
        echo "需要先构建前端"
    fi
}

# 构建前端
build_frontend() {
    log_info "构建前端应用..."
    
    if [ -d "frontend" ]; then
        cd frontend
        
        if [ -f "package.json" ]; then
            log_info "安装依赖..."
            npm install || {
                log_error "npm install 失败"
                return 1
            }
            
            log_info "构建前端..."
            npm run build || {
                log_error "npm run build 失败"
                return 1
            }
            
            log_success "前端构建完成"
        else
            log_error "package.json 不存在"
            return 1
        fi
        
        cd ..
    else
        log_error "frontend 目录不存在"
        return 1
    fi
}

# 测试Docker构建
test_docker_build() {
    log_info "测试Docker构建..."
    
    # 只构建前端阶段
    if docker build --target frontend-builder --no-cache -t autoclip:frontend-test . > frontend_build.log 2>&1; then
        log_success "前端Docker构建成功"
        
        # 检查构建的内容
        log_info "检查Docker构建内容..."
        docker run --rm autoclip:frontend-test sh -c "ls -la /app/frontend/dist/" > docker_frontend_contents.log 2>&1
        
        if grep -q "index.html" docker_frontend_contents.log; then
            log_success "Docker构建中包含index.html"
        else
            log_error "Docker构建中缺少index.html"
            echo "Docker构建内容:"
            cat docker_frontend_contents.log
        fi
    else
        log_error "前端Docker构建失败"
        echo "构建日志:"
        tail -20 frontend_build.log
        return 1
    fi
}

# 检查完整Docker构建
test_full_docker_build() {
    log_info "测试完整Docker构建..."
    
    if docker build --no-cache -t autoclip:full-test . > full_build.log 2>&1; then
        log_success "完整Docker构建成功"
        
        # 检查最终镜像中的前端文件
        log_info "检查最终镜像中的前端文件..."
        docker run --rm autoclip:full-test sh -c "ls -la /app/frontend/dist/" > final_frontend_contents.log 2>&1
        
        echo "最终镜像中的前端文件:"
        cat final_frontend_contents.log
        
        if grep -q "index.html" final_frontend_contents.log; then
            log_success "最终镜像包含前端文件"
        else
            log_error "最终镜像缺少前端文件"
        fi
        
        # 测试实际启动
        log_info "测试容器启动..."
        container_id=$(docker run -d -p 8001:8000 autoclip:full-test)
        
        sleep 5
        
        # 检查根路径响应
        if curl -s http://localhost:8001/ | grep -q "<!DOCTYPE html>"; then
            log_success "根路径返回HTML内容"
        else
            log_warning "根路径未返回HTML内容"
            echo "根路径响应:"
            curl -s http://localhost:8001/ | head -5
        fi
        
        # 清理测试容器
        docker stop "$container_id" > /dev/null 2>&1
        docker rm "$container_id" > /dev/null 2>&1
        
    else
        log_error "完整Docker构建失败"
        echo "构建日志:"
        tail -30 full_build.log
        return 1
    fi
}

# 清理测试资源
cleanup() {
    log_info "清理测试资源..."
    docker rmi autoclip:frontend-test > /dev/null 2>&1 || true
    docker rmi autoclip:full-test > /dev/null 2>&1 || true
    rm -f frontend_build.log full_build.log docker_frontend_contents.log final_frontend_contents.log
    log_success "清理完成"
}

# 主流程
main() {
    echo
    log_info "开始前端文件诊断..."
    echo
    
    # 检查本地前端构建
    check_local_frontend
    echo
    
    # 如果本地没有构建，尝试构建
    if [ ! -d "frontend/dist" ] || [ ! -f "frontend/dist/index.html" ]; then
        log_warning "检测到前端未构建，尝试构建..."
        if build_frontend; then
            echo
            check_local_frontend
        else
            log_error "前端构建失败，无法继续测试"
            exit 1
        fi
    fi
    
    echo
    
    # 测试Docker构建
    test_docker_build
    echo
    
    # 测试完整构建
    test_full_docker_build
    echo
    
    # 清理
    cleanup
    
    log_success "诊断完成！"
}

# 捕获退出信号并清理
trap cleanup EXIT

# 执行主流程
main "$@"