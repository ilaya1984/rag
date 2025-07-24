import os
import jwt
import asyncio
import socketio
from app.models import Users, ServiceProvider , Chat ,UserProfiles ,Roles
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from app.utils import validate_token_with_auth_service
from app.notification import send_push_notification
from urllib.parse import parse_qs
from socketio.exceptions import ConnectionRefusedError
import uuid
# Create ASGI Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

connected_users = {}  # sid -> account_id
print("Socket.IO server started newwwwwwwwwwwwwwwwxxxxxxxxxxxxxxxxxxwww")
user_sid_map={}
# from app.models import Base

# # Print all mapped classes
# for cls in Base.registry.mappers:
#     print(cls.class_.__name__)

async def user_info(user_role,account_id):
    try:
        async for db in get_db():
            user = None

            if user_role == "user" or user_role == "admin":
            # Step 2: Lookup Role by name (case-insensitive)
                result = await db.execute(
                    select(Roles).where(Roles.role_name.ilike(user_role))
                )
                role = result.scalar_one_or_none()
                # print("============>>>>>>>>>>",role.id)

                if not role:
                    raise ConnectionRefusedError(f"Invalid role: {user_role}")
                #, UserProfiles.role_id == role.id
                # Step 3: Lookup user with matching account_id and role_id
                result = await db.execute(
                    select(UserProfiles)
                    .where(UserProfiles.auth_id == account_id, UserProfiles.role_id == role.id)
                )
                user = result.scalar_one_or_none()
                return user
                # print(user,"==========================>")
            if not user:
                raise ConnectionRefusedError("Unauthorized access detected. The user could not be identified")

            # else: successful connection
            # user_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email
            
    except ValueError:
        return False

def is_valid_uuid(val):
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False

@sio.event
async def connect(sid, environ, auth):
    account_id = auth.get("userId") if auth else None
    user_role = auth.get("user_role") if auth else None
    print(f"User ID: {account_id}")
    print(f"🔌 Connected user_role: {user_role} SID: {sid}")
    if not account_id or not user_role:
        raise ConnectionRefusedError(" Missing authentication details")
    if not is_valid_uuid(account_id):
        raise ConnectionRefusedError("Invalid userId format")

    user=await user_info(user_role,account_id)

    # else: successful connection
    if not user:
        raise ConnectionRefusedError("User not found in database")

    user_name = (
        f"{user.first_name} {user.last_name}".strip()
        if user.first_name and user.last_name
        else user.email
    )
    if user_role == "admin":
        room = f"admin_room:{account_id}"
        await sio.save_session(sid, {...})
        await sio.enter_room(sid, room)  # Admin joins their own room
        print(f"Admin {account_id} listen ")   
    user_sid_map[account_id] = sid
    print(f" Authenticated: {user_name}")
    print(f"qqqqqqqqqqq zzzzzzzz Connected: {user_role} - {user_name}")
    await sio.emit("user_info", {"name": user_name}, to=sid)
    return "connected"



@sio.event
async def join(sid, data):
    try:
        account_id = data.get("userId")
        user_role = data.get("user_role")       
        user_name = data.get("user_name") or "Guest"
        print("connected_users:", connected_users)

        if not account_id or not user_role:
            await sio.emit("message", {
                "type": "system",
                "event": "invalid_token",
                "text": "Missing credentials"
            }, to=sid)
            return

        # USER joins admin-created room
        if user_role == "user":
            admin_id = data.get("admin_id")
            if not admin_id:
                await sio.emit("message", {
                    "type": "system",
                    "event": "missing_admin_id",
                    "text": "Missing admin ID for user"
                }, to=sid)
                return

            room = f"admin-room:{admin_id}"  # All users join their admin's room
            await sio.save_session(sid, {
                "account_id": account_id,
                "user_role": user_role,
                "room": room,
                "user_name": user_name,
                "admin_id": admin_id
            })
            await sio.enter_room(sid, room)
            connected_users[sid] = {
                "account_id": account_id,
                "user_role": user_role,
                "admin_id": admin_id,
                "user_name": user_name
            }

            # await sio.emit("message", {
            #     "type": "system",
            #     "event": "user_joined",
            #     "user_id": account_id,
            #     "user_name": user_name,
            #     "text": f"{user_name} joined the room"
            # }, room=room)

            await sio.emit("joined", {"room": room}, to=sid)
            await sio.emit("user_joined", {
                "userId": account_id,
                "userName": user_name
            }, room=f"admin_room:{admin_id}")

        # ADMIN creates own room
        elif user_role == "admin":
            room = f"admin-room:{account_id}"  # Admin’s own room

            await sio.save_session(sid, {
                "account_id": account_id,
                "user_role": user_role,
                "room": room,
                "user_name": user_name
            })
            await sio.enter_room(sid, room)
            connected_users[sid] = {
                "account_id": account_id,
                "user_role": user_role,
                "user_name": user_name
            }

            await sio.emit("message", {
                "type": "system",
                "event": "connected",
                "from": user_name,
                "text": f"Admin {user_name} is online"
            }, room=room)

            await sio.emit("joined", {"room": room}, to=sid)
            

        else:
            await sio.emit("message", {
                "type": "system",
                "event": "unauthorized",
                "text": f"Invalid user role: {user_role}"
            }, to=sid)
            return

    except Exception as e:
        print(f"[ERROR] join failed: {e}")
        await sio.emit("message", {
            "type": "system",
            "event": "error",
            "text": "Internal error"
        }, to=sid)


