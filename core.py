import os
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = "bcb884ea1ae74c0a9d558fe2100b0898"


def ai_response(text):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Malar Ma — a friendly, smart, slightly playful "
                    "Alexa-like virtual assistant. Keep answers short and natural."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    return completion.choices[0].message.content


def handle_command(command: str):
    c = command.lower()

    # --- ALEXA-LIKE FEATURES ---

    if "how are you" in c:
        return "I'm amazing bestie, especially when I’m helping you praneeth!"

    if c.startswith("open "):
        site = c.replace("open", "").strip().replace(" ", "")
        if not site.startswith("http"):
            link = f"https://www.{site}.com"
        else:
            link = site
        return f"Here you go: {link}"

    if c.startswith("play"):
        song = c.replace("play", "").strip()
        youtube_search = "https://www.youtube.com/results?search_query=" + song.replace(
            " ", "+"
        )
        return f"Here’s your music on YouTube: {youtube_search}"

    if "news" in c:
        today = datetime.now().strftime("%B %d, %Y")
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"

        r = requests.get(url)
        if r.status_code != 200:
            return "Sorry, I couldn't fetch the news right now."

        data = r.json()
        articles = data.get("articles", [])[:3]

        response = f"Top headlines for {today}:\n\n"
        for i, a in enumerate(articles, start=1):
            response += f"{i}. {a['title']}\n"

        return response

    # Default: Ask OpenAI (like Alexa for general questions)
    return ai_response(command)
