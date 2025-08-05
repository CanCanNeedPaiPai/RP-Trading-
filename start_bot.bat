@echo off
cd /d %~dp0

echo ======================================
echo 🚀 正在检查依赖并安装 requirements.txt
echo ======================================

pip install -r requirements.txt

echo ======================================
echo ✅ 依赖安装完成，启动机器人...
echo ======================================

python bot.py

pause
