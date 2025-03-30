from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv
import praw

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Reddit credentials
REDDIT_CLIENT_ID = os.getenv("kVOnmpoBa8W0GxF4kIOvCQ")
REDDIT_CLIENT_SECRET = os.getenv("owkJ70qd-toMz2cP8_42Qm6h0yJgPQ")
REDDIT_USER_AGENT = os.getenv("whatsapp-trend-bot")

app = Flask(__name__)

# Store user countries in memory
user_country_memory = {}

# ✅ Fetch top trending tech titles from Reddit
def fetch_reddit_trends(subreddit="technology", limit=3):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    posts = reddit.subreddit(subreddit).hot(limit=limit)
    trend_titles = [post.title for post in posts if not post.stickied]
    
    print("📥 Reddit trends:", trend_titles, flush=True)

    return "\n".join([f"- {title}" for title in trend_titles])


# ✅ Ask Groq to generate ideas based on real Reddit topics
def get_trend_response(user_message, user_country):
    reddit_trends = fetch_reddit_trends()

    prompt = f"""
You're a personal trend assistant for Instagram tech influencers.

Here are real Reddit trends today:
{reddit_trends}

Based on these, generate 3 *Instagram content ideas* for a tech influencer in {user_country}.
Each idea should include:
- A topic title
- A hook (1 line)
- Tool to create content
- Best time to post (in {user_country})
- Estimated trend lifespan

Format it for WhatsApp like this:

👨‍💻 *Today’s Tech Trends for Instagram Creators*

1️⃣ *Topic*  
🪝 Hook: "..."  
📲 Tool: ...  
📍 Best Time to Post ({user_country}): ...  
🕒 Trend lasts: ...
"""

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

    print("✅ Groq Status:", response.status_code, flush=True)
    print("🧠 Groq Raw:", response.text, flush=True)

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ Groq parse error:", str(e), flush=True)
        return "⚠️ Couldn't get content ideas right now. Try again soon."


# ✅ WhatsApp webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body").strip()
    from_number = request.form.get("From")

    resp = MessagingResponse()

    user_country = user_country_memory.get(from_number)

    if not user_country:
        if incoming_msg.lower() in ["india", "us", "uk", "germany", "canada"]:
            user_country_memory[from_number] = incoming_msg
            resp.message(f"✅ Got it! You're in {incoming_msg}. Now send 'tech' or 'trending' to get ideas.")
        else:
            resp.message("🌍 Hey! Before I send you trends — what country are you in? (e.g. India, US, UK)")
        return Response(str(resp), mimetype="application/xml"), 200

    # If country is set, generate response
    reply = get_trend_response(incoming_msg, user_country)
    resp.message(reply)
    return Response(str(resp), mimetype="application/xml"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
