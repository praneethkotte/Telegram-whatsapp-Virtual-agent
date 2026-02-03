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

    return {"ok": True}


if __name__ == "__main__":
    import os

    # LOCAL MODE (VSCode testing)
    if os.getenv("LOCAL_MODE") == "true":
        print("🟢 MalarMa LOCAL MODE activated (polling)...")
        from telegram.ext import Application, CommandHandler, MessageHandler, filters

        app = Application.builder().token(TELEGRAM_TOKEN).build()

        async def start(update, context):
            await update.message.reply_text(
                "🚀 MalarMa LOCAL! Try: news, how are you, play song"
            )

        async def handle_message(update, context):
            user_text = update.message.text
            reply = handle_command(user_text)
            await update.message.reply_text(reply)

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        print("✅ Polling active - Test in Telegram!")
        app.run_polling()

    # PRODUCTION MODE (Render webhook)
    else:
        print("🌐 MalarMa PRODUCTION MODE (webhook)...")
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port, debug=False)
