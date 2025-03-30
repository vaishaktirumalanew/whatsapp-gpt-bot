from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
from dotenv import load_dotenv
import praw

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
REDDIT_CLIENT_ID = os.environ["REDDIT_CLIENT_ID"]
REDDIT_CLIENT_SECRET = os.environ["REDDIT_CLIENT_SECRET"]
REDDIT_USER_AGENT = os.environ["REDDIT_USER_AGENT"]

app = Flask(__name__)

# Store user country in memory (for demo purposes)
user_country_memory = {}

# ✅ Fetch trending posts from dynamic subreddit
def fetch_reddit_trends(subreddit="technology", limit=3):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        posts = reddit.subreddit(subreddit).hot(limit=limit)
        trend_titles = [post.title for post in posts if not post.stickied]

        if not trend_titles:
            return f"No trending posts found in r/{subreddit} today."

        return "\n".join([f"- {title}" for title in trend_titles])

    except Exception as e:
        print(f"❌ Error fetching r/{subreddit}: {e}", flush=True)
        return f"⚠️ Couldn't find trending posts in r/{subreddit}. Try a different topic."


# ✅ Ask Groq to generate ideas based on trends

def get_trend_response(user_message, user_country):
    subreddit = user_message.lower().strip().replace(" ", "")
    reddit_trends = fetch_reddit_trends(subreddit=subreddit)

    prompt = f"""
You're a personal trend assistant for Instagram tech influencers.

Here are real Reddit trends from r/{subreddit}:
{reddit_trends}

Based on these, generate 3 *Instagram content ideas* for a tech influencer in {user_country}.
Each idea should include:
- A topic title
- A hook (1 line)
- Tool to create content
- Best time to post (in {user_country})
- Estimated trend lifespan

Format it for WhatsApp like this:

👨‍💼 *Today’s Tech Trends from r/{subreddit}*

1️⃣ *Topic*  
🪝 Hook: "..."  
📲 Tool: ...  
📍 Time to Post ({user_country}): ...  
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

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("❌ Groq parse error:", str(e), flush=True)
        return "⚠️ Couldn't generate content ideas. Try again."


@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body").strip()
    from_number = request.form.get("From")

    resp = MessagingResponse()

    user_country = user_country_memory.get(from_number)

    if not user_country:
        if incoming_msg.lower() in ["india", "us", "uk", "germany", "canada"]:
            user_country_memory[from_number] = incoming_msg
            resp.message(f"✅ Got it! You're in {incoming_msg}. Now send a topic like 'ai', 'gadgets', or 'startups'.")
        else:
            resp.message("🌍 Before I can send you trends, what's your country? (e.g. India, US, UK)")
        return Response(str(resp), mimetype="application/xml"), 200

    # If country is known, generate response from dynamic subreddit
    reply = get_trend_response(incoming_msg, user_country)
    resp.message(reply)
    return Response(str(resp), mimetype="application/xml"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

