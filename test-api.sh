#!/bin/bash

# API接口测试脚本
# 用于诊断AutoClip API接口问题

echo "🔍 AutoClip API接口测试"
echo "========================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务器地址
SERVER_URL="http://localhost:8000"

# 测试函数
test_api() {
    local endpoint=$1
    local description=$2
    
    echo -e "${BLUE}[测试]${NC} $description"
    echo "端点: $SERVER_URL$endpoint"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$SERVER_URL$endpoint" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        body=$(echo $response | sed -e 's/HTTPSTATUS\:.*//g')
        
        if [ "$http_code" == "200" ]; then
            echo -e "${GREEN}✓ 成功${NC} (HTTP $http_code)"
            echo "响应: $(echo $body | head -c 100)..."
        else
            echo -e "${RED}✗ 失败${NC} (HTTP $http_code)"
            echo "响应: $body"
        fi
    else
        echo -e "${RED}✗ 连接失败${NC}"
    fi
    echo
}

# 测试服务是否运行
echo -e "${BLUE}[INFO]${NC} 测试AutoClip API服务..."
echo

# 测试基础接口
test_api "/" "根路径"
test_api "/health" "健康检查"

# 测试有问题的接口
test_api "/api/video-categories" "视频分类接口"
test_api "/api/projects" "项目列表接口"

# 测试其他API接口
test_api "/api/browsers/detect" "浏览器检测接口"
test_api "/api/settings" "设置接口"

echo -e "${BLUE}[INFO]${NC} 测试完成！"