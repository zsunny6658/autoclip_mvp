#!/bin/bash

# Docker 健康检查脚本
# 用于检查 AutoClip 服务的健康状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 获取Docker Compose命令
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        return 1
    fi
}

# 检查容器状态
check_container_status() {
    local compose_file="${1:-docker-compose.yml}"
    log_info "检查容器状态..."
    
    local compose_cmd=$(get_docker_compose_cmd)
    if [ $? -ne 0 ]; then
        log_error "Docker Compose 不可用"
        return 1
    fi
    
    # 检查容器是否运行
    if $compose_cmd -f "$compose_file" ps | grep -q "Up"; then
        log_success "容器正在运行"
        
        # 显示详细状态
        echo "容器状态详情:"
        $compose_cmd -f "$compose_file" ps
        return 0
    else
        log_error "容器未运行"
        return 1
    fi
}

# 检查健康端点
check_health_endpoint() {
    local port="${1:-8000}"
    local host="${2:-localhost}"
    
    log_info "检查健康端点..."
    
    local url="http://$host:$port/health"
    if [ "$port" = "80" ]; then
        url="http://$host/health"
    fi
    
    if curl -f -s "$url" >/dev/null 2>&1; then
        log_success "健康端点响应正常"
        
        # 获取健康状态详情
        local health_response=$(curl -s "$url" 2>/dev/null)
        if [ -n "$health_response" ]; then
            echo "健康状态: $health_response"
        fi
        return 0
    else
        log_error "健康端点无响应"
        return 1
    fi
}

# 检查API端点
check_api_endpoint() {
    local port="${1:-8000}"
    local host="${2:-localhost}"
    
    log_info "检查API端点..."
    
    local url="http://$host:$port/docs"
    if [ "$port" = "80" ]; then
        url="http://$host/docs"
    fi
    
    if curl -f -s -I "$url" | grep -q "200 OK"; then
        log_success "API端点响应正常"
        return 0
    else
        log_warning "API端点可能不可用"
        return 1
    fi
}

# 检查日志错误
check_logs_for_errors() {
    local compose_file="${1:-docker-compose.yml}"
    log_info "检查容器日志..."
    
    local compose_cmd=$(get_docker_compose_cmd)
    local logs=$($compose_cmd -f "$compose_file" logs --tail=50 2>/dev/null)
    
    # 检查常见错误模式
    if echo "$logs" | grep -i "error" | grep -v "INFO" >/dev/null; then
        log_warning "发现错误日志"
        echo "最近的错误:"
        echo "$logs" | grep -i "error" | tail -3
        return 1
    else
        log_success "未发现严重错误"
        return 0
    fi
}

# 检查资源使用
check_resource_usage() {
    log_info "检查资源使用情况..."
    
    # 检查Docker统计
    if command -v docker &> /dev/null; then
        local stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep autoclip)
        if [ -n "$stats" ]; then
            echo "资源使用情况:"
            echo "容器名\t\t\tCPU使用率\t内存使用"
            echo "$stats"
            log_success "资源使用正常"
            return 0
        else
            log_warning "无法获取资源使用信息"
            return 1
        fi
    else
        log_warning "Docker 不可用，无法检查资源"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_info "检查磁盘空间..."
    
    # 检查关键目录的磁盘使用
    local uploads_dir="${UPLOADS_DIR:-./uploads}"
    local output_dir="${OUTPUT_DIR:-./output}"
    
    # 检查当前目录磁盘使用
    local disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt 90 ]; then
        log_error "磁盘使用率过高: ${disk_usage}%"
        return 1
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "磁盘使用率较高: ${disk_usage}%"
        return 1
    else
        log_success "磁盘使用率正常: ${disk_usage}%"
        return 0
    fi
}

# 检查网络连接
check_network_connectivity() {
    log_info "检查网络连接..."
    
    # 检查容器网络
    local compose_cmd=$(get_docker_compose_cmd)
    if [ $? -eq 0 ]; then
        local network_name=$(docker network ls | grep autoclip | awk '{print $2}' | head -1)
        if [ -n "$network_name" ]; then
            log_success "Docker网络正常: $network_name"
            return 0
        else
            log_warning "未找到AutoClip Docker网络"
            return 1
        fi
    else
        log_warning "无法检查Docker网络"
        return 1
    fi
}

