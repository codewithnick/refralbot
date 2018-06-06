import time
import random
import urllib3
from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import OperationalError
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
from bot.models import Person, Referral, Setting, Bot

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Join Group'),
            KeyboardButton(text='Set Wallet Address')
        ],
        [
            KeyboardButton(text='Set Email Address'),
            KeyboardButton(text='Referral Link')
        ],
        [
            KeyboardButton(text='Check Status'),
            KeyboardButton(text='Cancel')
        ],
        [
            KeyboardButton(text='Get More Token')
        ],
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
    config.refresh_from_db()
except (Setting.DoesNotExist, OperationalError):
    config = None

try:
    bot_specs = Bot.objects.get()
    bot_specs.refresh_from_db()
except (Bot.DoesNotExist, OperationalError):
    bot_specs = None

if config and bot_specs:
    bot = telepot.Bot(bot_specs.api_key)

    # bot = telepot.Bot('486245389:AAFwqUcArzLWJsvopZh4lgPll9RU8vVW57M')

    webhook = bot.getWebhookInfo()
    if not webhook['url']:
        print('No WEbhook set')
        try:
            bot.setWebhook(url=bot_specs.webhook)
        except:
            print('Error')
        # bot.setWebhook(url=END_POINT)
        print('SEt webhook: {}'.format(bot_specs.webhook))
    else:
        print('Webhook already set.')
    print(bot.getWebhookInfo())


def route(msg):
    msg = msg['message']
    content_type, chat_type, chat_id = telepot.glance(msg)
    user_id = msg['from']['id']
    print(content_type, chat_type, chat_id)

    if content_type != 'text' or msg['chat']['type'] != 'private':
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
    elif text == 'Yes I have joined':
        return check_member(chat_id, person)
    elif text == 'Set Wallet Address':
        return set_wallet_address(chat_id, person)
    elif text == 'Set Email Address':
        return set_email_address(chat_id, person)
    elif text == 'Referral Link':
        return generate(chat_id, person)
    elif text == 'Check Status':
        return check_bonus(chat_id, person)
    elif text == 'Get More Token':
        return display_investment_info(chat_id, person)
    elif text == 'Cancel':
        return cancel(chat_id, person)
    else:
        return start(chat_id, person)
        # bot.sendMessage(chat_id, '{}'.format(chat_id))


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
    time.sleep(3)
    bot.sendMessage(chat_id, 'Have you joined?', reply_markup=options)


def check_member(chat_id, person):
    try:
        member = bot.getChatMember(config.gcid, person.telegram_id)
    except:
        msg = 'You have not joined the channel yet. Please click the link'
        # bot.sendMessage(chat_id, msg)
        bot.sendMessage(chat_id, msg, reply_markup=MAIN_MENU)
        return
    if person.channel_member:
        msg = 'You have already received bonus for joining the group.'
        # bot.sendMessage(chat_id, msg)
        # time.sleep(3)
        bot.sendMessage(chat_id, msg, reply_markup=MAIN_MENU)
    else:
        person.channel_member = True
        person.bonus_amount += config.join_bonus_amount
        person.save()
        referrer = person.referred_by
        if referrer:
            referrer.bonus_amount += config.referral_bonus_amount
            ref_obj = Referral.objects.get(person=referrer)
            ref_obj.count += 1
            referrer.save()
            ref_obj.save()
            # msg_notif = 'Someone signed up using your referral link: you have received\
            #             additional bonus {} {}'.format(
            #     config.referral_bonus_amount,
            #     config.bonus_currency
            # )
            # bot.sendMessage(referrer.chat_id, msg_notif)
        msg_success = 'Congrats! you have received {} {}'.format(
            config.join_bonus_amount,
            config.bonus_currency
        )
        # bot.sendMessage(chat_id, msg_success)
        # time.sleep(3)
        bot.sendMessage(chat_id, msg_success, reply_markup=MAIN_MENU)


def start(chat_id, person):
    # if person.bonus_amount == 0:
    #     person.bonus_amount += config.join_bonus_amount
    #     person.save()
    #     msg = 'You have been rewared with {} {}'.format(
    #         config.join_bonus_amount,
    #         config.bonus_currency
    #     )
    #     bot.sendMessage(chat_id, msg)
    bot.sendMessage(chat_id, config.welcome_message, reply_markup=MAIN_MENU)


