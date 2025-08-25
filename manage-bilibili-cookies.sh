#!/bin/bash

# Bilibili Cookies 管理脚本
# 用于管理和部署 bilibili_cookies.txt 文件

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PARENT_DIR="$(dirname "$PROJECT_DIR")"

# 定义路径
EXTERNAL_COOKIES="$PARENT_DIR/bilibili_cookies.txt"
DATA_DIR="$PROJECT_DIR/data"
INTERNAL_COOKIES="$DATA_DIR/bilibili_cookies.txt"

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

# 检查 cookies 文件状态
check_cookies_status() {
    echo "=== Bilibili Cookies 文件状态检查 ==="
    echo
    
    log_info "项目目录: $PROJECT_DIR"
    log_info "外部cookies文件路径: $EXTERNAL_COOKIES"
    log_info "内部cookies文件路径: $INTERNAL_COOKIES"
    echo
    
    # 检查外部文件
    if [ -f "$EXTERNAL_COOKIES" ]; then
        local size=$(stat -f%z "$EXTERNAL_COOKIES" 2>/dev/null || stat -c%s "$EXTERNAL_COOKIES" 2>/dev/null)
        local mtime=$(stat -f%Sm "$EXTERNAL_COOKIES" 2>/dev/null || stat -c%y "$EXTERNAL_COOKIES" 2>/dev/null)
        log_success "外部cookies文件存在"
        log_info "  文件大小: ${size} bytes"
        log_info "  修改时间: ${mtime}"
    else
        log_warning "外部cookies文件不存在: $EXTERNAL_COOKIES"
    fi
    
    # 检查内部文件
    if [ -f "$INTERNAL_COOKIES" ]; then
        local size=$(stat -f%z "$INTERNAL_COOKIES" 2>/dev/null || stat -c%s "$INTERNAL_COOKIES" 2>/dev/null)
        local mtime=$(stat -f%Sm "$INTERNAL_COOKIES" 2>/dev/null || stat -c%y "$INTERNAL_COOKIES" 2>/dev/null)
        log_success "内部cookies文件存在"
        log_info "  文件大小: ${size} bytes"
        log_info "  修改时间: ${mtime}"
    else
        log_warning "内部cookies文件不存在: $INTERNAL_COOKIES"
    fi
    echo
}

# 复制 cookies 文件
copy_cookies() {
    echo "=== 复制 Bilibili Cookies 文件 ==="
    echo
    
    if [ ! -f "$EXTERNAL_COOKIES" ]; then
        log_error "外部cookies文件不存在: $EXTERNAL_COOKIES"
        log_info "请先将从浏览器导出的 bilibili_cookies.txt 文件放置在项目同级目录"
        return 1
    fi
    
    # 创建数据目录
    mkdir -p "$DATA_DIR"
    
    # 复制文件
    if cp "$EXTERNAL_COOKIES" "$INTERNAL_COOKIES"; then
        log_success "Cookies文件复制成功"
        
        # 设置权限
        chmod 644 "$INTERNAL_COOKIES"
        log_info "已设置文件权限为644"
        
        # 显示文件信息
        local size=$(stat -f%z "$INTERNAL_COOKIES" 2>/dev/null || stat -c%s "$INTERNAL_COOKIES" 2>/dev/null)
        log_info "文件大小: ${size} bytes"
        
        return 0
    else
        log_error "Cookies文件复制失败"
        return 1
    fi
}

# 验证 cookies 文件格式
validate_cookies() {
    echo "=== 验证 Cookies 文件格式 ==="
    echo
    
    local cookies_file="$INTERNAL_COOKIES"
    if [ ! -f "$cookies_file" ]; then
        log_error "Cookies文件不存在: $cookies_file"
        return 1
    fi
    
    # 检查文件是否为空
    if [ ! -s "$cookies_file" ]; then
        log_warning "Cookies文件为空"
        return 1
    fi
    
    # 检查是否包含bilibili相关的cookies
    if grep -q "bilibili\|\.bili\|SESSDATA" "$cookies_file"; then
        log_success "检测到Bilibili相关的cookies"
    else
        log_warning "未检测到Bilibili相关的cookies，请确认文件内容"
    fi
    
    # 检查文件格式（简单验证）
    local line_count=$(wc -l < "$cookies_file")
    log_info "Cookies条目数量: $line_count"
    
    # 检查常见的cookies格式
    if head -1 "$cookies_file" | grep -q "^#"; then
        log_info "检测到Netscape格式的cookies文件"
    elif head -1 "$cookies_file" | grep -q "^[^#].*\t"; then
        log_info "检测到标准的cookies.txt格式"
    else
        log_warning "未识别的cookies文件格式，可能影响使用"
    fi
    
    return 0
}

# 清理 cookies 文件
clean_cookies() {
    echo "=== 清理 Cookies 文件 ==="
    echo
    
    if [ -f "$INTERNAL_COOKIES" ]; then
        if rm "$INTERNAL_COOKIES"; then
            log_success "内部cookies文件已删除"
        else
            log_error "删除内部cookies文件失败"
            return 1
        fi
    else
        log_info "内部cookies文件不存在，无需清理"
    fi
    
    return 0
}

# 显示使用说明
show_help() {
    echo "Bilibili Cookies 管理脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  status     检查cookies文件状态"
    echo "  copy       复制外部cookies文件到项目内部"
    echo "  validate   验证cookies文件格式"
    echo "  clean      清理内部cookies文件"
    echo "  help       显示此帮助信息"
    echo ""
    echo "文件路径说明:"
    echo "  外部文件: $EXTERNAL_COOKIES"
    echo "  内部文件: $INTERNAL_COOKIES"
    echo ""
    echo "使用步骤:"
    echo "  1. 从浏览器导出bilibili的cookies.txt文件"
    echo "  2. 将文件放置在项目同级目录: $EXTERNAL_COOKIES"
    echo "  3. 运行: $0 copy"
    echo "  4. 运行: $0 validate"
    echo "  5. 重新部署Docker: ./docker-deploy.sh"
    echo ""
}

# 主函数
main() {
    case "${1:-status}" in
        "status")
            check_cookies_status
            ;;
        "copy")
            copy_cookies
            ;;
        "validate")
            validate_cookies
            ;;
        "clean")
            clean_cookies
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"