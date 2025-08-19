#!/usr/bin/env python3
"""
Demonstrate how to use the progress callback feature of snapshot_download
"""

import time
from pycsghub import snapshot_download


def progress_callback(progress_info):
    """
    Progress callback function
    Receives download progress information and prints it
    """
    print(f"\n=== Download progress update ===")
    print(f"Total files: {progress_info['total_files']}")
    print(f"Current downloaded: {progress_info['current_downloaded']}")
    print(f"Success count: {progress_info['success_count']}")
    print(f"Failed count: {progress_info['failed_count']}")
    print(f"Remaining count: {progress_info['remaining_count']}")
    
    if progress_info['successful_files']:
        print(f"Recently successful downloaded file: {progress_info['successful_files'][-1]}")
    
    if progress_info['remaining_files']:
        print(f"Next file to download: {progress_info['remaining_files'][0]}")
    
    if progress_info['total_files'] > 0:
        progress_percent = (progress_info['current_downloaded'] / progress_info['total_files']) * 100
        print(f"Overall progress: {progress_percent:.1f}%")
    
    print("=" * 30)


def main():
    """
    Main function - Demonstrate download with progress callback
    """
    print("Start demonstrating download with progress callback...")
    
    # Example model ID (please replace with actual model ID)
    repo_id = "example/model"
    
    try:
        # Use progress callback to download model
        local_path = snapshot_download(
            repo_id=repo_id,
            progress_callback=progress_callback,
            verbose=True,
            use_parallel=True,
            max_workers=4
        )
        
        print(f"\nDownload completed! Model saved to: {local_path}")
        
    except Exception as e:
        print(f"Error during download: {e}")


if __name__ == "__main__":
    main() 