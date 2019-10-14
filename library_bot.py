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

    def __init__(self, channel):
        self.channel = channel
        self.username = "library_bot"
        self.icon_emoji = ":robot_face:"
        self.timestamp = ""

    def get_welcome_message(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
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