# ✅ Typing event
@sio.event
def typing(sid, data):
    from_user_id = data.get('from_user_id')
    to_user_id = data.get('to_user_id')
    user_role = data.get('user_role')

    to_sid = user_sid_map.get(to_user_id)
    if to_sid:
        sio.emit('typing', {
            'from_user_id': from_user_id,
            'user_role': user_role
        }, to=to_sid)

# ✅ Stop typing event
@sio.event
def stop_typing(sid, data):
    from_user_id = data.get('from_user_id')
    to_user_id = data.get('to_user_id')

    to_sid = user_sid_map.get(to_user_id)
    if to_sid:
        sio.emit('stop_typing', {
            'from_user_id': from_user_id
        }, to=to_sid)

@sio.event
async def message(sid, data):
    session = await sio.get_session(sid)
    print("message data:", session)
    room = session.get("room")
    account_id = session.get("account_id")
    name = session.get("name")
    user_role = session.get("user_role")
    target_account_id = session.get("target_account_id")

    if not room or not account_id:
        return

    msg_type = data.get("type", "user")   
    event = data.get("event", "message")
    text = data.get("text", "")
    
    # Prepare message data for broadcasting
    broadcast_data = {
        "type": msg_type,
        "event": event,
        "from": name,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Send to all users in the room except the sender (skip_sid)
    await sio.emit("message", broadcast_data, room=room, skip_sid=sid)
    
    # Check if target user is offline and send push notification
    if target_account_id:
        # Check if target user is online (connected)
        target_online = False
        for connected_sid, connected_account_id in connected_users.items():
            if connected_account_id == target_account_id:
                target_online = True
                break
        
        # If target user is offline, send push notification
        if not target_online:
            try:
                # Get auth token from session
                auth_token = session.get("auth_token")
                
                if not auth_token:
                    print("⚠️ No auth token found in session, skipping push notification")
                    return
                
                # Get target user type from session
                target_type = session.get("target_user_type")
                
                if not target_type:
                    print(f"⚠️ No target user type found in session, skipping push notification")
                    return
                
                # Send push notification
                await send_push_notification(
                    auth_token=auth_token,
                    title=f"New message from {name}",
                    message=text,
                    type=target_type,
                    sender_id=target_account_id,
                    data={
                        "sender_id": account_id,
                        "sender_name": name
                     }
                )
                print(f"📱 Push notification sent to offline user {target_account_id}")
                
            except Exception as e:
                print(f"❌ Failed to send push notification: {e}")
                # Optionally emit error to client
                await sio.emit("error", {
                    "type": "push_notification_error",
                    "message": "Failed to send push notification to offline user"
                }, to=sid)

@sio.event
async def message_from_admin(sid, data):
    to_user_id = data.get("to_user_id")
    text = data.get("text")
    session = await sio.get_session(sid)
    from_user = session.get("user_name")

    target_sid = user_sid_map.get(to_user_id)
    if target_sid:
        await sio.emit("message", {
            "type":"user",
            "timestamp": datetime.utcnow().isoformat(),
            "from_user_id": session["account_id"],
            "from": from_user,
            "text": text,
            "event":"message",
            "sender_role": "admin"
        }, to=target_sid)


        

@sio.event
async def message_from_user(sid, data):
    text = data.get("text")
    session = await sio.get_session(sid)
    from_user_id = session["account_id"]
    from_user_name = session["user_name"]
    admin_id = session["admin_id"]

    target_sid = user_sid_map.get(admin_id)
    if target_sid:
        await sio.emit("message", {
            "from_user_id": from_user_id,
            "from_user_name": from_user_name,
            "text": text,
            "sender_role": "user"
        }, to=target_sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnect"""
    user_info = connected_users.pop(sid, None)

    if user_info:
        account_id = user_info.get("account_id")
        name = user_info.get("user_name")
        room = user_info.get("room")
        user_role = user_info.get("user_role")
        admin_id= user_info.get("admin_id")
        # Clean up sid map
        user_sid_map.pop(account_id, None)

        print(f"🔌 {name} ({user_role}) disconnected")

        # Notify others in room (like admin)
        if user_role == "user":
            admin_sid = user_sid_map.get(admin_id)
        if admin_sid:
            await sio.emit("user_disconnected", {
                "userId": account_id,
                "userName": name
            }, to=admin_sid, skip_sid=sid)
            print(f"🔔 Sent user_disconnected to admin: {admin_sid}")

