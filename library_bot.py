from database import LibraryDB
from pyzbar import pyzbar
import requests
import os
from PIL import Image

class LibraryBot:
    WELCOME_BLOCK = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Привет, хочешь почитать? :wave:\n\n"
            ),
        },
    }
    DIVIDER_BLOCK = {"type": "divider"}
    SELECT_BY_GENRE = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Поиск по жанрам"
        },
        "accessory": {
            "type": "multi_external_select",
            "action_id": "Genre",
            "placeholder": {
                "type": "plain_text",
                "text": "Искать",
                "emoji": True
            },
            "max_selected_items": 5
        }
    }
    SELECT_BY_BOOK_NAME = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Поиск по названию"
        },
        "accessory": {
            "type": "external_select",
            "action_id": "Name",
            "placeholder": {
                "type": "plain_text",
                "text": "Искать",
                "emoji": True
            },
        }
    }
    SELECT_BY_AUTHOR_SURNAME = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Поиск по фамилии"
        },
        "accessory": {
            "type": "multi_external_select",
            "action_id": "Author_surname",
            "placeholder": {
                "type": "plain_text",
                "text": "Искать",
                "emoji": True
            },
            "max_selected_items": 5
        }
    }
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]

    def __init__(self):
        self.username = "library_bot"
        self.icon_emoji = ":robot_face:"
        self.db = LibraryDB()

    def get_welcome_message(self, channel):
        return {
            "channel": channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": [
                self.WELCOME_BLOCK,
                self.DIVIDER_BLOCK,
                self.SELECT_BY_GENRE,
                self.SELECT_BY_AUTHOR_SURNAME,
                self.SELECT_BY_BOOK_NAME,
            ],
        }

    def get_menu_options(self, action, pattern):
        if action == "Name":
            selections = self.db.get_book_names()
        elif action == "Author_surname":
            selections = self.db.get_surnames()
        elif action == "Genre":
            selections = self.db.get_genres()
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
        return menu_options

    def recognize_book(self, channel, url, user_id, team_id):
        messages = []
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.SLACK_BOT_TOKEN}"},
            stream=True
        ).raw
        image = Image.open(response)
        for qr in pyzbar.decode(image):
            code = qr.data.decode('utf-8')
            book = self.db.get_book_by_id(code)
            if book[5]:
                messages += [
                    {
                        "channel": channel,
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"О! Это же _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*, хочешь взять ее?"
                                },
                                "accessory": {
                                    "type": "button",
                                    "action_id": "get_book",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Беру!",
                                        "emoji": True
                                    },
                                    "value": f"{code}"
                                }
                            }
                        ]
                    }
                ]
            elif str(book[7]) != user_id:
                messages += [
                    {
                        "channel": channel,
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": f"А, это _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*, кажется @{str(book[6])}"
                    f"забыл вернуть ее, напиши ему, пожалуйста <slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>"
                                },
                            }
                        ]
                    }
                ]
            else:
                messages += [
                    {
                        "channel": channel,
                        "blocks": [
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
                                                "value": f"{code}_{cluster}"
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
                    }
                ]
        if not messages:
            messages = [
                {
                    "channel": channel,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"Я не знаю что это(, попробуй еще раз."
                            }
                        }
                    ]
                }
            ]
        return messages
