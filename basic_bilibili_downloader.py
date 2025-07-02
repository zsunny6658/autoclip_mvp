

import yt_dlp
import sys
import os
import argparse

def download_bili_video(url, browser=None):
    """
    下载B站视频及其字幕（优先CC，其次AI）。
    - 视频保存为 mp4。
    - 字幕保存为 srt。
    - 可选：使用浏览器Cookie进行登录。
    """
    print(f"▶️ 开始处理链接: {url}")

    # 更新：现在我们指定下载 AI 字幕 'ai-zh'
    subtitle_lang = 'ai-zh'

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'writesubtitles': True,
        'subtitleslangs': [subtitle_lang],
        'subtitlesformat': 'srt',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'progress': True,
    }

    if browser:
        print(f"  - 尝试使用来自 [{browser}] 浏览器的Cookies...")
        ydl_opts['cookiesfrombrowser'] = (browser.lower(),)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get('title', 'unknown_video')
            
            print(f"  - 视频标题: {title}")
            print(f"  - 目标字幕类型: {subtitle_lang}")
            print("  - 开始下载视频和字幕，请稍候...")
            
            ydl.download([url])

            video_filename = f"{title}.mp4"
            # 更新：检查对应语言的字幕文件
            subtitle_filename = f"{title}.{subtitle_lang}.srt"

            print("\n✅ 处理完成!")
            if os.path.exists(video_filename):
                print(f"  - 视频已保存为: {video_filename}")
            else:
                print(f"  - 视频已下载，请检查当前目录下名为 '{title}' 的视频文件。")

            if os.path.exists(subtitle_filename):
                base_filename = os.path.splitext(video_filename)[0]
                final_subtitle_path = f"{base_filename}.srt"
                # 如果目标文件已存在，先删除，避免os.rename报错
                if os.path.exists(final_subtitle_path) and subtitle_filename != final_subtitle_path:
                    os.remove(final_subtitle_path)
                os.rename(subtitle_filename, final_subtitle_path)
                print(f"  - 字幕已保存为: {final_subtitle_path}")
            else:
                print("  - ⚠️ 未找到指定的字幕文件。")

    except yt_dlp.utils.DownloadError as e:
        print(f"\n❌ 下载失败: {e}")
    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="下载B站视频和字幕。依赖yt-dlp和ffmpeg。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("url", help="B站视频的链接。")
    parser.add_argument(
        "--browser",
        help="指定一个浏览器 (chrome, firefox, safari, edge 等) 来加载其Cookies。",
        default=None
    )
    args = parser.parse_args()

    if args.browser:
        print("ℹ️ 提示: 如果Cookie读取失败，请尝试完全关闭指定的浏览器后再试。")

    download_bili_video(args.url, args.browser)