def referral_signup(chat_id, person, text):
    try:
        code = int(text.split()[-1])
        referral = Referral.objects.get(code=code)
    except (ValueError, Referral.DoesNotExist):
        error_msg = 'Oops! Something looks wrong with that referral link.'
        bot.sendMessage(chat_id, error_msg)
        # time.sleep(2)
        # bot.sendMessage(chat_id, reply_markup=MAIN_MENU)
        # return HttpResponse(status=200)
    if referral.count >= config.max_referral_count:
        bot.sendMessage(chat_id, config.max_referral_message)
        return start(chat_id, person)
    person.referred_by = referral.person
    # referrer.save()
    person.save()
    return start(chat_id, person)


def set_wallet_address(chat_id, person):
    msg_enter = 'Please enter a valid Wave wallet address'
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
        time.sleep(4)
        bot.sendMessage(chat_id, config.menu_text, reply_markup=MAIN_MENU)
        return
    except Referral.DoesNotExist:
        random_digit = random.randint(100, 999)
        referral_digit = int(chat_id) - random_digit
        # url = 'bappa.pythonanywhere.com/bot/prod/referral/?join={}'.format(
        #     referral_digit)
        url = 'telegram.me/{}/?start={}'.format(bot_specs.name, referral_digit)
        ref = Referral(
            person=person,
            url=url,
            code=referral_digit
        )
        ref.save()
        msg = 'You referral Link is {}'.format(url)
        bot.sendMessage(chat_id, msg)
        time.sleep(5)
        bot.sendMessage(chat_id, config.menu_text, reply_markup=MAIN_MENU)


def check_bonus(chat_id, person):
    try:
        person = Person.objects.get(telegram_id=chat_id)
        bonus_msg = 'For joining the channel, you receive {} {}\nWhen another joins the channel via your referral link, you get {} {}\nCurrently you have {} {} bonus'.format(
            config.join_bonus_amount,
            config.bonus_currency,
            config.referral_bonus_amount,
            config.bonus_currency,
            person.bonus_amount,
            config.bonus_currency
        )
        bot.sendMessage(chat_id, bonus_msg)
        # bot.sendMessage(chat_id, config.menu_text,
        #                 reply_markup=MAIN_MENU)
    except Person.DoesNotExist:
        bonus_msg = 'For joining the channel, you receive {} {}\nWhen another joins the channel via your referral link, you get {} {}\nCurrently you have {} {} bonus'.format(
            config.join_bonus_amount,
            config.bonus_currency,
            config.referral_bonus_amount,
            config.bonus_currency,
            0,
            config.bonus_currency
        )
        bot.sendMessage(chat_id, bonus_msg)
        time.sleep(3)
        bot.sendMessage(chat_id, config.menu_text, reply_markup=MAIN_MENU)


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
    bot.sendMessage(chat_id, msg_success, reply_markup=MAIN_MENU)
    return HttpResponse(status=200)
    # msg_already_exists = 'You have already supplied a Waller Address.\
    #                       You can change it from main menu'
    # msg_invalid_address = 'This wallet address is invalid. Try again:'
    # msg_cancel = "Type 'cancel' or 'exit' to quit."
    # if person.wallet_address:
    #     person.pending_input = False
    #     person.save()
    #     bot.sendMessage(chat_id, msg_already_exists)
    #     bot.sendMessage(chat_id, '', reply_markup=MAIN_MENU)
    # elif len(text) < 50:
    #     bot.sendMessage(chat_id, msg_invalid_address)
    #     person.pending_input = False
    #     person.save()
    #     bot.sendMessage(chat_id, '', reply_markup=MAIN_MENU)
    # else:
    #     person.wallet_address = text
    #     person.pending_input = False
    #     person.save()
    #     bot.sendMessage(chat_id, msg_success)
    #     bot.sendMessage(chat_id, '', reply_markup=MAIN_MENU)


def process_email_address(chat_id, person, text):
    msg_success = 'Congrats! I have saved your email address'
    try:
        person.email = text
        person.pending_input = False
        person.save()
    except ValidationError:
        msg_error = 'Something looks wrong with this email address.\n \
                    Please enter a email.'
        bot.sendMessage(chat_id, msg_error, reply_markup=MAIN_MENU)
    # bot.sendMessage(chat_id, msg_success)
    # time.sleep(3)
    bot.sendMessage(chat_id, msg_success, reply_markup=MAIN_MENU)


def cancel(chat_id, person):
    person.pending_input = False
    person.save()
    bot.sendMessage(
        chat_id,
        'Okay bye! Send a message if you need anything else.'
    )


def display_investment_info(chat_id, person):
    # bot.sendMessage(chat_id, config.invest_info)
    bot.sendMessage(chat_id, config.invest_info, reply_markup=MAIN_MENU)
