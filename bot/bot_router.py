import time
import random
import urllib3
from django.http import HttpResponse
from django.conf import settings
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
from bot.models import Person, Referral, Setting, Bot

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Add Wallet Address')],
        [KeyboardButton(text='Change Wallet Address')],
        [KeyboardButton(text='Generate Referral Link')],
        [KeyboardButton(text='Check Bonus Amount')],
        [KeyboardButton(text='Cancel')],
    ],
    one_time_keyboard=True
)
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
    if person.pending_input:
        # This text is meant to be a user input at some stage.
        return process_input(chat_id, person, text)

    if text == '/start':
        return start(chat_id, person)
    if text == '/Add Wallet Address':
        return add_wallet_address(chat_id, person)
    if text == '/Change Wallet Address':
        return change_wallet_address(chat_id, person)
    elif text == '/Generate Referral Link':
        return generate(chat_id, person)
    elif text == 'Check Bonus Amount':
        return check_bonus(chat_id, person)
    elif text == 'Cancel':
        return cancel(chat_id, person)
    else:
        return start(chat_id, person)


def start(chat_id, person):
    if person.bonus_amount == 0:
        person.bonus_amount += config.join_bonus_amount
        person.save()
    msg = 'You have been rewared with {} {}'.format(
        config.join_bonus_amount,
        config.bonus_currency
    )
    bot.sendMessage(chat_id, config.welcome_message)
    bot.sendMessage(chat_id, msg)
    bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)


def add_wallet_address(chat_id, person):
    msg_enter = 'Please enter a valid wallet address'
    person.pending_input = True
    person.current_stage = 1
    person.save()
    bot.sendMessage(chat_id, msg_enter)


def change_wallet_address(chat_id, person):
    person.wallet_address = ''
    person.save()
    add_wallet_address(chat_id, person)


def generate(chat_id, person):
    random_digit = random.randint(100, 999)
    referral_digit = int(chat_id) - random_digit
    url = 'bappa.pythonanywhere.com/bot/prod/referral/?join={}'.format(
        referral_digit)
    ref = Referral(
        person=person,
        url=url
    )
    ref.save()
    msg = 'You referral Link is {}'.format(url)
    bot.sendMessage(chat_id, msg)
    time.sleep(2)
    bot.sendMessage(chat_id, MAIN_MENU)


def check_bonus(chat_id, person):
    pass


def cancel(chat_id, person):
    pass


def process_input(chat_id, person, text):
    stage = person.current_stage
    if stage == 1:
        return process_wallet_address(chat_id, person, text)


def process_wallet_address(chat_id, person, text):
    msg_success = 'Congrats! I have saved your wallet address.'
    msg_already_exists = 'You have already supplied a Waller Address.\
                          You can change it from main menu'
    msg_invalid_address = 'This wallet address is invalid. Try again:'
    msg_cancel = "Type 'cancel' or 'exit' to quit."
    if person.wallet_address:
        person.pending_input = False
        person.save()
        bot.sendMessage(chat_id, msg_already_exists)
        bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)
    elif len(text) < 50:
        bot.sendMessage(chat_id, msg_invalid_address)
        person.pending_input = False
        person.save()
        bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)
    else:
        person.wallet_address = text
        person.pending_input = False
        person.save()
        bot.sendMessage(chat_id, msg_success)
        bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)
    return HttpResponse(status=200)
