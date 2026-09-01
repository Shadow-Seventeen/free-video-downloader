#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.downloader import VideoDownloader
import json

def test_bilibili_video():
    downloader = VideoDownloader()
    url = "https://www.bilibili.com/video/BV1jUgA6YEw6/?spm_id_from=333.1387.upload.video_card.click&vd_source=c560d6ba0469a144a9cdcc0bfd06c011"

    try:
        print("正在解析视频...")
        result = downloader.parse_video(url)

        print("\n=== 解析结果 ===")
        print(f"标题: {result['title']}")
        print(f"平台: {result['platform']}")
        print(f"时长: {result['duration_string']}")
        print(f"上传者: {result['uploader']}")
        print(f"描述: {result['description']}")
        print(f"字幕语言: {result['subtitles']}")
        print(f"自动字幕: {result['automatic_captions']}")

        print(f"\n=== 格式列表 (共{len(result['formats'])}种) ===")
        for i, fmt in enumerate(result['formats']):
            print(f"\n格式 {i+1}:")
            print(f"  format_id: {fmt['format_id']}")
            print(f"  标签: {fmt['label']}")
            print(f"  分辨率: {fmt['resolution']}")
            print(f"  大小: {fmt['filesize']}")
            print(f"  有音频: {fmt['has_audio']}")
            print(f"  视频编码: {fmt['vcodec']}")
            print(f"  音频编码: {fmt['acodec']}")

        # 检查formats是否为空
        if not result['formats']:
            print("\n⚠️  警告: 视频没有可用的格式！")

        # 检查第一个格式的format_id
        if result['formats']:
            first_format_id = result['formats'][0].get('format_id')
            print(f"\n第一个格式的format_id: '{first_format_id}'")
            print(f"format_id是否存在: {bool(first_format_id)}")

    except Exception as e:
        print(f"解析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bilibili_video()