#!/bin/bash

# AutoClip 生产环境 Docker 部署脚本
# 兼容 Docker Compose v1+ 和 v2+
# 使用公共函数库简化代码

# 导入公共函数库
DOCKER_UTILS_PATH="$(dirname "$0")/docker-utils.sh"
if [ -f "$DOCKER_UTILS_PATH" ]; then
    source "$DOCKER_UTILS_PATH"
else
    echo "❌ 无法找到 docker-utils.sh 文件"
    echo "请确保 docker-utils.sh 在同一目录下"
    exit 1
fi

# 设置错误处理
set_error_trap

# ==================== 配置参数 ====================

# 默认参数
COMPOSE_FILE="docker-compose.prod.yml"
SKIP_BUILD="false"
NO_CACHE="false"
CLEANUP_IMAGES="false"
CREATE_SYSTEMD_SERVICE="false"
ENABLE_MONITORING="false"
QUIET_MODE="false"
DEBUG="false"

# ==================== 生产环境专用函数 ====================

# 检查用户权限
check_user_permissions() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "检测到root用户，建议使用普通用户运行此脚本"
        if ! confirm_action "是否继续？" "n"; then
            exit 1
        fi
    fi
}

# 检查生产环境前置条件
check_prod_prerequisites() {
    log_step "检查生产环境前置条件..."
    
    # 检查Docker环境
    if ! check_docker_status; then
        exit 1
    fi
    
    if ! check_docker_compose_status; then
        exit 1
    fi
    
    # 检查必需文件
    local required_files=("$COMPOSE_FILE" "Dockerfile" "requirements.txt")
    if ! check_required_files "${required_files[@]}"; then
        exit 1
    fi
    
    # 验证Compose文件
    if ! validate_compose_files "$COMPOSE_FILE"; then
        exit 1
    fi
    
    log_success "生产环境前置条件检查通过"
}

# 验证生产环境配置
validate_prod_environment() {
    log_step "验证生产环境配置..."
    
    # 生产环境必须有.env文件
    if ! check_environment_file true; then
        log_error "生产环境需要 .env 文件"
        log_info "请先配置 .env 文件并设置必要的环境变量"
        exit 1
    fi
    
    # 加载和验证环境变量
    if ! load_environment; then
        exit 1
    fi
    
    # 生产环境必须配置API密钥
    if ! validate_api_keys true; then
        log_error "生产环境必须配置 API 密钥"
        exit 1
    fi
    
    log_success "生产环境配置验证通过"
}

# 检查端口占用
check_prod_port_usage() {
    local port="${PROD_PORT:-80}"
    log_step "检查端口占用..."
    
    if check_port_usage "$port"; then
        log_success "端口检查通过"
    else
        log_warning "端口$port已被占用，请检查是否有其他服务运行"
        if ! confirm_action "是否继续？" "n"; then
            exit 1
        fi
    fi
}

# 创建生产环境目录
create_prod_directories() {
    log_step "创建生产环境目录..."
    
    # 生产环境使用绝对路径
    local prod_dirs=(
        "${UPLOADS_DIR:-/var/lib/autoclip/uploads}"
        "${OUTPUT_DIR:-/var/lib/autoclip/output}/clips"
        "${OUTPUT_DIR:-/var/lib/autoclip/output}/collections"
        "${OUTPUT_DIR:-/var/lib/autoclip/output}/metadata"
        "${DATA_DIR:-/var/lib/autoclip/data}"
        "${INPUT_DIR:-/var/lib/autoclip/input}"
        "${LOG_DIR:-/var/log/autoclip}"
    )
    
    if ! create_project_directories "${prod_dirs[@]}"; then
        exit 1
    fi
    
    # 设置生产环境权限
    local current_user=$(whoami)
    for dir in "${prod_dirs[@]}"; do
        if [ -d "$dir" ]; then
            # 尝试设置权限（可能需要sudo）
            if [ -w "$(dirname "$dir")" ]; then
                chown -R "$current_user:$current_user" "$dir" 2>/dev/null || true
            fi
        fi
    done
    
    log_success "生产环境目录创建完成"
}

# 设置生产环境配置
setup_prod_config() {
    log_step "设置生产环境配置..."
    
    local data_dir="${DATA_DIR:-/var/lib/autoclip/data}"
    local settings_file="$data_dir/settings.json"
    
    if [ ! -f "$settings_file" ]; then
        if [ -f "data/settings.example.json" ]; then
            cp "data/settings.example.json" "$settings_file"
            chmod 644 "$settings_file"
            log_success "生产环境配置文件已创建"
        else
            log_warning "未找到配置模板，将使用默认配置"
        fi
    else
        log_success "生产环境配置文件已存在"
    fi
}

