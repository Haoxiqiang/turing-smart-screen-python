#!/bin/bash

# Turing Smart Screen Python - 桌面启动器安装脚本
# 该脚本用于在用户桌面环境安装启动器

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 创建应用程序目录（如果不存在）
mkdir -p ~/.local/share/applications

# 复制桌面文件
cp "$SCRIPT_DIR/turing-smart-screen.desktop" ~/.local/share/applications/

# 更新桌面数据库
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications
fi

echo "桌面启动器已安装"
echo "你可以在应用程序菜单中找到 'Turing Smart Screen Python'"