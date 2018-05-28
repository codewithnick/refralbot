import json
import time
from django.http import HttpResponse
from django.conf import settings
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ForceReply
from bot.models import Person, Referral, Setting, Bot

settings = Setting.objects.get()
specs = Bot.objects.get()

bot = telepot.bot(specs.api_key)
# bot = telepot.Bot('486245389:AAFwqUcArzLWJsvopZh4lgPll9RU8vVW57M')
webhook = bot.getWebhookInfo()
if not webhook['url']:
    bot.setWebhook(url=settings.END_POINT)
print(bot.getWebhookInfo())


def route(chat_data):
    pass
