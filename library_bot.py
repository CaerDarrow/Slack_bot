from block_kit import BlockKit
from slack import WebClient
import os
from flask import Flask, request, make_response, Response
import requests
import qrcode
from io import BytesIO

class LibraryBot(BlockKit):
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]

    def __init__(self):
        BlockKit.__init__(self)
        # Slack client for Web API requests
        self.slack_client = WebClient(self.SLACK_BOT_TOKEN)

    # Verifying that requests came from Slack
    def verify_slack_token(self, request_token):
        return self.SLACK_VERIFICATION_TOKEN != request_token

    def start_bot(self, channel_id):
        blocks = self.get_search_message()
        response = self.slack_client.chat_postMessage(
            icon_emoji=":robot_face:",
            channel=channel_id,
            blocks=blocks,
        )

    def send_auth_verify_message(self, email):
        response = self.slack_client.users_lookupByEmail(
            email=email
        )
        if response['ok']:
            user_id = response['user']['id']
            response = self.slack_client.conversations_open(users=[user_id])
            channel = response['channel']['id']
            blocks = self.verify_block(email)
            response = self.slack_client.chat_postMessage(
                icon_emoji=":robot_face:",
                channel=channel,
                blocks=blocks
            )

    def send_slack_id_to_site(self, user_name, user_id):
        base_url = 'http://42lib.site'
        requests.post(
            url=f'{base_url}/api/?',
            json={
                "user_name": user_name,
                "user_id": user_id
            }
        )

    def send_books(self, channel_id, url, user_name, team_id):
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.SLACK_BOT_TOKEN}"},
            stream=True
        ).raw
        blocks = self.recognize_book(response, user_name, team_id)
        response = self.slack_client.chat_postMessage(
            icon_emoji=":robot_face:",
            channel=channel_id,
            blocks=blocks
        )

    def show_more_books(self, channel_id, ts, blocks, action_id, action_value, team_id):
        blocks = self.get_more_books(action_id, action_value, blocks, team_id)
        response = self.slack_client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            as_user=True
        )

    def user_get_book(self, channel_id, ts, action_value, user_name, user_id):
        blocks = self.get_book(action_value, user_name, user_id)
        response = self.slack_client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            as_user=True
        )

    def user_return_book_to_cluster(self, channel_id, ts, action_value):
        blocks = self.return_book_to_cluster(action_value)
        response = self.slack_client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            as_user=True
        )

    def user_approve_book(self, ts, channel_id, val, user_name):
        blocks = self.approve_book(user_name, val)
        response = self.slack_client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            as_user=True
        )

    def user_deny_book(self, ts, channel_id, val, user_name):
        blocks = self.deny_book(user_name, val)
        response = self.slack_client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            as_user=True
        )

    def delete_message(self, ts, channel_id):
        self.slack_client.chat_delete(
            channel=channel_id,
            ts=ts
        )

    def user_return_book_to_user(self, ts, channel_id, user, user_name, val):
        blocks = self.return_book_to_user(ts, channel_id, val, user_name)
        response = self.slack_client.conversations_open(users=[user])
        channel = response['channel']['id']
        response = self.slack_client.chat_postMessage(
            icon_emoji=":robot_face:",
            channel=channel,
            blocks=blocks
        )

    def user_hide_books(self, ts, channel_id, blocks, action_value):
        blocks = self.hide_books(action_value, blocks)
        response = self.slack_client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            as_user=True
        )

    def show_books_to_user(self, ts, channel_id, selectors, blocks, team_id):
        blocks = blocks + self.show_books(selectors, team_id)
        response = self.slack_client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=blocks,
            as_user=True
        )

    def add_book_dialog(self, trigger_id):
        response = self.slack_client.views_open(
            trigger_id=trigger_id,
            view=self.add_book()
        )

    def add_genre_dialog(self, view_id):
        response = self.slack_client.views_update(
            view_id=view_id,
            view=self.add_genre()
        )

    def new_book(self, user_id, book_name, author_info, genre, cluster):
        info = author_info.split()
        author_surname, author_initials = info[0], info[1] if len(info) == 2 else ''
        book_id = self.db.add_book(author_surname.capitalize(), author_initials, book_name.capitalize(), genre.lower(), cluster)
        response = self.slack_client.conversations_open(users=[user_id])
        channel_id = response['channel']['id']
        img = qrcode.make(book_id)
        bio = BytesIO()
        bio.name = f'{book_name}.jpeg'
        img.save(bio, 'JPEG')
        bio.seek(0)
        response = self.slack_client.files_upload(
            channels=channel_id,
            file=bio,
            title=f"{book_name}",
            initial_comment=f"_{author_info}_ *'{book_name}'* добавлена, распечатай"
            f" этот код и наклей на книгу! И не забудь отнести ее в {cluster}"
        )