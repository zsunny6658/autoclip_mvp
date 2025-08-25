#!/usr/bin/env python3
"""
B站视频下载器 - 基于yt-dlp实现B站视频和字幕下载
集成到自动切片工具项目中
"""

import os
import re
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import yt_dlp
import subprocess

try:
    from .error_handler import FileIOError, ValidationError, ProcessingError
except ImportError:
    # 独立运行时的导入
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.error_handler import FileIOError, ValidationError, ProcessingError

logger = logging.getLogger(__name__)

class BilibiliVideoInfo:
    """B站视频信息类"""
    def __init__(self, info_dict: Dict[str, Any]):
        self.bvid = info_dict.get('id', '')
        self.title = info_dict.get('title', 'unknown_video')
        self.duration = info_dict.get('duration', 0)
        self.uploader = info_dict.get('uploader', 'unknown')
        self.description = info_dict.get('description', '')
        self.thumbnail_url = info_dict.get('thumbnail', '')
        self.view_count = info_dict.get('view_count', 0)
        self.upload_date = info_dict.get('upload_date', '')
        self.webpage_url = info_dict.get('webpage_url', '')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'bvid': self.bvid,
            'title': self.title,
            'duration': self.duration,
            'uploader': self.uploader,
            'description': self.description,
            'thumbnail_url': self.thumbnail_url,
            'view_count': self.view_count,
            'upload_date': self.upload_date,
            'webpage_url': self.webpage_url
        }

