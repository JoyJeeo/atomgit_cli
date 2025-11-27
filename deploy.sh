#!/bin/bash
# -*- coding: utf-8 -*-

# AtomGit CLI 部署脚本
# 用法: ./deploy.sh [build|install|twine]
# pip install build twine
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 构建函数
build() {
    echo -e "${GREEN}[BUILD]${NC} 开始构建..."
    
    # 清理旧的构建文件
    echo -e "${YELLOW}清理旧的构建文件...${NC}"
    rm -rf dist/*
    
    # 构建
    echo -e "${YELLOW}开始构建包...${NC}"
    python -m build
    
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
    pip uninstall atomgit -y 2>/dev/null || true
    
    # 安装新版本
    echo -e "${YELLOW}安装新版本...${NC}"
    pip install "$WHL_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 安装成功！${NC}"
        echo -e "${GREEN}已安装版本：${NC}"
        pip show atomgit | grep "Version\|Location"
    else
        echo -e "${RED}✗ 安装失败！${NC}"
        exit 1
    fi
}

# 上传到 PyPI 函数
twine_upload() {
    echo -e "${GREEN}[TWINE]${NC} 准备上传到 PyPI..."
    
    # 检查环境变量
    if [ -z "$atomgitsdktoken" ]; then
        echo -e "${RED}✗ 错误：未设置环境变量 atomgitsdktoken${NC}"
        echo -e "${YELLOW}请设置环境变量：${NC}"
        echo -e "${YELLOW}  export atomgitsdktoken=\"your-token-here\"${NC}"
        echo ""
        echo -e "${YELLOW}提示：可以将以下内容添加到 ~/.bashrc 或 ~/.zshrc：${NC}"
        echo -e "${YELLOW}  export atomgitsdktoken=\"your-token-here\"${NC}"
        exit 1
    fi
    
    # 检查 dist 目录
    if [ ! -d "dist" ]; then
        echo -e "${RED}✗ dist 目录不存在！${NC}"
        echo -e "${YELLOW}请先运行: ./deploy.sh build${NC}"
        exit 1
    fi
    
    # 检查 dist 目录是否为空
    if [ -z "$(ls -A dist/)" ]; then
        echo -e "${RED}✗ dist 目录为空！${NC}"
        echo -e "${YELLOW}请先运行: ./deploy.sh build${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}准备上传的文件：${NC}"
    ls -lh dist/
    
    # 确认上传
    echo ""
    echo -e "${YELLOW}是否确认上传到 PyPI? (y/N)${NC}"
    read -r confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "${YELLOW}已取消上传${NC}"
        exit 0
    fi
    
    # 上传
    echo -e "${YELLOW}开始上传...${NC}"
    #twine upload dist/* -u "__token__" -p "$atomgitsdktoken"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 上传成功！${NC}"
    else
        echo -e "${RED}✗ 上传失败！${NC}"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "AtomGit CLI 部署脚本"
    echo ""
    echo "用法:"
    echo "  ./deploy.sh build       构建包（清理 dist 目录并重新构建）"
    echo "  ./deploy.sh install     安装构建好的包"
    echo "  ./deploy.sh twine       上传包到 PyPI"
    echo ""
    echo "环境变量:"
    echo "  atomgitsdktoken        PyPI 上传 token（使用 twine 时必需）"
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
        twine)
            twine_upload
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

