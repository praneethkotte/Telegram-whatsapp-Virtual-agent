import os
import threading
import speech_recognition as sr
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from core import handle_command, speak_laptop
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def laptop_voice_listener():
    r = sr.Recognizer()
    mic = sr.Microphone()

    print("LAPTOP VOICE ACTIVE")

    while True:
        try:
            with mic as source:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            text = r.recognize_google(audio)
            print(f"LAPTOP VOICE YOU: {text}")
            handle_command(text, chat_id="laptop", platform="laptop")
        except:
            pass


def laptop_keyboard_listener():
    print("LAPTOP KEYBOARD ACTIVE — You can type now")
    while True:
        user_input = input("YOU (Laptop): ")
        handle_command(user_input, chat_id="laptop", platform="laptop")


async def telegram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if update.message.text:
        text = update.message.text
        reply = handle_command(text, chat_id, platform="telegram", bot=context.bot)
        await update.message.reply_text(reply)

    if update.message.voice:
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive("voice.ogg")

        import speech_recognition as sr

        r = sr.Recognizer()

        with sr.AudioFile("voice.ogg") as source:
            audio = r.record(source)

        text = r.recognize_google(audio)
        os.remove("voice.ogg")

        reply = handle_command(text, chat_id, platform="telegram", bot=context.bot)
        await update.message.reply_text(reply)


if __name__ == "__main__":
    print("Starting Malar Ma...")
    speak_laptop("Hi Praneeth! Your Malar Ma is here.")

    threading.Thread(target=laptop_voice_listener, daemon=True).start()
    threading.Thread(target=laptop_keyboard_listener, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.VOICE, telegram_handler))

    print("BOT IS LIVE — Telegram + Laptop Ready")
    app.run_polling()
