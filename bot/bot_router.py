import json
import time
from django.http import HttpResponse
from django.conf import settings
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
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
    bot = telepot.Bot(specs.api_key)

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

    if content_type != 'text':
        return HttpResponse(status=200)

    try:
        person = Person.objects.get(telegram_id=chat_id)
    except Person.DoesNotExist:
        person = Person(telegram_id=chat_id)
        person.save()

    text = msg['text']
    if text == '/start':
        return start(chat_id, person)
    elif text == '/Generate Referral Link':
        return generate(chat_id, person)
    elif text == 'Check Bonus Amount':
        return check_bonus(chat_id, person)
    elif text == 'Cancel':
        return cancel(chat_id, person)
    else:
        return start(chat_id, person)


def start(chat_id, person):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Generate Referral Link')],
            [KeyboardButton(text='Check Bonus Amount')],
            [KeyboardButton(text='Cancel')],
        ],
        one_time_keyboard=True
    )
    bot.sendMessage(chat_id, config.welcome_text)
    bot.sendMessage(chat_id, 'Choose an option', reply_markup=keyboard)


def generate(chat_id, person):
    pass


def check_bonus(chat_id, person):
    pass


def cancel(chat_id, person):
    pass
