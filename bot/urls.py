from django.urls import path
from django.conf import settings
from . import views


app_name = 'bot'
urlpatterns = [
    path('prod/hook/{}/'.format(settings.SECRET), views.hook, name='hook'),
    path('prod/referall/', views.referall, name='referall_join')
]
