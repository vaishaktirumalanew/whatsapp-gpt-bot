from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    print("✅ Webhook hit from Twilio!")

    resp = MessagingResponse()
    resp.message("Test successful ✅ The bot is connected.")
    return Response(str(resp), mimetype="application/xml"), 200

if __name__ == "__main__":
    app.run(port=5000)
