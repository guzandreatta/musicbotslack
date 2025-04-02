import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")  # Por si querés validar firmas
HEADERS = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
    "Content-type": "application/json"
}


def get_converted_links(original_url):
    res = requests.get(f"https://api.song.link/v1-alpha.1/links?url={original_url}")
    if res.status_code != 200:
        return None
    data = res.json()
    platforms = data.get("linksByPlatform", {})
    spotify = platforms.get("spotify", {}).get("url")
    apple = platforms.get("appleMusic", {}).get("url")

    return spotify, apple


@app.route("/slack/events", methods=["POST"])
def slack_events():
    event_data = request.json

    # Verificación inicial para confirmar a Slack
    if "challenge" in event_data:
        return jsonify({"challenge": event_data["challenge"]})

    # Procesar evento de mensaje
    if "event" in event_data:
        event = event_data["event"]
        text = event.get("text", "")
        user = event.get("user")
        channel = event.get("channel")

        if "spotify.com" in text or "music.apple.com" in text:
            links = [word for word in text.split() if "spotify.com" in word or "music.apple.com" in word]
            for link in links:
                spotify, apple = get_converted_links(link)
                msg = "*🎵 Enlaces en otras plataformas:*\n"
                if spotify:
                    msg += f"🎧 Spotify: {spotify}\n"
                if apple:
                    msg += f"🍎 Apple Music: {apple}\n"

                payload = {
                    "channel": channel,
                    "text": msg
                }

                requests.post("https://slack.com/api/chat.postMessage", json=payload, headers=HEADERS)

    return "OK", 200
