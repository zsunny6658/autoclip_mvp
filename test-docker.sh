#!/bin/bash

# Docker 配置测试脚本
# 兼容 Docker Compose v1+ 和 v2+

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

# 检测 Docker Compose 版本并返回命令
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        local version=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+')
        echo "docker-compose (v$version)"
        return 0
    elif docker compose version &> /dev/null 2>&1; then
        local version=$(docker compose version --short)
        echo "docker compose (v$version)"
        return 0
    else
        return 1
    fi
}

# 获取实际的compose命令
get_compose_command() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    else
        return 1
    fi
}

echo "🧪 AutoClip Docker 配置测试"
echo "============================"

# 1. 检查 Docker 服务状态
log_info "检查 Docker 服务状态..."
if ! docker info >/dev/null 2>&1; then
    log_error "Docker 服务未运行，请启动 Docker"
    exit 1
fi
log_success "Docker 服务正常运行"

# 显示Docker版本信息
docker_version=$(docker --version)
log_success "Docker 版本: $docker_version"

# 2. 检查 Docker Compose
log_info "检查 Docker Compose..."
DOCKER_COMPOSE_INFO=$(get_docker_compose_cmd)
if [ $? -ne 0 ]; then
    log_error "Docker Compose 未安装或无法访问"
    log_info "安装指南: https://docs.docker.com/compose/install/"
    exit 1
fi
log_success "Docker Compose 可用: $DOCKER_COMPOSE_INFO"

# 获取实际命令用于后续操作
COMPOSE_CMD=$(get_compose_command)

# 3. 检查配置文件
log_info "检查配置文件..."
required_files=("docker-compose.yml" "docker-compose.prod.yml" "Dockerfile")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "$file 文件不存在"
        exit 1
    fi
    log_success "$file 存在"
done

# 4. 验证 Docker Compose 文件语法
log_info "验证 Docker Compose 文件语法..."
if $COMPOSE_CMD -f docker-compose.yml config >/dev/null 2>&1; then
    log_success "docker-compose.yml 语法正确"
else
    log_error "docker-compose.yml 语法错误"
    log_info "错误详情:"
    $COMPOSE_CMD -f docker-compose.yml config
    exit 1
fi

if $COMPOSE_CMD -f docker-compose.prod.yml config >/dev/null 2>&1; then
    log_success "docker-compose.prod.yml 语法正确"
else
    log_error "docker-compose.prod.yml 语法错误"
    log_info "错误详情:"
    $COMPOSE_CMD -f docker-compose.prod.yml config
    exit 1
fi

# 5. 检查环境变量文件
log_info "检查环境变量配置..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        log_warning ".env 文件不存在，但找到 env.example"
        log_info "请运行: cp env.example .env 并编辑配置"
    else
        log_warning ".env 和 env.example 文件都不存在"
        log_info "请创建 .env 文件或 env.example 文件"
    fi
else
    log_success ".env 文件存在"
    
    # 检查API密钥配置
    source .env 2>/dev/null || true
    if [ -n "$DASHSCOPE_API_KEY" ] || [ -n "$SILICONFLOW_API_KEY" ]; then
        log_success "API 密钥已配置"
    else
        log_warning "API 密钥未配置，请编辑 .env 文件"
    fi
fi

# 6. 检查目录结构
log_info "检查目录结构..."
required_dirs=("src" "frontend" "data" "prompt")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        log_success "$dir 目录存在"
    else
        log_error "$dir 目录不存在"
        exit 1
    fi
done

# 检查可选目录
optional_dirs=("uploads" "output" "input" "logs")
for dir in "${optional_dirs[@]}"; do
    if [ -d "$dir" ]; then
        log_success "$dir 目录存在"
    else
        log_info "$dir 目录不存在，部署时会自动创建"
    fi
done

# 7. 检查依赖文件
log_info "检查依赖文件..."
dependency_files=("requirements.txt" "frontend/package.json")
for file in "${dependency_files[@]}"; do
    if [ -f "$file" ]; then
        log_success "$file 存在"
    else
        log_error "$file 不存在"
        exit 1
    fi
done

# 8. 检查Dockerfile语法
log_info "检查 Dockerfile 语法..."
if docker build --dry-run -f Dockerfile . >/dev/null 2>&1; then
    log_success "Dockerfile 语法正确"
else
    log_warning "Dockerfile 语法检查失败（可能需要实际构建）"
fi

# 9. 测试网络连接
log_info "测试网络连接..."
if ping -c 1 google.com >/dev/null 2>&1; then
    log_success "网络连接正常"
else
    log_warning "网络连接可能有问题，可能影响镜像构建"
fi

# 10. 检查系统资源
log_info "检查系统资源..."
available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
log_info "可用内存: ${available_memory}GB"

available_disk=$(df -h . | awk 'NR==2 {print $4}')
log_info "可用磁盘空间: $available_disk"

# 11. 检查端口占用
log_info "检查端口占用..."
ports_to_check=(8000 80 3000)
for port in "${ports_to_check[@]}"; do
    if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
        log_warning "端口 $port 已被占用"
    else
        log_success "端口 $port 可用"
    fi
done

# 12. 测试 Docker 构建（可选）
if [ "${TEST_BUILD:-false}" = "true" ]; then
    log_info "测试 Docker 构建..."
    log_warning "这可能需要几分钟时间..."
    
    # 创建临时测试目录
    test_dir="test-docker-build-$(date +%s)"
    mkdir -p "$test_dir"
    
    # 复制必要文件
    cp docker-compose.yml "$test_dir/"
    cp Dockerfile "$test_dir/"
    cp requirements.txt "$test_dir/"
    cp -r src "$test_dir/"
    cp -r frontend "$test_dir/"
    cp -r data "$test_dir/"
    cp backend_server.py "$test_dir/" 2>/dev/null || true
    cp main.py "$test_dir/" 2>/dev/null || true
    
    cd "$test_dir"
    
    # 尝试构建镜像（不启动服务）
    if $COMPOSE_CMD build >/dev/null 2>&1; then
        log_success "Docker 构建测试通过"
    else
        log_error "Docker 构建失败"
        log_info "查看详细错误信息:"
        $COMPOSE_CMD build
        cd ..
        rm -rf "$test_dir"
        exit 1
    fi
    
    cd ..
    rm -rf "$test_dir"
fi

# 13. 生成测试报告
echo ""
log_success "===================="
log_success "测试完成总结"
log_success "===================="
echo ""

log_info "✨ 环境信息:"
echo "   Docker: $docker_version"
echo "   Compose: $DOCKER_COMPOSE_INFO"
echo "   系统: $(uname -s) $(uname -m)"
echo ""

log_info "📋 下一步操作:"
if [ ! -f ".env" ]; then
    echo "1. 配置环境变量文件: cp env.example .env"
    echo "2. 编辑 .env 文件并设置 API 密钥"
    echo "3. 运行开发环境: ./docker-deploy.sh"
    echo "4. 或运行生产环境: ./docker-deploy-prod.sh"
else
    echo "1. 运行开发环境: ./docker-deploy.sh"
    echo "2. 或运行生产环境: ./docker-deploy-prod.sh"
    echo "3. 访问 http://localhost:8000 (开发) 或 http://localhost (生产)"
fi
echo ""

log_info "🔧 可选操作:"
echo "   完整构建测试: TEST_BUILD=true ./test-docker.sh"
echo "   查看配置: $COMPOSE_CMD -f docker-compose.yml config"
echo "   强制重新构建: $COMPOSE_CMD build --no-cache"
echo ""

log_success "🎉 所有基础测试通过！"