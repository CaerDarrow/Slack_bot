from flask import Flask, request, make_response, Response
import os
import json

from slack import WebClient

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
#SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]

# Slack client for Web API requests
slack_client = WebClient(SLACK_BOT_TOKEN)

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)
# Helper for verifying that requests came from Slack
# def verify_slack_token(request_token):
#     if SLACK_VERIFICATION_TOKEN != request_token:
#         print("Error: invalid verification token!")
#         print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
#         return make_response("Request contains invalid Slack verification token", 403)

# The endpoint Slack will send the user's menu selection to
@app.route("/")
def index():
    return '<b>Hello!!<b/>'

@app.route("/slack/message_actions", methods=["POST"])
def message_actions():

    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Verify that the request came from Slack
    #verify_slack_token(form_json["token"])

    # Check to see what the user's selection was and update the message accordingly
    button = form_json["actions"][0]["action_id"]
    if button == "button1":
        message_text = "cappuccino"
    else:
        message_text = "latte"

    response = slack_client.chat_update(
      channel=form_json["channel"]["id"],
      ts=form_json["message_ts"],
      text="One {}, right coming up! :coffee:".format(message_text)
    )

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)

# Start the Flask server
if __name__ == "__main__":
    app.run()