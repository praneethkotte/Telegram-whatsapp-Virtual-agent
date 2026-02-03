import os
import threading
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from core import handle_command

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LOCAL_MODE = os.getenv("LOCAL_MODE", "true").lower() == "true"

greeted_users = set()


def telegram_send_func(chat_id, msg_type, text=None, file=None):
    from telegram import Bot

    bot = Bot(token=TELEGRAM_TOKEN)
    if msg_type == "text":
        bot.send_message(chat_id, text)
    elif msg_type == "voice":
        bot.send_voice(chat_id, open(file, "rb"))


async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in greeted_users:
        greeted_users.add(chat_id)
        handle_command("startup", chat_id, telegram_send_func)
    if update.message.voice:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        await voice_file.download_to_drive("voice.ogg")
        # Use OpenAI Whisper or skip transcription here
        text = "voice input received"
        handle_command(text, chat_id, telegram_send_func)
        os.remove("voice.ogg")
        return
    if update.message.text:
        text = update.message.text
        handle_command(text, chat_id, telegram_send_func)


def laptop_listener():
    from inputimeout import inputimeout, TimeoutOccurred

    while True:
        try:
            user_input = inputimeout(prompt="YOU (Laptop): ", timeout=10)
            if user_input:
                handle_command(user_input, "laptop")
        except TimeoutOccurred:
            continue


if __name__ == "__main__":
    if LOCAL_MODE:
        thread = threading.Thread(target=laptop_listener, daemon=True)
        thread.start()

        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(
            MessageHandler(filters.TEXT | filters.VOICE, handle_telegram_message)
        )
        print("Malar Ma Ready! Laptop + Telegram Mode")
        app.run_polling()
