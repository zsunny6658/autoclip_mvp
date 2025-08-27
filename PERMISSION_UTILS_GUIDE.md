# AutoClip 权限工具库使用指南

## 概述

权限工具库 (`permission-utils.sh`) 是一个统一的权限管理工具，用于处理 AutoClip 项目在不同环境下的权限问题。该工具库提供了一致的接口来修复开发环境和生产环境的权限问题。

## 文件结构

```
permission-utils.sh     # 权限工具库主文件
docker-deploy.sh        # 开发环境部署脚本（使用权限工具库）
docker-deploy-prod.sh   # 生产环境部署脚本（使用权限工具库）
fix-permissions.sh      # 权限修复脚本（使用权限工具库）
fix-docker-permissions.sh # Docker权限修复脚本（使用权限工具库）
```

## 主要功能

### 1. 开发环境权限修复 (`fix_dev_permissions`)

自动处理开发环境所需的目录和文件权限：

- 创建必要的目录结构
- 设置正确的目录权限 (755)
- 创建配置文件 (settings.json, projects.json)
- 设置容器用户权限 (10001:10001)

### 2. 生产环境权限修复 (`fix_prod_permissions`)

自动处理生产环境所需的目录和文件权限：

- 创建生产环境目录结构
- 设置正确的目录权限 (755)
- 设置目录所有者
- 创建生产环境配置文件
- 设置容器用户权限 (10001:10001)

### 3. 权限验证 (`verify_permissions`)

验证关键目录和文件的权限是否正确设置。

## 使用方法

### 在脚本中导入

```bash
# 导入权限工具库
PERMISSION_UTILS_PATH="$(dirname "$0")/permission-utils.sh"
if [ -f "$PERMISSION_UTILS_PATH" ]; then
    source "$PERMISSION_UTILS_PATH"
else
    echo "❌ 无法找到 permission-utils.sh 文件"
    exit 1
fi
```

### 调用权限修复函数

```bash
# 修复开发环境权限
fix_dev_permissions

# 修复生产环境权限
fix_prod_permissions

# 验证权限
verify_permissions
```

## 自动化集成

权限修复功能已集成到以下脚本中：

1. **docker-deploy.sh** - 开发环境一键部署脚本
   - 在设置开发环境时自动修复权限
   - 无需手动运行权限修复脚本

2. **docker-deploy-prod.sh** - 生产环境一键部署脚本
   - 在设置生产环境时自动修复权限
   - 无需手动运行权限修复脚本

3. **fix-permissions.sh** - 独立权限修复脚本
   - 可单独运行以修复权限问题

4. **fix-docker-permissions.sh** - Docker权限修复脚本
   - 可单独运行以修复Docker相关权限问题

## 权限模型

### 目录权限

所有目录设置为 `755` (rwxr-xr-x) 权限：
- 所有者：读、写、执行
- 组用户：读、执行
- 其他用户：读、执行

### 文件权限

配置文件设置为 `644` (rw-r--r--) 权限：
- 所有者：读、写
- 组用户：读
- 其他用户：读

### 容器用户权限

为了与Docker容器中的用户保持一致，所有数据目录都设置为用户ID `10001` 和组ID `10001`：
- 这与Dockerfile中创建的 `appuser` 用户一致
- 避免了容器内外的权限冲突

## 故障排除

### 权限不足错误

如果遇到权限不足的错误，请尝试以下解决方案：

1. **使用sudo运行脚本**：
   ```bash
   sudo ./fix-permissions.sh
   ```

2. **手动创建目录并设置权限**：
   ```bash
   sudo mkdir -p data uploads output input logs
   sudo chown -R $USER:$USER data uploads output input logs
   sudo chmod -R 755 data uploads output input logs
   ```

3. **检查磁盘空间**：
   ```bash
   df -h
   ```

### 容器权限问题

如果容器无法访问数据目录，请检查：

1. **目录所有权**：
   ```bash
   ls -la data/
   # 确保目录所有者为 10001:10001
   ```

2. **重新构建容器**：
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

## 最佳实践

1. **部署时自动修复权限**：
   - 使用 `docker-deploy.sh` 或 `docker-deploy-prod.sh` 进行部署
   - 这些脚本会自动处理权限修复

2. **定期检查权限**：
   - 定期运行 `verify_permissions` 函数检查权限状态

3. **生产环境特殊处理**：
   - 生产环境使用绝对路径
   - 配置文件权限设置为 600 以提高安全性

4. **避免手动修改权限**：
   - 尽量使用脚本自动处理权限
   - 手动修改可能导致不一致

## 更新日志

### v1.0.0
- 初始版本
- 支持开发环境和生产环境权限修复
- 集成到部署脚本中
- 提供独立的权限修复脚本