# 清理旧镜像
cleanup_old_images() {
    log_step "清理旧镜像..."
    
    # 删除悬挂镜像
    docker image prune -f &>/dev/null || true
    
    # 可选：清理未使用的镜像
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        docker image prune -a -f &>/dev/null || true
        log_success "已清理所有未使用的镜像"
    else
        log_success "已清理悬挂镜像"
    fi
}

# 部署生产环境
deploy_prod_application() {
    log_step "部署生产环境应用..."
    
    # 停止现有容器
    stop_containers "$COMPOSE_FILE" 30
    
    # 清理旧镜像
    cleanup_old_images
    
    # 构建镜像（如果需要）
    if [ "$SKIP_BUILD" = "false" ]; then
        build_images "$COMPOSE_FILE" "$NO_CACHE"
    else
        log_info "跳过镜像构建"
    fi
    
    # 启动服务
    start_services "$COMPOSE_FILE" true
    
    # 等待服务就绪
    perform_prod_health_check
    
    log_success "生产环境应用部署完成"
}

# 执行生产环境健康检查
perform_prod_health_check() {
    log_step "执行生产环境健康检查..."
    
    local port="${PROD_PORT:-80}"
    local host="localhost"
    
    # 构建健康检查URL
    local health_url="http://$host"
    if [ "$port" != "80" ]; then
        health_url="http://$host:$port"
    fi
    health_url="$health_url/health"
    
    # 等待服务启动（生产环境等待时间更长）
    if wait_for_service "$health_url" 60 3; then
        # 检查容器状态
        if check_container_status "$COMPOSE_FILE"; then
            log_success "生产环境健康检查通过"
        else
            log_error "容器状态检查失败"
            exit 1
        fi
    else
        log_warning "健康检查超时，检查容器状态"
        if ! check_container_status "$COMPOSE_FILE"; then
            log_error "生产环境部署失败"
            show_prod_troubleshooting_info
            exit 1
        fi
    fi
}

# 创建系统服务
create_systemd_service() {
    if [ "$CREATE_SYSTEMD_SERVICE" != "true" ]; then
        return 0
    fi
    
    log_step "创建系统服务..."
    
    local service_file="/etc/systemd/system/autoclip.service"
    local working_dir=$(pwd)
    
    # 检查是否有sudo权限
    if ! sudo -v >/dev/null 2>&1; then
        log_error "创建系统服务需要sudo权限"
        return 1
    fi
    
    # 创建systemd服务文件
    sudo tee "$service_file" > /dev/null <<EOF
[Unit]
Description=AutoClip Production Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$working_dir
ExecStart=$DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d
ExecStop=$DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down
TimeoutStartSec=0
User=$(whoami)
Group=$(groups | awk '{print $1}')

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable autoclip.service
    log_success "系统服务已创建并启用"
}

# 设置监控
setup_monitoring() {
    if [ "$ENABLE_MONITORING" != "true" ]; then
        return 0
    fi
    
    log_step "设置监控..."
    
    # 创建监控脚本
    local monitor_script="/usr/local/bin/autoclip-monitor.sh"
    
    # 检查是否有sudo权限
    if ! sudo -v >/dev/null 2>&1; then
        log_warning "设置监控需要sudo权限，跳过"
        return 0
    fi
    
    sudo tee "$monitor_script" > /dev/null <<'EOF'
#!/bin/bash
# AutoClip 监控脚本

COMPOSE_CMD="docker-compose"
if command -v "docker compose" &> /dev/null; then
    COMPOSE_CMD="docker compose"
fi

COMPOSE_FILE="docker-compose.prod.yml"
cd /opt/autoclip || exit 1

# 检查服务状态
if ! $COMPOSE_CMD -f $COMPOSE_FILE ps | grep -q "Up"; then
    echo "$(date): AutoClip service is down, attempting restart..."
    $COMPOSE_CMD -f $COMPOSE_FILE up -d
fi

# 检查磁盘空间
DISK_USAGE=$(df /var/lib/autoclip | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): Disk usage is $DISK_USAGE%, cleaning up old files..."
    find /var/lib/autoclip/uploads -type f -mtime +7 -delete
fi
EOF

    sudo chmod +x "$monitor_script"
    
    # 添加到crontab
    (sudo crontab -l 2>/dev/null; echo "*/5 * * * * $monitor_script >> /var/log/autoclip/monitor.log 2>&1") | sudo crontab -
    
    log_success "监控已设置"
}

