# import json
# import time
# from django.http import HttpResponse
# from django.conf import settings
import telepot
# from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ForceReply
# from bot.models import Person, Referral, Setting, Bot

# settings = Setting.objects.get()
# specs = Bot.objects.get()

# bot = telepot.bot(specs.api_key)
# Secret GUID number to hide our endpoint
SECRET = "b6f2a100-6263-11e8-adc0-fa7ae01bbebc"

# Our URL to serve as the webhook for Telegram
END_POINT = 'bappa.pythonanywhere.com/bot/prod/hook/{}'.format(SECRET)
bot = telepot.Bot('486245389:AAFwqUcArzLWJsvopZh4lgPll9RU8vVW57M')
webhook = bot.getWebhookInfo()
if not webhook['url']:
    print('No WEbhook set')
    # bot.setWebhook(url=settings.END_POINT)
    bot.setWebhook(url=END_POINT)
    print('SEt webhook: {}'.format(END_POINT))
else:
    print('Webhook already set.')
# print(bot.getWebhookInfo())


def route(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)

    if content_type == 'text':
        bot.sendMessage(chat_id, msg['text'])
