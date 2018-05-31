import time
import random
import urllib3
from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ValidationError
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
from bot.models import Person, Referral, Setting, Bot

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Join Group')],
        [KeyboardButton(text='Set Wallet Address')],
        [KeyboardButton(text='Set Email Address')],
        [KeyboardButton(text='Generate Referral Link')],
        [KeyboardButton(text='Check Bonus Amount')],
        [KeyboardButton(text='Cancel')],
    ],
    one_time_keyboard=True,
    resize_keyboard=True
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
    user_id = msg['from']['id']
    print(content_type, chat_type, chat_id)

    if content_type != 'text':
        return HttpResponse(status=200)

    try:
        person = Person.objects.get(telegram_id=chat_id)
    except Person.DoesNotExist:
        person = Person(telegram_id=user_id)
        person.save()

    text = msg['text']
    if person.pending_input:
        # This text is meant to be a user input at some stage.
        return process_input(chat_id, person, text)

    if text == '/start':
        return start(chat_id, person)
    elif is_deep_linked(text):
        return referral_signup(chat_id, person, text)
    elif text == 'Join Group':
        return send_group_invite(chat_id, person)
    elif text == 'Set Wallet Address':
        return set_wallet_address(chat_id, person)
    elif text == 'Set Email Address':
        return change_wallet_address(chat_id, person)
    elif text == 'Generate Referral Link':
        return generate(chat_id, person)
    elif text == 'Check Bonus Amount':
        return check_bonus(chat_id, person)
    elif text == 'Cancel':
        return cancel(chat_id, person)
    else:
        # return start(chat_id, person)
        bot.sendMessage(chat_id, '{}'.format(chat_id))


def is_deep_linked(text):
    temp = text.split()
    return len(temp) == 2 and text.startswith('/start')


def send_group_invite(chat_id, person):
    invite_link = bot.exportChatInviteLink(config.gcid)
    invite_msg = '{} \n {}'.format(config.gc_invite, invite_link)
    bot.sendMessage(chat_id, invite_msg)
    options = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Yes I have joined')],
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    time.sleep(2)
    bot.sendMessage(chat_id, 'Have you joined?', reply_markup=options)


def start(chat_id, person):
    if person.bonus_amount == 0:
        person.bonus_amount += config.join_bonus_amount
        person.save()
        msg = 'You have been rewared with {} {}'.format(
            config.join_bonus_amount,
            config.bonus_currency
        )
        bot.sendMessage(chat_id, msg)
    bot.sendMessage(chat_id, config.welcome_message)
    bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)


def referral_signup(chat_id, person, text):
    try:
        code = int(text.split()[-1])
        referrer = Referral.objects.get(code=code)
    except (ValueError, Referral.DoesNotExist):
        error_msg = 'Oops! Something looks wrong with that referral link.'
        bot.sendMessage(chat_id, error_msg)
        time.sleep(2)
        bot.sendMessage(chat_id, reply_markup=MAIN_MENU)
        return HttpResponse(status=200)
    referrer.bonus_amount += config.referral_bonus_amount
    person.referrered_by = referrer
    referrer.save()
    person.save()
    return start(chat_id, person)


def set_wallet_address(chat_id, person):
    msg_enter = 'Please enter a valid wallet address'
    person.pending_input = True
    person.current_stage = 1
    person.save()
    bot.sendMessage(chat_id, msg_enter)


def set_email_address(chat_id, person):
    msg_enter = 'Please enter your email address:'
    person.pending_input = True
    person.current_stage = 2
    person.save()
    bot.sendMessage(chat_id, msg_enter)


def change_wallet_address(chat_id, person):
    person.wallet_address = ''
    person.save()
    set_wallet_address(chat_id, person)


def generate(chat_id, person):
    try:
        referral = Referral.objects.get(person=person)
        msg = 'Your referral link is: {}\n'.format(referral.url)
        bot.sendMessage(chat_id, msg)
        time.sleep(2)
        bot.sendMessage(chat_id, reply_markup=MAIN_MENU)
        return
    except Referral.DoesNotExist:
        random_digit = random.randint(100, 999)
        referral_digit = int(chat_id) - random_digit
        # url = 'bappa.pythonanywhere.com/bot/prod/referral/?join={}'.format(
        #     referral_digit)
        url = 'telegram.me/bottocksbot/?start={}'.format(referral_digit)
        ref = Referral(
            person=person,
            url=url
        )
        ref.save()
        msg = 'You referral Link is {}'.format(url)
        bot.sendMessage(chat_id, msg)
        time.sleep(2)
        bot.sendMessage(chat_id, reply_markup=MAIN_MENU)


def check_bonus(chat_id, person):
    try:
        person = Person.objects.get(telegram_id=chat_id)
        bonus_msg = 'You have {} {} bonus'.format(
            person.bonus_amount,
            config.bonus_currency
        )
        bot.sendMessage(chat_id, bonus_msg)
        bot.sendMessage(chat_id, reply_markup=MAIN_MENU)
    except Person.DoesNotExist:
        msg = 'You have no bonus yet.'
        bot.sendMessage(chat_id, msg)
        bot.sendMessage(chat_id, reply_markup=MAIN_MENU)


def cancel(chat_id, person):
    person.pending_input = False
    person.save()
    bot.sendMessage(chat_id, reply_markup=MAIN_MENU)


def process_input(chat_id, person, text):
    stage = person.current_stage
    if stage == 1:
        return process_wallet_address(chat_id, person, text)
    elif stage == 2:
        return process_email_address(chat_id, person, text)


def process_wallet_address(chat_id, person, text):
    msg_success = 'Congrats! I have saved your wallet address.'
    person.wallet_address = text
    person.pending_input = False
    person.save()
    bot.sendMessage(chat_id, msg_success)
    bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)
    return HttpResponse(status=200)
    # msg_already_exists = 'You have already supplied a Waller Address.\
    #                       You can change it from main menu'
    # msg_invalid_address = 'This wallet address is invalid. Try again:'
    # msg_cancel = "Type 'cancel' or 'exit' to quit."
    # if person.wallet_address:
    #     person.pending_input = False
    #     person.save()
    #     bot.sendMessage(chat_id, msg_already_exists)
    #     bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)
    # elif len(text) < 50:
    #     bot.sendMessage(chat_id, msg_invalid_address)
    #     person.pending_input = False
    #     person.save()
    #     bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)
    # else:
    #     person.wallet_address = text
    #     person.pending_input = False
    #     person.save()
    #     bot.sendMessage(chat_id, msg_success)
    #     bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)


def process_email_address(chat_id, person, text):
    msg_success = 'Congrats! I have saved your email address'
    try:
        person.email = text
        person.pending_input = False
        person.save()
    except ValidationError:
        msg_error = 'Something looks wrong with this email address.\n \
                    Please enter a email.'
        bot.sendMessage(chat_id, msg_error)
    bot.sendMessage(chat_id, msg_success)
    bot.sendMessage(chat_id, 'Choose an option', reply_markup=MAIN_MENU)
