#!/bin/bash

# AutoClip Docker 重新构建脚本
# 兼容 Docker Compose v1+ 和 v2+

# 导入公共函数库
DOCKER_UTILS_PATH="$(dirname "$0")/docker-utils.sh"
if [ -f "$DOCKER_UTILS_PATH" ]; then
    source "$DOCKER_UTILS_PATH"
else
    echo "❌ 无法找到 docker-utils.sh 文件"
    echo "请确保 docker-utils.sh 在同一目录下"
    
    # 如果找不到公共函数库，提供一个简单的兼容函数
    get_docker_compose_cmd() {
        if command -v docker-compose &> /dev/null; then
            echo "docker-compose"
        elif docker compose version &> /dev/null 2>&1; then
            echo "docker compose"
        else
            echo "docker-compose"  # 默认回退
        fi
    }
    
    # 设置全局变量
    export DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
fi

# 检查 Docker Compose 是否可用
if ! check_docker_compose_status &> /dev/null; then
    echo "⚠️  Docker Compose 检测失败，尝试手动设置..."
    if command -v docker-compose &> /dev/null; then
        export DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        export DOCKER_COMPOSE_CMD="docker compose"
    else
        echo "❌ Docker Compose 未安装或无法访问"
        exit 1
    fi
fi

echo "📝 检查环境配置..."

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，正在从 env.example 复制..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ .env 文件创建成功！"
    else
        echo "❌ env.example 文件不存在，请检查项目结构"
        exit 1
    fi
fi

# 读取环境变量
source .env

# 显示关键配置
echo "📊 当前配置信息:"
echo "  DEV_PORT: ${DEV_PORT:-8063}"
echo "  PORT: ${PORT:-8000}"
echo "  CONTAINER_PREFIX: ${CONTAINER_PREFIX:-autoclip}"
echo "  DOCKER_IMAGE_TAG: ${DOCKER_IMAGE_TAG:-latest}"
echo ""

echo "🔧 停止并清理现有容器..."
$DOCKER_COMPOSE_CMD down --remove-orphans

echo "🧹 清理Docker缓存..."
docker system prune -f

echo "🔨 重新构建Docker镜像（无缓存）..."
$DOCKER_COMPOSE_CMD build --no-cache

echo "🚀 启动容器..."
$DOCKER_COMPOSE_CMD up -d

echo "⏳ 等待容器启动..."
sleep 10

echo "📊 检查容器状态..."
$DOCKER_COMPOSE_CMD ps

echo "📝 查看容器日志（最近50行）..."
$DOCKER_COMPOSE_CMD logs --tail=50

echo "🌐 服务地址："
echo "  前端: http://localhost:${DEV_PORT:-8063}"
echo "  API:  http://localhost:${DEV_PORT:-8063}/api"
echo "  健康检查: http://localhost:${DEV_PORT:-8063}/api/health"

echo ""
echo "✅ Docker重新构建完成！"
echo ""
echo "💡 提示: 如果还有问题，请检查以下内容："
echo "   1. 确保端口${DEV_PORT:-8063}没有被其他进程占用"
echo "   2. 检查防火墙设置"
echo "   3. 查看详细日志: $DOCKER_COMPOSE_CMD logs -f"
echo "   4. 检查.env文件配置是否正确"
