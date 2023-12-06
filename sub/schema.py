
from post.models import Post

from graphene_django import DjangoObjectType
import channels_graphql_ws
import graphene

from graphene_django.filter import DjangoFilterConnectionField

class PostNode(DjangoObjectType):
    class Meta:
        model = Post
        filter_fields = []
        interfaces = (graphene.relay.Node, )


class Query(graphene.ObjectType):
    post = graphene.relay.Node.Field(PostNode)
    all_posts = DjangoFilterConnectionField(PostNode)



class CreatePostMutation(graphene.Mutation):
    message = graphene.String()

    class Arguments:
        # The input arguments for this mutation
        title = graphene.String(required=True)
        content = graphene.String(required=True)
 

    @classmethod
    def mutate(cls, root, info, title, content):
        Post.objects.create(
            title= title,
            content= content,
            author= info.context.user
        )
        # Notice we return an instance of this mutation
        NotifyCreatedPost.broadcast(payload={
            "event": "test",
            "username": info.context.user.username
        }, group=info.context.user.username)
        return CreatePostMutation(message='success')

class Mutation(graphene.ObjectType):
    create_post = CreatePostMutation.Field()




class NotifyCreatedPost(channels_graphql_ws.Subscription):
    """Simple GraphQL subscription."""
    event = graphene.String()
    username = graphene.String()


    class Arguments:
        """That is how subscription arguments are defined."""
        username = graphene.String()

    @staticmethod
    def subscribe(self, info, username=None):
        """Called when user subscribes."""
        del info
        # Return the list of subscription group names.
        return [username] if username is not None else None


    @staticmethod
    def publish(payload, info, username=None):
        """Called to notify the client."""
        # Here `payload` contains the `payload` from the `broadcast()`
        # invocation (see below). You can return `None` if you wish to
        # suppress the notification to a particular client. For example,
        # this allows to avoid notifications for the actions made by
        # this particular client.

        return NotifyCreatedPost(event=payload, username=username)
class OnNewChatMessage(channels_graphql_ws.Subscription):
    """Subscription triggers on a new chat message."""

    sender = graphene.String()
    chatroom = graphene.String()
    text = graphene.String()

    class Arguments:
        """Subscription arguments."""

        chatroom = graphene.String()

    def subscribe(self, info, chatroom=None):
        """Client subscription handler."""
        del info
        # Specify the subscription group client subscribes to.
        return [chatroom] if chatroom is not None else None

    def publish(self, info, chatroom=None):
        """Called to prepare the subscription notification message."""

        # The `self` contains payload delivered from the `broadcast()`.
        new_msg_chatroom = self["chatroom"]
        new_msg_text = self["text"]
        new_msg_sender = self["sender"]

        # Method is called only for events on which client explicitly
        # subscribed, by returning proper subscription groups from the
        # `subscribe` method. So he either subscribed for all events or
        # to particular chatroom.
        assert chatroom is None or chatroom == new_msg_chatroom

        # Avoid self-notifications.
        user = info.context.channels_scope["user"]
        if user.is_authenticated and new_msg_sender == user.username:
            return None

        return OnNewChatMessage(
            chatroom=chatroom, text=new_msg_text, sender=new_msg_sender
        )

    @classmethod
    async def new_chat_message(cls, chatroom, text, sender):
        """Auxiliary function to send subscription notifications.

        It is generally a good idea to encapsulate broadcast invocation
        inside auxiliary class methods inside the subscription class.
        That allows to consider a structure of the `payload` as an
        implementation details.
        """
        await cls.broadcast(
            group=chatroom,
            payload={"chatroom": chatroom, "text": text, "sender": sender},
        )


class Subscription(graphene.ObjectType):
    """Root GraphQL subscription."""
    notified_created_post = NotifyCreatedPost.Field()
    on_new_chat_message = OnNewChatMessage.Field()

schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription,)

# async def demo_middleware(next_middleware, root, info, *args, **kwds):
#     """Demo GraphQL middleware.

#     For more information read:
#     https://docs.graphene-python.org/en/latest/execution/middleware/#middleware
#     """
#     # Skip Graphiql introspection requests, there are a lot.
#     if (
#         info.operation.name is not None
#         and info.operation.name.value != "IntrospectionQuery"
#     ):
#         print("Demo middleware report")
#         print("    operation :", info.operation.operation)
#         print("    name      :", info.operation.name.value)

#     # Invoke next middleware.
#     result = next_middleware(root, info, *args, **kwds)
#     if graphql.pyutils.is_awaitable(result):
#         result = await result
#     return result


class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    """Channels WebSocket consumer which provides GraphQL API."""

    # Uncomment to send keepalive message every 42 seconds.
    send_keepalive_every = 42

    # Uncomment to process requests sequentially (useful for tests).
    # strict_ordering = True

    async def on_connect(self, payload):
        """New client connection handler."""
        # You can `raise` from here to reject the connection.
        print("New client connected!")
        # self.scope["user"] = await channels.auth.get_user(self.scope)


    # middleware = [demo_middleware]
    schema = schema
