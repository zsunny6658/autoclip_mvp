#!/bin/bash

# 权限修复脚本
# 修复AutoClip Docker部署中的文件权限问题

set -e

echo "🔧 AutoClip 权限修复脚本"
echo "=========================="

# 导入权限工具库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/permission-utils.sh" ]; then
    source "$SCRIPT_DIR/permission-utils.sh"
else
    echo "❌ 未找到permission-utils.sh，请确保文件存在"
    exit 1
fi

# 获取当前用户信息
CURRENT_USER=$(whoami)
CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)

log_info "当前用户: $CURRENT_USER (UID: $CURRENT_UID, GID: $CURRENT_GID)"

# 显示系统信息
show_system_info() {
    log_info "系统信息："
    echo "操作系统: $(uname -s)"
    echo "内核版本: $(uname -r)"
    echo "当前用户: $CURRENT_USER"
    echo "UID/GID: $CURRENT_UID/$CURRENT_GID"
    echo "工作目录: $(pwd)"
    echo ""
}

# 主流程
main() {
    echo
    log_info "开始权限修复流程..."
    echo
    
    show_system_info
    
    # 修复开发环境权限
    fix_dev_permissions
    echo
    
    if verify_permissions; then
        echo
        log_success "🎉 权限修复完成！"
        echo
        log_info "接下来可以重新构建Docker容器："
        # 检测 Docker Compose 命令
        local compose_cmd="docker-compose"
        if ! command -v docker-compose &> /dev/null; then
            if docker compose version &> /dev/null 2>&1; then
                compose_cmd="docker compose"
            fi
        fi
        
        echo "  $compose_cmd down"
        echo "  $compose_cmd build --no-cache"
        echo "  $compose_cmd up -d"
        echo
    else
        echo
        log_error "❌ 权限修复失败，请检查系统权限"
        exit 1
    fi
}

# 执行主流程
main "$@"