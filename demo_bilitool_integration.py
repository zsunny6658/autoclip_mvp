#!/usr/bin/env python3
"""
bilitool 集成演示脚本
展示如何在实际项目中使用 bilitool 进行B站视频上传
"""

import asyncio
import os
from pathlib import Path
from src.upload.upload_manager import UploadManager, Platform
from src.config import config_manager

async def demo_single_upload():
    """演示单个视频上传"""
    print("\n🎬 演示单个视频上传")
    print("=" * 40)
    
    upload_manager = UploadManager()
    
    # 检查登录状态
    print("1. 检查B站登录状态...")
    is_logged_in = await upload_manager.verify_platform_credential(Platform.BILIBILI)
    
    if not is_logged_in:
        print("❌ 未登录B站，请先登录")
        print("执行登录...")
        
        success = upload_manager.set_bilibili_credential(export_cookies=True)
        if not success:
            print("❌ 登录失败，跳过上传演示")
            return
        
        print("✅ 登录成功")
    else:
        print("✅ 已登录B站")
    
    # 创建测试视频文件（如果不存在）
    test_video = Path("test_video.mp4")
    if not test_video.exists():
        print("\n2. 创建测试视频文件...")
        # 创建一个空的测试文件（实际使用中应该是真实的视频文件）
        test_video.write_bytes(b"fake video content")
        print(f"✅ 测试视频文件已创建: {test_video}")
    
    # 创建上传任务
    print("\n3. 创建上传任务...")
    try:
        task = await upload_manager.create_upload_task(
            task_id="demo_single_upload",
            platform=Platform.BILIBILI,
            video_path=str(test_video.absolute()),
            title="演示视频 - 单个上传",
            desc="这是一个使用 bilitool 集成的演示视频",
            tags=["演示", "bilitool", "自动上传"],
            tid=21,  # 日常分区
            auto_start=False  # 先不自动开始
        )
        print(f"✅ 上传任务创建成功: {task.task_id}")
    except Exception as e:
        print(f"❌ 创建上传任务失败: {e}")
        return
    
    # 开始上传
    print("\n4. 开始上传...")
    try:
        await upload_manager.start_upload(task.task_id)
        print("✅ 上传已开始")
    except Exception as e:
        print(f"❌ 开始上传失败: {e}")
        return
    
    # 监控上传进度
    print("\n5. 监控上传进度...")
    max_wait_time = 300  # 最多等待5分钟
    wait_time = 0
    
    while wait_time < max_wait_time:
        status = upload_manager.get_task_status(task.task_id)
        print(f"   状态: {status['status']}, 进度: {status['progress']}%")
        
        if status['status'] in ['success', 'failed', 'cancelled']:
            break
        
        await asyncio.sleep(10)
        wait_time += 10
    
    # 显示最终结果
    final_status = upload_manager.get_task_status(task.task_id)
    if final_status['status'] == 'success':
        print(f"🎉 上传成功！")
        if 'result' in final_status and final_status['result']:
            print(f"   视频链接: {final_status['result']}")
    else:
        print(f"❌ 上传失败: {final_status.get('error', '未知错误')}")
    
    # 清理测试文件
    if test_video.exists():
        test_video.unlink()
        print(f"🗑️  测试文件已清理: {test_video}")

async def demo_batch_upload():
    """演示批量视频上传"""
    print("\n📚 演示批量视频上传")
    print("=" * 40)
    
    upload_manager = UploadManager()
    
    # 检查登录状态
    print("1. 检查B站登录状态...")
    is_logged_in = await upload_manager.verify_platform_credential(Platform.BILIBILI)
    
    if not is_logged_in:
        print("❌ 未登录B站，请先登录")
        return
    
    print("✅ 已登录B站")
    
    # 创建多个测试视频文件
    print("\n2. 创建测试视频文件...")
    test_videos = []
    for i in range(3):
        video_path = Path(f"test_clip_{i+1}.mp4")
        if not video_path.exists():
            video_path.write_bytes(f"fake video content {i+1}".encode())
        test_videos.append(video_path)
        print(f"   ✅ {video_path}")
    
    # 创建批量上传任务
    print("\n3. 创建批量上传任务...")
    tasks = []
    
    for i, video_path in enumerate(test_videos):
        try:
            task = await upload_manager.create_upload_task(
                task_id=f"demo_batch_{i+1}",
                platform=Platform.BILIBILI,
                video_path=str(video_path.absolute()),
                title=f"演示切片 {i+1} - 批量上传",
                desc=f"这是第 {i+1} 个演示切片，使用 bilitool 批量上传",
                tags=["演示", "切片", f"第{i+1}集"],
                tid=21,  # 日常分区
                auto_start=False
            )
            tasks.append(task)
            print(f"   ✅ 任务 {i+1}: {task.task_id}")
        except Exception as e:
            print(f"   ❌ 创建任务 {i+1} 失败: {e}")
    
    if not tasks:
        print("❌ 没有成功创建任何任务")
        return
    
    # 逐个开始上传（避免并发过多）
    print("\n4. 开始批量上传...")
    for i, task in enumerate(tasks):
        try:
            await upload_manager.start_upload(task.task_id)
            print(f"   ✅ 开始上传任务 {i+1}: {task.title}")
            await asyncio.sleep(2)  # 间隔2秒
        except Exception as e:
            print(f"   ❌ 开始任务 {i+1} 失败: {e}")
    
    # 监控所有任务状态
    print("\n5. 监控批量上传进度...")
    max_wait_time = 600  # 最多等待10分钟
    wait_time = 0
    
    while wait_time < max_wait_time:
        all_tasks = upload_manager.get_all_tasks()
        active_tasks = [t for t in all_tasks if t['status'] == 'uploading']
        
        if not active_tasks:
            print("   ✅ 所有任务都已完成")
            break
        
        print(f"   📊 还有 {len(active_tasks)} 个任务在上传中...")
        for task in active_tasks:
            print(f"      - {task['task_id']}: {task['progress']}%")
        
        await asyncio.sleep(15)
        wait_time += 15
    
    # 显示最终结果
    print("\n6. 批量上传结果:")
    final_tasks = upload_manager.get_all_tasks()
    success_count = 0
    failed_count = 0
    
    for task in final_tasks:
        if task['task_id'].startswith('demo_batch_'):
            if task['status'] == 'success':
                success_count += 1
                print(f"   ✅ {task['task_id']}: 上传成功")
            else:
                failed_count += 1
                print(f"   ❌ {task['task_id']}: {task['status']} - {task.get('error', '')}")
    
    print(f"\n📊 批量上传完成: 成功 {success_count} 个，失败 {failed_count} 个")
    
    # 清理测试文件
    print("\n7. 清理测试文件...")
    for video_path in test_videos:
        if video_path.exists():
            video_path.unlink()
            print(f"   🗑️  {video_path}")

