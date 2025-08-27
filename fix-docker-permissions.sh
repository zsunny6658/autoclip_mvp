#!/bin/bash
# 修复Docker部署权限问题脚本

set -e

# 导入Docker Compose兼容性支持
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/docker-compose-compat.sh" ]; then
    source "$SCRIPT_DIR/docker-compose-compat.sh"
else
    echo "❌ 未找到docker-compose-compat.sh，请确保文件存在"
    exit 1
fi

# 导入权限工具库
if [ -f "$SCRIPT_DIR/permission-utils.sh" ]; then
    source "$SCRIPT_DIR/permission-utils.sh"
else
    echo "❌ 未找到permission-utils.sh，请确保文件存在"
    exit 1
fi

# 检查是否以root身份运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要以root身份运行以修复权限问题"
        echo "请使用: sudo $0"
        exit 1
    fi
}

# 显示权限状态
show_permissions() {
    log_info "当前权限状态:"
    echo "----------------------------------------"
    ls -la | grep -E "(data|input|output|uploads|logs)" || true
    echo "----------------------------------------"
}

# 重建Docker容器
rebuild_container() {
    log_info "重建Docker容器以应用权限修复..."
    
    # 设置Docker Compose命令
    if ! setup_docker_compose true; then
        log_error "Docker Compose不可用，无法重建容器"
        return 1
    fi
    
    # 停止现有容器
    if $DOCKER_COMPOSE_CMD ps -q autoclip >/dev/null 2>&1; then
        log_info "停止现有容器..."
        $DOCKER_COMPOSE_CMD down
    fi
    
    # 重建并启动
    log_info "重建并启动容器..."
    $DOCKER_COMPOSE_CMD up --build -d
    
    log_success "Docker容器已重建并启动"
}

# 主函数
main() {
    log_info "开始修复Docker权限问题..."
    echo "========================================"
    
    # 检查root权限
    check_root
    
    # 显示当前状态
    log_info "修复前的权限状态:"
    show_permissions
    
    # 修复开发环境权限
    fix_dev_permissions
    
    # 显示修复后状态
    log_info "修复后的权限状态:"
    show_permissions
    
    # 询问是否重建容器
    echo
    read -p "是否要重建Docker容器以应用修复？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rebuild_container
    else
        # 设置Docker Compose命令以显示正确的提示
        if ! setup_docker_compose true; then
            log_info "权限已修复，请手动重建容器以应用更改:"
            echo "  docker-compose down  # 或 docker compose down"
            echo "  docker-compose up --build -d  # 或 docker compose up --build -d"
        else
            log_info "权限已修复，请手动重建容器以应用更改:"
            echo "  $DOCKER_COMPOSE_CMD down"
            echo "  $DOCKER_COMPOSE_CMD up --build -d"
        fi
    fi
    
    echo "========================================"
    log_success "权限修复完成！"
}

# 运行主函数
main "$@"