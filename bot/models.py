from django.db import models
from solo.models import SingletonModel


class Person(models.Model):

    class Meta:
        verbose_name_plural = 'people'

    telegram_id = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, null=True, blank=True)
    wallet_address = models.CharField(max_length=100, null=True, blank=True)
    bonus_amount = models.IntegerField(default=0)
    referred_by = models.ForeignKey(
        'self',
        related_name='references',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    channel_member = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    pending_input = models.BooleanField(default=False)
    current_stage = models.IntegerField(default=0)

    def __str__(self):
        return self.telegram_id


class Referral(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE)
    url = models.URLField(max_length=150)
    code = models.IntegerField(default=123)
    count = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}'.format(self.url)


class Setting(SingletonModel):
    gcid = models.CharField(
        'Telegram Group Channel ID',
        max_length=50,
        default=''
    )
    gc_invite = models.TextField(
        'Message to display when inviting user to group channel',
        blank=True,
        null=True
    )
    max_referral_count = models.IntegerField(default=100)
    max_referral_message = models.TextField(
        'Message to display when user reaches max number of referrals',
        blank=True,
        null=True
    )
    bonus_currency = models.CharField(default='ETH', max_length=50)
    referral_bonus_amount = models.IntegerField(default=500)
    join_bonus_amount = models.IntegerField(default=500)
    welcome_message = models.TextField(
        'Message to display when a user joins the chat.'
    )
    unavailable_message = models.TextField(
        'Message to display when bot is unavailable.'
    )
    invest_info = models.TextField(
        'Information on how users can invest in ICO',
        default='default'
    )
    max_users = models.IntegerField(default=1000)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Bot Settings'


class Bot(SingletonModel):
    api_key = models.CharField('API Key', max_length=100)
    name = models.CharField('Bot Name', max_length=50)
    webhook = models.URLField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ReceivedMessage(models.Model):
    message_id = models.IntegerField()

    def __str__(self):
        return str(self.message_id)
