import os
import requests
from flask import Flask, request
from core import handle_command
from dotenv import load_dotenv
from gtts import gTTS

load_dotenv()

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"


def send_text(chat_id, text):
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


def send_voice(chat_id, text):
    tts = gTTS(text)
    tts.save("reply.mp3")

    url = BASE_URL + "sendVoice"
    files = {"voice": open("reply.mp3", "rb")}
    data = {"chat_id": chat_id}

    requests.post(url, files=files, data=data)
    os.remove("reply.mp3")


@app.route("/", methods=["POST"])
def receive_update():
    data = request.json
    chat_id = data["message"]["chat"]["id"]

    if "text" in data["message"]:
        user_text = data["message"]["text"]
        reply = handle_command(user_text)
        send_text(chat_id, reply)
        send_voice(chat_id, reply)

    elif "voice" in data["message"]:
        send_text(chat_id, "I heard your voice! Please type your command for now.")
        # (Later I can add real speech-to-text here)

    return {"ok": True}


if __name__ == "__main__":
    app.run(port=5000)
