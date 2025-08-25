# Docker权限问题解决方案

## 问题描述

Docker部署后发现`data`、`input`、`logs`、`output`、`uploads`等目录的所有权不是`appuser`，而是其他用户ID（如1000:1001或root:root），导致应用无法正常访问这些目录。

```bash
# 问题示例
drwxr-xr-x+ 1    1000    1001   134 Aug 25 13:26 data
drwxr-xr-x+ 1 root    root        0 Aug 25 13:27 input
drwxr-xr-x+ 1 root    root        0 Aug 25 13:27 logs
```

## 解决方案

### 1. Dockerfile 修改

**主要变更：**
- 设置高位的用户ID和组ID (10001:10001)
- 在创建目录时立即设置正确的权限
- 添加启动脚本来监控权限状态

```dockerfile
# 创建应用用户（安全最佳实践）
# 使用高位UID/GID避免与宿主机用户冲突
RUN groupadd -r -g 10001 appuser && useradd -r -g appuser -u 10001 appuser

# 创建必要的目录并设置正确的权限
RUN mkdir -p input output/clips output/collections output/metadata uploads data logs && \
    chown -R appuser:appuser input output uploads data logs
```

### 2. Docker Compose 配置修改

**主要变更：**
- 添加`user: "10001:10001"`参数
- 添加`init: true`提升进程管理

```yaml
services:
  autoclip:
    # 设置用户ID以解决权限问题
    user: "10001:10001"
    # 使用init进程处理信号
    init: true
```

### 3. 权限修复脚本

提供了两个修复脚本：

#### 3.1 `fix-docker-permissions.sh` (需要root权限)
- 全面的权限修复，包括本地目录权限
- 自动重建Docker容器
- 适用于生产环境部署

#### 3.2 `fix-docker-permissions-simple.sh` (无需root权限)  
- 创建必要目录和配置文件
- 检查Docker Compose配置
- 重建容器以应用修复

### 4. 验证脚本

#### `test-docker-permissions.sh`
验证权限修复效果：
- 检查容器内目录权限
- 测试文件创建权限
- 验证API服务状态

## 使用方法

### 快速修复

1. **使用简单修复脚本**（推荐）：
```bash
./fix-docker-permissions-simple.sh
```

2. **使用完整修复脚本**（需要sudo）：
```bash
sudo ./fix-docker-permissions.sh
```

### 手动修复

1. **停止现有容器**：
```bash
docker-compose down
```

2. **创建必要目录**：
```bash
mkdir -p data input output uploads logs
```

3. **重建并启动容器**：
```bash
docker-compose up --build -d
```

### 验证修复

运行验证脚本：
```bash
./test-docker-permissions.sh
```

## 技术原理

### 问题根因
1. **Docker卷挂载覆盖**：Docker Compose的卷挂载会覆盖容器内目录的权限设置
2. **用户ID不匹配**：容器内的appuser与宿主机用户ID不一致
3. **权限继承**：挂载的目录继承了宿主机的权限设置

### 解决原理
1. **高位用户ID**：容器内appuser使用高位UID/GID (10001:10001)，避免与宿主机常用用户冲突
2. **Docker Compose用户配置**：通过`user`参数确保容器以正确用户身份运行
3. **权限预设**：在Dockerfile中预先设置目录权限

## 文件变更清单

### 修改的文件
- `Dockerfile` - 用户创建和权限设置
- `docker-compose.yml` - 添加user和init配置  
- `docker-compose.prod.yml` - 生产环境配置同步

### 新增的文件
- `fix-docker-permissions.sh` - 完整权限修复脚本
- `fix-docker-permissions-simple.sh` - 简单权限修复脚本
- `test-docker-permissions.sh` - 权限验证脚本
- `DOCKER_PERMISSIONS_FIX.md` - 此说明文档

## 常见问题

### Q: 修复后容器无法启动
**A:** 检查以下项目：
1. 确认本地目录存在：`ls -la data input output uploads logs`
2. 检查Docker Compose语法：`docker-compose config`
3. 查看容器日志：`docker-compose logs autoclip`

### Q: API仍然无法访问文件
**A:** 验证容器内权限：
```bash
docker exec $(docker-compose ps -q autoclip) ls -la /app/
```

### Q: 在不同系统上部署时权限不同
**A:** 使用固定的UID/GID配置，避免依赖系统默认用户ID。

## 最佳实践

1. **始终使用固定用户ID**：避免跨环境的权限问题
2. **配置Docker Compose用户参数**：确保容器以正确身份运行
3. **验证修复效果**：使用提供的测试脚本验证
4. **文档化权限配置**：为团队成员提供清晰的部署说明

## 相关资源

- [Docker官方权限配置文档](https://docs.docker.com/engine/reference/builder/#user)
- [Docker Compose用户配置](https://docs.docker.com/compose/compose-file/05-services/#user)
- 项目的其他Docker相关文档：`DOCKER_GUIDE.md`