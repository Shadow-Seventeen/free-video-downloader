#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from backend.downloader import VideoDownloader
import json

def test_duration_issue():
    downloader = VideoDownloader()
    url = "https://www.bilibili.com/video/BV1jUgA6YEw6/?spm_id_from=333.1387.upload.video_card.click&vd_source=c560d6ba0469a144a9cdcc0bfd06c011"

    try:
        print("正在解析视频...")
        result = downloader.parse_video(url)

        print("\n=== 视频原始信息 ===")
        print(f"标题: {result['title']}")
        print(f"平台: {result['platform']}")
        print(f"总时长: {result['duration_string']} ({result['duration']}秒)")

        print(f"\n=== 所有可用格式 (共{len(result['formats'])}种) ===")
        for fmt in result['formats']:
            print(f"\nFormat ID: {fmt['format_id']}")
            print(f"  标签: {fmt['label']}")
            print(f"  分辨率: {fmt['resolution']}")
            print(f"  文件大小: {fmt['filesize'] or '未知'} bytes")
            print(f"  有音频: {fmt['has_audio']}")
            print(f"  视频编码: {fmt['vcodec']}")
            print(f"  音频编码: {fmt['acodec']}")

        # 检查是否有完整时长的格式
        print(f"\n=== 分析时长问题 ===")
        full_duration_formats = []
        short_duration_formats = []

        # 获取完整视频时长
        full_duration = result['duration']  # 秒

        # 模拟获取每个格式的实际时长
        # 注意：yt-dlp 的格式信息中通常不包含精确的时长，我们需要特殊处理
        for fmt in result['formats']:
            # 这里我们无法直接获取每个格式的精确时长
            # 但可以通过一些特征来判断是否可能是完整版本
            fmt_id = str(fmt['format_id'])

            # B站的一些格式ID规律：
            # 高质量格式通常是更大的数字（720p=64, 480p=32, 360p=16）
            # 但这只是规律，不是绝对

            # 检查文件大小是否合理
            if fmt['filesize']:
                # 估算：1小时视频，720p应该至少 200MB 以上
                estimated_size_720p = full_duration * 500 * 1024  # 500KB/s 估算
                estimated_size_480p = full_duration * 300 * 1024  # 300KB/s 估算

                if fmt['height'] == 720 and fmt['filesize'] > estimated_size_720p * 0.5:
                    full_duration_formats.append(fmt)
                elif fmt['height'] == 480 and fmt['filesize'] > estimated_size_480p * 0.5:
                    full_duration_formats.append(fmt)
                else:
                    short_duration_formats.append(fmt)
            else:
                # 没有文件大小信息，假设是完整版本
                full_duration_formats.append(fmt)

        print(f"\n可能完整的格式：")
        for fmt in full_duration_formats:
            print(f"  - {fmt['format_id']}: {fmt['label']}")

        print(f"\n可能不完整的格式：")
        for fmt in short_duration_formats:
            print(f"  - {fmt['format_id']}: {fmt['label']}")

        # 建议使用的格式
        print(f"\n建议：")
        if full_duration_formats:
            print("建议使用格式ID:", [f['format_id'] for f in full_duration_formats])
            print("这些格式的文件大小相对合理")
        else:
            print("所有格式的文件大小信息都不完整，建议使用 format_id='best'")

        # 测试使用 'best' 格式
        print(f"\n=== 测试 'best' 格式 ===")
        try:
            best_info = downloader.get_direct_url(url, "best")
            print(f"'best' 格式信息:")
            print(f"  扩展名: {best_info['ext']}")
            print(f"  文件大小: {best_info['filesize'] or '未知'}")
        except Exception as e:
            print(f"'best' 格式获取失败: {str(e)}")

    except Exception as e:
        print(f"解析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duration_issue()