import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.http import HttpResponse
from .models import Person, Referral, Setting, Bot, ReceivedMessage
import telepot


@csrf_exempt
@require_POST
def hook(request):
    '''
    Main entry point for the bot.
    Django view to receive POST requests from Telegram,
    Extract the message JSON, and send for further processing.
    '''
    data = json.loads(request.body.decode('utf-8'))

    try:
        flavour = telepot.flavor(data['message'])
    except:
        flavour = telepot.flavor(data['callback_query'])

    mid = data['update_id']
    if ReceivedMessage.objects.filter(message_id=mid).exists():
        return HttpResponse(status=200)
    else:
        rm = ReceivedMessage(message_id=mid)
        rm.save()

    if flavour == 'chat':
        return chat_router(data['message'])

    return HttpResponse(status=200)


def chat_router(message):
    pass
