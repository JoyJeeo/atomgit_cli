#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from setuptools import setup

SETUP_ROOT = Path(__file__).resolve().parent
VERSION_NAMESPACE = {}
exec(
    SETUP_ROOT.joinpath("src", "atomgit", "version.py").read_text(encoding="utf-8"),
    VERSION_NAMESPACE,
)
__version__ = VERSION_NAMESPACE["__version__"]


# 读取README文件
def read_readme():
    try:
        return SETUP_ROOT.joinpath("README.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        return "AtomGit CLI - 基于Transformers和Hugging Face Hub的模型文件上传下载工具"


# 读取依赖文件
def read_requirements():
    try:
        lines = SETUP_ROOT.joinpath("requirements.txt").read_text(encoding="utf-8")
        return [
            line.strip()
            for line in lines.splitlines()
            if line.strip() and not line.startswith("#")
        ]
    except FileNotFoundError:
        return [
            "click>=8.1.7",
            "requests>=2.31.0",
            "tqdm>=4.66.1",
            "pathlib>=1.0.1",
            "colorama>=0.4.6",
            "tabulate>=0.9.0",
            "huggingface-hub>=0.20.0",
            "datasets>=2.16.0",
        ]


setup(
    script_name=str(SETUP_ROOT.joinpath("setup.py")),
    name="atomgit",
    version=__version__,
    author="JoyJeeo",
    author_email="JoyJeeo@163.com",
    description="AtomGit模型文件上传下载CLI工具",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/JoyJeeo/atomgit_cli",
    license="Apache-2.0",
    packages=[
        "atomgit",
        "atomgit.download",
        "atomgit.infrastructure",
        "atomgit.lifecycle",
        "atomgit.services",
    ],
    package_dir={"": "src"},
    py_modules=["atomgit_hub"],
    include_package_data=False,
    install_requires=read_requirements(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "atomgit=atomgit.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
    ],
    keywords="transformers huggingface model dataset upload download cli",
    project_urls={
        "Bug Reports": "https://github.com/JoyJeeo/atomgit_cli/issues",
        "Source": "https://github.com/JoyJeeo/atomgit_cli",
    },
)
