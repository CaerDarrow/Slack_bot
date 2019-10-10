from flask import Flask, request, make_response, Response
from flask_ngrok import run_with_ngrok
import os
import json
from slack import WebClient
from database import LibraryDB

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
# SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]

# Slack client for Web API requests
slack_client = WebClient(SLACK_BOT_TOKEN)

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)
run_with_ngrok(app)


# Helper for verifying that requests came from Slack
# def verify_slack_token(request_token):
#     if SLACK_VERIFICATION_TOKEN != request_token:
#         print("Error: invalid verification token!")
#         print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
#         return make_response("Request contains invalid Slack verification token", 403)


@app.route("/slack/message_options", methods=["POST"])
def message_options():
    db = LibraryDB()
    form_json = json.loads(request.form["payload"])
    pattern = form_json["value"].lower()
    if form_json["action_id"] == "genres":
        selections = db.get_genres()
    elif form_json["action_id"] == "book_names":
        selections = db.get_book_names()
    menu_options = {
        "options": [
            {
                "text": {
                    "type": "plain_text",
                    "text": selection[0],
                    "emoji": True
                },
                "value": selection[0],
            } for selection in selections if pattern in selection[0].lower()
        ]
    }
    db.close()
    return Response(json.dumps(menu_options), mimetype='application/json')


#bot dialog link:
#slack://user?team=TP74BRUES&id=UP74SGMRC
#slack://file?team=TP74BRUES&id=FNV8JLNN6

# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    # Parse the request payload
    form_json = json.loads(request.form["payload"])

    # Verify that the request came from Slack
    # verify_slack_token(form_json["token"])

    # Check to see what the user's selection was and update the message accordingly
    db = LibraryDB()
    book_list = []
    team_id = form_json["team"]["id"]
    if form_json["actions"][0]["action_id"] == "genres":
        genres = form_json["actions"][0]["selected_options"]
        for genre in genres:
            book_list += [
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{genre['value']}*"
                    }
                },
                {
                    "type": "divider"
                },
            ]
            book_list += [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас в {str(book[5])}" if book[5]
                        else f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас у {str(book[6])}<slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>"
                    }
                } for book in db.get_book_list_by_genre(genre['value'])
            ]
    book_list += [
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Назад",
                        "emoji": True
                    },
                    "value": "click_me_123"
                }
            ]
        }
    ]
    db.close()
    response = slack_client.chat_update(
        channel=form_json["channel"]["id"],
        ts=form_json["message"]["ts"],
        blocks=book_list,
        as_user=True
    )

    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run()
