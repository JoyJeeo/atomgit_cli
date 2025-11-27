#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AtomGit CLI 主入口文件

使用方法:
    python -m atomgit [command] [options]
"""

try:
    from .cli import cli
except ImportError:
    from cli import cli

if __name__ == '__main__':
    cli() 