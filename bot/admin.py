from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import Person, Referral, Setting, Bot


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'email', 'bonus_amount', 'channel_member']
    read_only_fields = ['channel_member']
    exclude = ['pending_input', 'current_stage']
    list_filter = ['date_joined', 'channel_member', 'bonus_amount']
    search_fields = ['telegram_id', 'email']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['person', 'url', 'code', 'count', 'date_created']
    read_only_fields = ['count']


@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ['api_key', 'name', 'webhook']

admin.site.register(Setting, SingletonModelAdmin)
