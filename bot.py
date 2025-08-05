import os
import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 加载 .env 文件中的变量
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# 设置 Intents
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# 启动事件
@client.event
async def on_ready():
    print(f"✅ 已登录机器人账号: {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("📢 机器人已上线，开始推送财经快讯！（带图片预览 + 双语）")
    news_job.start()

# 定时任务：获取新闻
@tasks.loop(minutes=5)  # 每 5 分钟执行一次
async def news_job():
    url = "https://www.bloomberg.com/markets"  # 你可以换成任何财经新闻源
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    # 解析 Bloomberg 新闻标题和链接
    article = soup.find("a", class_="story-package-module__story__headline-link")
    if not article:
        return

    title = article.get_text(strip=True)
    link = "https://www.bloomberg.com" + article["href"]

    # 简单翻译（这里为了演示，直接加上中文提示）
    translated = f"【中文翻译】{title}"

    # 尝试获取图片
    img_tag = soup.find("img")
    image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

    # 发送到 Discord
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="📢 Bloomberg 快讯",
            description=f"🌍 英文: {title}\n\n🇨🇳 中文: {translated}\n\n🔗 [阅读原文]({link})",
            color=0x1E90FF
        )
        if image_url:
            embed.set_image(url=image_url)

        await channel.send(embed=embed)

# 启动机器人
client.run(TOKEN)
