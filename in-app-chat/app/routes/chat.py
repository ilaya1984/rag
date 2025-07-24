# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from typing import Dict
# from datetime import datetime

# from app.database import get_db
# from app.models import Chat
# from app.routes.schema import ChartMessageSchema, ChatMetadataResponse

# router = APIRouter()

# # Store active websocket connections
# online_users: Dict[str, WebSocket] = {}

# def send_push_notification(to_user: str, message: str):
#     print(f"[PUSH] To: {to_user} => {message}")

# def send_sms_alert(to_user: str, message: str):
#     print(f"[SMS] To: {to_user} => {message}")


# @router.websocket("/ws/{user_id}")
# async def chat_websocket(websocket: WebSocket, user_id: str, db: AsyncSession = Depends(get_db)):
#     await websocket.accept()
#     online_users[user_id] = websocket
#     print(f"[CONNECTED] {user_id}")

#     try:
#         while True:
#             data = await websocket.receive_json()
#             to_user = data.get("to")
#             booking_id = data.get("booking_id")
#             message_text = data.get("message")

#             if not to_user or not booking_id or not message_text:
#                 await websocket.send_json({"error": "Missing 'to', 'booking_id', or 'message'"})
#                 continue

#             result = await db.execute(
#                 select(Chat).filter_by(
#                     sender_id=user_id,
#                     receiver_id=to_user,
#                     booking_id=booking_id
#                 )
#             )
#             chat_instance = result.scalars().first()

#             if not chat_instance:
#                 chat_instance = Chat(
#                     sender_id=user_id,
#                     receiver_id=to_user,
#                     booking_id=booking_id,
#                     messages=[],
#                     status="active"
#                 )
#                 db.add(chat_instance)
#                 await db.commit()
#                 await db.refresh(chat_instance)

#             new_msg = {
#                 "from": user_id,
#                 "text": message_text,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
#             chat_instance.messages = (chat_instance.messages or []) + [new_msg]
#             await db.commit()

#             if to_user in online_users:
#                 print(f"[REALTIME] Sending to {to_user}")
#                 await online_users[to_user].send_json({
#                     "from": user_id,
#                     "message": message_text,
#                     "booking_id": booking_id
#                 })
#             else:
#                 print(f"[OFFLINE] {to_user} not connected")
#                 send_push_notification(to_user, message_text)
#                 send_sms_alert(to_user, message_text)

#     except WebSocketDisconnect:
#         print(f"[DISCONNECTED] {user_id}")
#     except Exception as e:
#         print(f"[ERROR] {user_id}: {e}")
#     finally:
#         online_users.pop(user_id, None)


# @router.get("/chat/account_id/{chat_id}", response_model=ChatMetadataResponse)
# async def get_chat_metadata(chat_id: str, db: AsyncSession = Depends(get_db)):
#     try:
#         result = await db.execute(select(Chat).filter_by(id=chat_id))
#         chat = result.scalar_one_or_none()

#         if not chat:
#             raise HTTPException(status_code=404, detail="Chat not found")

#         return ChatMetadataResponse(
#             chat_id=str(chat.id),
#             participants=[str(chat.sender_id), str(chat.receiver_id)],
#             booking_id=str(chat.booking_id),
#             created_at=chat.created_at.isoformat() if chat.created_at else None,
#             status=chat.status,
#             message_count=len(chat.messages or [])
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to retrieve chat metadata: {str(e)}")


# @router.post("/chat/send")
# async def send_message(message_data: ChartMessageSchema, db: AsyncSession = Depends(get_db)):
#     new_message = Chat(
#         booking_id=message_data.booking_id,
#         sender_id=message_data.sender_id,
#         receiver_id=message_data.receiver_id,
#         messages=message_data.messages,
#     )

#     db.add(new_message)
#     await db.commit()
#     await db.refresh(new_message)

#     return new_message