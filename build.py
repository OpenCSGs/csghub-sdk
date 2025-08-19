#!/usr/bin/env python3
"""
Build script for handling version information
"""

import re
from pathlib import Path


def get_version():
    """Get version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'version = "([^"]+)"', content)
            if match:
                return match.group(1)
    return "0.1.0"  # default version


def update_version_in_init():
    """Update version in __init__.py"""
    init_path = Path("pycsghub/__init__.py")
    if init_path.exists():
        with open(init_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Update version
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
