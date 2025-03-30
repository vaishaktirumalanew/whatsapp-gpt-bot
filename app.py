from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

# Store user info temporarily (for demo purposes)
user_country_memory = {}

def get_trend_response(user_message, user_country):
    prompt = f"""
You're a personal content trend assistant for Instagram tech influencers.

Based on the message: "{user_message}" — generate a list of 3 *tech-related trending content ideas* from what’s popular on Instagram today.

Each idea should include:
- A bold topic title
- A catchy hook to grab attention
- A relevant tool to create content (e.g., CapCut, Meta AI, phone camera, etc.)
- The *best time to post* based on this country: "{user_country}"
- An estimate of how long this trend will stay hot

Format it *clearly for WhatsApp* like this:

👨‍💻 *Today's Tech Trends for Instagram Creators*

1️⃣ *Topic Name*  
🪝 Hook: "..."  
📲 Tool: ...  
📍 Best Time to Post ({user_country}): ...  
🕒 Trend lasts: ...

Make it short, viral-friendly, and helpful for Instagram creators.
"""

    print("🔁 Sending to Groq...", flush=True)

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8
        }
    )

    print("✅ Status:", response.status_code, flush=True)
    print("🧠 Raw:", response.text, flush=True)

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ Failed to parse:", str(e), flush=True)
        return "⚠️ I couldn’t fetch trends right now. Try again soon."

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body").strip()
    from_number = request.form.get("From")

    print(f"📩 From {from_number}: {incoming_msg}", flush=True)

    resp = MessagingResponse()

    # Check if we have a country stored
    user_country = user_country_memory.get(from_number)

    if not user_country:
        if incoming_msg.lower() in ["india", "us", "uk", "germany", "canada"]:
            user_country_memory[from_number] = incoming_msg
            resp.message(f"✅ Got it! You're in {incoming_msg}. Now send me a keyword like 'trending' or 'tech'.")
        else:
            resp.message("🌍 Hey! Before I send trends — tell me which country you're in (e.g. India, US, UK):")
        return Response(str(resp), mimetype="application/xml"), 200

    # Country known — send trends
    reply = get_trend_response(incoming_msg, user_country)
    resp.message(reply)
    return Response(str(resp), mimetype="application/xml"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
