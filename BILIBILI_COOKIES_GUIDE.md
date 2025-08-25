# Bilibili Cookies 配置指南

## 概述

AutoClip 支持从 B 站下载视频，为了提高下载成功率和访问需要登录的视频，可以配置 Bilibili cookies。本指南详细说明了如何在 Docker 环境中配置和使用 Bilibili cookies。

## 文件位置

- **外部文件位置**: `../bilibili_cookies.txt` (与项目目录同级)
- **容器内位置**: `/app/data/bilibili_cookies.txt`
- **本地映射位置**: `./data/bilibili_cookies.txt`

## 配置步骤

### 1. 从浏览器获取 Cookies

#### 方法A：使用浏览器扩展（推荐）
1. 安装 "Get cookies.txt LOCALLY" 扩展
2. 访问 bilibili.com 并确保已登录
3. 点击扩展图标，选择"Export"
4. 保存为 `bilibili_cookies.txt`

#### 方法B：手动复制原始 Cookies（新增支持）
1. 在 bilibili.com 上打开开发者工具 (F12)
2. 转到 Application/存储 → Cookies → https://www.bilibili.com
3. 选中并复制所有cookies（可以直接复制一整行）
4. 将复制的内容保存为 `bilibili_cookies.txt`

**原始 cookies 字符串格式示例**：
```
SESSDATA=your_sessdata_here; bili_jct=your_bili_jct_here; DedeUserID=12345678; DedeUserID__ckMd5=your_ckmd5_here; _uuid=your_uuid_here
```

#### 方法C：手动创建 Netscape 格式
按照 Netscape 格式手动创建：
```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	FALSE	1735689600	SESSDATA	your_sessdata_value
.bilibili.com	TRUE	/	FALSE	1735689600	bili_jct	your_bili_jct_value
.bilibili.com	TRUE	/	FALSE	1735689600	DedeUserID	12345678
```

### 2. 放置 Cookies 文件

将导出的 `bilibili_cookies.txt` 文件放置在与 autoclip_mvp 项目目录同级的位置：

```
parent_directory/
├── autoclip_mvp/          # 项目目录
│   ├── docker-deploy.sh
│   ├── Dockerfile
│   └── ...
└── bilibili_cookies.txt   # cookies文件放这里
```

### 3. 使用管理脚本

提供了便捷的管理脚本来处理 cookies 文件，**支持自动格式转换**：

```bash
# 检查 cookies 文件状态
./manage-bilibili-cookies.sh status

# 预览转换结果（不修改文件）
./manage-bilibili-cookies.sh convert

# 复制并自动转换外部 cookies 文件到项目内部
./manage-bilibili-cookies.sh copy

# 验证 cookies 文件格式
./manage-bilibili-cookies.sh validate

# 清理内部 cookies 文件
./manage-bilibili-cookies.sh clean

# 查看帮助信息
./manage-bilibili-cookies.sh help
```

**支持的 cookies 格式**：
- ✅ **Netscape 格式**：标准的 cookies.txt 格式
- ✅ **Tab 分隔格式**：缺少头部的 cookies 数据
- ✅ **原始浏览器字符串**：分号分隔的 cookies 字符串
- ❌ JSON 格式：暂不支持（需要手动转换）

### 4. 部署应用

```bash
# 开发环境部署
./docker-deploy.sh

# 生产环境部署
./docker-deploy-prod.sh
```

## 自动化处理

部署脚本会自动处理 cookies 文件：

1. **检测外部文件**: 自动检查 `../bilibili_cookies.txt` 是否存在
2. **自动复制**: 如果外部文件存在，会自动复制到项目内部
3. **权限设置**: 自动设置正确的文件权限
4. **容器挂载**: 通过 Docker volume 挂载到容器内部

## 环境变量配置

可以通过环境变量自定义 cookies 配置：

```bash
# .env 文件中的配置
BILIBILI_COOKIES_FILE=/app/data/bilibili_cookies.txt
CONTAINER_MODE=auto
SKIP_BROWSER_COOKIES_IN_CONTAINER=true
DEFAULT_BROWSER=chrome
```

## 容器环境适配

系统会自动检测容器环境并适配：

- **容器环境**: 使用 cookies 文件而不是浏览器 cookies
- **本地环境**: 优先使用浏览器 cookies
- **自动检测**: 通过 `/.dockerenv` 等标识文件自动判断环境

## 故障排除

### 1. Cookies 文件未找到

**问题**: 部署时提示 cookies 文件不存在

**解决方案**:
```bash
# 检查文件位置
ls -la ../bilibili_cookies.txt

# 使用管理脚本检查状态
./manage-bilibili-cookies.sh status

# 手动复制
./manage-bilibili-cookies.sh copy
```

### 2. 权限问题

**问题**: 容器内无法访问 cookies 文件

**解决方案**:
```bash
# 检查文件权限
ls -la data/bilibili_cookies.txt

# 修复权限
chmod 644 data/bilibili_cookies.txt

# 重新部署
./docker-deploy.sh
```

### 3. Cookies 格式错误

**问题**: cookies 文件格式不正确

**解决方案**:
```bash
# 验证 cookies 格式
./manage-bilibili-cookies.sh validate

# 重新从浏览器导出
# 确保使用正确的 cookies.txt 格式
```

### 4. 下载仍然失败

**问题**: 配置了 cookies 但下载仍失败

**解决方案**:
1. 检查 cookies 是否过期
2. 重新登录 B 站并导出新的 cookies
3. 确认 SESSDATA 等关键 cookies 存在
4. 检查视频是否需要特殊权限

## 日志和监控

### 查看容器日志
```bash
# 查看实时日志
docker-compose logs -f autoclip

# 查看 B 站下载相关日志
docker-compose logs autoclip | grep -i bilibili
```

### 容器内检查
```bash
# 进入容器
docker-compose exec autoclip bash

# 检查 cookies 文件
ls -la /app/data/bilibili_cookies.txt
cat /app/data/bilibili_cookies.txt

# 检查环境变量
env | grep -i bilibili
```

## 安全注意事项

1. **文件权限**: cookies 文件包含敏感信息，确保权限设置正确
2. **定期更新**: cookies 会过期，需要定期更新
3. **备份**: 建议备份有效的 cookies 文件
4. **生产环境**: 生产环境中使用更严格的权限 (600)

## 最佳实践

1. **定期检查**: 定期使用管理脚本检查 cookies 状态
2. **自动化**: 将 cookies 更新流程自动化
3. **监控**: 监控下载成功率，及时发现 cookies 问题
4. **文档**: 记录 cookies 来源和更新时间

## 相关文件

- `manage-bilibili-cookies.sh` - Cookies 管理脚本
- `docker-deploy.sh` - 开发环境部署脚本
- `docker-deploy-prod.sh` - 生产环境部署脚本
- `docker-compose.yml` - 开发环境配置
- `docker-compose.prod.yml` - 生产环境配置
- `src/utils/bilibili_downloader.py` - B 站下载器实现