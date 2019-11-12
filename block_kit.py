from database import LibraryDB
# from pyzbar import pyzbar
import requests
from PIL import Image

class BlockKit:
    def __init__(self):
        self.username = "library_bot"
        self.icon_emoji = ":robot_face:"
        self.db = LibraryDB()
        self.options = {}

    # def recognize_book(self, response, user_id, team_id):
    #     blocks = []
    #     image = Image.open(response)
    #     for qr in pyzbar.decode(image):
    #         code = qr.data.decode('utf-8')
    #         # TODO: API
    #         book = self.db.get_book_by_id(code)
    #         if book[5]:
    #             blocks += [
    #                 {
    #                     "type": "section",
    #                     "text": {
    #                         "type": "mrkdwn",
    #                         "text": f"О! Это же _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*, хочешь взять ее?"
    #                     },
    #                     "accessory": {
    #                         "type": "button",
    #                         "action_id": "get_book",
    #                         "text": {
    #                             "type": "plain_text",
    #                             "text": "Беру!",
    #                             "emoji": True
    #                         },
    #                         "value": f"{code}"
    #                     }
    #                 }
    #             ]
    #         elif str(book[7]) != user_id:
    #             blocks = [
    #                 {
    #                     "type": "section",
    #                     "text": {
    #                         "type": "mrkdwn",
    #                         "text": f"А, это _{str(book[1])} {str(book[2])}_ *'{str(book[3])}'*, кажется @{str(book[6])}"
    #                         f"забыл вернуть ее, напиши ему, пожалуйста <slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>"
    #                     },
    #                 }
    #             ]
    #         else:
    #             blocks += self.get_return_book_block(code)
    #
    #     if not blocks:
    #         blocks = [
    #             {
    #                 "type": "section",
    #                 "text": {
    #                     "type": "mrkdwn",
    #                     "text": f"Я не знаю что это(, попробуй еще раз."
    #                 }
    #             }
    #         ]
    #     return blocks

    def get_menu_options(self, pattern):
        base_url = 'http://42lib.site'
        response = requests.get(
            url=f'{base_url}/api/get_russian_tags',
        ).json()
        print(pattern, response.keys())
        for text, value in response.items():
            if pattern in text.lower():
                print(text, value)
        #TODO: normal length
        menu_options = {
            "options": [
                {
                    "text": {
                        "type": "plain_text",
                        "text": value[:20],
                        "emoji": True
                    },
                    "value": value
                } for text, value in response.items() if pattern in text.lower()
            ]
        }
        print(menu_options)
        return menu_options

    def get_search_message(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "Привет, хочешь почитать? :wave:\n\n"
                    ),
                },
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Поиск по тегу, названию, автору"
                },
                "accessory": {
                    "type": "multi_external_select",
                    "action_id": "tags",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Поиск...",
                        "emoji": True
                    },
                    "min_query_length": 2
                }
            }
        ]

    def get_book_list(self, tag, team_id, start):
        base_url = 'http://42lib.site'
        books = list(requests.get(
            url=f"{base_url}/api/tag_{tag}",
        ).json().values())
        books_count = len(books)
        book_list = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"#{tag}"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "_{0}_ \n*'{1}'*\nCейчас".format(*[author['text'] for author in book['author']], book['book_name']) +
                                (f" в {book['place']}" if book['status'] == 'online' else f" у @{book['place']}")
                        # f"<slack://user?team={team_id}&id={str(book[7])}|:speech_balloon:>")
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
                        "value": f"{tag}"
                    }
                ]
            }
        ]
        if books_count - start > 10:
            more_button = {
                    "action_id": f"getmore-{tag}",
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Еще..",
                        "emoji": True
                    },
                    "value": f"{start + 10}"
                }
            book_list[1]['elements'].insert(0, more_button)
        return book_list

    def get_more_books(self, action_id, action_value, blocks, team_id):
        tag = action_id.split('-')[1]
        book_list = self.get_book_list(tag, team_id, int(action_value))
        new_blocks = []
        for section in blocks:
            if "elements" not in section.keys() or "elements" in section.keys()\
                    and section["elements"][0]["action_id"] != action_id:
                if "text" in section.keys() and section["text"]["text"][1:] == tag:
                    new_blocks += book_list
                else:
                    new_blocks.append(section)
        return new_blocks

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

    def verify_block(self, email):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Привет, нажми кнопку, чтобы привязать свой акаунт."
                },
                "accessory": {
                    "action_id": "verify",
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Тык",
                        "emoji": True
                    },
                    "value": f"{email.split('@')[0]}"
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
        new_blocks = []
        for section in blocks:
            if "text" in section.keys() and section["text"]["text"][1:] == action_value:
                continue
            elif "elements" in section.keys():
                if section["elements"][0]['value'] == action_value:
                    continue
                else:
                    try:
                        if section["elements"][0]["action_id"].split('-')[1] == action_value:
                            continue
                    except IndexError:
                        new_blocks.append(section)
            else:
                new_blocks.append(section)
        return new_blocks

    def show_books(self, selectors, team_id):
        blocks = []
        for i in range(len(selectors)):
            blocks += self.get_book_list(selectors[i]['value'], team_id, 0)
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


