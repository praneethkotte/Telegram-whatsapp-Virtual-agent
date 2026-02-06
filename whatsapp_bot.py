from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from core import handle_command, speak_whatsapp

app = Flask(__name__)


@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").lower()
    chat_id = request.values.get("From")

    response_text = handle_command(incoming_msg, chat_id, platform="whatsapp")

    resp = MessagingResponse()
    msg = resp.message(response_text)

    audio_file = speak_whatsapp(response_text)
    if audio_file:
        msg.media(f"https://your-render-url.com/{audio_file}")

    return str(resp)


if __name__ == "__main__":
    app.run(port=5000)
