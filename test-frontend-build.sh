#!/bin/bash

# 前端构建测试脚本
# 用于测试和验证前端 TypeScript 编译问题

set -e

echo "🔍 前端构建测试脚本"
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

# 清理Docker构建缓存
cleanup_docker_cache() {
    log_info "清理Docker构建缓存..."
    docker builder prune -f > /dev/null 2>&1 || true
    log_success "Docker缓存清理完成"
}

# 测试前端构建阶段
test_frontend_build() {
    log_info "测试前端构建阶段..."
    
    # 使用no-cache选项构建前端阶段
    if docker build --target frontend-builder --no-cache -t autoclip:frontend-test . > frontend_build.log 2>&1; then
        log_success "前端构建阶段成功"
        return 0
    else
        log_error "前端构建阶段失败"
        echo "错误日志："
        tail -n 30 frontend_build.log
        return 1
    fi
}

# 检查TypeScript文件
check_typescript_files() {
    log_info "检查TypeScript文件..."
    
    # 检查关键文件是否存在
    local files=(
        "frontend/src/pages/ProcessingPage.tsx"
        "frontend/src/components/AddClipToCollectionModal.tsx"
        "frontend/src/components/ClipCard.tsx"
        "frontend/src/components/CollectionCard.tsx"
        "frontend/src/components/CollectionCardMini.tsx"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file 存在"
        else
            log_error "✗ $file 不存在"
        fi
    done
}

# 验证ProcessingPage.tsx内容
verify_processing_page() {
    log_info "验证ProcessingPage.tsx内容..."
    
    local file="frontend/src/pages/ProcessingPage.tsx"
    if [ -f "$file" ]; then
        # 检查是否包含problematic patterns
        if grep -q "status\.status === 'processing'" "$file"; then
            log_warning "⚠ 发现可能有问题的状态比较代码"
        else
            log_success "✓ 没有发现状态比较冲突"
        fi
        
        # 检查parseInt是否有进制参数
        if grep -E "parseInt\([^,)]*\)" "$file"; then
            log_warning "⚠ 发现可能缺少进制参数的parseInt"
        else
            log_success "✓ parseInt调用正确"
        fi
    fi
}

# 显示文件行数
show_file_lines() {
    log_info "显示ProcessingPage.tsx关键行..."
    local file="frontend/src/pages/ProcessingPage.tsx"
    if [ -f "$file" ]; then
        echo "第170-180行："
        sed -n '170,180p' "$file" 2>/dev/null || echo "无法读取指定行"
        echo ""
        echo "第185-195行："
        sed -n '185,195p' "$file" 2>/dev/null || echo "无法读取指定行"
    fi
}

# 清理测试镜像
cleanup_test_images() {
    log_info "清理测试镜像..."
    docker rmi autoclip:frontend-test > /dev/null 2>&1 || true
    log_success "测试镜像清理完成"
}

# 主流程
main() {
    echo
    log_info "开始前端构建测试..."
    echo
    
    # 检查文件
    check_typescript_files
    echo
    
    # 验证关键文件
    verify_processing_page
    echo
    
    # 显示关键行
    show_file_lines
    echo
    
    # 清理缓存
    cleanup_docker_cache
    echo
    
    # 测试构建
    if test_frontend_build; then
        log_success "🎉 前端构建测试通过！"
    else
        log_error "❌ 前端构建测试失败"
        exit 1
    fi
    
    # 清理
    cleanup_test_images
    
    echo
    log_success "测试完成！"
}

# 执行主流程
main "$@"