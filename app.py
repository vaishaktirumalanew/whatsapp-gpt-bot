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

# Store user data in memory
user_state = {}

# ✅ Fetch trending post details from subreddit at a given index
def fetch_reddit_post(subreddit="technology", index=0):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        posts = [post for post in reddit.subreddit(subreddit).hot(limit=10) if not post.stickied]
        if index < len(posts):
            post = posts[index]
            return {
                "title": post.title,
                "upvotes": post.score,
                "comments": post.num_comments,
                "flair": post.link_flair_text or "None",
                "url": post.url
            }
        return None

    except Exception as e:
        print(f"❌ Error fetching r/{subreddit}: {e}", flush=True)
        return None

# ✅ Generate a 1-minute creator script based on Reddit post
def get_trend_response(subreddit, user_country, index=0):
    post = fetch_reddit_post(subreddit=subreddit, index=index)

    if not post:
        return f"⚠️ Couldn't find more trending posts in r/{subreddit}. Try another topic."

    prompt = f"""
You're a creative content assistant for short-form video creators.

Here’s a trending Reddit post from r/{subreddit}:

Title: {post['title']}
Upvotes: {post['upvotes']}
Comments: {post['comments']}
Flair: {post['flair']}

Using this info, write a compelling 1-minute video script a creator can say on camera.
Include:
- A hook that grabs attention
- A short, engaging explanation
- A call-to-action or question for the audience

Then suggest:
- A video concept / format
- Editing style ideas
- Best time to post in {user_country}

Format output cleanly for WhatsApp.
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
        return data["choices"][0]["message"]["content"] + f"

To see more trending topics from r/{subreddit}, reply with \"more\"."
    except Exception as e:
        print("❌ Groq parse error:", str(e), flush=True)
        return "⚠️ Couldn't generate a script. Try again."

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.form.get("Body").strip()
    from_number = request.form.get("From")

    resp = MessagingResponse()

    state = user_state.get(from_number, {"country": None, "subreddit": None, "index": 0})

    if not state["country"]:
        if incoming_msg.lower() in ["india", "us", "uk", "germany", "canada"]:
            state["country"] = incoming_msg
            user_state[from_number] = state
            resp.message(f"✅ Got it! You're in {incoming_msg}. Now send a topic like 'ai', 'gadgets', or 'startups'.")
        else:
            resp.message("🌍 Before I can send you trends, what's your country? (e.g. India, US, UK)")
        return Response(str(resp), mimetype="application/xml"), 200

    if incoming_msg.lower() == "more":
        if not state["subreddit"]:
            resp.message("❗ Send a topic first like 'tech' or 'gadgets' before asking for more.")
            return Response(str(resp), mimetype="application/xml"), 200
        state["index"] += 1
        reply = get_trend_response(state["subreddit"], state["country"], state["index"])
        resp.message(reply)
        return Response(str(resp), mimetype="application/xml"), 200

    # If it's a new topic request
    subreddit = incoming_msg.lower().strip().replace(" ", "")
    state["subreddit"] = subreddit
    state["index"] = 0
    user_state[from_number] = state

    reply = get_trend_response(subreddit, state["country"], 0)
    resp.message(reply)
    return Response(str(resp), mimetype="application/xml"), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

