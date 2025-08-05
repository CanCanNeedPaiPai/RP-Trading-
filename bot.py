import os

# Debug 输出环境变量
print("=== DEBUG: 环境变量检查 ===")
print("DISCORD_TOKEN:", os.getenv("DISCORD_TOKEN"))
print("DISCORD_CHANNEL_ID:", os.getenv("DISCORD_CHANNEL_ID"))
print("=========================")

# 保持进程不退出，防止 Render 马上关掉
import time
while True:
    time.sleep(60)

