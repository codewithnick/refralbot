import json
import time
from django.http import HttpResponse
from django.conf import settings
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ForceReply
from bot.models import Person, Referral, Setting, Bot
import urllib3

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(
        proxy_url=proxy_url,
        num_pools=3,
        maxsize=10,
        retries=False,
        timeout=30
    ),
}
telepot.api._onetime_pool_spec = (
    urllib3.ProxyManager,
    dict(
        proxy_url=proxy_url,
        num_pools=1,
        maxsize=1,
        retries=False,
        timeout=30
    )
)

try:
    config = Setting.objects.get()
except Setting.DoesNotExist:
    config = None

try:
    specs = Bot.objects.get()
except Bot.DoesNotExist:
    specs = None

if config and specs:
    bot = telepot.bot(specs.api_key)

    # bot = telepot.Bot('486245389:AAFwqUcArzLWJsvopZh4lgPll9RU8vVW57M')

    webhook = bot.getWebhookInfo()
    if not webhook['url']:
        print('No WEbhook set')
        bot.setWebhook(url=settings.END_POINT)
        # bot.setWebhook(url=END_POINT)
        print('SEt webhook: {}'.format(settings.END_POINT))
    else:
        print('Webhook already set.')
    print(bot.getWebhookInfo())


def route(msg):
    msg = msg['message']
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(content_type, chat_type, chat_id)

    if content_type == 'text':
        bot.sendMessage(chat_id, msg['text'])
        bot.sendMessage(
            chat_id,
            'The end point is {}'.format(settings.END_POINT)
        )
