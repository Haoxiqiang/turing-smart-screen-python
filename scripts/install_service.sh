#!/bin/bash

# Turing Smart Screen Python - systemd服务安装脚本
# 该脚本用于安装systemd服务，使程序在系统启动时自动运行

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo "请不要以root用户运行此脚本"
    echo "systemd服务将为当前用户安装"
    exit 1
fi

# 获取当前用户名
USERNAME=$(whoami)

# 替换服务文件中的用户占位符
sed "s/%i/$USERNAME/g" "$SCRIPT_DIR/turing-smart-screen.service" > "/tmp/turing-smart-screen.service"

# 复制服务文件到systemd目录
echo "正在安装systemd服务..."
sudo cp "/tmp/turing-smart-screen.service" /etc/systemd/system/turing-smart-screen.service

# 重新加载systemd配置
echo "重新加载systemd配置..."
sudo systemctl daemon-reload

# 启用服务
echo "启用服务..."
sudo systemctl enable turing-smart-screen.service

# 显示服务状态
echo "服务安装完成！"
echo ""
echo "相关命令："
echo "  启动服务: sudo systemctl start turing-smart-screen"
echo "  停止服务: sudo systemctl stop turing-smart-screen"
echo "  重启服务: sudo systemctl restart turing-smart-screen"
echo "  查看状态: sudo systemctl status turing-smart-screen"
echo "  查看日志: journalctl -u turing-smart-screen -f"
echo ""
echo "程序将在系统启动时自动运行"