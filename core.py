import os
import requests
import urllib.parse
import pygame
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from gtts import gTTS
from pathlib import Path

# Load .env properly
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# News API key
NEWS_API_KEY = "bcb884ea1ae74c0a9d558fe2100b0898"

# Pygame init
pygame.mixer.init()

# Track user states for Telegram
user_states = {}

# Retry limit
RETRY_LIMIT = 3


# ---- Voice functions ----
def speak_laptop(text):
    print(f"MALARMA: {text}")
    try:
        tts = gTTS(text)
        tts.save("temp.mp3")
        pygame.mixer.music.load("temp.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        os.remove("temp.mp3")
    except:
        pass
    return text


def speak_telegram(chat_id, text):
    try:
        tts = gTTS(text[:200])
        tts.save("telegram_voice.mp3")
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVoice"
        with open("telegram_voice.mp3", "rb") as f:
            files = {"voice": f}
            data = {"chat_id": chat_id}
            requests.post(url, files=files, data=data)
        os.remove("telegram_voice.mp3")
    except:
        pass


def send_telegram_text(chat_id, text):
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    requests.post(url, json=data)


# ---- News functions ----
def get_news_by_location(country="in", state=None, city=None):
    today = datetime.now().strftime("%B %d, %Y")
    q = (
        f"{city} {state} {country}"
        if city
        else f"{state} {country}" if state else country
    )
    news_text = f"TOP {q.upper()} NEWS {today}:\n\n"
    url = f"https://newsapi.org/v2/everything?q={urllib.parse.quote(q)}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            if articles:
                for i, article in enumerate(articles[:3]):
                    title = (
                        article["title"][:80] + "..."
                        if len(article["title"]) > 80
                        else article["title"]
                    )
                    link = article.get("url", "")
                    news_text += f"{i+1}. <b>{title}</b>\n{link}\n\n"
            else:
                news_text += "No news found."
        else:
            news_text += "News service unavailable."
    except:
        news_text += "News temporarily unavailable."
    return news_text


# ---- Music / website ----
def play_music(query):
    search_url = (
        f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    )
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--new-window")
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        driver.get(search_url)
        time.sleep(4)
        first_video = driver.find_element(By.ID, "video-title")
        first_video.click()
        return f"Playing '{query}' on YouTube:\n{search_url}"
    except:
        return f"YouTube: {search_url}"


def open_website(url):
    try:
        subprocess.Popen(
            [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                url,
                "--new-window",
            ]
        )
        return f"Opened: {url}"
    except:
        return f"Link: {url}"


# ---- AI command handler ----
def handle_command(user_input, chat_id=None, first_message=False):
    global user_states
    user_input = user_input.lower().strip()
    print(f"USER SAID: {user_input}")

    # Startup greeting
    if first_message:
        msg = "Hi Praneeth! Your Malar Ma is here"
        speak_laptop(msg)
        if chat_id:
            send_telegram_text(chat_id, msg)
        return msg

    # Initialize user state
    if chat_id and chat_id not in user_states:
        user_states[chat_id] = "main_menu"

    # ---- NEWS FLOW ----
    if "news" in user_input:
        # Ask country
        retries = 0
        while retries < RETRY_LIMIT:
            country = input("Country (Laptop) or enter via Telegram: ").strip()
            if country:
                break
            retries += 1
        else:
            country = "India"

        # Ask state
        retries = 0
        while retries < RETRY_LIMIT:
            state = input("State (Laptop) or enter via Telegram: ").strip()
            if state:
                break
            retries += 1
        else:
            state = "All"

        # Ask city
        retries = 0
        while retries < RETRY_LIMIT:
            city = input(
                "City (Laptop) or enter via Telegram (type 'all' for none): "
            ).strip()
            if city:
                break
            retries += 1
        else:
            city = None

        news_text = get_news_by_location(country, state, city)
        print(news_text)
        if chat_id:
            send_telegram_text(chat_id, news_text)
            speak_telegram(chat_id, news_text)
        return news_text

    # ---- OPEN WEBSITE ----
    elif user_input.startswith("open "):
        site_name = user_input[5:].strip()
        if not site_name.startswith("http"):
            site_name = f"https://www.{site_name}.com"
        msg = open_website(site_name)
        if chat_id:
            send_telegram_text(chat_id, msg)
        speak_laptop(msg)
        return msg

    # ---- PLAY MUSIC ----
    elif "play" in user_input:
        song = user_input.replace("play", "").strip()
        msg = play_music(song)
        if chat_id:
            send_telegram_text(chat_id, msg)
        speak_laptop(msg)
        return msg

    # ---- DEFAULT AI RESPONSE ----
    else:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly virtual assistant named Malar Ma",
                },
                {"role": "user", "content": user_input},
            ],
        )
        output = completion.choices[0].message.content
        if chat_id:
            send_telegram_text(chat_id, output)
            speak_telegram(chat_id, output)
        speak_laptop(output)
        return output
