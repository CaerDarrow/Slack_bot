class LibraryBot:
    """Constructs the onboarding message and stores the state of which tasks were completed."""

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
            "action_id": "genres",
            "placeholder": {
                "type": "plain_text",
                "text": "Искать",
                "emoji": True
            },
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
            "action_id": "book_names",
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
            "action_id": "surnames",
            "placeholder": {
                "type": "plain_text",
                "text": "Искать",
                "emoji": True
            },
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
                self.SELECT_BY_BOOK_NAME,
                self.SELECT_BY_AUTHOR_SURNAME,
            ],
        }