class BilibiliDownloader:
    """
B站视频下载器
    """
    
    def __init__(self, download_dir: Optional[Path] = None, browser: Optional[str] = None, settings: Optional[Dict[str, Any]] = None):
        """
        初始化下载器
        
        Args:
            download_dir: 下载目录，默认为当前目录
            browser: 浏览器类型，用于获取cookies
            settings: 配置信息
        """
        self.download_dir = download_dir or Path.cwd()
        self.browser = browser
        self.settings = settings or {}
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 检测容器环境
        self.is_container = self._detect_container_environment()
        
        # 获取cookies配置
        self.cookies_file = self.settings.get('bilibili_cookies_file', '/app/data/bilibili_cookies.txt')
        self.skip_browser_cookies = self.settings.get('skip_browser_cookies_in_container', True)
        
        # 记录环境信息
        if self.is_container:
            logger.info(f"检测到容器环境，cookies文件路径: {self.cookies_file}")
            if self.skip_browser_cookies:
                logger.info("容器环境中将跳过--cookies-from-browser参数")
        else:
            logger.info("检测到本地环境，将使用浏览器cookies")
    
    def _detect_container_environment(self) -> bool:
        """
        检测是否在容器环境中运行
        
        Returns:
            是否在容器环境中
        """
        # 检查常见的容器环境标识
        container_indicators = [
            Path('/.dockerenv'),  # Docker环境标识文件
            Path('/run/.containerenv'),  # Podman环境标识文件
        ]
        
        for indicator in container_indicators:
            if indicator.exists():
                return True
        
        # 检查环境变量
        if os.getenv('CONTAINER_MODE') == 'true':
            return True
        
        # 检查cgroup信息（Docker容器特征）
        try:
            with open('/proc/1/cgroup', 'r') as f:
                content = f.read()
                if 'docker' in content or 'containerd' in content:
                    return True
        except (FileNotFoundError, PermissionError):
            pass
        
        return False
        
    def validate_bilibili_url(self, url: str) -> bool:
        """
        验证B站视频链接格式
        
        Args:
            url: 视频链接
            
        Returns:
            是否为有效的B站链接
        """
        bilibili_patterns = [
            r'https?://www\.bilibili\.com/video/[Bb][Vv][0-9A-Za-z]+',
            r'https?://bilibili\.com/video/[Bb][Vv][0-9A-Za-z]+',
            r'https?://b23\.tv/[0-9A-Za-z]+',
            r'https?://www\.bilibili\.com/video/av\d+',
            r'https?://bilibili\.com/video/av\d+'
        ]
        
        return any(re.match(pattern, url) for pattern in bilibili_patterns)
    
    async def get_video_info(self, url: str) -> BilibiliVideoInfo:
        """
        获取视频信息（不下载）
        
        Args:
            url: 视频链接
            
        Returns:
            视频信息对象
        """
        if not self.validate_bilibili_url(url):
            raise ValidationError(f"无效的B站视频链接: {url}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        # 容器环境适配
        if self.is_container and self.skip_browser_cookies:
            logger.info("容器环境：跳过cookies-from-browser参数")
            # 尝试使用cookies文件（如果存在）
            if Path(self.cookies_file).exists():
                ydl_opts['cookiefile'] = self.cookies_file
                logger.info(f"使用cookies文件: {self.cookies_file}")
            else:
                logger.info("未找到cookies文件，将以匿名模式访问")
        elif self.browser:
            ydl_opts['cookies_from_browser'] = self.browser.lower()
            logger.info(f'yt-dlp cookies_from_browser: {ydl_opts.get("cookies_from_browser")}')
        
        try:
            loop = asyncio.get_event_loop()
            info_dict = await loop.run_in_executor(
                None, 
                self._extract_info_sync, 
                url, 
                ydl_opts
            )
            return BilibiliVideoInfo(info_dict)
        except Exception as e:
            raise ProcessingError(f"获取视频信息失败: {str(e)}")
    
    def _extract_info_sync(self, url: str, ydl_opts: Dict[str, Any]) -> Dict[str, Any]:
        """同步方式提取视频信息"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    
    async def download_video_and_subtitle(
        self, 
        url: str, 
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, str]:
        """
        下载视频和字幕文件
        
        Args:
            url: 视频链接
            progress_callback: 进度回调函数，参数为(状态信息, 进度百分比)
            
        Returns:
            包含video_path和subtitle_path的字典
        """
        if not self.validate_bilibili_url(url):
            raise ValidationError(f"无效的B站视频链接: {url}")
        
        # 获取视频信息
        video_info = await self.get_video_info(url)
        
        # 清理文件名，移除特殊字符
        safe_title = self._sanitize_filename(video_info.title)
        
        # 设置下载选项 - 专注AI字幕
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'writeautosub': True,  # 下载AI字幕
            'writesubtitles': True,  # 下载普通字幕
            'subtitleslangs': ['ai-zh'],  # 专注AI字幕
            'subtitlesformat': 'srt',  # 强制SRT格式
            'outtmpl': str(self.download_dir / f'{safe_title}.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'progress': True,
        }
        
        # 容器环境适配
        if self.is_container and self.skip_browser_cookies:
            logger.info("容器环境：跳过cookies-from-browser参数")
            # 尝试使用cookies文件（如果存在）
            if Path(self.cookies_file).exists():
                ydl_opts['cookiefile'] = self.cookies_file
                logger.info(f"使用cookies文件: {self.cookies_file}")
            else:
                logger.info("未找到cookies文件，将以匿名模式访问")
        elif self.browser:
            ydl_opts['cookies_from_browser'] = self.browser.lower()
            logger.info(f'yt-dlp cookies_from_browser: {ydl_opts.get("cookies_from_browser")}')
        
        # 添加进度钩子
        if progress_callback:
            ydl_opts['progress_hooks'] = [self._create_progress_hook(progress_callback)]
        
        try:
            if progress_callback:
                progress_callback("开始下载视频和字幕...", 0)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._download_sync,
                url,
                ydl_opts
            )
            
            # 查找下载的文件
            video_path = self._find_downloaded_video(safe_title)
            subtitle_path = self._find_downloaded_subtitle(safe_title)
            
            if progress_callback:
                progress_callback("下载完成", 100)
            
            result = {
                'video_path': str(video_path) if video_path else '',
                'subtitle_path': str(subtitle_path) if subtitle_path else '',
                'video_info': video_info.to_dict()
            }
            
            logger.info(f"下载完成: {video_info.title}")
            return result
            
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            if progress_callback:
                progress_callback(error_msg, 0)
            raise ProcessingError(error_msg)
    
    def _download_sync(self, url: str, ydl_opts: Dict[str, Any]):
        """同步方式下载 - 使用subprocess确保容器环境适配，并支持进度回调"""
        # 构造yt-dlp命令
        safe_title = ydl_opts.get('outtmpl', '').split('/')[-1].replace('%(ext)s', '')
        if not safe_title:
            safe_title = "video"
        
        # 获取进度回调函数
        progress_callback = None
        if 'progress_hooks' in ydl_opts and ydl_opts['progress_hooks']:
            # 从第一个hook中提取回调函数
            original_hook = ydl_opts['progress_hooks'][0]
            if hasattr(original_hook, '__closure__') and original_hook.__closure__:
                progress_callback = original_hook.__closure__[0].cell_contents
        
        # 构造基本命令
        cmd = [
            "yt-dlp",
            "--write-sub",
            "--sub-lang", "ai-zh",
            "--sub-format", "srt",
            "--output", f"{safe_title}.%(ext)s",  # 只用文件名
            "--progress",  # 启用进度输出
        ]
        
        # 容器环境适配
        if self.is_container and self.skip_browser_cookies:
            logger.info("容器环境：跳过--cookies-from-browser参数")
            # 尝试使用cookies文件（如果存在）
            if Path(self.cookies_file).exists():
                cmd.extend(["--cookies", self.cookies_file])
                logger.info(f"使用cookies文件: {self.cookies_file}")
            else:
                logger.info("未找到cookies文件，将以匿名模式访问")
        elif self.browser:
            browser = self.browser.lower()
            cmd.extend(["--cookies-from-browser", browser])
            logger.info(f"使用浏览器cookies: {browser}")
        
        cmd.append(url)
        
        logger.info(f"[subprocess] yt-dlp命令: {' '.join(cmd)}")
        
        # 执行命令并实时解析进度
        import subprocess
        import re
        
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(self.download_dir),
            bufsize=1,
            universal_newlines=True
        )
        
        # 解析进度信息
        progress_pattern = re.compile(r'\[download\]\s+(\d+\.?\d*)%')
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(f"[subprocess] {output.strip()}")
                
                # 解析进度
                if progress_callback:
                    match = progress_pattern.search(output)
                    if match:
                        try:
                            progress = float(match.group(1))
                            progress_callback(f"下载中... {progress:.1f}%", progress)
                        except ValueError:
                            pass
        
        result = process.poll()
        if result != 0:
            logger.error(f"yt-dlp命令执行失败，返回码: {result}")
        
        # 列出下载目录所有文件
        import os
        files = os.listdir(self.download_dir)
        logger.info(f"[subprocess] 下载目录内容: {files}")
        
        # 查找字幕文件
        subtitle_file = None
        for f in files:
            if f.endswith('.srt') or f.endswith('.ass'):
                subtitle_file = f
                break
        if subtitle_file:
            logger.info(f"[subprocess] 找到字幕文件: {subtitle_file}")
        else:
            logger.warning(f"[subprocess] 未找到字幕文件，标题: {safe_title}")
    
    def _create_progress_hook(self, progress_callback: Callable[[str, float], None]):
        """创建进度回调钩子"""
        def progress_hook(d):
            if d['status'] == 'downloading':
                if 'total_bytes' in d and d['total_bytes']:
                    progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif '_percent_str' in d:
                    # 从百分比字符串中提取数字
                    percent_str = d['_percent_str'].strip().rstrip('%')
                    try:
                        progress = float(percent_str)
                    except ValueError:
                        progress = 0
                else:
                    progress = 0
                
                speed = d.get('_speed_str', '')
                eta = d.get('_eta_str', '')
                status = f"下载中... {speed} ETA: {eta}"
                progress_callback(status, progress)
            elif d['status'] == 'finished':
                progress_callback("下载完成，正在处理...", 95)
        
        return progress_hook
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符"""
        # 移除或替换不安全的字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip()
    
    def _find_downloaded_video(self, title: str) -> Optional[Path]:
        """查找下载的视频文件"""
        possible_extensions = ['.mp4', '.mkv', '.webm', '.flv']
        
        for ext in possible_extensions:
            video_path = self.download_dir / f"{title}{ext}"
            if video_path.exists():
                return video_path
        
        # 如果精确匹配失败，尝试模糊匹配
        for file_path in self.download_dir.glob(f"{title}*"):
            if file_path.suffix.lower() in possible_extensions:
                return file_path
        
        return None
    
    def _find_downloaded_subtitle(self, title: str) -> Optional[Path]:
        """查找下载的字幕文件 - 简化版本，专注AI字幕"""
        logger.info(f"正在查找字幕文件，标题: {title}")
        
        # 首先检查AI字幕文件
        ai_subtitle_path = self.download_dir / f"{title}.ai-zh.srt"
        if ai_subtitle_path.exists():
            # 重命名为标准格式
            standard_path = self.download_dir / f"{title}.srt"
            if not standard_path.exists():
                ai_subtitle_path.rename(standard_path)
                logger.info(f"重命名AI字幕文件: {title}.ai-zh.srt -> {title}.srt")
                return standard_path
            return ai_subtitle_path
        
        # 检查是否已经是标准格式
        standard_path = self.download_dir / f"{title}.srt"
        if standard_path.exists():
            logger.info(f"找到标准字幕文件: {title}.srt")
            return standard_path
        
        # 模糊匹配字幕文件
        for file_path in self.download_dir.glob(f"{title}*.srt"):
            logger.info(f"找到字幕文件: {file_path.name}")
            return file_path
        
        logger.warning(f"未找到字幕文件，标题: {title}")
        return None
    
    def _convert_vtt_to_srt(self, vtt_path: Path, srt_path: Path):
        """将VTT字幕文件转换为SRT格式"""
        try:
            with open(vtt_path, 'r', encoding='utf-8') as vtt_file:
                vtt_content = vtt_file.read()
            
            # 简单的VTT到SRT转换
            lines = vtt_content.split('\n')
            srt_lines = []
            subtitle_count = 1
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 跳过VTT头部信息
                if line.startswith('WEBVTT') or line.startswith('NOTE') or not line:
                    i += 1
                    continue
                
                # 查找时间戳行
                if '-->' in line:
                    # 转换时间格式 (VTT使用点，SRT使用逗号)
                    time_line = line.replace('.', ',')
                    srt_lines.append(str(subtitle_count))
                    srt_lines.append(time_line)
                    
                    # 获取字幕文本
                    i += 1
                    subtitle_text = []
                    while i < len(lines) and lines[i].strip():
                        subtitle_text.append(lines[i].strip())
                        i += 1
                    
                    srt_lines.extend(subtitle_text)
                    srt_lines.append('')  # 空行分隔
                    subtitle_count += 1
                
                i += 1
            
            # 写入SRT文件
            with open(srt_path, 'w', encoding='utf-8') as srt_file:
                srt_file.write('\n'.join(srt_lines))
                
        except Exception as e:
            logger.error(f"VTT转SRT转换失败: {e}")
            raise
    
    def cleanup_temp_files(self, title: str):
        """清理临时文件"""
        try:
            # 清理可能的临时文件
            for pattern in [f"{title}*.part", f"{title}*.tmp", f"{title}*.ytdl"]:
                for temp_file in self.download_dir.glob(pattern):
                    temp_file.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    def download(self, url, safe_title):
        # 1. 构造yt-dlp命令
        browser = self.browser.lower() if self.browser else "chrome"
        cmd = [
            "yt-dlp",
            "--write-sub",
            "--sub-lang", "ai-zh",
            "--sub-format", "srt",
            "--output", str(self.download_dir / f'{safe_title}.%(ext)s'),
            "--cookies-from-browser", browser,
            url
        ]
        logger.info(f"[subprocess] yt-dlp命令: {' '.join(cmd)}")
        # 2. 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.download_dir))
        logger.info(f"[subprocess] yt-dlp stdout: {result.stdout}")
        logger.info(f"[subprocess] yt-dlp stderr: {result.stderr}")
        if result.returncode != 0:
            logger.error(f"yt-dlp命令执行失败，返回码: {result.returncode}")
        # 3. 列出下载目录所有文件
        import os
        files = os.listdir(self.download_dir)
        logger.info(f"[subprocess] 下载目录内容: {files}")
        # 4. 查找字幕文件
        subtitle_file = None
        for f in files:
            if f.endswith('.srt') or f.endswith('.ass'):
                subtitle_file = f
                break
        if subtitle_file:
            logger.info(f"[subprocess] 找到字幕文件: {subtitle_file}")
        else:
            logger.warning(f"[subprocess] 未找到字幕文件，标题: {safe_title}")

# 便捷函数
async def download_bilibili_video(
    url: str, 
    download_dir: Optional[Path] = None,
    browser: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> Dict[str, str]:
    """
    便捷的B站视频下载函数
    
    Args:
        url: B站视频链接
        download_dir: 下载目录
        browser: 浏览器类型
        settings: 配置信息
        progress_callback: 进度回调函数
        
    Returns:
        包含video_path和subtitle_path的字典
    """
    downloader = BilibiliDownloader(download_dir, browser, settings)
    return await downloader.download_video_and_subtitle(url, progress_callback)

async def get_bilibili_video_info(url: str, browser: Optional[str] = None, settings: Optional[Dict[str, Any]] = None) -> BilibiliVideoInfo:
    """
    便捷的B站视频信息获取函数
    
    Args:
        url: B站视频链接
        browser: 浏览器类型
        settings: 配置信息
        
    Returns:
        视频信息对象
    """
    downloader = BilibiliDownloader(browser=browser, settings=settings)
    return await downloader.get_video_info(url)