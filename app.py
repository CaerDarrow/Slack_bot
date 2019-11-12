from flask import Flask, request, make_response, Response
# from flask_ngrok import run_with_ngrok
from library_bot import LibraryBot
import requests
import json

# Flask webserver for incoming traffic from Slack
app = Flask(__name__)
bot = LibraryBot()

@app.route("/slack/message_options", methods=["POST"])
def message_options():
    form_json = json.loads(request.form["payload"])
    bot.verify_slack_token(form_json["token"])
    pattern = form_json["value"].lower()
    menu_options = bot.get_menu_options(pattern)
    print(menu_options)
    return Response(json.dumps(menu_options), mimetype='application/json')

@app.route("/slack/reg_events", methods=["POST"])
def reg_events():
    form_json = request.json
    bot.verify_slack_token(form_json["token"])
    if 'challenge' in form_json.keys():
        challenge = form_json['challenge']
        return Response(challenge, mimetype='text/plain')
    elif form_json['event']['type'] == 'message' and 'files' in form_json['event'].keys()\
            and form_json['event']['user'] != 'UP74SGMRC':
        channel_id = form_json['event']['channel']
        team_id = form_json['team_id']
        user_id = form_json['event']['user']
        file_url = form_json['event']['files'][0]['thumb_480']
        bot.send_books(channel_id, file_url, user_id, team_id)
    return make_response("", 200)


@app.route("/slack/commands", methods=["POST"])
def commands():
    form_json = request.form
    bot.verify_slack_token(form_json["token"])
    if form_json['command'] == '/newbook':
        bot.add_book_dialog(form_json['trigger_id'])
    elif form_json['command'] == '/booklist':
        bot.start_bot(form_json['channel_id'])
    elif form_json['command'] == '/test':
        bot.send_auth_verify_message('ApxuBapuyc@bk.ru')
    return make_response("", 200)

# The endpoint Slack will send the user's menu selection to
@app.route("/slack/message_actions", methods=["POST"])
def message_actions():
    form_json = json.loads(request.form["payload"])
    if bot.verify_slack_token(form_json["token"]):
        return make_response("Request contains invalid Slack verification token", 403)
    team_id = form_json["team"]["id"]
    # if form_json['type'] == 'view_submission':
    #     values = form_json['view']['state']['values']
    #     book_name = values['book_name']['book_name']['value']
    #     author_info = values['author_info']['author_info']['value']
    #     genre = values['genre']['genre']['value'] if 'value' in values['genre']['genre'].keys()\
    #         else values['genre']['genre']['selected_option']['value']
    #     genre = genre.lower()
    #     cluster = values['cluster']['cluster']['selected_option']['value']
    #     bot.new_book(form_json['user']['id'], book_name, author_info, genre, cluster)
    #     return make_response("", 200)
    action = form_json["actions"][0]
    # if action['action_id'] == 'add_genre':
    #     bot.add_genre_dialog(form_json['view']['id'])
    #     return make_response("", 200)
    channel_id = form_json["channel"]["id"]
    blocks = form_json["message"]["blocks"]
    ts = form_json["message"]["ts"]
    if action["action_id"].startswith("getmore"):
        bot.show_more_books(channel_id, ts, blocks, action["action_id"], action["value"], team_id)
    elif action["action_id"] == "get_book":
        bot.user_get_book(channel_id, ts, action["value"], form_json['user']['username'], form_json['user']['id'])
    elif action["action_id"] == "return_book_to_cluster":
        bot.user_return_book_to_cluster(channel_id, ts, action["selected_option"]["value"])
    elif action["action_id"] == "approve":
        ts, channel_id, val = action['value'][1:].split('+')
        bot.user_approve_book(ts, channel_id, val, form_json['user']['username'])
        bot.user_get_book(form_json["channel"]["id"], form_json["message"]["ts"], val, form_json['user']['username'],
                          form_json['user']['id'])
    elif action["action_id"] == "deny":
        bot.delete_message(ts, channel_id)
        ts, channel_id, val = action['value'][1:].split('+')
        bot.user_deny_book(ts, channel_id, val, form_json['user']['username'])
    elif action["action_id"] == "return_book_to_user":
        bot.user_return_book_to_user(ts, channel_id, action['selected_user'], form_json['user']['username'],
                                 blocks[1]['elements'][0]['options'][0]['value'].split('_')[0])
    elif action["action_id"] == "hide_lib":
        bot.user_hide_books(ts, channel_id, blocks, action["value"])
    elif action["action_id"] == 'verify':
        bot.send_slack_id_to_site(action['value'], form_json['user']['id'])
    elif action["action_id"] == 'tags':
        selectors = action["selected_options"]
        bot.show_books_to_user(ts, channel_id, selectors, blocks, team_id)
    return make_response("", 200)


# Start the Flask server
if __name__ == "__main__":
    app.run()
