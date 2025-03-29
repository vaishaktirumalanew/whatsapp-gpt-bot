from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    print("✅ Got a POST request to /whatsapp!")
    resp = MessagingResponse()
    resp.message("Test reply: The bot is working.")
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)


