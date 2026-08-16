#!/bin/bash
# -*- coding: utf-8 -*-

# AtomGit CLI 本地构建脚本
# 用法: ./deploy.sh [build|install|checksums]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

require_conda_python() {
    if [ -z "${CONDA_PREFIX:-}" ] || [ ! -x "$CONDA_PREFIX/bin/python" ]; then
        echo -e "${RED}✗ 请先激活目标 conda 环境${NC}"
        exit 1
    fi
    PYTHON_BIN="$CONDA_PREFIX/bin/python"
}

# 构建函数
build() {
    require_conda_python
    echo -e "${GREEN}[BUILD]${NC} 开始构建..."
    
    # 清理旧的构建文件
    echo -e "${YELLOW}清理旧的构建文件...${NC}"
    rm -rf dist/*
    
    # 构建
    echo -e "${YELLOW}开始构建包...${NC}"
    "$PYTHON_BIN" -m build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 构建成功！${NC}"
        echo -e "${GREEN}构建产物：${NC}"
        ls -lh dist/
    else
        echo -e "${RED}✗ 构建失败！${NC}"
        exit 1
    fi
}

# 安装函数
install() {
    require_conda_python
    echo -e "${GREEN}[INSTALL]${NC} 开始安装..."
    
    # 检查 dist 目录是否存在
    if [ ! -d "dist" ]; then
        echo -e "${RED}✗ dist 目录不存在！${NC}"
        echo -e "${YELLOW}请先运行: ./deploy.sh build${NC}"
        exit 1
    fi
    
    # 查找 whl 文件
    WHL_FILE=$(ls dist/*.whl 2>/dev/null | head -n 1)
    
    if [ -z "$WHL_FILE" ]; then
        echo -e "${RED}✗ 未找到 .whl 文件！${NC}"
        echo -e "${YELLOW}请先运行: ./deploy.sh build${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}找到安装包: $WHL_FILE${NC}"
    
    # 卸载旧版本
    echo -e "${YELLOW}卸载旧版本...${NC}"
    "$PYTHON_BIN" -m pip uninstall atomgit -y 2>/dev/null || true
    
    # 安装新版本
    echo -e "${YELLOW}安装新版本...${NC}"
    "$PYTHON_BIN" -m pip install "$WHL_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 安装成功！${NC}"
        echo -e "${GREEN}已安装版本：${NC}"
        "$PYTHON_BIN" -m pip show atomgit | grep "Version\|Location"
    else
        echo -e "${RED}✗ 安装失败！${NC}"
        exit 1
    fi
}

checksums() {
    require_conda_python
    if [ ! -d "dist" ]; then
        echo -e "${RED}✗ dist 目录不存在；请先运行 ./deploy.sh build${NC}"
        exit 1
    fi
    wheel_file=$(find dist -maxdepth 1 -type f -name 'atomgit-*.whl' -print -quit)
    if [ -z "$wheel_file" ]; then
        echo -e "${RED}✗ 未找到 AtomGit wheel${NC}"
        exit 1
    fi
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$wheel_file" > dist/SHA256SUMS
    else
        shasum -a 256 "$wheel_file" > dist/SHA256SUMS
    fi
    echo -e "${GREEN}✓ 已生成 dist/SHA256SUMS；仅供 GitHub Release 审核使用${NC}"
}

# 显示帮助信息
show_help() {
    echo "AtomGit CLI 部署脚本"
    echo ""
    echo "用法:"
    echo "  ./deploy.sh build       构建包（清理 dist 目录并重新构建）"
    echo "  ./deploy.sh install     安装构建好的包"
    echo "  ./deploy.sh checksums   生成 GitHub Release 所需 SHA256SUMS"
    echo ""
    echo "build/install/checksums 必须在已激活的 conda 环境中运行。"
}

# 主函数
main() {
    case "${1:-}" in
        build)
            build
            ;;
        install)
            install
            ;;
        checksums)
            checksums
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}✗ 未知命令: ${1:-}${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
