#!/bin/bash

# Turing Smart Screen Python - 后台运行脚本
# 该脚本用于在后台启动turing-smart-screen-python程序

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/turing.pid"
LOG_FILE="$SCRIPT_DIR/turing.log"

# 检查是否已经运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "程序已经在运行 (PID: $PID)"
        exit 1
    else
        # PID文件存在但进程不存在，删除PID文件
        rm -f "$PID_FILE"
    fi
fi

# 激活虚拟环境（如果存在）
if [ -f "$SCRIPT_DIR/venv3/bin/activate" ]; then
    source "$SCRIPT_DIR/venv3/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# 后台运行程序
echo "正在后台启动turing-smart-screen-python..."
nohup "$SCRIPT_DIR/venv3/bin/python3" "$SCRIPT_DIR/main.py" > "$LOG_FILE" 2>&1 &

# 保存PID
echo $! > "$PID_FILE"

echo "程序已在后台运行 (PID: $(cat "$PID_FILE"))"
echo "日志文件: $LOG_FILE"
echo "使用 'stop.sh' 脚本停止程序"