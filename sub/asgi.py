import os

from django.urls import path
from .schema import MyGraphqlWsConsumer
import channels.auth
import channels.routing
import django.contrib.admin
import django.contrib.auth
import django.core.asgi
import graphene
import graphql

import channels_graphql_ws

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sub.settings')
# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
application = channels.routing.ProtocolTypeRouter(
    {
        "http": django.core.asgi.get_asgi_application(),
        "websocket": channels.auth.AuthMiddlewareStack(
            channels.routing.URLRouter(
                [path("ws/graphql/", MyGraphqlWsConsumer.as_asgi())]
            )
        ),
    }
)
