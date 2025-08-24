# AutoClip Docker 部署与故障排除指南

## 目录
- [快速开始](#快速开始)
- [Docker 构建优化](#docker-构建优化)
- [常见问题与解决方案](#常见问题与解决方案)
- [部署配置](#部署配置)
- [故障排除](#故障排除)
- [维护与更新](#维护与更新)

## 快速开始

### 环境要求
- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ 可用内存
- 5GB+ 可用磁盘空间

### 一键部署
```bash
# 开发环境
./docker-deploy.sh

# 生产环境
./docker-deploy-prod.sh
```

### 手动部署
```bash
# 1. 复制环境配置
cp env.example .env

# 2. 编辑环境变量（必须配置API密钥）
vim .env

# 3. 构建并启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

## Docker 构建优化

### 多阶段构建架构
```
前端构建阶段 (node:20-alpine) → 生产环境 (python:3.11-slim)
     ↓                              ↓
  构建React应用                   运行FastAPI服务
  优化资源文件                   集成前端资源
  清理构建缓存                   配置运行环境
```

### 关键优化策略

1. **Alpine Linux 网络配置**
   - 更新证书存储：`ca-certificates`
   - 移除已废弃的 `libc6-compat` 包
   - 添加 Git 支持构建过程

2. **依赖同步机制**
   ```dockerfile
   # 智能依赖管理
   RUN set -e; \
       if [ ! -f package-lock.json ]; then \
           npm install; \
       elif ! npm ci --frozen-lockfile 2>/dev/null; then \
           rm -f package-lock.json; \
           npm install; \
       fi
   ```

3. **安全配置**
   - 非root用户运行：`appuser`
   - 最小权限原则
   - 清理敏感信息

## 常见问题与解决方案

### 网络连接问题

**症状**：SSL错误或包下载失败
```
ERROR: unable to select packages: libc6-compat (no such package)
SSL routines::unexpected eof while reading
```

**解决方案**：
1. 更新Docker镜像源
2. 配置代理（如需要）
3. 使用最新版Alpine基础镜像

### 依赖同步问题

**症状**：前端构建失败，版本冲突
```
npm ERR! peer dep missing: @typescript-eslint/eslint-plugin@^7.18.0
```

**解决方案**：
1. 删除lock文件重新生成
2. 统一TypeScript版本
3. 使用智能依赖检查脚本

### API函数参数错误

**症状**：API函数调用参数数量不匹配
```
error TS2554: Expected 2 arguments, but got 3
```

**解决方案**：
1. 检查API函数定义的参数数量
2. 修正所有调用处的参数数量
3. 移除多余的参数（如title参数）

### TypeScript编译错误

**症状**：前端构建失败，类型检查错误
```
error TS2554: Expected 2 arguments, but got 3
error TS2367: This comparison appears to be unintentional
```

**解决方案**：
1. 为parseInt调用添加进制参数
2. 修复类型比较逻辑
3. 使用类型窄化处理联合类型

### 内存不足

**症状**：构建过程中断，OOM错误
**解决方案**：
1. 增加Docker内存限制
2. 分阶段构建减少并发
3. 清理构建缓存

## 部署配置

### 开发环境
```yaml
# docker-compose.yml
services:
  autoclip:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./output:/app/output
    environment:
      - NODE_ENV=development
```

### 生产环境
```yaml
# docker-compose.prod.yml
services:
  autoclip:
    image: autoclip:latest
    restart: unless-stopped
    networks:
      - autoclip-network
    healthcheck:
      test: ["CMD-SHELL", "/app/health-check.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 环境变量配置
```bash
# .env 文件示例
DASHSCOPE_API_KEY=your_dashscope_key
SILICONFLOW_API_KEY=your_siliconflow_key
LLM_PROVIDER=dashscope
PORT=8000
LOG_LEVEL=INFO
```

## 故障排除

### 诊断工具

1. **检查Docker状态**
   ```bash
   ./test-docker.sh
   ```

2. **查看容器日志**
   ```bash
   docker-compose logs -f autoclip
   ```

3. **进入容器调试**
   ```bash
   docker-compose exec autoclip bash
   ```

### 常见错误代码

| 错误类型 | 错误消息 | 解决方案 |
|---------|---------|---------|
| 网络错误 | SSL routines error | 更新证书，检查网络 |
| 构建失败 | npm ci failed | 删除lock文件重新生成 |
| 权限错误 | Permission denied | 检查文件权限，使用正确用户 |
| 端口冲突 | Port already in use | 修改端口或停止冲突服务 |
| 内存不足 | OOM killed | 增加内存限制或优化代码 |

### 修复步骤

1. **网络问题修复**
   ```bash
   # 更新Docker镜像
   docker pull node:20-alpine
   docker pull python:3.11-slim
   
   # 清理构建缓存
   docker builder prune -f
   ```

2. **依赖问题修复**
   ```bash
   # 重新构建（无缓存）
   docker-compose build --no-cache
   
   # 强制重新创建容器
   docker-compose up --force-recreate
   ```

3. **完全重置**
   ```bash
   # 停止所有容器
   docker-compose down -v
   
   # 清理所有数据
   docker system prune -a -f
   
   # 重新部署
   ./docker-deploy.sh
   ```

## 维护与更新

### 日常维护
```bash
# 查看资源使用
docker stats

# 清理日志
docker-compose logs --tail=0 -f

# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz uploads/ output/ data/
```

### 更新流程
```bash
# 1. 备份数据
./backup.sh

# 2. 停止服务
docker-compose down

# 3. 拉取最新代码
git pull origin main

# 4. 重新构建
docker-compose build

# 5. 启动服务
docker-compose up -d

# 6. 验证服务
curl http://localhost:8000/health
```

### 性能优化
1. **定期清理**
   - 删除临时文件
   - 清理Docker缓存
   - 压缩日志文件

2. **监控指标**
   - CPU使用率 < 70%
   - 内存使用率 < 80%
   - 磁盘使用率 < 85%

3. **扩容策略**
   - 水平扩容：多实例部署
   - 垂直扩容：增加资源配置
   - 负载均衡：分散请求压力

## 技术支持

### 获取帮助
1. 查看日志：`docker-compose logs`
2. 检查状态：`./test-docker.sh`
3. 重启服务：`docker-compose restart`
4. 完全重置：`./docker-deploy.sh`

### 联系方式
- 项目地址：https://github.com/zsunny6658/autoclip_mvp
- 问题反馈：GitHub Issues
- 文档更新：欢迎PR贡献

---
**最后更新**：2024-08-24
**版本**：v1.0