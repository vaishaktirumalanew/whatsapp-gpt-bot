from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv
import sys

# Load environment variables (for local dev)
load_dotenv()

# Get Groq API key from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

def get_trend_response(user_message):
    prompt = f"""
You are a content trend assistant. Based on this message: "{user_message}",
provide 3 trending content topics from areas like X, movies, politics, food, or history.

For each topic:
- Suggest a catchy hook
- Recommend tools for creation (e.g., CapCut, Canva)
- Suggest the best time to post
- Estimate how long the trend will last

Make it WhatsApp-friendly.
"""

    print("🔄 Sending request to Groq...", flush=True)
    print("Prompt:", prompt, flush=True)

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mixtral-8x7b-32768",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8
        }
    )

    print("✅ Groq status code:", response.status_code, flush=True)
    print("🧠 Raw response text:", response.text, flush=True)

    try:
        data = response.json()
        print("🧠 Parsed JSON:", data, flush=True)

        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        else:
            return "⚠️ I couldn’t get content ideas right now. Try again in a few seconds."

    except Exception as e:
        print("❌ Exception while parsing Groq response:", str(e), flush=True)
        return "⚠️ Oops! Something broke while getting your content ideas."

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")
    print(f"📩 User said: {incoming_msg}", flush=True)

    reply = get_trend_response(incoming_msg)

    twilio_resp = MessagingResponse()
    twilio_resp.message(reply)

    return Response(str(twilio_resp), mimetype="application/xml"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
