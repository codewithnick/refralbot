from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import Person, Referral, Setting, Bot

admin.site.register(Person)
admin.site.register(Referral)
admin.site.register(Bot)
admin.site.register(Setting, SingletonModelAdmin)
