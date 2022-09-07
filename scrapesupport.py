import json
import os
from typing import Optional

import nextcord
import privatebinapi
import requests
import yaml
import log

intents = nextcord.Intents.default()
intents.message_content = True
client = nextcord.Client(intents=intents)

with open("config.yml", 'r') as f:
    config = yaml.safe_load(f)
    token = config.get('token')
    uri = config.get('uri')
    platform = config.get('platform')
    bot_message: str = config.get('bot_message')
cache_folder = 'cache'
working_dir = os.getcwd()


async def save_to_cache(attachment: nextcord.Attachment) -> Optional[str]:
    i = 0
    local_file = os.path.join(working_dir, cache_folder, str(i) + ".txt")
    while os.path.exists(local_file):
        i = i + 1
        local_file = os.path.join(working_dir, cache_folder, str(i) + ".txt")

    try:
        await attachment.save(local_file)
        log.info(attachment.filename, 'was saved!')
        with open(local_file, 'r') as local_file_stream:
            local_file_content = local_file_stream.read()

        os.remove(local_file)
        return local_file_content
    except any:
        log.error(attachment.filename, 'could not be saved.')

    return None


def upload_to_bin(content: str) -> (str, bool):
    if platform == 'hastebin':
        log.info(f"Uploading to {platform}...")

        response = requests.post(uri + 'documents', data=content)
        response_content = json.loads(response.text)['key']

        success = len(response_content) <= 10

        log.info('Api response:', str(response.text), success)
        if success:
            return (uri + response_content), True
    if platform == 'privatebin':
        log.info(f"Uploading to {platform}...")

        response = privatebinapi.send(uri, text=content, formatting='syntaxhighlighting')
        success = response['status'] == 0

        log.info('Api response:', str(response['status']), success)
        if success:
            return response['full_url'], True
    return "Wrong configuration or return value", False


def clear_cache() -> None:
    path = os.path.join(working_dir, cache_folder)
    if os.path.exists(path):
        os.removedirs(path)
    os.mkdir(path)


@client.event
async def on_ready():
    log.info('We have logged in as', client.user)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if len(message.attachments) > 0:
        for attachment in message.attachments:
            if attachment.content_type.startswith('text'):
                attachment_content = await save_to_cache(attachment)
                if attachment_content:
                    link, success = upload_to_bin(attachment_content)
                    if success:
                        await message.channel.send(bot_message.format(link=link),
                                                   reference=message,
                                                   mention_author=False)
        return


clear_cache()
log.load_logging_handlers()
client.run(token)
