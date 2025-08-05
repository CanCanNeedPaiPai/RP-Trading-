import os
import discord
import requests
import feedparser
from discord.ext import tasks
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# 保存已发送的新闻ID，避免重复
last_rss_id = None
last_tweet_id = None


# 翻译函数（DeepL）
def translate_text(text, target_lang="ZH"):
    if not DEEPL_API_KEY:
        return f"[未配置DEEPL] {text}"

    url = "https://api-free.deepl.com/v2/translate"
    payload = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "target_lang": target_lang
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()["translations"][0]["text"]
    return text


# 获取 RSS 新闻（CoinDesk）
def fetch_rss_news():
    feed = feedparser.parse("https://www.coindesk.com/arc/outboundfeeds/rss/")
    if not feed.entries:
        return None

    entry = feed.entries[0]  # 最新一条
    title = entry.title
    link = entry.link
    news_id = entry.id if "id" in entry else entry.link

    image_url = None
    if "media_content" in entry:
        image_url = entry.media_content[0]['url']

    return news_id, title, link, image_url


# 获取 Twitter 新闻
def fetch_twitter_news(username="business"):
    if not TWITTER_BEARER_TOKEN:
        return None

    url = f"https://api.twitter.com/2/tweets/search/recent?query=from:{username}&tweet.fields=created_at&max_results=5"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("❌ Twitter API 调用失败:", response.text)
        return None

    data = response.json()
    if "data" not in data:
        return None

    latest_tweet = data["data"][0]
    text = latest_tweet["text"]
    tweet_id = latest_tweet["id"]
    link = f"https://twitter.com/{username}/status/{tweet_id}"

    return tweet_id, text, link


@client.event
async def on_ready():
    print(f"✅ 已登录为 {client.user}")
    check_news.start()


# 每 10 秒检查一次新闻
@tasks.loop(seconds=10)
async def check_news():
    global last_rss_id, last_tweet_id
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ 找不到频道，请检查 CHANNEL_ID")
        return

    # ====== 检查 RSS 新闻 ======
    news = fetch_rss_news()
    if news:
        news_id, title, link, image_url = news
        if news_id != last_rss_id:  # 只发新的
            last_rss_id = news_id
            zh_title = translate_text(title, "ZH")

            embed = discord.Embed(
                title="🌐 RSS 财经快讯",
                description=f"**英文**: {title}\n\n**中文**: {zh_title}\n\n🔗 [阅读原文]({link})",
                color=0x00BFFF
            )
            if image_url:
                embed.set_image(url=image_url)

            await channel.send(embed=embed)

    # ====== 检查 Twitter 新闻 ======
    tweet = fetch_twitter_news("business")
    if tweet:
        tweet_id, text, link = tweet
        if tweet_id != last_tweet_id:  # 只发新的
            last_tweet_id = tweet_id
            zh_text = translate_text(text, "ZH")

            embed = discord.Embed(
                title="🐦 Twitter 财经速递",
                description=f"**英文**: {text}\n\n**中文**: {zh_text}\n\n🔗 [查看推文]({link})",
                color=0x1DA1F2
            )
            await channel.send(embed=embed)


client.run(DISCORD_TOKEN)

