import os
import logging
import asyncio
import ssl as ssl_lib
import certifi
import slack
import json
from library_bot import LibraryBot


async def start_bot(web_client: slack.WebClient, user_id: str, channel: str):
    # Create a new Library Bot.
    library_bot = LibraryBot(channel)

    # Get the library bot welcome message
    message = library_bot.get_welcome_message()

    # Post the onboarding message in Slack
    response = await web_client.chat_postMessage(**message)

    # Capture the timestamp of the message we've just posted so
    # we can use it to update the message after a user
    # has completed an onboarding task.
    library_bot.timestamp = response["ts"]


# ============== Message Events ============= #
# When a user sends a DM, the event type will be 'message'.
# Here we'll link the message callback to the 'message' event.
@slack.RTMClient.run_on(event="message")
async def message(**payload):
    """Display the onboarding welcome message after receiving a message
    that contains "start".
    """
    data = payload["data"]
    web_client = payload["web_client"]
    channel_id = data.get("channel")
    user_id = data.get("user")
    text = data.get("text")
    files = data.get("files")
    if text and text.lower() == "start":
        return await start_bot(web_client, user_id, channel_id)
    if text and text.lower() == "picture":
        web_client.files_upload(
            channels=channel_id,
            file="file.jpg",
            title='Book about dogge'
        )
    elif files and files[0]["id"] == "FPA25U8NB":
        await web_client.conversations_open(users=[user_id])
        await web_client.chat_postMessage(
            channel=channel_id,
            text=f"А, это {files[0]['name']}!",
        )


@slack.RTMClient.run_on(event="im_open")
async def im_open(**payload):
    data = payload["data"]
    web_client = payload["web_client"]
    channel_id = data.get("channel")
    user_id = data.get("user")
    await web_client.chat_postMessage(
        channel=channel_id,
        text=f"А, это {user_id}!",
    )

@slack.RTMClient.run_on(event="star_added")
async def star_added(**payload):
    data = payload["data"]
    print(data)
    web_client = payload["web_client"]
    channel_id = data.get("channel")
    user_id = data.get("user")
    await web_client.chat_postMessage(
        channel=channel_id,
        text=f"А, это {user_id}!",
    )

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    slack_token = os.environ["SLACK_BOT_TOKEN"]
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    rtm_client = slack.RTMClient(
        token=slack_token, ssl=ssl_context, run_async=True, loop=loop
    )
    loop.run_until_complete(rtm_client.start())