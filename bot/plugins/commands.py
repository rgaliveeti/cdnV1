from telethon.events import NewMessage
from telethon.tl.custom.message import Message
from bot import TelegramBot
from bot.config import Telegram

@TelegramBot.on(NewMessage(incoming=True, pattern=r'^/start$'))
async def welcome(event: NewMessage.Event | Message):
    await event.reply(
        message='contact @ignore709',
    )

@TelegramBot.on(NewMessage(chats=Telegram.OWNER_ID, incoming=True, pattern=r'^/log$'))
async def send_log(event: NewMessage.Event | Message):
    await event.reply(file='event-log.txt')
