# 优化的多阶段构建 Dockerfile
# 支持更好的缓存和安全性

# ==================== 阶段1: 前端构建 ====================
FROM node:20-alpine AS frontend-builder

# 设置工作目录
WORKDIR /app/frontend

# 创建非root用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# 安装必要的构建工具和网络工具
RUN apk update && apk add --no-cache \
    ca-certificates \
    git

# 复制依赖文件（利用Docker缓存）
COPY frontend/package.json ./
# 复制package-lock.json（如果存在）
COPY frontend/package-lock.json* ./

# 安装依赖（包含devDependencies用于构建）
# 如果lock文件不存在或不同步，先生成新的lock文件
RUN set -e; \
    if [ ! -f package-lock.json ]; then \
        echo "No lock file found, running npm install to generate one"; \
        npm install; \
    elif ! npm ci --frozen-lockfile 2>/dev/null; then \
        echo "Lock file out of sync, regenerating with npm install"; \
        rm -f package-lock.json; \
        npm install; \
    else \
        echo "Using existing synchronized lock file"; \
    fi

# 复制源代码
COPY frontend/ ./

# 构建应用
RUN npm run build

# 清理不必要的文件
RUN rm -rf node_modules && \
    rm -rf .npm

# ==================== 阶段2: Python依赖安装 ====================
FROM python:3.11-slim AS python-builder

# 安装构建工具
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==================== 阶段3: 最终运行环境 ====================
FROM python:3.11-slim AS production

# 设置环境变量
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# 创建应用用户（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 设置工作目录
WORKDIR /app

# 复制Python虚拟环境
COPY --from=python-builder /opt/venv /opt/venv

# 复制后端源代码
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser backend_server.py ./
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser prompt/ ./prompt/

# 复制构建好的前端文件
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/dist ./frontend/dist

# 创建必要的目录并设置权限
RUN mkdir -p input output/clips output/collections output/metadata uploads data logs

# 复制配置文件（如果存在）
COPY --chown=appuser:appuser data/settings.example.json ./data/settings.example.json

# 创建健康检查脚本
RUN echo '#!/bin/bash\n\
set -e\n\
# 检查应用端口\n\
curl -f http://localhost:${PORT:-8000}/health > /dev/null 2>&1 || exit 1\n\
# 检查关键目录\n\
[ -d "/app/uploads" ] || exit 1\n\
[ -d "/app/output" ] || exit 1\n\
echo "Health check passed"\n\
exit 0' > /app/health-check.sh && \
    chmod +x /app/health-check.sh

# 设置所有目录和文件的所有权（必须在切换用户前执行）
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 添加标签元数据
LABEL maintainer="AutoClip Team" \
      version="1.0" \
      description="AutoClip AI视频切片系统" \
      org.opencontainers.image.source="https://github.com/zsunny6658/autoclip_mvp"

# 健康检查（使用固定值，因为Docker构建时不支持环境变量）
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
    CMD ["/app/health-check.sh"]

# 启动命令
CMD ["python", "backend_server.py"]
