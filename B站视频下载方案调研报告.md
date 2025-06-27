# B站视频下载方案调研报告

## 调研目标
为自动切片推荐系统增加通过B站链接下载视频和字幕的能力。

## 测试环境
- 操作系统：macOS 24.5.0
- Python版本：3.10+
- 测试视频：https://www.bilibili.com/video/BV1sDK3zzENZ/

## 技术方案对比

### 1. yt-dlp（推荐方案）

#### 优势
- ✅ **功能最全面**：支持视频、音频、字幕下载
- ✅ **格式支持丰富**：支持多种视频格式和质量选择
- ✅ **活跃维护**：持续更新，支持最新的B站API
- ✅ **字幕支持**：可以下载CC字幕和自动生成字幕
- ✅ **信息提取**：可以获取视频元数据（标题、时长、描述等）
- ✅ **已安装**：系统中已安装yt-dlp 2025.05.22版本

#### 测试结果
```bash
# 成功下载视频
yt-dlp --format 100050+30280 --output downloads/BV1sDK3zzENZ.%(ext)s --merge-output-format mp4 https://www.bilibili.com/video/BV1sDK3zzENZ/

# 获取视频信息
- 标题：你期待被谁认可，就被谁奴役
- 时长：3分47秒
- 分辨率：1440x1080
- 文件大小：14.7MB
- 格式：MP4
```

#### 字幕下载限制
- ⚠️ **需要登录**：B站字幕下载需要用户登录状态
- ⚠️ **需要cookies**：必须提供有效的B站cookies才能下载字幕
- ⚠️ **弹幕字幕**：目前只能获取到弹幕格式的字幕

### 2. you-get

#### 状态
- ❌ **未安装**：系统中未安装you-get
- ❌ **功能有限**：相比yt-dlp功能较少
- ❌ **维护状态**：更新频率较低

### 3. bilibili-api-python

#### 状态
- ❌ **未安装**：系统中未安装bilibili-api-python
- ❌ **编程复杂度**：需要更多编程工作
- ❌ **API限制**：可能受到B站API限制

## 推荐实现方案

### 核心方案：yt-dlp + 字幕处理

#### 1. 视频下载
```python
import subprocess
from pathlib import Path

def download_bilibili_video(url, output_dir="downloads"):
    """下载B站视频"""
    cmd = [
        'yt-dlp',
        '--format', 'best[height<=1080]',  # 选择1080p以下最佳质量
        '--output', f'{output_dir}/%(id)s.%(ext)s',
        '--merge-output-format', 'mp4',
        '--write-info-json',
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.returncode == 0
```

#### 2. 字幕处理策略

##### 方案A：使用cookies登录（推荐）
```python
def download_with_cookies(url, cookies_file, output_dir="downloads"):
    """使用cookies下载视频和字幕"""
    cmd = [
        'yt-dlp',
        '--cookies', cookies_file,
        '--format', 'best[height<=1080]',
        '--write-sub',
        '--write-auto-sub',
        '--sub-lang', 'zh-Hans,zh-CN,zh',
        '--output', f'{output_dir}/%(id)s.%(ext)s',
        '--merge-output-format', 'mp4',
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.returncode == 0
```

##### 方案B：从浏览器获取cookies
```python
def download_with_browser_cookies(url, browser="chrome", output_dir="downloads"):
    """从浏览器获取cookies下载"""
    cmd = [
        'yt-dlp',
        '--cookies-from-browser', browser,
        '--format', 'best[height<=1080]',
        '--write-sub',
        '--write-auto-sub',
        '--sub-lang', 'zh-Hans,zh-CN,zh',
        '--output', f'{output_dir}/%(id)s.%(ext)s',
        '--merge-output-format', 'mp4',
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.returncode == 0
```

##### 方案C：无字幕下载 + 语音识别
```python
def download_video_only(url, output_dir="downloads"):
    """仅下载视频，后续通过语音识别生成字幕"""
    cmd = [
        'yt-dlp',
        '--format', 'best[height<=1080]',
        '--output', f'{output_dir}/%(id)s.%(ext)s',
        '--merge-output-format', 'mp4',
        '--write-info-json',
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    return result.returncode == 0
```

## 集成到现有系统的建议

### 1. 新增依赖
```txt
# requirements.txt 新增
yt-dlp>=2025.05.22
```

### 2. 新增模块结构
```
src/
├── utils/
│   ├── bilibili_downloader.py    # B站下载器
│   └── subtitle_processor.py     # 字幕处理器
├── pipeline/
│   └── step0_download.py         # 新增下载步骤
```

### 3. 用户界面集成
- 在Streamlit界面添加B站链接输入框
- 支持cookies文件上传
- 显示下载进度
- 自动检测视频信息

### 4. 错误处理
- 网络连接失败
- 视频不存在或已删除
- 格式不支持
- cookies无效
- 下载中断

## 实施建议

### 第一阶段：基础视频下载
1. 实现基本的B站视频下载功能
2. 集成到现有项目管理系统
3. 测试各种视频格式的兼容性

### 第二阶段：字幕支持
1. 实现cookies管理功能
2. 支持字幕下载和格式转换
3. 添加字幕质量检测

### 第三阶段：用户体验优化
1. 添加下载进度显示
2. 支持批量下载
3. 优化错误提示和处理

## 技术风险

### 1. B站API变化
- **风险**：B站可能更新API，导致下载失败
- **缓解**：使用yt-dlp等成熟工具，有社区维护

### 2. 法律合规
- **风险**：下载视频可能涉及版权问题
- **缓解**：仅用于个人学习和研究，不用于商业用途

### 3. 网络限制
- **风险**：B站可能限制下载频率
- **缓解**：添加下载间隔和重试机制

## 结论

**推荐使用yt-dlp作为核心下载工具**，原因如下：

1. **功能完整**：支持视频、音频、字幕下载
2. **稳定可靠**：有活跃的社区维护
3. **易于集成**：命令行工具，易于在Python中调用
4. **格式丰富**：支持多种视频格式和质量选择

**字幕下载建议采用方案A（cookies登录）**，这是最可靠的方式，可以获取到完整的字幕信息。

**实施优先级**：
1. 高优先级：基础视频下载功能
2. 中优先级：字幕下载支持
3. 低优先级：用户体验优化

该方案可以很好地集成到现有的自动切片推荐系统中，为用户提供更便捷的视频获取方式。 