import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user_by_jwt(token):
    try:
        # Note: settings.SIMPLE_JWT['SIGNING_KEY'] might be used, but by default it's SECRET_KEY
        # Check settings.SIMPLE_JWT['ALGORITHM'] too. 'HS256' is default.
        signing_key = getattr(settings, 'SIMPLE_JWT', {}).get('SIGNING_KEY', settings.SECRET_KEY)
        algorithm = getattr(settings, 'SIMPLE_JWT', {}).get('ALGORITHM', 'HS256')
        
        payload = jwt.decode(token, signing_key, algorithms=[algorithm])
        user = User.objects.get(id=payload['user_id'])
        return user
    except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist, KeyError):
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        
        token = query_params.get("token")
        if token:
            scope['user'] = await get_user_by_jwt(token[0])
        else:
            scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)
