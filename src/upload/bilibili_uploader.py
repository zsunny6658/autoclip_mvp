#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于bilitool实现的B站视频上传功能。

安装依赖:
# 如果遇到externally-managed-environment错误，使用以下方法之一:
# 方法1: 使用虚拟环境 (推荐)
python3 -m venv venv
source venv/bin/activate
pip install bilitool

# 方法2: 使用pipx
brew install pipx
pipx install bilitool

# 方法3: 强制安装到用户目录 (不推荐)
pip3 install --user --break-system-packages bilitool
"""

import asyncio
import os
import subprocess
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import tempfile

try:
    from bilitool import LoginController, UploadController, FeedController
    BILITOOL_AVAILABLE = True
except ImportError:
    # 如果没有安装bilitool，提供一个模拟实现
    BILITOOL_AVAILABLE = False
    
    class LoginController:
        def login_bilibili(self, export: bool = False):
            raise NotImplementedError("bilitool not installed. Please install it first.")
        
        def check_bilibili_login(self):
            return False
        
        def logout_bilibili(self):
            pass
    
    class UploadController:
        def upload_video_entry(self, **kwargs):
            raise NotImplementedError("bilitool not installed. Please install it first.")
        
        def append_video_entry(self, **kwargs):
            raise NotImplementedError("bilitool not installed. Please install it first.")
    
    class FeedController:
        def print_video_list_info(self, **kwargs):
            raise NotImplementedError("bilitool not installed. Please install it first.")

from ..utils.error_handler import safe_execute, error_handler

logger = logging.getLogger(__name__)

class BilibiliUploader:
    """基于bilitool的B站视频上传器"""
    
    def __init__(self):
        """初始化B站上传器"""
        if not BILITOOL_AVAILABLE:
            logger.warning("bilitool未安装，上传功能将不可用")
            
        self.login_controller = LoginController()
        self.upload_controller = UploadController()
        self.feed_controller = FeedController()
        self._is_logged_in = False
        
    def check_bilitool_available(self) -> bool:
        """检查bilitool是否可用
        
        Returns:
            bool: bilitool是否可用
        """
        return BILITOOL_AVAILABLE
    
    def login_interactive(self, export_cookies: bool = True) -> bool:
        """交互式登录B站
        
        Args:
            export_cookies: 是否导出cookies
            
        Returns:
            bool: 登录是否成功
        """
        if not BILITOOL_AVAILABLE:
            raise RuntimeError("bilitool未安装，请先安装bilitool")
            
        try:
            # 使用bilitool的交互式登录
            self.login_controller.login_bilibili(export=export_cookies)
            self._is_logged_in = True
            logger.info("B站登录成功")
            return True
        except Exception as e:
            logger.error(f"B站登录失败：{str(e)}")
            self._is_logged_in = False
            return False
    
    def logout(self) -> bool:
        """退出登录
        
        Returns:
            bool: 退出是否成功
        """
        if not BILITOOL_AVAILABLE:
            return True
            
        try:
            self.login_controller.logout_bilibili()
            self._is_logged_in = False
            logger.info("已退出B站登录")
            return True
        except Exception as e:
            logger.error(f"退出登录失败：{str(e)}")
            return False
    
    def verify_credential(self) -> bool:
        """验证登录凭证是否有效
        
        Returns:
            bool: 凭证是否有效
        """
        if not BILITOOL_AVAILABLE:
            return False
            
        try:
            is_logged_in = self.login_controller.check_bilibili_login()
            self._is_logged_in = is_logged_in
            if is_logged_in:
                logger.info("B站登录状态有效")
            else:
                logger.warning("B站登录状态无效，请重新登录")
            return is_logged_in
        except Exception as e:
            logger.error(f"验证登录状态失败：{str(e)}")
            self._is_logged_in = False
            return False
    
    async def upload_video(
        self,
        video_path: str,
        title: str,
        desc: str = "",
        tags: List[str] = None,
        cover_path: str = None,
        tid: int = 21,  # 默认分区：日常
        source: str = "",  # 转载来源，原创留空
        dynamic: str = "",  # 动态描述
        **kwargs
    ) -> Dict[str, Any]:
        """上传视频到B站
        
        Args:
            video_path: 视频文件路径
            title: 视频标题
            desc: 视频描述
            tags: 视频标签列表
            cover_path: 封面图片路径
            tid: 分区ID (21=日常, 17=单机游戏, 171=电子竞技等)
            source: 转载来源，原创留空
            dynamic: 动态描述
            **kwargs: 其他参数
            
        Returns:
            Dict: 上传结果
        """
        if not BILITOOL_AVAILABLE:
            raise RuntimeError("bilitool未安装，请先安装bilitool")
            
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在：{video_path}")
            
        # 验证登录状态
        if not self.verify_credential():
            raise ValueError("未登录或登录状态无效，请先登录B站")
            
        try:
            # 准备上传参数
            upload_params = {
                "video_path": video_path,
                "title": title[:80],  # B站标题限制80字符
                "desc": desc[:2000],  # 描述限制2000字符
                "tag": ",".join(tags[:12]) if tags else "",  # 最多12个标签
                "tid": tid,
                "source": source,
                "dynamic": dynamic,
            }
            
            # 如果有封面，添加封面路径
            if cover_path and os.path.exists(cover_path):
                upload_params["cover"] = cover_path
                
            logger.info(f"开始上传视频：{title}")
            logger.info(f"视频路径：{video_path}")
            logger.info(f"分区ID：{tid}")
            
            # 执行上传 - bilitool的upload_video_entry是同步函数
            # 在异步环境中运行同步函数
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.upload_controller.upload_video_entry(**upload_params)
            )
            
            logger.info(f"视频上传成功：{title}")
            
            return {
                "success": True,
                "message": "上传成功",
                "title": title,
                "video_path": video_path,
                "upload_params": upload_params,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"视频上传失败：{str(e)}")
            return {
                "success": False,
                "message": f"上传失败：{str(e)}",
                "title": title,
                "video_path": video_path,
                "error": str(e)
            }
    
    async def append_video_to_collection(
        self,
        video_path: str,
        bvid: str,
        **kwargs
    ) -> Dict[str, Any]:
        """追加视频到已有视频（分P投稿）
        
        Args:
            video_path: 视频文件路径
            bvid: 目标视频的BV号
            **kwargs: 其他参数
            
        Returns:
            Dict: 追加结果
        """
        if not BILITOOL_AVAILABLE:
            raise RuntimeError("bilitool未安装，请先安装bilitool")
            
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在：{video_path}")
            
        # 验证登录状态
        if not self.verify_credential():
            raise ValueError("未登录或登录状态无效，请先登录B站")
            
        try:
            logger.info(f"开始追加视频到 {bvid}")
            logger.info(f"视频路径：{video_path}")
            
            # 执行追加上传
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.upload_controller.append_video_entry(
                    video_path=video_path,
                    bvid=bvid,
                    **kwargs
                )
            )
            
            logger.info(f"视频追加成功到 {bvid}")
            
            return {
                "success": True,
                "message": "追加成功",
                "bvid": bvid,
                "video_path": video_path,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"视频追加失败：{str(e)}")
            return {
                "success": False,
                "message": f"追加失败：{str(e)}",
                "bvid": bvid,
                "video_path": video_path,
                "error": str(e)
            }
    
    def get_video_categories(self) -> List[Dict[str, Any]]:
        """获取B站视频分区列表
        
        Returns:
            List: 分区列表
        """
        # B站主要分区ID参考
        categories = [
            {"tid": 1, "name": "动画", "desc": "原创或转载动画"},
            {"tid": 13, "name": "番剧", "desc": "连载动画"},
            {"tid": 167, "name": "国创", "desc": "国产原创相关"},
            {"tid": 3, "name": "音乐", "desc": "音乐相关"},
            {"tid": 129, "name": "舞蹈", "desc": "舞蹈相关"},
            {"tid": 4, "name": "游戏", "desc": "游戏相关"},
            {"tid": 17, "name": "单机游戏", "desc": "单机游戏相关"},
            {"tid": 171, "name": "电子竞技", "desc": "电竞相关"},
            {"tid": 172, "name": "手机游戏", "desc": "手游相关"},
            {"tid": 65, "name": "网络游戏", "desc": "网游相关"},
            {"tid": 5, "name": "娱乐", "desc": "娱乐杂谈"},
            {"tid": 71, "name": "综艺", "desc": "综艺相关"},
            {"tid": 137, "name": "明星", "desc": "明星相关"},
            {"tid": 131, "name": "Korea相关", "desc": "韩国相关"},
            {"tid": 36, "name": "知识", "desc": "知识分享"},
            {"tid": 201, "name": "科学科普", "desc": "科学科普"},
            {"tid": 124, "name": "社科·法律·心理", "desc": "社科法律心理"},
            {"tid": 228, "name": "人文历史", "desc": "人文历史"},
            {"tid": 207, "name": "财经商业", "desc": "财经商业"},
            {"tid": 208, "name": "校园学习", "desc": "校园学习"},
            {"tid": 209, "name": "职业职场", "desc": "职业职场"},
            {"tid": 229, "name": "设计·创意", "desc": "设计创意"},
            {"tid": 122, "name": "野生技能协会", "desc": "技能分享"},
            {"tid": 188, "name": "科技", "desc": "科技相关"},
            {"tid": 95, "name": "数码", "desc": "数码产品"},
            {"tid": 230, "name": "汽车", "desc": "汽车相关"},
            {"tid": 231, "name": "工业·工程·机械", "desc": "工业工程机械"},
            {"tid": 160, "name": "生活", "desc": "生活相关"},
            {"tid": 138, "name": "搞笑", "desc": "搞笑内容"},
            {"tid": 21, "name": "日常", "desc": "日常生活"},
            {"tid": 76, "name": "美食圈", "desc": "美食制作"},
            {"tid": 75, "name": "动物圈", "desc": "动物相关"},
            {"tid": 161, "name": "手工", "desc": "手工制作"},
            {"tid": 162, "name": "绘画", "desc": "绘画创作"},
            {"tid": 163, "name": "运动", "desc": "运动健身"},
            {"tid": 174, "name": "其他", "desc": "其他内容"},
        ]
        
        return categories
    
    def get_upload_status(self) -> Dict[str, Any]:
        """获取上传器状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            "bilitool_available": BILITOOL_AVAILABLE,
            "is_logged_in": self._is_logged_in,
            "login_valid": self.verify_credential() if BILITOOL_AVAILABLE else False
        }