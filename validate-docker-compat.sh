#!/bin/bash

# Docker 脚本兼容性验证工具
# 检查项目中所有脚本是否正确实现了 Docker Compose v1+/v2+ 兼容性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
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

echo "🔍 Docker Compose 兼容性验证工具"
echo "======================================"

# 导入兼容性检查脚本
if [ -f "./docker-compose-compat.sh" ]; then
    source ./docker-compose-compat.sh
    setup_docker_compose
else
    log_warning "docker-compose-compat.sh 不存在，使用内置检查"
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        log_error "Docker Compose 未安装"
        exit 1
    fi
fi

echo ""

# 查找所有 shell 脚本
scripts=($(find . -maxdepth 1 -name "*.sh" -type f | grep -v validate-docker-compat.sh | sort))

if [ ${#scripts[@]} -eq 0 ]; then
    log_warning "未找到任何 shell 脚本"
    exit 0
fi

log_info "找到 ${#scripts[@]} 个脚本文件"
echo ""

# 验证结果统计
total_scripts=0
compatible_scripts=0
has_issues=0

# 逐个检查脚本
for script in "${scripts[@]}"; do
    ((total_scripts++))
    script_name=$(basename "$script")
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "检查脚本: $script_name"
    
    # 检查是否包含 docker-compose 命令
    hardcoded_compose=$(grep -n "docker-compose " "$script" 2>/dev/null | grep -v "docker-compose --version" | grep -v "command -v docker-compose" || true)
    
    if [ -n "$hardcoded_compose" ]; then
        log_error "发现硬编码的 docker-compose 命令:"
        echo "$hardcoded_compose" | while read line; do
            echo "  $line"
        done
        ((has_issues++))
    else
        log_success "未发现硬编码的 docker-compose 命令"
    fi
    
    # 检查是否使用了兼容性变量
    uses_compose_var=$(grep -n "\\$DOCKER_COMPOSE_CMD\\|\\${DOCKER_COMPOSE_CMD}" "$script" 2>/dev/null || true)
    uses_compose_func=$(grep -n "get_docker_compose_cmd\\|setup_docker_compose\\|run_compose_cmd" "$script" 2>/dev/null || true)
    
    if [ -n "$uses_compose_var" ] || [ -n "$uses_compose_func" ]; then
        log_success "使用了兼容性变量或函数"
        ((compatible_scripts++))
        
        if [ -n "$uses_compose_var" ]; then
            echo "  变量使用: $(echo "$uses_compose_var" | wc -l) 处"
        fi
        if [ -n "$uses_compose_func" ]; then
            echo "  函数使用: $(echo "$uses_compose_func" | wc -l) 处"
        fi
    else
        # 检查是否包含任何 compose 相关命令
        has_compose=$(grep -n "compose " "$script" 2>/dev/null || true)
        if [ -n "$has_compose" ]; then
            log_warning "包含 compose 命令但未使用兼容性处理"
        else
            log_info "不包含 compose 命令（无需兼容性处理）"
            ((compatible_scripts++))
        fi
    fi
    
    # 检查是否有错误处理
    has_error_handling=$(grep -n "set -e\\|exit 1\\|return 1" "$script" 2>/dev/null || true)
    if [ -n "$has_error_handling" ]; then
        log_success "包含错误处理"
    else
        log_warning "缺少错误处理"
    fi
    
    echo ""
done

# 显示总结报告
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 兼容性验证报告"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "总脚本数: $total_scripts"
echo "兼容脚本数: $compatible_scripts"
echo "有问题脚本数: $has_issues"

compatibility_rate=$((compatible_scripts * 100 / total_scripts))
echo "兼容性比率: $compatibility_rate%"

echo ""

if [ $has_issues -eq 0 ]; then
    log_success "🎉 所有脚本都已正确实现 Docker Compose 兼容性！"
    echo ""
    log_info "当前 Docker Compose 环境："
    show_compose_info
else
    log_error "发现 $has_issues 个脚本需要修复"
    echo ""
    log_info "修复建议："
    echo "1. 将硬编码的 'docker-compose' 替换为 '\$DOCKER_COMPOSE_CMD'"
    echo "2. 在脚本开始处添加兼容性检查："
    echo "   source ./docker-compose-compat.sh"
    echo "   setup_docker_compose"
    echo "3. 或者使用内置兼容性函数："
    echo "   get_docker_compose_cmd() { ... }"
    echo ""
    exit 1
fi

echo ""
log_info "💡 测试建议："
echo "1. 测试 v1 版本: docker-compose --version"
echo "2. 测试 v2 版本: docker compose version"
echo "3. 运行主要脚本验证功能"
echo ""