from flask import Flask, request, make_response, Response
from flask_ngrok import run_with_ngrok
import os
import json
from slack import WebClient
from database import LibraryDB
from library_bot import LibraryBot

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
    builder = LibraryBot()
    pattern = form_json["value"].lower()
    menu_options = builder.get_menu_options(form_json["action_id"], pattern)
    return Response(json.dumps(menu_options), mimetype='application/json')


# bot dialog link:
# slack://user?team=TP74BRUES&id=UP74SGMRC
# slack://share-file?team=TP74BRUES&id=FPA25U8NB

def build_blocks(action, selector, team_id, start):
    db = LibraryDB()
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
                        "text": f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас в {str(book[5])}" if book[5]
                        else f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас у @{str(book[6])}"
                        f"<slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>"
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

def start_bot(channel):
    library_bot = LibraryBot()
    message = library_bot.get_welcome_message(channel)
    response = slack_client.chat_postMessage(**message)

def send_books(channel, url, user_name, team_id):
    library_bot = LibraryBot()
    messages = library_bot.recognize_book(channel, url, user_name, team_id)
    for message in messages:
        response = slack_client.chat_postMessage(**message)

@app.route("/slack/reg_events", methods=["POST"])
def reg_events():
    form_json = request.json
    if 'challenge' in form_json.keys():
        challenge = form_json['challenge']
        return Response(challenge, mimetype='text/plain')
    elif form_json['event']['type'] == 'message':
        channel_id = form_json['event']['channel']
        if 'text' in form_json['event'].keys() and form_json['event']['text'].lower() == 'start':
            start_bot(channel_id)
        elif 'files' in form_json['event'].keys():
            team_id = form_json['team_id']
            user_id = form_json['event']['user']
            file_url = form_json['event']['files'][0]['thumb_480']
            send_books(channel_id, file_url, user_id, team_id)
    return make_response("", 200)

# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    form_json = json.loads(request.form["payload"])
    verify_slack_token(form_json["token"])
    book_list = []
    team_id = form_json["team"]["id"]
    blocks = form_json["message"]["blocks"]
    ts = form_json["message"]["ts"]
    channel_id = form_json["channel"]["id"]
    action = form_json["actions"][0]
    if action["action_id"].startswith("getmore"):
        true_action = action["action_id"].split('-')[1]
        selector, start = action["value"].split('-')
        blocks = [build_blocks(true_action, selector, team_id, int(start))[0]
                  if "text" in section.keys() and section["text"]["text"] == selector else section
                  for section in blocks]
    elif action["action_id"] == "get_book":
        db = LibraryDB()
        db.take_book(action["value"], form_json['user']['username'], form_json['user']['id'])
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Когда дочитаешь книгу, выбери кластер, в который ты хочешь вернуть книгу,"
                    f"или пользователя, которому ты хочешь ее передать"
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                        "action_id": "return_book_to_cluster",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Выбери кластер",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": cluster,
                                    "emoji": True
                                },
                                "value": f"{action['value']}_{cluster}"
                            } for cluster in ["Atlantis", "Illusion", "Mirage", "Oasis"]]
                    },
                    {
                        "type": "users_select",
                        "action_id": "return_book_to_user",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Выбери пользователя",
                            "emoji": True
                        }
                    },
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Чтобы получить это сообщение просто сосканируй QR-код еще раз"
                    }
                ]
            },
        ]
    elif action["action_id"] == "return_book_to_cluster":
        db = LibraryDB()
        book_id, cluster = action["selected_option"]["value"].split('_')
        db.return_book(book_id, cluster)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Спасибо!"
                }
            }
        ]
    elif action["action_id"] == "approve":
        ts, channel_id, val = action['value'][1:].split('+')
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Спасибо, книга теперь у @{form_json['user']['username']}!"
                }
            }
        ]
        slack_client.chat_update(
            channel=form_json["channel"]["id"],
            ts=form_json["message"]["ts"],
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Когда дочитаешь книгу, выбери кластер, в который ты хочешь вернуть книгу,"
                        f"или пользователя, которому ты хочешь ее передать"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "static_select",
                            "action_id": "return_book_to_cluster",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Выбери кластер",
                                "emoji": True
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": cluster,
                                        "emoji": True
                                    },
                                    "value": f"{val}_{cluster}"
                                } for cluster in ["Atlantis", "Illusion", "Mirage", "Oasis"]]
                        },
                        {
                            "type": "users_select",
                            "action_id": "return_book_to_user",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Выбери пользователя",
                                "emoji": True
                            }
                        },
                    ]
                }
            ]
        )
    elif action["action_id"] == "deny":
        slack_client.chat_delete(
            channel=channel_id,
            ts=ts
        )
        ts, channel_id, val = action['value'][1:].split('+')
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Извини, но @{form_json['user']['username']} отклонил запрос( попробуй еще раз."
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "static_select",
                        "action_id": "return_book_to_cluster",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Выбери кластер",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": cluster,
                                    "emoji": True
                                },
                                "value": f"{val}_{cluster}"
                            } for cluster in ["Atlantis", "Illusion", "Mirage", "Oasis"]]
                    },
                    {
                        "type": "users_select",
                        "action_id": "return_book_to_user",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Выбери пользователя",
                            "emoji": True
                        }
                    },
                ]
            }
        ]
    elif action["action_id"] == "return_book_to_user":
        user = action['selected_user']
        #db = LibraryDB()
        response = slack_client.conversations_open(users=[user])
        channel = response['channel']['id']
        response = slack_client.chat_postMessage(
            channel=channel,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"@{form_json['user']['username']} хочет передать тебе book"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "action_id": "approve",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Принять"
                            },
                            "style": "primary",
                            "value": f"1{ts}+{channel_id}+{blocks[1]['elements'][0]['options'][0]['value'].split('_')[0]}"
                        },
                        {
                            "type": "button",
                            "action_id": "deny",
                            "text": {
                                "type": "plain_text",
                                "emoji": True,
                                "text": "Отклонить"
                            },
                            "style": "danger",
                            "value": f"2{ts}+{channel_id}+{blocks[1]['elements'][0]['options'][0]['value'].split('_')[0]}"
                        }
                    ]
                }
            ]
        )

    elif action["action_id"] == "hide_lib":
        blocks = [section for section in blocks if "text" in section.keys()
                  and section["text"]["text"] != action["value"] or
                  "elements" in section.keys() and
                  section["elements"][0]["value"] != action["value"]]
    else:
        selectors = [action["selected_option"]] if action["action_id"] == "Name" else action["selected_options"]
        for i in range(len(selectors)):
            list_b = build_blocks(action["action_id"], selectors[i]['value'], team_id, 0)
            book_list += list_b
    response = slack_client.chat_update(
        channel=channel_id,
        ts=ts,
        blocks=blocks + book_list,
        as_user=True
    )
    # Send an HTTP 200 response with empty body so Slack knows we're done here
    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run()
