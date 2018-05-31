import csv
import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from .models import ReceivedMessage, Person
from . import bot_router


@csrf_exempt
@require_POST
def hook(request):
    '''
    Main entry point for the bot.
    Django view to receive POST requests from Telegram,
    Extract the message JSON, and send for further processing.
    '''
    message = json.loads(request.body.decode('utf-8'))

    mid = message['update_id']
    if ReceivedMessage.objects.filter(message_id=mid).exists():
        return HttpResponse(status=200)
    else:
        rm = ReceivedMessage(message_id=mid)
        rm.save()
    return bot_router.route(message)


class Echo(object):
    """An object that implements just the write method of the file-like interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def generate_csv(request):
    people = Person.objects.all()  # Assume 50,000 objects inside
    model = people.model
    headers = ['telegram_id', 'email', 'wallet_address', 'bonus_amount']
    model_fields = model._meta.fields
    model_fields = [f for f in model_fields if f.name in headers]

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse(
        (writer.writerow(row)
         for row in stream(headers, people, model_fields)),
        content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="all_users.csv"'
    return response


def get_row(obj, model_fields):
    row = []
    for field in model_fields:
        # if type(field) == models.ForeignKey:
        #     val = getattr(obj, field.name)
        #     if val:
        #         val = val.__unicode__()
        # elif type(field) == models.ManyToManyField:
        #     val = u', '.join([item.__unicode__()
        #                       for item in getattr(obj, field.name).all()])
        # elif field.choices:
        #     val = getattr(obj, 'get_%s_display' % field.name)()
        # else:
        val = getattr(obj, field.name)
        row.append(str(val).encode("utf-8"))
    return row


def stream(headers, data, model_fields):  # Helper function to inject headers

    if headers:
        yield headers
    for obj in data:
        yield get_row(obj, model_fields)
