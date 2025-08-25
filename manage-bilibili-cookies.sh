#!/bin/bash

# Bilibili Cookies 管理脚本
# 用于管理和部署 bilibili_cookies.txt 文件

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
PARENT_DIR="$(dirname "$PROJECT_DIR")"

# 定义路径
EXTERNAL_COOKIES="$PARENT_DIR/bilibili_cookies.txt"
DATA_DIR="${DATA_DIR:-$PROJECT_DIR/data}"  # 支持环境变量配置
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

# 检测 cookies 文件格式
detect_cookies_format() {
    local cookies_file="$1"
    
    if [ ! -f "$cookies_file" ]; then
        echo "unknown"
        return 1
    fi
    
    # 检查是否已经是Netscape格式
    if head -1 "$cookies_file" | grep -q "^# Netscape HTTP Cookie File"; then
        echo "netscape"
        return 0
    fi
    
    # 检查是否是标准的tab分隔格式
    if head -5 "$cookies_file" | grep -q $'\t'; then
        echo "tab_separated"
        return 0
    fi
    
    # 检查是否是原始的浏览器cookies字符串格式
    local first_line=$(head -1 "$cookies_file")
    if echo "$first_line" | grep -q "SESSDATA=\|bili_jct=\|DedeUserID="; then
        if echo "$first_line" | grep -q "; "; then
            echo "browser_string"
            return 0
        fi
    fi
    
    # 检查是否是JSON格式
    if head -1 "$cookies_file" | grep -q "^[\[{]"; then
        echo "json"
        return 0
    fi
    
    echo "unknown"
    return 1
}

# 解析浏览器cookies字符串
parse_browser_cookies() {
    local cookies_string="$1"
    local output_file="$2"
    
    # 获取当前时间戳（一年后过期）
    local expire_time=$(($(date +%s) + 31536000))
    
    # 写入Netscape格式头部
    cat > "$output_file" << 'EOF'
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.
# 此文件由AutoClip自动生成，包含Bilibili登录信息

EOF
    
    # 解析cookies字符串
    echo "$cookies_string" | tr ';' '\n' | while IFS= read -r cookie; do
        # 清理空格
        cookie=$(echo "$cookie" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        
        if [ -z "$cookie" ]; then
            continue
        fi
        
        # 分离cookie名称和值
        if echo "$cookie" | grep -q "="; then
            local name=$(echo "$cookie" | cut -d'=' -f1)
            local value=$(echo "$cookie" | cut -d'=' -f2-)
            
            # 写入Netscape格式
            # 格式: domain  flag  path  secure  expiration  name  value
            echo -e ".bilibili.com\tTRUE\t/\tFALSE\t$expire_time\t$name\t$value" >> "$output_file"
        fi
    done
    
    return 0
}

# 转换cookies格式为Netscape格式
convert_to_netscape() {
    local input_file="$1"
    local output_file="$2"
    
    log_info "检测cookies文件格式..."
    local format=$(detect_cookies_format "$input_file")
    
    case "$format" in
        "netscape")
            log_info "检测到Netscape格式，直接复制"
            cp "$input_file" "$output_file"
            return 0
            ;;
        "browser_string")
            log_info "检测到浏览器cookies字符串格式，开始转换..."
            local cookies_content=$(cat "$input_file")
            parse_browser_cookies "$cookies_content" "$output_file"
            log_success "已转换为Netscape格式"
            return 0
            ;;
        "tab_separated")
            log_info "检测到Tab分隔格式，添加Netscape头部..."
            {
                echo "# Netscape HTTP Cookie File"
                echo "# This is a generated file! Do not edit."
                echo "# 此文件由AutoClip自动生成，包含Bilibili登录信息"
                echo ""
                cat "$input_file"
            } > "$output_file"
            log_success "已添加Netscape头部"
            return 0
            ;;
        "json")
            log_warning "检测到JSON格式，暂不支持自动转换"
            log_info "请将JSON格式转换为浏览器cookies字符串格式"
            return 1
            ;;
        "unknown")
            log_warning "无法识别cookies格式，尝试作为原始字符串处理..."
            local cookies_content=$(cat "$input_file")
            if echo "$cookies_content" | grep -q "SESSDATA="; then
                parse_browser_cookies "$cookies_content" "$output_file"
                log_success "已按原始字符串转换为Netscape格式"
                return 0
            else
                log_error "无法处理的cookies格式"
                return 1
            fi
            ;;
        *)
            log_error "未知的cookies格式: $format"
            return 1
            ;;
    esac
}
copy_cookies() {
    echo "=== 复制并转换 Bilibili Cookies 文件 ==="
    echo
    
    if [ ! -f "$EXTERNAL_COOKIES" ]; then
        log_error "外部cookies文件不存在: $EXTERNAL_COOKIES"
        log_info "请先将从浏览器导出的 bilibili_cookies.txt 文件放置在项目同级目录"
        return 1
    fi
    
    # 创建数据目录
    mkdir -p "$DATA_DIR"
    
    # 先检测并转换格式
    log_info "分析cookies文件格式..."
    if convert_to_netscape "$EXTERNAL_COOKIES" "$INTERNAL_COOKIES"; then
        log_success "Cookies文件处理成功"
        
        # 设置权限
        chmod 644 "$INTERNAL_COOKIES"
        log_info "已设置文件权限为644"
        
        # 显示文件信息
        local size=$(stat -f%z "$INTERNAL_COOKIES" 2>/dev/null || stat -c%s "$INTERNAL_COOKIES" 2>/dev/null)
        log_info "文件大小: ${size} bytes"
        
        # 验证转换后的文件
        log_info "验证转换后的文件..."
        if validate_converted_cookies "$INTERNAL_COOKIES"; then
            log_success "文件转换和验证都成功完成"
        else
            log_warning "文件转换成功，但验证发现一些问题"
        fi
        
        return 0
    else
        log_error "Cookies文件处理失败"
        return 1
    fi
}

