#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "AtomGit CLI - 基于Transformers和Hugging Face Hub的模型文件上传下载工具"

# 读取依赖文件
def read_requirements():
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return [
            'click>=8.1.7',
            'requests>=2.31.0',
            'tqdm>=4.66.1',
            'pathlib>=1.0.1',
            'colorama>=0.4.6',
            'tabulate>=0.9.0',
            'huggingface-hub>=0.20.0',
            'datasets>=2.16.0'
        ]

setup(
    name='atomgit',
    version='1.0.5+yuto.1',
    author='JoyJeeo',
    author_email='JoyJeeo@163.com',
    description='AtomGit模型文件上传下载CLI工具',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/JoyJeeo/atomgit_cli',
    license='Apache-2.0',
    packages=['atomgit'],
    package_dir={'atomgit': '.'},
    py_modules=['atomgit_hub'],
    install_requires=read_requirements(),
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'atomgit=atomgit.cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving',
        'Topic :: Utilities',
    ],
    keywords='transformers huggingface model dataset upload download cli',
    project_urls={
        'Bug Reports': 'https://github.com/JoyJeeo/atomgit_cli/issues',
        'Source': 'https://github.com/JoyJeeo/atomgit_cli',
    },
)
