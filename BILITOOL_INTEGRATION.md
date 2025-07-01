# Bilitool 集成使用指南

本文档介绍如何使用集成了 bilitool 的 B站视频上传功能。

## 安装依赖

### 方法1: 使用虚拟环境 (推荐)

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install bilitool
pip install -r requirements.txt
```

### 方法2: 使用 pipx

```bash
brew install pipx
pipx install bilitool
```

### 方法3: 强制安装到用户目录 (不推荐)

```bash
pip3 install --user --break-system-packages bilitool
```

## 基本使用

### 1. 初始化上传管理器

```python
from src.upload.upload_manager import UploadManager, Platform

# 创建上传管理器
upload_manager = UploadManager()
```

### 2. B站登录

```python
# 交互式登录（推荐）
success = upload_manager.set_bilibili_credential(export_cookies=True)
if success:
    print("登录成功")
else:
    print("登录失败")

# 验证登录状态
is_valid = await upload_manager.verify_platform_credential(Platform.BILIBILI)
print(f"登录状态: {is_valid}")
```

### 3. 获取B站分区信息

```python
# 获取所有分区
categories = upload_manager.get_platform_categories(Platform.BILIBILI)
for category in categories:
    print(f"{category['tid']}: {category['name']} - {category['desc']}")
```

### 4. 上传单个视频

```python
import asyncio

async def upload_single_video():
    # 创建上传任务
    task = await upload_manager.create_upload_task(
        task_id="video_001",
        platform=Platform.BILIBILI,
        video_path="/path/to/your/video.mp4",
        title="你的视频标题",
        desc="视频描述内容",
        tags=["标签1", "标签2", "标签3"],
        tid=21,  # 日常分区
        cover_path="/path/to/cover.jpg",  # 可选封面
        auto_start=True  # 自动开始上传
    )
    
    # 等待上传完成
    while True:
        status = upload_manager.get_task_status(task.task_id)
        if status['status'] in ['success', 'failed', 'cancelled']:
            break
        await asyncio.sleep(5)  # 等待5秒后再检查
    
    print(f"上传结果: {status['status']}")
    if status['status'] == 'success':
        print(f"上传成功: {status['result']}")
    else:
        print(f"上传失败: {status['error']}")

# 运行上传
asyncio.run(upload_single_video())
```

### 5. 批量上传切片视频

```python
async def upload_clips_batch(clips_info):
    """批量上传切片视频
    
    Args:
        clips_info: 切片信息列表，每个元素包含 path, title, desc, tags 等
    """
    tasks = []
    
    # 创建所有上传任务
    for i, clip in enumerate(clips_info):
        task = await upload_manager.create_upload_task(
            task_id=f"clip_{i:03d}",
            platform=Platform.BILIBILI,
            video_path=clip['path'],
            title=clip['title'],
            desc=clip.get('desc', ''),
            tags=clip.get('tags', []),
            tid=clip.get('tid', 21),  # 默认日常分区
            auto_start=False  # 先不自动开始
        )
        tasks.append(task)
    
    # 逐个开始上传（避免并发过多）
    for task in tasks:
        await upload_manager.start_upload(task.task_id)
        print(f"开始上传: {task.title}")
        
        # 可以选择等待当前任务完成再开始下一个
        # 或者并发上传多个任务
        await asyncio.sleep(2)  # 间隔2秒
    
    # 监控所有任务状态
    while True:
        all_tasks = upload_manager.get_all_tasks()
        active_tasks = [t for t in all_tasks if t['status'] == 'uploading']
        
        if not active_tasks:
            break  # 所有任务都完成了
            
        print(f"还有 {len(active_tasks)} 个任务在上传中...")
        await asyncio.sleep(10)
    
    # 输出最终结果
    final_tasks = upload_manager.get_all_tasks()
    success_count = len([t for t in final_tasks if t['status'] == 'success'])
    failed_count = len([t for t in final_tasks if t['status'] == 'failed'])
    
    print(f"批量上传完成: 成功 {success_count} 个，失败 {failed_count} 个")

