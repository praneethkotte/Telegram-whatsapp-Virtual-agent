import os
import threading
import speech_recognition as sr
from core import handle_command
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Load dotenv
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Track users
greeted_users = set()
user_states = {}


# ---- LAPTOP VOICE / KEYBOARD LISTENER ----
def laptop_listener():
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source)
    print("LAPTOP MIC ACTIVE")
    while True:
        try:
            # Keyboard input
            user_input = input("YOU (Laptop): ").strip()
            if user_input:
                handle_command(user_input)
        except Exception as e:
            print(f"Error: {e}")


# ---- TELEGRAM HANDLER ----
async def telegram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in greeted_users:
        greeted_users.add(chat_id)
        handle_command("startup", chat_id, first_message=True)

    # Voice message
    if update.message.voice:
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive("voice.ogg")
        text = "Voice transcription not implemented here yet"
        handle_command(text, chat_id)
        return

    # Text message
    if update.message.text:
        handle_command(update.message.text, chat_id)


# ---- MAIN ----
if __name__ == "__main__":
    # Start laptop thread
    threading.Thread(target=laptop_listener, daemon=True).start()

    # Start Telegram using v20+ correct builder
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.VOICE, telegram_handler))

    print("MALAR MA READY! Laptop & Telegram active.")

    # Run the bot
    app.run_polling()
