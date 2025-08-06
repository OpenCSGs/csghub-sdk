#!/usr/bin/env python3
"""
构建脚本，用于处理版本信息
"""

import re
from pathlib import Path


def get_version():
    """从pyproject.toml中获取版本号"""
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'version = "([^"]+)"', content)
            if match:
                return match.group(1)
    return "0.7.4"  # 默认版本


def update_version_in_init():
    """更新__init__.py中的版本号"""
    init_path = Path("pycsghub/__init__.py")
    if init_path.exists():
        with open(init_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 更新版本号
        new_content = re.sub(
            r'__version__ = "[^"]*"',
            f'__version__ = "{get_version()}"',
            content
        )

        with open(init_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated version to {get_version()} in __init__.py")


if __name__ == "__main__":
    update_version_in_init()