# 显示生产环境部署信息
show_prod_deployment_info() {
    local port="${PROD_PORT:-80}"
    local server_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
    
    echo
    show_separator "=" 50 "AutoClip 生产环境部署成功"
    echo
    
    log_info "🌐 访问地址:"
    if [ "$port" = "80" ]; then
        echo "   前端界面: http://localhost (或 http://$server_ip)"
        echo "   API文档: http://localhost/docs (或 http://$server_ip/docs)"
    else
        echo "   前端界面: http://localhost:$port (或 http://$server_ip:$port)"
        echo "   API文档: http://localhost:$port/docs (或 http://$server_ip:$port/docs)"
    fi
    echo
    
    log_info "📋 生产环境管理命令:"
    echo "   查看日志: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs -f"
    echo "   停止服务: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down"
    echo "   重启服务: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE restart"
    echo "   更新服务: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE pull && $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d"
    echo
    
    log_info "📁 数据目录:"
    echo "   上传文件: ${UPLOADS_DIR:-/var/lib/autoclip/uploads}/"
    echo "   输出文件: ${OUTPUT_DIR:-/var/lib/autoclip/output}/"
    echo "   配置文件: ${DATA_DIR:-/var/lib/autoclip/data}/settings.json"
    echo "   日志文件: ${LOG_DIR:-/var/log/autoclip}/"
    echo
    
    log_info "🔒 安全建议:"
    echo "   1. 配置防火墙，只开放必要端口"
    echo "   2. 使用HTTPS代理（如Nginx）"
    echo "   3. 定期备份数据"
    echo "   4. 监控系统资源使用"
    echo
    
    log_info "📊 监控命令:"
    echo "   查看资源使用: docker stats"
    echo "   查看容器状态: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE ps"
    echo "   查看健康状态: curl http://localhost/health"
    echo
    
    if [ "$CREATE_SYSTEMD_SERVICE" = "true" ]; then
        log_info "🎛️  系统服务命令:"
        echo "   启动服务: sudo systemctl start autoclip"
        echo "   停止服务: sudo systemctl stop autoclip"
        echo "   查看状态: sudo systemctl status autoclip"
        echo
    fi
    
    log_info "🔧 其他工具:"
    echo "   健康检查: ./docker-health-check.sh --prod"
    echo "   配置测试: ./test-docker.sh"
    echo "   环境检查: python check_setup.py"
    echo
}

# 显示生产环境故障排除信息
show_prod_troubleshooting_info() {
    echo
    log_info "🔧 生产环境故障排除建议:"
    echo "   1. 查看日志: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs"
    echo "   2. 检查配置: ./test-docker.sh"
    echo "   3. 重新构建: $0 --no-cache"
    echo "   4. 检查端口: netstat -tulpn | grep :80"
    echo "   5. 检查资源: docker stats"
    echo "   6. 系统日志: journalctl -u autoclip"
    echo
}

# ==================== 命令行参数处理 ====================

show_help() {
    echo "AutoClip 生产环境 Docker 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -f, --file FILE        指定 Docker Compose 文件 (默认: docker-compose.prod.yml)"
    echo "  --skip-build           跳过镜像构建"
    echo "  --no-cache             不使用缓存构建镜像"
    echo "  --cleanup-images       清理所有未使用的镜像"
    echo "  --create-service       创建systemd系统服务"
    echo "  --enable-monitoring    启用监控"
    echo "  -q, --quiet            静默模式"
    echo "  --debug                启用调试模式"
    echo "  -h, --help             显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                              # 标准生产环境部署"
    echo "  $0 --no-cache                   # 不使用缓存重新构建"
    echo "  $0 --create-service             # 创建系统服务"
    echo "  $0 --enable-monitoring          # 启用监控"
    echo "  $0 --cleanup-images --create-service --enable-monitoring  # 完整部署"
}

# 解析命令行参数
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            --skip-build)
                SKIP_BUILD="true"
                shift
                ;;
            --no-cache)
                NO_CACHE="true"
                shift
                ;;
            --cleanup-images)
                CLEANUP_IMAGES="true"
                shift
                ;;
            --create-service)
                CREATE_SYSTEMD_SERVICE="true"
                shift
                ;;
            --enable-monitoring)
                ENABLE_MONITORING="true"
                shift
                ;;
            -q|--quiet)
                QUIET_MODE="true"
                export QUIET_MODE="true"
                shift
                ;;
            --debug)
                DEBUG="true"
                export DEBUG="true"
                shift
                ;;
            -h|--help)
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
}

# ==================== 主函数 ====================

main() {
    # 解析命令行参数
    parse_arguments "$@"
    
    # 初始化Docker工具库
    if ! init_docker_utils "$QUIET_MODE"; then
        exit 1
    fi
    
    if [ "$QUIET_MODE" = "false" ]; then
        echo
        show_separator "=" 60 "AutoClip 生产环境部署"
        echo
        log_info "使用配置文件: $COMPOSE_FILE"
        echo
    fi
    
    # 执行部署步骤
    check_user_permissions
    check_prod_prerequisites
    validate_prod_environment
    check_prod_port_usage
    create_prod_directories
    setup_prod_config
    deploy_prod_application
    
    # 可选功能
    create_systemd_service
    setup_monitoring
    
    if [ "$QUIET_MODE" = "false" ]; then
        show_prod_deployment_info
    else
        log_success "生产环境部署完成"
    fi
    
    # 清理临时文件
    cleanup_temp_files true
}

# 执行主函数
main "$@"