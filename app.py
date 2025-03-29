from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv

# Load environment variables (for local use)
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

    data = response.json()

    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    else:
        # Log the full error for debugging
        print("❌ Groq API Error:", data)
        return "Hmm… I couldn’t generate ideas right now. Try again in a few seconds!"
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")
    print(f"✅ User said: {incoming_msg}")

    reply = get_trend_response(incoming_msg)

    twilio_resp = MessagingResponse()
    twilio_resp.message(reply)

    return Response(str(twilio_resp), mimetype="application/xml"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