# 示例切片信息
clips = [
    {
        'path': '/path/to/clip1.mp4',
        'title': '精彩片段1：开场白',
        'desc': '这是开场白的精彩片段',
        'tags': ['精彩', '开场', '片段'],
        'tid': 21
    },
    {
        'path': '/path/to/clip2.mp4',
        'title': '精彩片段2：高潮部分',
        'desc': '这是高潮部分的精彩片段',
        'tags': ['精彩', '高潮', '片段'],
        'tid': 21
    }
]

# 运行批量上传
asyncio.run(upload_clips_batch(clips))
```

### 6. 分P投稿（追加视频到已有视频）

```python
async def append_to_collection():
    """将相关切片追加到主视频作为分P"""
    
    # 首先上传主视频
    main_task = await upload_manager.create_upload_task(
        task_id="main_video",
        platform=Platform.BILIBILI,
        video_path="/path/to/main_video.mp4",
        title="完整视频合集",
        desc="这是完整的视频内容",
        tags=["合集", "完整版"],
        tid=21,
        auto_start=True
    )
    
    # 等待主视频上传完成
    while True:
        status = upload_manager.get_task_status(main_task.task_id)
        if status['status'] == 'success':
            main_bvid = status['result'].get('bvid')
            break
        elif status['status'] in ['failed', 'cancelled']:
            print("主视频上传失败")
            return
        await asyncio.sleep(5)
    
    print(f"主视频上传成功，BV号: {main_bvid}")
    
    # 追加相关切片
    uploader = upload_manager.uploaders[Platform.BILIBILI]
    
    related_clips = [
        "/path/to/clip1.mp4",
        "/path/to/clip2.mp4",
        "/path/to/clip3.mp4"
    ]
    
    for clip_path in related_clips:
        result = await uploader.append_video_to_collection(
            video_path=clip_path,
            bvid=main_bvid
        )
        
        if result['success']:
            print(f"成功追加: {clip_path}")
        else:
            print(f"追加失败: {clip_path} - {result['error']}")

# 运行分P投稿
asyncio.run(append_to_collection())
```

## 常用分区ID参考

| 分区ID | 分区名称 | 说明 |
|--------|----------|------|
| 21 | 日常 | 日常生活内容 |
| 17 | 单机游戏 | 单机游戏相关 |
| 171 | 电子竞技 | 电竞相关内容 |
| 36 | 知识 | 知识分享 |
| 188 | 科技 | 科技相关内容 |
| 160 | 生活 | 生活相关内容 |
| 138 | 搞笑 | 搞笑内容 |
| 122 | 野生技能协会 | 技能分享 |

## 错误处理

```python
try:
    # 上传操作
    task = await upload_manager.create_upload_task(...)
except FileNotFoundError:
    print("视频文件不存在")
except ValueError as e:
    print(f"参数错误: {e}")
except RuntimeError as e:
    print(f"运行时错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 注意事项

1. **首次使用需要交互式登录**：bilitool 需要用户扫码或输入账号密码进行登录
2. **登录状态持久化**：登录成功后会保存登录状态，下次使用无需重新登录
3. **视频格式要求**：建议使用 MP4 格式，分辨率不超过 1080p
4. **标题和描述限制**：标题最多80字符，描述最多2000字符
5. **标签限制**：最多12个标签
6. **上传速度**：bilitool 会自动选择最佳上传线路
7. **并发限制**：建议不要同时上传过多视频，避免触发平台限制

## 集成到现有项目

在你的切片生成流水线中，可以在最后一步添加上传功能：

```python
# 在 src/pipeline/step6_video.py 中添加
from ..upload.upload_manager import UploadManager, Platform

async def upload_generated_clips(clips_data, upload_config):
    """上传生成的切片视频"""
    upload_manager = UploadManager()
    
    # 验证登录状态
    if not await upload_manager.verify_platform_credential(Platform.BILIBILI):
        print("请先登录B站账号")
        return False
    
    # 批量上传
    for clip in clips_data:
        await upload_manager.create_upload_task(
            task_id=clip['id'],
            platform=Platform.BILIBILI,
            video_path=clip['output_path'],
            title=clip['title'],
            desc=clip['description'],
            tags=clip['tags'],
            tid=upload_config.get('tid', 21)
        )
    
    return True
```

这样就完成了 bilitool 的集成，可以实现一键上传切片视频到B站！