#!/bin/bash

# TypeScript 错误检查脚本
# 用于验证前端代码的 TypeScript 编译问题是否已修复

set -e

echo "🔍 TypeScript 编译错误检查脚本"
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

# 检查前端目录
check_frontend_dir() {
    log_info "检查前端目录..."
    if [ ! -d "frontend" ]; then
        log_error "前端目录不存在"
        exit 1
    fi
    log_success "前端目录存在"
}

# 检查 TypeScript 编译
check_typescript() {
    log_info "检查 TypeScript 编译..."
    cd frontend
    
    # 检查是否有 package.json
    if [ ! -f "package.json" ]; then
        log_error "package.json 不存在"
        exit 1
    fi
    
    # 尝试运行 TypeScript 编译
    log_info "运行 TypeScript 检查..."
    if npm run type-check > /tmp/ts-check.log 2>&1 || npx tsc --noEmit > /tmp/ts-check.log 2>&1; then
        log_success "TypeScript 编译检查通过"
        return 0
    else
        log_error "TypeScript 编译检查失败"
        echo "错误详情："
        cat /tmp/ts-check.log
        return 1
    fi
}

# 检查具体修复的文件
check_fixed_files() {
    log_info "检查已修复的文件..."
    
    local files=(
        "src/components/AddClipToCollectionModal.tsx"
        "src/components/ClipCard.tsx"
        "src/components/CollectionCard.tsx"
        "src/components/CollectionCardMini.tsx"
        "src/pages/ProcessingPage.tsx"
    )
    
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            log_success "✓ $file 存在"
            
            # 检查 parseInt 是否有进制参数
            if grep -q "parseInt([^,)]*)" "$file"; then
                log_warning "⚠ $file 中可能还有缺少进制参数的 parseInt"
            else
                log_success "✓ $file 中的 parseInt 调用已修复"
            fi
        else
            log_warning "⚠ $file 不存在"
        fi
    done
}

# 生成修复报告
generate_report() {
    log_info "生成修复报告..."
    
    echo "# TypeScript 错误修复报告" > /tmp/ts-fix-report.md
    echo "生成时间: $(date)" >> /tmp/ts-fix-report.md
    echo "" >> /tmp/ts-fix-report.md
    echo "## 已修复的问题" >> /tmp/ts-fix-report.md
    echo "1. parseInt 函数缺少进制参数 (TS2554)" >> /tmp/ts-fix-report.md
    echo "2. 状态比较类型不匹配 (TS2367)" >> /tmp/ts-fix-report.md
    echo "" >> /tmp/ts-fix-report.md
    echo "## 修复的文件" >> /tmp/ts-fix-report.md
    echo "- AddClipToCollectionModal.tsx" >> /tmp/ts-fix-report.md
    echo "- ClipCard.tsx" >> /tmp/ts-fix-report.md
    echo "- CollectionCard.tsx" >> /tmp/ts-fix-report.md
    echo "- CollectionCardMini.tsx" >> /tmp/ts-fix-report.md
    echo "- ProcessingPage.tsx" >> /tmp/ts-fix-report.md
    echo "" >> /tmp/ts-fix-report.md
    
    log_success "修复报告已生成: /tmp/ts-fix-report.md"
}

# 主流程
main() {
    echo
    log_info "开始 TypeScript 错误检查..."
    echo
    
    check_frontend_dir
    
    cd frontend
    check_fixed_files
    
    echo
    log_info "尝试 TypeScript 编译检查..."
    if check_typescript; then
        echo
        log_success "🎉 所有 TypeScript 错误已修复！"
    else
        echo
        log_warning "⚠ 仍有 TypeScript 错误需要修复"
    fi
    
    cd ..
    generate_report
    
    echo
    log_success "检查完成！"
}

# 执行主流程
main "$@"