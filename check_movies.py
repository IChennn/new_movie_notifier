#!/usr/bin/env python3
"""
109 Cinemas Premium 新宿 - 新電影通知腳本
透過 LINE Messaging API 推播新上映電影
"""

import json
import os
import requests
from bs4 import BeautifulSoup

# 從環境變數讀取（在 GitHub Secrets 設定）
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

MOVIES_URL = "https://109cinemas.net/premiumshinjuku/movies.html"
DATA_FILE = "movies_seen.json"


def fetch_current_movies():
    """抓取目前上映中的電影列表"""
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(MOVIES_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    movies = {}

    for h3 in soup.select("h3"):
        title = h3.get_text(strip=True)
        if title:
            parent = h3.find_parent("a") or h3.find_parent("li") or h3
            link_tag = parent.find("a") if parent else None
            url = link_tag["href"] if link_tag and link_tag.get("href") else ""
            if url and not url.startswith("http"):
                url = "https://109cinemas.net" + url
            movies[title] = url

    return movies


def load_seen_movies():
    """讀取之前記錄的電影"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen_movies(movies):
    """儲存目前電影列表"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)


def send_line_message(text):
    """透過 LINE Messaging API 發送訊息"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()
    print("LINE 訊息發送成功！")


def main():
    print("正在抓取電影資訊...")
    current = fetch_current_movies()
    seen = load_seen_movies()

    new_movies = {t: u for t, u in current.items() if t not in seen}

    if new_movies:
        lines = ["🎬 新宿 Premier 109 有新電影上映！\n"]
        for title, url in new_movies.items():
            if url:
                lines.append(f"・{title}\n  {url}")
            else:
                lines.append(f"・{title}")
        message = "\n".join(lines)
        print(message)
        send_line_message(message)
    else:
        print("沒有新電影。")

    seen.update(current)
    save_seen_movies(seen)
    print(f"目前共記錄 {len(seen)} 部電影。")


if __name__ == "__main__":
    main()