# 运行完整健康检查
run_full_health_check() {
    local compose_file="${1:-docker-compose.yml}"
    local port="${2:-8000}"
    local host="${3:-localhost}"
    
    echo
    log_info "🏥 AutoClip 健康检查"
    log_info "===================="
    echo
    
    local checks_passed=0
    local total_checks=0
    
    # 执行各项检查
    local checks=(
        "check_container_status $compose_file"
        "check_health_endpoint $port $host"
        "check_api_endpoint $port $host" 
        "check_logs_for_errors $compose_file"
        "check_resource_usage"
        "check_disk_space"
        "check_network_connectivity"
    )
    
    for check in "${checks[@]}"; do
        total_checks=$((total_checks + 1))
        if eval "$check"; then
            checks_passed=$((checks_passed + 1))
        fi
        echo
    done
    
    # 显示总结
    echo "===================="
    log_info "健康检查总结"
    echo "通过检查: $checks_passed/$total_checks"
    
    if [ $checks_passed -eq $total_checks ]; then
        log_success "✨ 所有健康检查通过！服务运行正常"
        return 0
    elif [ $checks_passed -ge $((total_checks - 1)) ]; then
        log_warning "⚠️  大部分检查通过，服务基本正常"
        return 0
    else
        log_error "💥 多项检查失败，服务可能存在问题"
        return 1
    fi
}

# 监控模式
monitor_mode() {
    local compose_file="${1:-docker-compose.yml}"
    local port="${2:-8000}"
    local interval="${3:-30}"
    
    log_info "启动监控模式，检查间隔: ${interval}秒"
    log_info "按 Ctrl+C 退出监控"
    
    while true; do
        echo "==================== $(date) ===================="
        run_full_health_check "$compose_file" "$port"
        sleep "$interval"
    done
}

# 快速检查模式
quick_check() {
    local port="${1:-8000}"
    local host="${2:-localhost}"
    
    log_info "快速健康检查..."
    
    if check_health_endpoint "$port" "$host"; then
        log_success "服务正常运行"
        exit 0
    else
        log_error "服务异常"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "AutoClip Docker 健康检查脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --full              运行完整健康检查（默认）"
    echo "  --quick             快速健康检查"
    echo "  --monitor [间隔]     监控模式，默认30秒间隔"
    echo "  --prod              使用生产环境配置"
    echo "  --port PORT         指定端口，默认8000"
    echo "  --host HOST         指定主机，默认localhost"
    echo "  --help              显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 完整健康检查"
    echo "  $0 --quick           # 快速检查"
    echo "  $0 --monitor 60      # 60秒间隔监控"
    echo "  $0 --prod            # 生产环境检查"
}

# 主函数
main() {
    # 默认参数
    local mode="full"
    local compose_file="docker-compose.yml"
    local port="8000"
    local host="localhost"
    local monitor_interval="30"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --full)
                mode="full"
                shift
                ;;
            --quick)
                mode="quick"
                shift
                ;;
            --monitor)
                mode="monitor"
                if [[ $2 =~ ^[0-9]+$ ]]; then
                    monitor_interval="$2"
                    shift 2
                else
                    shift
                fi
                ;;
            --prod)
                compose_file="docker-compose.prod.yml"
                port="80"
                shift
                ;;
            --port)
                port="$2"
                shift 2
                ;;
            --host)
                host="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 加载环境变量（如果存在）
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    fi
    
    # 执行相应模式
    case $mode in
        "full")
            run_full_health_check "$compose_file" "$port" "$host"
            ;;
        "quick")
            quick_check "$port" "$host"
            ;;
        "monitor")
            monitor_mode "$compose_file" "$port" "$monitor_interval"
            ;;
        *)
            log_error "未知模式: $mode"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"