import redis
import json

# Setup standard Redis connection
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

WAITING_QUEUE = "waiting_users"
ACTIVE_ROOMS_PREFIX = "active_room:"
ONLINE_USERS_PREFIX = "online:"

def set_user_online(user_id, channel_name):
    """Store user in Redis online dict with their channel name."""
    redis_client.set(f"{ONLINE_USERS_PREFIX}{user_id}", json.dumps({
        "user_id": user_id,
        "channel_name": channel_name
    }))

def remove_user_online(user_id):
    """Remove user from online dict."""
    redis_client.delete(f"{ONLINE_USERS_PREFIX}{user_id}")

def get_user_channel(user_id):
    """Get the channel name for a specific user_id."""
    data = redis_client.get(f"{ONLINE_USERS_PREFIX}{user_id}")
    if data:
        return json.loads(data).get("channel_name")
    return None

def add_to_waiting_queue(user_id):
    """Add user to waiting queue list."""
    redis_client.lrem(WAITING_QUEUE, 0, user_id)
    redis_client.rpush(WAITING_QUEUE, user_id)

def remove_from_waiting_queue(user_id):
    """Remove user from queue."""
    redis_client.lrem(WAITING_QUEUE, 0, user_id)

def get_waiting_user(exclude_user_id):
    """Get a user from queue who is not the excluding user."""
    users = redis_client.lrange(WAITING_QUEUE, 0, -1)
    for u in users:
        if str(u) != str(exclude_user_id):
            redis_client.lrem(WAITING_QUEUE, 0, u)
            return u
    return None

import time

def create_active_room(room_id, user1_id, user2_id):
    """Create an active room."""
    redis_client.set(f"{ACTIVE_ROOMS_PREFIX}{room_id}", json.dumps({
        "user1": user1_id,
        "user2": user2_id,
        "start_time": time.time()
    }))

def get_active_room(room_id):
    """Get active room details."""
    data = redis_client.get(f"{ACTIVE_ROOMS_PREFIX}{room_id}")
    if data:
        return json.loads(data)
    return None

def delete_active_room(room_id):
    """Delete an active room."""
    redis_client.delete(f"{ACTIVE_ROOMS_PREFIX}{room_id}")
