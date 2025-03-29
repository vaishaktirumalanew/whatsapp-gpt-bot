from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    print("✅ Twilio webhook hit!")

    # Generate a Twilio response
    resp = MessagingResponse()
    msg = resp.message("This is a test from your Flask bot!")

    # Return TwiML as the response with 200 OK
    return Response(str(resp), mimetype="application/xml"), 200

if __name__ == "__main__":
    app.run(port=5000)
