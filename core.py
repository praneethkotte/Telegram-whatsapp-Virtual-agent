import os
import requests
import urllib.parse
import subprocess
import time
from datetime import datetime
from gtts import gTTS
import pygame
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

pygame.mixer.init()

user_states = {}


def speak_laptop(text):
    print(f"Assistan: {text}")
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


def speak_telegram(chat_id, text, bot):
    try:
        tts = gTTS(text[:200])
        tts.save("telegram_voice.mp3")
        with open("telegram_voice.mp3", "rb") as audio:
            bot.send_voice(chat_id=chat_id, voice=audio)
        os.remove("telegram_voice.mp3")
    except:
        pass


def speak_whatsapp(text):
    try:
        tts = gTTS(text[:200])
        tts.save("whatsapp_voice.mp3")
        return "whatsapp_voice.mp3"
    except:
        return None


def main_menu(chat_id=None, platform="laptop", bot=None):
    response = (
        "Praneeth! Your Assistan is here. What can I do today?\n"
        "Say or type:\n"
        "1. News\n"
        "2. Open YouTube\n"
        "3. Open Website"
    )

    if platform == "telegram" and bot:
        speak_telegram(chat_id, "How can I help you today?", bot)
        bot.send_message(chat_id=chat_id, text=response)

    return speak_laptop(response)


def ask_country(chat_id=None, platform="laptop", bot=None):
    user_states[chat_id] = "waiting_country"
    msg = "Select country: India, USA, UK, or World."
    if platform == "telegram" and bot:
        speak_telegram(chat_id, "Which country?", bot)
        bot.send_message(chat_id=chat_id, text=msg)
    return speak_laptop(msg)


def ask_state(chat_id, country, platform="laptop", bot=None):
    user_states[chat_id] = ("waiting_state", country)
    msg = f"Now say a state name in {country}."
    if platform == "telegram" and bot:
        speak_telegram(chat_id, f"{country} news. Which state?", bot)
        bot.send_message(chat_id=chat_id, text=msg)
    return speak_laptop(msg)


def ask_city(chat_id, country, state, platform="laptop", bot=None):
    user_states[chat_id] = ("waiting_city", country, state)
    msg = f"Now say a city in {state}."
    if platform == "telegram" and bot:
        speak_telegram(chat_id, f"{state} news. Which city?", bot)
        bot.send_message(chat_id=chat_id, text=msg)
    return speak_laptop(msg)


def get_news(country, state, city):
    today = datetime.now().strftime("%B %d, %Y")
    query = f"{city} {state} {country}"
    url = f"https://newsapi.org/v2/everything?q={urllib.parse.quote(query)}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])

            if not articles:
                return None

            news_text = f"TOP NEWS FOR {city}, {state}, {country} — {today}\n\n"

            for i, article in enumerate(articles[:3]):
                news_text += f"{i+1}. {article['title']}\n{article['url']}\n\n"

            return news_text
        else:
            return None
    except:
        return None


def open_website(site):
    url = f"https://www.{site}.com"
    subprocess.Popen(
        [r"C:\Program Files\Google\Chrome\Application\chrome.exe", url, "--new-window"]
    )
    return f"Opened {site}: {url}"


def handle_command(user_input, chat_id=None, platform="laptop", bot=None):
    user_input = user_input.lower().strip()

    if chat_id not in user_states:
        user_states[chat_id] = "main_menu"

    if "hi Assistan" in user_input:
        user_states[chat_id] = "main_menu"
        return main_menu(chat_id, platform, bot)

    state = user_states.get(chat_id)

    if state == "waiting_country":
        country = user_input
        return ask_state(chat_id, country, platform, bot)

    if isinstance(state, tuple) and state[0] == "waiting_state":
        country = state[1]
        state_name = user_input
        return ask_city(chat_id, country, state_name, platform, bot)

    if isinstance(state, tuple) and state[0] == "waiting_city":
        country, state_name = state[1], state[2]
        city = user_input

        news = get_news(country, state_name, city)

        if not news:
            msg = (
                "No news found for this city.\n"
                "Do you want:\n"
                "1. Try another city\n"
                "2. Try another state\n"
                "3. Back to main menu"
            )
            if platform == "telegram" and bot:
                speak_telegram(chat_id, "No news found. What next?", bot)
                bot.send_message(chat_id=chat_id, text=msg)
            return speak_laptop(msg)

        user_states[chat_id] = "main_menu"

        if platform == "telegram" and bot:
            speak_telegram(chat_id, f"Here is latest news for {city}", bot)
            bot.send_message(chat_id=chat_id, text=news)

        return speak_laptop(news)

    if "news" in user_input:
        user_states[chat_id] = "waiting_country"
        return ask_country(chat_id, platform, bot)

    if user_input.startswith("open "):
        site = user_input.replace("open ", "").strip()
        result = open_website(site)

        if platform == "telegram" and bot:
            bot.send_message(chat_id=chat_id, text=result)

        return speak_laptop(result)

    return main_menu(chat_id, platform, bot)