def demo_config_management():
    """演示配置管理"""
    print("\n⚙️  演示配置管理")
    print("=" * 40)
    
    # 获取当前配置
    print("1. 当前配置:")
    bilibili_config = config_manager.get_bilibili_config()
    print(f"   自动上传: {bilibili_config.auto_upload}")
    print(f"   默认分区: {bilibili_config.default_tid}")
    print(f"   最大并发: {bilibili_config.max_concurrent_uploads}")
    print(f"   上传超时: {bilibili_config.upload_timeout_minutes} 分钟")
    print(f"   自动生成标签: {bilibili_config.auto_generate_tags}")
    print(f"   标签限制: {bilibili_config.tag_limit}")
    
    # 更新配置
    print("\n2. 更新配置...")
    config_manager.update_settings(
        bilibili_auto_upload=True,
        bilibili_default_tid=36,  # 知识分区
        bilibili_max_concurrent_uploads=2
    )
    print("   ✅ 配置已更新")
    
    # 显示更新后的配置
    print("\n3. 更新后的配置:")
    updated_config = config_manager.get_bilibili_config()
    print(f"   自动上传: {updated_config.auto_upload}")
    print(f"   默认分区: {updated_config.default_tid}")
    print(f"   最大并发: {updated_config.max_concurrent_uploads}")
    
    # 导出完整配置
    print("\n4. 导出完整配置:")
    full_config = config_manager.export_config()
    print(f"   配置项数量: {len(full_config)}")
    for section, config in full_config.items():
        print(f"   {section}: {len(config) if isinstance(config, dict) else 'N/A'} 项")

def demo_platform_info():
    """演示平台信息获取"""
    print("\n📺 演示平台信息获取")
    print("=" * 40)
    
    upload_manager = UploadManager()
    
    # 获取B站分区信息
    print("1. B站分区信息:")
    try:
        categories = upload_manager.get_platform_categories(Platform.BILIBILI)
        print(f"   总分区数: {len(categories)}")
        
        # 显示前10个分区
        print("   前10个分区:")
        for i, category in enumerate(categories[:10]):
            if isinstance(category, dict):
                print(f"     {category.get('tid', 'N/A')}: {category.get('name', 'N/A')}")
            else:
                print(f"     {category}")
        
        # 查找特定分区
        print("\n   常用分区:")
        common_tids = [21, 36, 17, 171, 188]  # 日常、知识、单机游戏、电竞、科技
        for category in categories:
            if isinstance(category, dict) and category.get('tid') in common_tids:
                print(f"     {category['tid']}: {category['name']} - {category.get('desc', '')}")
    
    except Exception as e:
        print(f"   ❌ 获取分区信息失败: {e}")
    
    # 获取平台状态
    print("\n2. 平台状态:")
    try:
        status = upload_manager.get_platform_status(Platform.BILIBILI)
        print(f"   B站状态: {status}")
    except Exception as e:
        print(f"   ❌ 获取平台状态失败: {e}")

async def main():
    """主演示函数"""
    print("🚀 bilitool 集成功能演示")
    print("=" * 50)
    
    # 检查 bilitool 是否可用
    try:
        from src.upload.bilibili_uploader import BilibiliUploader
        uploader = BilibiliUploader()
        if hasattr(uploader, '_mock_mode') and uploader._mock_mode:
            print("⚠️  bilitool 未安装，运行在模拟模式")
            print("   请先运行: python3 install_bilitool.py")
            print("   或手动安装: pip install bilitool")
            print("\n以下演示将在模拟模式下运行...\n")
        else:
            print("✅ bilitool 已安装，功能完全可用\n")
    except Exception as e:
        print(f"❌ 检查 bilitool 状态失败: {e}\n")
    
    # 演示菜单
    while True:
        print("\n选择演示功能:")
        print("1. 配置管理演示")
        print("2. 平台信息获取演示")
        print("3. 单个视频上传演示")
        print("4. 批量视频上传演示")
        print("5. 退出")
        
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == "1":
            demo_config_management()
        elif choice == "2":
            demo_platform_info()
        elif choice == "3":
            await demo_single_upload()
        elif choice == "4":
            await demo_batch_upload()
        elif choice == "5":
            print("👋 演示结束")
            break
        else:
            print("❌ 无效选择，请重新输入")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 演示过程中发生错误: {e}")