from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env (if running locally)
load_dotenv()

# Init OpenAI client using env var (Render will inject this)
client = OpenAI()

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

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )

    return response.choices[0].message.content


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body")
    print(f"User said: {incoming_msg}")

    reply = get_trend_response(incoming_msg)

    resp = MessagingResponse()
    resp.message(reply)

    from flask import Response
    return Response(str(resp), mimetype="application/xml"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
