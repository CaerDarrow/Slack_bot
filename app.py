from flask import Flask, request, make_response, Response
from flask_ngrok import run_with_ngrok
import os
import json
from slack import WebClient
from database import LibraryDB

# Your app's Slack bot user token
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]

# Slack client for Web API requests
slack_client = WebClient(SLACK_BOT_TOKEN)

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)
run_with_ngrok(app)

#Helper for verifying that requests came from Slack
def verify_slack_token(request_token):
    if SLACK_VERIFICATION_TOKEN != request_token:
        print("Error: invalid verification token!")
        print("Received {} but was expecting {}".format(request_token, SLACK_VERIFICATION_TOKEN))
        return make_response("Request contains invalid Slack verification token", 403)


@app.route("/slack/message_options", methods=["POST"])
def message_options():
    form_json = json.loads(request.form["payload"])
    verify_slack_token(form_json["token"])
    db = LibraryDB()
    pattern = form_json["value"].lower()
    if form_json["action_id"] == "Name":
        selections = db.get_book_names()
    elif form_json["action_id"] == "Author_surname":
        selections = db.get_surnames()
    elif form_json["action_id"] == "Genre":
        selections = db.get_genres()
    print(selections)
    menu_options = {
        "options": [
            {
                "text": {
                    "type": "plain_text",
                    "text": selection[0],
                    "emoji": True
                },
                "value": selection[0]
            } for selection in selections if pattern in selection[0].lower()
        ]
    }
    db.close()
    return Response(json.dumps(menu_options), mimetype='application/json')


# bot dialog link:
# slack://user?team=TP74BRUES&id=UP74SGMRC
# slack://file?team=TP74BRUES&id=FNV8JLNN6

def build_blocks(action, selector, team_id, start):
    db = LibraryDB()
    #books = db.get_book_list_by(action, selector)
    if action == "Name":
        books = db.get_book_list_by_book_names(selector)
    elif action == "Author_surname":
        books = db.get_book_list_by_surnames(selector)
    elif action == "Genre":
        books = db.get_book_list_by_genre(selector)
    books_count = len(books)
    if books_count - start > 10:
        list_b = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{selector}"
                },
                "accessory": {
                    "type": "button",
                    "action_id": f"getmore-{action}",
                    "text": {
                        "type": "plain_text",
                        "text": "Еще..",
                        "emoji": True
                    },
                    "value": f"{selector}-{start + 10}"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас в {str(book[5])}" if book[
                            5]
                        else f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас у @{str(book[6])} <slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>"
                    } for book in books[start:min(start + 10, books_count)]]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "action_id": "hide_lib",
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Скрыть",
                            "emoji": True
                        },
                        "value": f"{selector}"
                    }
                ]
            }
        ]
    else:
        list_b = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{selector}"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас в {str(book[5])}" if book[5]
                        else f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас у @{str(book[6])} <slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>"
                    } for book in books[start:min(start + 10, books_count)]]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "action_id": "hide_lib",
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Скрыть",
                            "emoji": True
                        },
                        "value": f"{selector}"
                    }
                ]
            }
        ]
    return list_b

# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    form_json = json.loads(request.form["payload"])
    verify_slack_token(form_json["token"])
    book_list = []
    team_id = form_json["team"]["id"]
    blocks = form_json["message"]["blocks"]
    action = form_json["actions"][0]
    if action["action_id"].startswith("getmore"):
        true_action = action["action_id"].split('-')[1]
        selector, start = action["value"].split('-')
        blocks = [build_blocks(true_action, selector, team_id, int(start))[0]
                  if "text" in section.keys() and section["text"]["text"] == selector else section
                  for section in blocks]
    elif action["action_id"] == "hide_lib":
        blocks = [section for section in blocks if "text" in section.keys()
                  and section["text"]["text"] != action["value"] or
                  "elements" in section.keys() and
                  section["elements"][0]["value"] != action["value"]]
    else:
        selectors = [action["selected_option"]] if action["action_id"] == "Name" else action["selected_options"]
        for i in range(len(selectors)):
            list_b = build_blocks(action["action_id"], selectors[i]['value'], team_id, 0)
            print(list_b)
            book_list += list_b
    response = slack_client.chat_update(
        channel=form_json["channel"]["id"],
        ts=form_json["message"]["ts"],
        blocks=blocks + book_list,
        as_user=True
    )
    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run()