# 验证转换后的cookies文件
validate_converted_cookies() {
    local cookies_file="$1"
    local validation_passed=true
    
    # 检查文件是否为空
    if [ ! -s "$cookies_file" ]; then
        log_warning "Cookies文件为空"
        return 1
    fi
    
    # 检查是否包含Netscape头部
    if head -1 "$cookies_file" | grep -q "^# Netscape HTTP Cookie File"; then
        log_success "✓ 包含Netscape格式头部"
    else
        log_warning "⚠ 缺少Netscape格式头部"
        validation_passed=false
    fi
    
    # 检查关键的Bilibili cookies
    local required_cookies=("SESSDATA" "bili_jct" "DedeUserID")
    for cookie in "${required_cookies[@]}"; do
        if grep -q "$cookie" "$cookies_file"; then
            log_success "✓ 找到关键cookie: $cookie"
        else
            log_warning "⚠ 缺少关键cookie: $cookie"
            validation_passed=false
        fi
    done
    
    # 检查格式是否正确（简单验证）
    local non_comment_lines=$(grep -v "^#" "$cookies_file" | grep -v "^$" | wc -l)
    if [ "$non_comment_lines" -gt 0 ]; then
        log_success "✓ 包含 $non_comment_lines 个cookies条目"
        
        # 检查是否有Tab分隔格式
        local tab_separated_lines=$(grep -v "^#" "$cookies_file" | grep -v "^$" | grep $'\t' | wc -l)
        if [ "$tab_separated_lines" -gt 0 ]; then
            log_success "✓ 检测到 $tab_separated_lines 个正确的Tab分隔格式条目"
        else
            log_warning "⚠ 未检测到Tab分隔格式，可能影响使用"
            validation_passed=false
        fi
    else
        log_warning "⚠ 未找到有效的cookies条目"
        validation_passed=false
    fi
    
    if [ "$validation_passed" = true ]; then
        log_success "✓ Cookies文件验证通过"
        return 0
    else
        log_warning "⚠ Cookies文件验证发现问题，但仍可能正常使用"
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

# 仅转换格式（不复制文件）
convert_format() {
    echo "=== 转换 Cookies 文件格式 ==="
    echo
    
    if [ ! -f "$EXTERNAL_COOKIES" ]; then
        log_error "外部cookies文件不存在: $EXTERNAL_COOKIES"
        return 1
    fi
    
    log_info "检测外部cookies文件格式..."
    local format=$(detect_cookies_format "$EXTERNAL_COOKIES")
    log_info "检测到格式: $format"
    
    case "$format" in
        "netscape")
            log_success "文件已经是Netscape格式，无需转换"
            ;;
        "browser_string")
            log_info "检测到浏览器cookies字符串格式"
            log_info "示例转换结果:"
            echo "# Netscape HTTP Cookie File"
            echo "# 这是转换后的示例格式"
            local cookies_content=$(head -1 "$EXTERNAL_COOKIES")
            echo "$cookies_content" | tr ';' '\n' | head -3 | while IFS= read -r cookie; do
                cookie=$(echo "$cookie" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
                if [ -n "$cookie" ] && echo "$cookie" | grep -q "="; then
                    local name=$(echo "$cookie" | cut -d'=' -f1)
                    local value=$(echo "$cookie" | cut -d'=' -f2-)
                    echo ".bilibili.com	TRUE	/	FALSE	1735689600	$name	$value"
                fi
            done
            ;;
        *)
            log_warning "不支持的格式: $format"
            ;;
    esac
    
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
    echo "Bilibili Cookies 管理脚本 - 支持自动格式转换"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  status     检查cookies文件状态"
    echo "  copy       复制并转换外部cookies文件到项目内部"
    echo "  convert    仅检测并显示转换示例（不修改文件）"
    echo "  validate   验证cookies文件格式"
    echo "  clean      清理内部cookies文件"
    echo "  help       显示此帮助信息"
    echo ""
    echo "文件路径说明:"
    echo "  外部文件: $EXTERNAL_COOKIES"
    echo "  内部文件: $INTERNAL_COOKIES"
    echo ""
    echo "支持的cookies格式:"
    echo "  1. Netscape格式 (# Netscape HTTP Cookie File...)"
    echo "  2. Tab分隔格式 (.bilibili.com\tTRUE\t/...)"
    echo "  3. 浏览器原始cookies字符串 (SESSDATA=xxx; bili_jct=yyy; ...)"
    echo ""
    echo "使用步骤:"
    echo "  1. 从浏览器导出bilibili的cookies信息"
    echo "  2. 将cookies信息保存为: $EXTERNAL_COOKIES"
    echo "  3. 运行: $0 convert  # 预览转换结果"
    echo "  4. 运行: $0 copy     # 正式转换并复制"
    echo "  5. 运行: $0 validate # 验证结果"
    echo "  6. 重新部署Docker: ./docker-deploy.sh"
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
        "convert")
            convert_format
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