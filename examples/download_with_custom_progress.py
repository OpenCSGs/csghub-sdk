#!/usr/bin/env python3
"""
Demonstrate how to use custom progress display for model download
"""

import time
from datetime import datetime
from pycsghub import snapshot_download


class CustomProgressTracker:
    """Custom progress tracker"""
    
    def __init__(self):
        self.start_time = None
        self.last_update_time = None
        
    def progress_callback(self, progress_info):
        """Custom progress callback function"""
        current_time = datetime.now()

        if self.start_time is None:
            self.start_time = current_time
            self.last_update_time = current_time

        time_since_last = (current_time - self.last_update_time).total_seconds()
        if time_since_last >= 1.0 or progress_info['current_downloaded'] == progress_info['total_files']:
            self._print_progress(progress_info, current_time)
            self.last_update_time = current_time
    
    def _print_progress(self, progress_info, current_time):
        """Print progress information"""
        total_files = progress_info['total_files']
        current_downloaded = progress_info['current_downloaded']
        success_count = progress_info['success_count']
        failed_count = progress_info['failed_count']
        remaining_count = progress_info['remaining_count']
        
        if total_files > 0:
            progress_percent = (current_downloaded / total_files) * 100
        else:
            progress_percent = 0
        
        elapsed_time = (current_time - self.start_time).total_seconds()
        
        if current_downloaded > 0:
            avg_time_per_file = elapsed_time / current_downloaded
            estimated_remaining = avg_time_per_file * remaining_count
        else:
            estimated_remaining = 0
        
        bar_length = 30
        filled_length = int(bar_length * progress_percent / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r[{bar}] {progress_percent:5.1f}% | "
              f"Downloaded: {current_downloaded}/{total_files} | "
              f"Success: {success_count} | "
              f"Failed: {failed_count} | "
              f"Remaining: {remaining_count} | "
              f"Elapsed: {elapsed_time:.1f}s | "
              f"Estimated remaining: {estimated_remaining:.1f}s", end='', flush=True)
        
        # If download completed, newline
        if current_downloaded == total_files:
            print()  # Newline


def main():
    """
    Main function - Demonstrate custom progress tracking
    """
    print("Start demonstrating custom progress tracking for model download...")
    
    progress_tracker = CustomProgressTracker()
    
    repo_id = "OpenCSG/csg-wukong-1B"
    
    try:
        local_path = snapshot_download(
            repo_id=repo_id,
            progress_callback=progress_tracker.progress_callback,
            verbose=False,
            use_parallel=True,
            max_workers=4
        )
        
        print(f"\n✅ Download completed! Model saved to: {local_path}")
        
    except Exception as e:
        print(f"\n❌ Error during download: {e}")


if __name__ == "__main__":
    main() 