#!/usr/bin/env python3
"""
演示如何使用自定义进度显示进行模型下载
"""

import time
from datetime import datetime
from pycsghub import snapshot_download


class CustomProgressTracker:
    """自定义进度跟踪器"""
    
    def __init__(self):
        self.start_time = None
        self.last_update_time = None
        
    def progress_callback(self, progress_info):
        """自定义进度回调函数"""
        current_time = datetime.now()
        
        # 初始化开始时间
        if self.start_time is None:
            self.start_time = current_time
            self.last_update_time = current_time
        
        # 计算时间间隔
        time_since_last = (current_time - self.last_update_time).total_seconds()
        
        # 只在有变化或超过1秒时更新显示
        if time_since_last >= 1.0 or progress_info['current_downloaded'] == progress_info['total_files']:
            self._print_progress(progress_info, current_time)
            self.last_update_time = current_time
    
    def _print_progress(self, progress_info, current_time):
        """打印进度信息"""
        total_files = progress_info['total_files']
        current_downloaded = progress_info['current_downloaded']
        success_count = progress_info['success_count']
        failed_count = progress_info['failed_count']
        remaining_count = progress_info['remaining_count']
        
        # 计算进度百分比
        if total_files > 0:
            progress_percent = (current_downloaded / total_files) * 100
        else:
            progress_percent = 0
        
        # 计算运行时间
        elapsed_time = (current_time - self.start_time).total_seconds()
        
        # 计算预估剩余时间
        if current_downloaded > 0:
            avg_time_per_file = elapsed_time / current_downloaded
            estimated_remaining = avg_time_per_file * remaining_count
        else:
            estimated_remaining = 0
        
        # 创建进度条
        bar_length = 30
        filled_length = int(bar_length * progress_percent / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # 打印进度信息
        print(f"\r[{bar}] {progress_percent:5.1f}% | "
              f"已下载: {current_downloaded}/{total_files} | "
              f"成功: {success_count} | "
              f"失败: {failed_count} | "
              f"剩余: {remaining_count} | "
              f"用时: {elapsed_time:.1f}s | "
              f"预估剩余: {estimated_remaining:.1f}s", end='', flush=True)
        
        # 如果下载完成，换行
        if current_downloaded == total_files:
            print()  # 换行


def main():
    """
    主函数 - 演示自定义进度跟踪
    """
    print("开始演示自定义进度跟踪的模型下载...")
    
    # 创建自定义进度跟踪器
    progress_tracker = CustomProgressTracker()
    
    # 示例模型ID（请替换为实际的模型ID）
    repo_id = "example/model"
    
    try:
        # 使用自定义进度回调下载模型
        local_path = snapshot_download(
            repo_id=repo_id,
            progress_callback=progress_tracker.progress_callback,
            verbose=False,  # 关闭详细输出以避免干扰进度条
            use_parallel=True,
            max_workers=4
        )
        
        print(f"\n✅ 下载完成！模型保存在: {local_path}")
        
    except Exception as e:
        print(f"\n❌ 下载过程中出现错误: {e}")


if __name__ == "__main__":
    main() 