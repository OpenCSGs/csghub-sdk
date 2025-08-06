#!/usr/bin/env python3
"""
演示如何使用 snapshot_download 的进度回调功能
"""

import time
from pycsghub import snapshot_download


def progress_callback(progress_info):
    """
    进度回调函数
    接收下载进度信息并打印
    """
    print(f"\n=== 下载进度更新 ===")
    print(f"总文件数: {progress_info['total_files']}")
    print(f"当前已下载: {progress_info['current_downloaded']}")
    print(f"成功下载: {progress_info['success_count']}")
    print(f"失败下载: {progress_info['failed_count']}")
    print(f"剩余待下载: {progress_info['remaining_count']}")
    
    if progress_info['successful_files']:
        print(f"最近成功下载的文件: {progress_info['successful_files'][-1]}")
    
    if progress_info['remaining_files']:
        print(f"下一个待下载文件: {progress_info['remaining_files'][0]}")
    
    # 计算进度百分比
    if progress_info['total_files'] > 0:
        progress_percent = (progress_info['current_downloaded'] / progress_info['total_files']) * 100
        print(f"总体进度: {progress_percent:.1f}%")
    
    print("=" * 30)


def main():
    """
    主函数 - 演示带进度回调的下载
    """
    print("开始演示带进度回调的模型下载...")
    
    # 示例模型ID（请替换为实际的模型ID）
    repo_id = "example/model"
    
    try:
        # 使用进度回调下载模型
        local_path = snapshot_download(
            repo_id=repo_id,
            progress_callback=progress_callback,
            verbose=True,
            use_parallel=True,
            max_workers=4
        )
        
        print(f"\n下载完成！模型保存在: {local_path}")
        
    except Exception as e:
        print(f"下载过程中出现错误: {e}")


if __name__ == "__main__":
    main() 