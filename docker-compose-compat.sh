#!/bin/bash

# Docker Compose 兼容性检查脚本
# 可以被其他脚本source使用，提供统一的兼容性处理

# 获取 Docker Compose 命令（兼容 v1+ 和 v2+）
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
        return 0
    elif docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
        return 0
    else
        echo "docker-compose"  # 默认回退
        return 1
    fi
}

# 检查 Docker Compose 是否可用并设置全局变量
setup_docker_compose() {
    local quiet="${1:-false}"
    
    if [ "$quiet" = "false" ]; then
        echo "🔍 检查 Docker Compose 兼容性..."
    fi
    
    # 尝试获取命令
    if ! DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd); then
        if [ "$quiet" = "false" ]; then
            echo "❌ Docker Compose 未安装或无法访问"
            echo "安装指南: https://docs.docker.com/compose/install/"
        fi
        return 1
    fi
    
    # 导出为全局变量
    export DOCKER_COMPOSE_CMD
    
    if [ "$quiet" = "false" ]; then
        # 获取版本信息
        local version_info=""
        if command -v docker-compose &> /dev/null; then
            local version=$(docker-compose --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
            version_info="docker-compose (v${version:-unknown})"
        elif docker compose version &> /dev/null 2>&1; then
            local version=$(docker compose version --short 2>/dev/null || echo "unknown")
            version_info="docker compose (v$version)"
        fi
        
        echo "✅ Docker Compose 可用: $version_info"
        echo "📝 使用命令: $DOCKER_COMPOSE_CMD"
    fi
    
    return 0
}

# 执行 Docker Compose 命令（带错误处理）
run_compose_cmd() {
    local cmd_args="$@"
    
    if [ -z "$DOCKER_COMPOSE_CMD" ]; then
        if ! setup_docker_compose true; then
            echo "❌ 无法设置 Docker Compose 命令"
            return 1
        fi
    fi
    
    echo "🚀 执行: $DOCKER_COMPOSE_CMD $cmd_args"
    $DOCKER_COMPOSE_CMD $cmd_args
}

# 显示兼容性信息
show_compose_info() {
    echo "🐳 Docker Compose 兼容性信息"
    echo "================================="
    
    # 检查 v1 (docker-compose)
    if command -v docker-compose &> /dev/null; then
        local v1_version=$(docker-compose --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
        echo "✅ Docker Compose v1: 可用 (v${v1_version:-unknown})"
    else
        echo "❌ Docker Compose v1: 不可用"
    fi
    
    # 检查 v2 (docker compose)
    if docker compose version &> /dev/null 2>&1; then
        local v2_version=$(docker compose version --short 2>/dev/null || echo "unknown")
        echo "✅ Docker Compose v2: 可用 (v$v2_version)"
    else
        echo "❌ Docker Compose v2: 不可用"
    fi
    
    echo ""
    echo "💡 当前使用: ${DOCKER_COMPOSE_CMD:-未设置}"
    echo ""
}

# 如果直接运行此脚本，显示兼容性信息
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    setup_docker_compose
    echo ""
    show_compose_info
    
    echo "📚 使用方法："
    echo "在其他脚本中添加："
    echo "  source ./docker-compose-compat.sh"
    echo "  setup_docker_compose"
    echo "  run_compose_cmd up -d"
    echo ""
fi