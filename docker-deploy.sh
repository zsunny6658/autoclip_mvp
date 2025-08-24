#!/bin/bash

# AutoClip Docker 一键部署脚本
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
COMPOSE_FILE="docker-compose.yml"
SKIP_BUILD="false"
NO_CACHE="false"
SKIP_HEALTH_CHECK="false"
QUIET_MODE="false"
DEBUG="false"

# ==================== 业务函数 ====================

# 检查开发环境前置条件
check_dev_prerequisites() {
    log_step "检查开发环境前置条件..."
    
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
    
    log_success "前置条件检查通过"
}

# 设置开发环境
setup_dev_environment() {
    log_step "设置开发环境..."
    
    # 检查环境变量文件
    if ! check_environment_file true; then
        # 尝试自动创建
        if setup_environment_file; then
            log_warning "请编辑 .env 文件并配置你的 API 密钥"
            log_info "重要: 请设置 DASHSCOPE_API_KEY 或 SILICONFLOW_API_KEY"
            log_info "编辑完成后，重新运行此脚本"
            exit 0
        else
            exit 1
        fi
    fi
    
    # 加载和验证环境变量
    if ! load_environment; then
        exit 1
    fi
    
    if ! validate_api_keys true; then
        exit 1
    fi
    
    # 创建项目目录
    if ! create_project_directories; then
        exit 1
    fi
    
    # 设置配置文件
    setup_config_file
    
    log_success "开发环境设置完成"
}

# 设置配置文件
setup_config_file() {
    log_step "设置配置文件..."
    
    local data_dir="${DATA_DIR:-./data}"
    local settings_file="$data_dir/settings.json"
    
    if [ ! -f "$settings_file" ]; then
        if [ -f "$data_dir/settings.example.json" ]; then
            cp "$data_dir/settings.example.json" "$settings_file"
            log_success "从示例文件创建配置文件"
        else
            log_warning "未找到配置文件模板，将使用默认配置"
        fi
    else
        log_info "配置文件已存在"
    fi
}

# 部署流程
deploy_application() {
    log_step "开始部署应用..."
    
    # 停止现有容器
    stop_containers "$COMPOSE_FILE"
    
    # 构建镜像（如果需要）
    if [ "$SKIP_BUILD" = "false" ]; then
        build_images "$COMPOSE_FILE" "$NO_CACHE"
    else
        log_info "跳过镜像构建"
    fi
    
    # 启动服务
    start_services "$COMPOSE_FILE" true
    
    # 健康检查（如果需要）
    if [ "$SKIP_HEALTH_CHECK" = "false" ]; then
        perform_health_check
    else
        log_info "跳过健康检查"
    fi
    
    log_success "应用部署完成"
}

# 执行健康检查
perform_health_check() {
    log_step "执行健康检查..."
    
    local port="${DEV_PORT:-8000}"
    local health_url="http://localhost:$port/health"
    
    # 等待服务启动
    if wait_for_service "$health_url" 30 2; then
        # 检查容器状态
        check_container_status "$COMPOSE_FILE"
    else
        log_warning "健康检查超时，但容器可能仍在启动中"
        # 简单检查容器状态
        if ! check_container_status "$COMPOSE_FILE"; then
            log_error "部署失败，容器未正常运行"
            show_troubleshooting_info
            exit 1
        fi
    fi
}

# 显示部署信息
show_deployment_info() {
    local port="${DEV_PORT:-8000}"
    
    echo
    show_separator "=" 50 "AutoClip 部署成功"
    echo
    
    log_info "🌐 访问地址:"
    echo "   前端界面: http://localhost:$port"
    echo "   API文档: http://localhost:$port/docs"
    echo "   健康检查: http://localhost:$port/health"
    echo
    
    log_info "📋 常用命令:"
    echo "   查看日志: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs -f"
    echo "   停止服务: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down"
    echo "   重启服务: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE restart"
    echo "   更新服务: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE pull && $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d"
    echo
    
    log_info "📁 数据目录:"
    echo "   上传文件: ${UPLOADS_DIR:-./uploads}/"
    echo "   输出文件: ${OUTPUT_DIR:-./output}/"
    echo "   配置文件: ${DATA_DIR:-./data}/settings.json"
    echo "   日志文件: ./logs/"
    echo
    
    log_info "🔧 其他工具:"
    echo "   健康检查: ./docker-health-check.sh --quick"
    echo "   配置测试: ./test-docker.sh"
    echo "   环境检查: python check_setup.py"
    echo
}

# 显示故障排除信息
show_troubleshooting_info() {
    echo
    log_info "🔧 故障排除建议:"
    echo "   1. 查看日志: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs"
    echo "   2. 检查配置: ./test-docker.sh"
    echo "   3. 重新构建: $0 --no-cache"
    echo "   4. 完全重置: $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down && $0"
    echo "   5. 检查环境: python check_setup.py"
    echo
}

# ==================== 命令行参数处理 ====================

show_help() {
    echo "AutoClip Docker 一键部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -f, --file FILE        指定 Docker Compose 文件 (默认: docker-compose.yml)"
    echo "  --skip-build           跳过镜像构建"
    echo "  --no-cache             不使用缓存构建镜像"
    echo "  --skip-health-check    跳过健康检查"
    echo "  -q, --quiet            静默模式"
    echo "  --debug                启用调试模式"
    echo "  -h, --help             显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                     # 标准部署"
    echo "  $0 --no-cache          # 不使用缓存重新构建"
    echo "  $0 --skip-build        # 跳过构建，直接启动"
    echo "  $0 -q                  # 静默模式部署"
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
            --skip-health-check)
                SKIP_HEALTH_CHECK="true"
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
        show_separator "=" 60 "AutoClip Docker 一键部署"
        echo
        log_info "使用配置文件: $COMPOSE_FILE"
        echo
    fi
    
    # 执行部署步骤
    check_dev_prerequisites
    setup_dev_environment
    deploy_application
    
    if [ "$QUIET_MODE" = "false" ]; then
        show_deployment_info
    else
        log_success "部署完成"
    fi
    
    # 清理临时文件
    cleanup_temp_files true
}

# 执行主函数
main "$@"