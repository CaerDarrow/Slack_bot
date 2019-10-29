from database import LibraryDB
# from pyzbar import pyzbar
from PIL import Image


class BlockKit:
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

    def __init__(self):
        self.username = "library_bot"
        self.icon_emoji = ":robot_face:"
        self.db = LibraryDB()

    def recognize_book(self, response, user_id, team_id):
        blocks = []
        image = Image.open(response)
        # for qr in pyzbar.decode(image):
        #     code = qr.data.decode('utf-8')
        #     book = self.db.get_book_by_id(code)
        #     if book[5]:
        #         blocks += [
        #             {
        #                 "type": "section",
        #                 "text": {
        #                     "type": "mrkdwn",
        #                     "text": f"О! Это же _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*, хочешь взять ее?"
        #                 },
        #                 "accessory": {
        #                     "type": "button",
        #                     "action_id": "get_book",
        #                     "text": {
        #                         "type": "plain_text",
        #                         "text": "Беру!",
        #                         "emoji": True
        #                     },
        #                     "value": f"{code}"
        #                 }
        #             }
        #         ]
        #     elif str(book[7]) != user_id:
        #         blocks = [
        #             {
        #                 "type": "section",
        #                 "text": {
        #                     "type": "mrkdwn",
        #                     "text": f"А, это _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*, кажется @{str(book[6])}"
        #                     f"забыл вернуть ее, напиши ему, пожалуйста <slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>"
        #                 },
        #             }
        #         ]
        #     else:
        #         blocks += self.get_return_book_block(code)
        #
        # if not blocks:
        #     blocks = [
        #         {
        #             "type": "section",
        #             "text": {
        #                 "type": "mrkdwn",
        #                 "text": f"Я не знаю что это(, попробуй еще раз."
        #             }
        #         }
        #     ]
        return blocks

    def get_welcome_message(self):
        return [
            self.WELCOME_BLOCK,
            self.DIVIDER_BLOCK,
            self.SELECT_BY_GENRE,
            self.SELECT_BY_AUTHOR_SURNAME,
            self.SELECT_BY_BOOK_NAME,
        ]

    def get_menu_options(self, action, pattern):
        if action == "Name":
            selections = self.db.get_book_names()
        elif action == "Author_surname":
            selections = self.db.get_surnames()
        elif action == "Genre" or action == "Genre_view":
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

    def get_book_list(self, action, selector, team_id, start):
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
                            "text": f"_{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*\nCейчас в {str(book[5])}" if
                            book[5]
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

    def get_more_books(self, action_id, action_value, blocks, team_id):
        true_action = action_id.split('-')[1]
        selector, start = action_value.split('-')
        blocks = [self.get_book_list(true_action, selector, team_id, int(start))[0]
                  if "text" in section.keys() and section["text"]["text"] == selector else section
                  for section in blocks]
        return blocks

    def get_return_book_block(self, book_id):
        return [
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
                                "value": f"{book_id}_{cluster}"
                            } for cluster in ["Atlantis", "Illusion", "Mirage", "Oasis"]
                        ]
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

    def get_book(self, action_value, user_name, user_id):
        self.db.take_book(action_value, user_name, user_id)
        blocks = self.get_return_book_block(action_value)
        return blocks

    def return_book_to_cluster(self, action_value):
        book_id, cluster = action_value.split('_')
        self.db.return_book(book_id, cluster)
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Спасибо!"
                }
            }
        ]

    def approve_book(self, user_name, val):
        book = self.db.get_book_by_id(val)
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Спасибо, _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'* теперь у @{user_name}!"
                }
            }
        ]

    def deny_book(self, user_name, val):
        # TODO: block
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Извини, но @{user_name} отклонил запрос( попробуй еще раз."
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

    def return_book_to_user(self, ts, channel_id, val, user_name):
        book = self.db.get_book_by_id(val)
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"@{user_name} хочет передать тебе _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*"
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
                        "value": f"1{ts}+{channel_id}+{val}"
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
                        "value": f"2{ts}+{channel_id}+{val}"
                    }
                ]
            }
        ]

    def hide_books(self, action_value, blocks):
        blocks = [section for section in blocks if "text" in section.keys()
                  and section["text"]["text"] != action_value or
                  "elements" in section.keys() and
                  section["elements"][0]["value"] != action_value]
        return blocks

    def show_books(self, selectors, action_id, team_id):
        blocks = []
        for i in range(len(selectors)):
            blocks += self.get_book_list(action_id, selectors[i]['value'], team_id, 0)
        return blocks

    def add_book(self):
        selections = self.db.get_genres()
        return {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Добавление книги",
                "emoji": True
            },
            "submit": {
                "type": "plain_text",
                "text": "Отправить",
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": "Отмена",
                "emoji": True
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "genre",
                    "label": {
                        "type": "plain_text",
                        "text": "Выбрать жанр",
                        "emoji": True
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "genre",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Научная фантастика",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": selection[0],
                                    "emoji": True
                                },
                                "value": selection[0]
                            } for selection in selections
                        ]
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "action_id": "add_genre",
                            "text": {
                                "type": "plain_text",
                                "text": "Моего жанра нет в списке"
                            }
                        }
                    ]
                },
                {
                    "type": "input",
                    "block_id": "author_info",
                    "label": {
                        "type": "plain_text",
                        "text": "Фамилия и инициалы автора"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "author_info",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Адамс Д.Н."
                        }
                    },
                    "hint": {
                        "type": "plain_text",
                        "text": "Порядок важен :)"
                    }
                },
                {
                    "type": "input",
                    "block_id": "book_name",
                    "label": {
                        "type": "plain_text",
                        "text": "Название книги"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "book_name",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Автостопом по галактие"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "cluster",
                    "label": {
                        "type": "plain_text",
                        "text": "В каком кластере ты оставишь книгу?",
                        "emoji": True
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "cluster",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Кластер",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": cluster,
                                    "emoji": True
                                },
                                "value": cluster
                            } for cluster in ["Atlantis", "Illusion", "Mirage", "Oasis"]
                        ]
                    },
                }
            ]
        }

    def add_genre(self):
        return {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Добавление книги",
                "emoji": True
            },
            "submit": {
                "type": "plain_text",
                "text": "Отправить",
                "emoji": True
            },
            "close": {
                "type": "plain_text",
                "text": "Отмена",
                "emoji": True
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "genre",
                    "label": {
                        "type": "plain_text",
                        "text": "Добавить новый жанр"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "genre",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Научная фантастика"
                        }
                    },
                },
                {
                    "type": "input",
                    "block_id": "author_info",
                    "label": {
                        "type": "plain_text",
                        "text": "Фамилия и инициалы автора"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "author_info",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Адамс Д.Н."
                        }
                    },
                    "hint": {
                        "type": "plain_text",
                        "text": "Порядок важен :)"
                    }
                },
                {
                    "type": "input",
                    "block_id": "book_name",
                    "label": {
                        "type": "plain_text",
                        "text": "Название книги"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "book_name",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Автостопом по галактие"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "cluster",
                    "label": {
                        "type": "plain_text",
                        "text": "В каком кластере ты оставишь книгу?",
                        "emoji": True
                    },
                    "element": {
                        "type": "static_select",
                        "action_id": "cluster",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Кластер",
                            "emoji": True
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": cluster,
                                    "emoji": True
                                },
                                "value": cluster
                            } for cluster in ["Atlantis", "Illusion", "Mirage", "Oasis"]
                        ]
                    },
                }
            ]
        }


