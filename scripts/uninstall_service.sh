#!/bin/bash

# Turing Smart Screen Python - systemd服务卸载脚本
# 该脚本用于卸载systemd服务

# 停止服务
echo "正在停止服务..."
sudo systemctl stop turing-smart-screen.service

# 禁用服务
echo "正在禁用服务..."
sudo systemctl disable turing-smart-screen.service

# 删除服务文件
echo "正在删除服务文件..."
sudo rm -f /etc/systemd/system/turing-smart-screen.service

# 重新加载systemd配置
echo "重新加载systemd配置..."
sudo systemctl daemon-reload

echo "服务已成功卸载"