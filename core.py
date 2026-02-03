import os
import requests
import urllib.parse
import pygame
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from openai import OpenAI
from datetime import datetime
from gtts import gTTS

# Initialize pygame mixer globally
pygame.mixer.init()

# Global state tracking
user_states = {}
NEWS_API_KEY = "bcb884ea1ae74c0a9d558fe2100b0898"  # replace with your NewsAPI key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --- Voice Functions --- #
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
    except Exception as e:
        print("Voice error:", e)
    return text


def speak_telegram(chat_id, text, telegram_send_func):
    print(f"TELEGRAM VOICE: {text[:50]}...")
    try:
        tts = gTTS(text[:200])
        tts.save("telegram_voice.mp3")
        telegram_send_func(chat_id, "voice", file="telegram_voice.mp3")
        os.remove("telegram_voice.mp3")
    except Exception as e:
        print("Telegram voice error:", e)


def send_telegram_text(chat_id, text, telegram_send_func):
    telegram_send_func(chat_id, "text", text=text)


# --- News Functions --- #
def get_news_by_location(country="in", state=None, city=None):
    today = datetime.now().strftime("%B %d, %Y")
    q = (
        f"{city} {state} {country}"
        if city and city != "all"
        else f"{state} {country}" if state and state != "all" else country
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
                    news_text += f"{i+1}. {title}\n{link}\n\n"
            else:
                news_text += "No news found for this location"
        else:
            news_text += "News service unavailable"
    except:
        news_text += "News temporarily unavailable"
    return news_text


# --- Website / YouTube --- #
def open_website(url):
    try:
        subprocess.Popen(
            [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                url,
                "--new-window",
            ]
        )
        return f"Opened {url}"
    except:
        return f"Cannot open {url}, here is the link: {url}"


def play_youtube(query):
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
        return f"Playing '{query}' on YouTube"
    except:
        return f"YouTube: {search_url}"


# --- Command Handler --- #
def handle_command(
    user_input, chat_id=None, telegram_send_func=None, first_message=False
):
    user_input = user_input.lower().strip()
    print(f"USER SAID: {user_input}")

    # Initialize user state
    if chat_id and chat_id not in user_states:
        user_states[chat_id] = "main_menu"

    # Startup message
    if first_message:
        msg = "Hi Praneeth! Your Malar Ma is here"
        if chat_id == "laptop":
            speak_laptop(msg)
        elif telegram_send_func:
            send_telegram_text(chat_id, msg, telegram_send_func)
        return msg

    # Main menu trigger
    if "hi malar ma" in user_input or user_states.get(chat_id) == "main_menu":
        user_states[chat_id] = "main_menu"
        msg = """Praneeth! How can I help you today?  
Options:  
1. News  
2. Open YouTube  
3. Open Website  
Type your choice or say it."""
        if chat_id == "laptop":
            speak_laptop(msg)
        elif telegram_send_func:
            send_telegram_text(chat_id, msg, telegram_send_func)
        return msg

    # --- News flow with 3 chances --- #
    if "news" in user_input:
        user_states[chat_id] = ("waiting_country", 3)
        msg = "🌍 News - Select country: India, USA, UK, World"
        if chat_id == "laptop":
            speak_laptop(msg)
        elif telegram_send_func:
            send_telegram_text(chat_id, msg, telegram_send_func)
        return msg

    # Process country/state/city with attempts
    if chat_id and isinstance(user_states.get(chat_id), tuple):
        state_data = user_states[chat_id]
        if state_data[0] == "waiting_country":
            country = user_input
            attempts = state_data[1]
            if country.lower() not in ["india", "usa", "uk", "world"]:
                attempts -= 1
                if attempts <= 0:
                    user_states[chat_id] = "main_menu"
                    return (
                        speak_laptop(
                            "Too many failed attempts. Returning to main menu."
                        )
                        if chat_id == "laptop"
                        else send_telegram_text(
                            chat_id,
                            "Too many failed attempts. Returning to main menu.",
                            telegram_send_func,
                        )
                    )
                else:
                    user_states[chat_id] = ("waiting_country", attempts)
                    return (
                        speak_laptop(
                            f"Input not recognized. You have {attempts} tries left."
                        )
                        if chat_id == "laptop"
                        else send_telegram_text(
                            chat_id,
                            f"Input not recognized. You have {attempts} tries left.",
                            telegram_send_func,
                        )
                    )
            user_states[chat_id] = ("waiting_state", country, 3)
            msg = f"Country selected: {country}. Now select state."
            return (
                speak_laptop(msg)
                if chat_id == "laptop"
                else send_telegram_text(chat_id, msg, telegram_send_func)
            )

        elif state_data[0] == "waiting_state":
            country = state_data[1]
            state_name = user_input
            attempts = state_data[2]
            if not state_name:
                attempts -= 1
                if attempts <= 0:
                    user_states[chat_id] = "main_menu"
                    return (
                        speak_laptop(
                            "Too many failed attempts. Returning to main menu."
                        )
                        if chat_id == "laptop"
                        else send_telegram_text(
                            chat_id,
                            "Too many failed attempts. Returning to main menu.",
                            telegram_send_func,
                        )
                    )
                else:
                    user_states[chat_id] = ("waiting_state", country, attempts)
                    return (
                        speak_laptop(
                            f"Input not recognized. You have {attempts} tries left."
                        )
                        if chat_id == "laptop"
                        else send_telegram_text(
                            chat_id,
                            f"Input not recognized. You have {attempts} tries left.",
                            telegram_send_func,
                        )
                    )
            user_states[chat_id] = ("waiting_city", country, state_name, 3)
            msg = f"State selected: {state_name}. Now select city or say 'all'."
            return (
                speak_laptop(msg)
                if chat_id == "laptop"
                else send_telegram_text(chat_id, msg, telegram_send_func)
            )

        elif state_data[0] == "waiting_city":
            country, state_name, attempts = state_data[1], state_data[2], state_data[3]
            city = user_input
            if not city:
                attempts -= 1
                if attempts <= 0:
                    user_states[chat_id] = "main_menu"
                    return (
                        speak_laptop(
                            "Too many failed attempts. Returning to main menu."
                        )
                        if chat_id == "laptop"
                        else send_telegram_text(
                            chat_id,
                            "Too many failed attempts. Returning to main menu.",
                            telegram_send_func,
                        )
                    )
                else:
                    user_states[chat_id] = (
                        "waiting_city",
                        country,
                        state_name,
                        attempts,
                    )
                    return (
                        speak_laptop(
                            f"Input not recognized. You have {attempts} tries left."
                        )
                        if chat_id == "laptop"
                        else send_telegram_text(
                            chat_id,
                            f"Input not recognized. You have {attempts} tries left.",
                            telegram_send_func,
                        )
                    )
            # Get news
            news_text = get_news_by_location(country, state_name, city)
            user_states[chat_id] = "main_menu"
            return (
                speak_laptop(news_text)
                if chat_id == "laptop"
                else send_telegram_text(chat_id, news_text, telegram_send_func)
            )

    # --- Open YouTube --- #
    if "youtube" in user_input or "play" in user_input:
        query = (
            user_input.replace("youtube", "").replace("play", "").strip()
            or "popular song"
        )
        result = play_youtube(query)
        user_states[chat_id] = "main_menu"
        return (
            speak_laptop(result)
            if chat_id == "laptop"
            else send_telegram_text(chat_id, result, telegram_send_func)
        )

    # --- Open Website --- #
    if "open" in user_input:
        site = user_input.replace("open", "").strip()
        url = f"https://www.{site}.com"
        result = open_website(url)
        user_states[chat_id] = "main_menu"
        return (
            speak_laptop(result)
            if chat_id == "laptop"
            else send_telegram_text(chat_id, result, telegram_send_func)
        )

    # Default
    msg = "I didn't understand. Try again or say 'Hi Malar Ma' to see options."
    if chat_id == "laptop":
        return speak_laptop(msg)
    elif telegram_send_func:
        return send_telegram_text(chat_id, msg, telegram_send_func)
