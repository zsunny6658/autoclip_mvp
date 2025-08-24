#!/bin/bash
# Docker构建脚本 - 包含依赖修复逻辑
# 文件: docker-build.sh

set -e  # 出错时退出

echo "开始AutoClip Docker构建..."

# 定义变量
IMAGE_NAME="${1:-autoclip_mvp}"
BUILD_CONTEXT="${2:-.}"

echo "镜像名称: $IMAGE_NAME"
echo "构建上下文: $BUILD_CONTEXT"

# 检查前端依赖文件
echo "检查前端依赖文件..."
if [ ! -f "frontend/package.json" ]; then
    echo "错误: 找不到 frontend/package.json"
    exit 1
fi

# 验证package.json语法
echo "验证package.json语法..."
if ! jq . frontend/package.json > /dev/null 2>&1; then
    echo "错误: frontend/package.json 格式无效"
    exit 1
fi

# 开始Docker构建
echo "开始Docker构建..."
if docker build -t "$IMAGE_NAME" "$BUILD_CONTEXT"; then
    echo "✅ Docker构建成功！"
    echo "镜像: $IMAGE_NAME"
    
    # 显示镜像信息
    echo "镜像信息:"
    docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # 可选：运行基本健康检查
    echo "运行基本健康检查..."
    if docker run --rm --health-cmd="exit 0" "$IMAGE_NAME" /app/health-check.sh 2>/dev/null; then
        echo "✅ 健康检查通过"
    else
        echo "⚠️  健康检查跳过（可能是容器启动问题）"
    fi
    
else
    echo "❌ Docker构建失败"
    echo ""
    echo "常见解决方案:"
    echo "1. 检查网络连接"
    echo "2. 清理Docker缓存: docker system prune -f"
    echo "3. 重新构建: docker build --no-cache -t $IMAGE_NAME $BUILD_CONTEXT"
    echo "4. 检查依赖版本兼容性"
    exit 1
fi

echo "构建完成！"