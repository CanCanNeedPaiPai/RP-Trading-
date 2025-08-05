import os
import requests
import feedparser
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import discord
from discord.ext import tasks

# 读取环境变量
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
translator = GoogleTranslator(source="en", target="zh-CN")

# 你的新闻源（RSS 优先，网页备用）
RSS_FEEDS = [
    "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",   # WSJ Markets
    "https://www.coindesk.com/arc/outboundfeeds/rss/", # CoinDesk
]
WEB_FALLBACKS = [
    "https://www.bloomberg.com/crypto",
    "https://www.reuters.com/markets/",
]

latest_titles = set()

def fetch_from_rss():
    """优先从 RSS 获取新闻"""
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = entry.title
                link = entry.link
                # 获取封面图（如果 RSS 有）
                image = None
                if "media_content" in entry and len(entry.media_content) > 0:
                    image = entry.media_content[0]["url"]
                elif "media_thumbnail" in entry and len(entry.media_thumbnail) > 0:
                    image = entry.media_thumbnail[0]["url"]

                articles.append((title, link, image))
        except Exception as e:
            print(f"RSS 抓取失败: {url}, 错误: {e}")
    return articles

def fetch_from_web():
    """兜底从网页抓取新闻"""
    articles = []
    for url in WEB_FALLBACKS:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            # 抓前3个标题
            for h in soup.find_all(["h2", "h3"])[:3]:
                title = h.get_text(strip=True)
                link = h.find("a")["href"] if h.find("a") else url
                if not link.startswith("http"):
                    link = url + link
                # 找图片
                img = soup.find("img")
                image = img["src"] if img else None
                articles.append((title, link, image))
        except Exception as e:
            print(f"网页抓取失败: {url}, 错误: {e}")
    return articles

@tasks.loop(seconds=10)  # 每 10 秒检查一次
async def fetch_and_post():
    global latest_titles
    channel = client.get_channel(DISCORD_CHANNEL_ID)

    # 先尝试 RSS
    articles = fetch_from_rss()

    # 如果 RSS 没抓到，再用网页
    if not articles:
        articles = fetch_from_web()

    for title, link, image in articles:
        if title not in latest_titles:
            latest_titles.add(title)

            # 翻译中文
            try:
                translation = translator.translate(title)
            except Exception:
                translation = "翻译失败"

            embed = discord.Embed(
                title=title,
                url=link,
                description=f"**中文翻译：** {translation}"
            )
            if image:
                embed.set_image(url=image)

            await channel.send(embed=embed)

@client.event
async def on_ready():
    print(f"机器人已上线：{client.user}")
    fetch_and_post.start()

client.run(DISCORD_TOKEN)
