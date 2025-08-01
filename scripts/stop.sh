#!/bin/bash

# Turing Smart Screen Python - 停止脚本
# 该脚本用于停止后台运行的turing-smart-screen-python程序

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/turing.pid"

# 检查PID文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "程序似乎没有在运行 (PID文件不存在)"
    exit 1
fi

# 读取PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ps -p $PID > /dev/null; then
    echo "正在停止程序 (PID: $PID)..."
    kill $PID
    
    # 等待进程结束
    TIMEOUT=30
    COUNT=0
    while ps -p $PID > /dev/null && [ $COUNT -lt $TIMEOUT ]; do
        sleep 1
        COUNT=$((COUNT + 1))
    done
    
    # 如果进程仍未结束，强制杀死
    if ps -p $PID > /dev/null; then
        echo "进程未正常退出，强制终止..."
        kill -9 $PID
    fi
    
    # 删除PID文件
    rm -f "$PID_FILE"
    echo "程序已停止"
else
    echo "程序未在运行 (PID: $PID)"
    # 删除过期的PID文件
    rm -f "$PID_FILE"
fi