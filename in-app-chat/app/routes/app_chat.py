from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Chat, Users, ServiceProvider
from app.database import get_db
from app.utils import get_id_header
from app.helper import StandardResponse, ErrorResponse
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified
from app.schema import UpdateMessageRequest, BulkChatSaveRequest
from typing import Annotated

router = APIRouter()

@router.post("/chat/save/{booking_id}")
async def create_bulk_chat_save(
    booking_id: str,
    request: BulkChatSaveRequest,
    Authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """Create bulk chat save for a booking ID"""
    try:
        # Validate authorization
        if not Authorization:
            return ErrorResponse(status_code=401, message="Authorization header is required")
        
        auth_response = await get_id_header(Authorization)
        if not auth_response or auth_response.status_code != 200:
            return ErrorResponse(status_code=401, message="Unauthorized")
        
        auth_data = auth_response.json()
        user_account_id = auth_data.get("account_id")
        
        if not user_account_id:
            return ErrorResponse(status_code=401, message="Invalid token - account_id not found")
        
        # Validate required fields
        if not request.sender_id or not request.receiver_id:
            return ErrorResponse(status_code=400, message="sender_id and receiver_id are required")
        
        # Sort messages into sender_messages and receiver_messages based on user_id
        sender_messages = []
        receiver_messages = []
        
        for message in request.messages:
            if not message.get("user_id"):
                return ErrorResponse(status_code=400, message="Each message must have a user_id field")
            
            message_user_id = message.get("user_id")
            
            if message_user_id == request.sender_id:
                sender_messages.append(message)
            elif message_user_id == request.receiver_id:
                receiver_messages.append(message)
            else:
                return ErrorResponse(
                    status_code=400, 
                    message=f"Message user_id '{message_user_id}' does not match sender_id or receiver_id"
                )
        
        # Check if chat record already exists for this booking
        existing_chat = await db.execute(
            select(Chat).where(Chat.booking_id == booking_id)
        )
        existing_chat = existing_chat.scalar_one_or_none()
        
        if existing_chat:
            # Update existing chat record
            existing_chat.sender_id = request.sender_id
            existing_chat.receiver_id = request.receiver_id
            
            # Merge existing messages with new messages
            existing_sender_messages = existing_chat.sender_messages or []
            existing_receiver_messages = existing_chat.receiver_messages or []
            
            # Add new sender messages
            for msg in sender_messages:
                # Check if message already exists by ID
                if not any(existing_msg.get("id") == msg.get("id") for existing_msg in existing_sender_messages):
                    existing_sender_messages.append(msg)
                    # print(f"🔍 Debug: Added sender message: {msg.get('id')}")
                else:
                    # print(f"🔍 Debug: Skipped duplicate sender message: {msg.get('id')}")
                    pass
            
            # Add new receiver messages
            for msg in receiver_messages:
                # Check if message already exists by ID
                if not any(existing_msg.get("id") == msg.get("id") for existing_msg in existing_receiver_messages):
                    existing_receiver_messages.append(msg)
                    # print(f"🔍 Debug: Added receiver message: {msg.get('id')}")
                else:
                    # print(f"🔍 Debug: Skipped duplicate receiver message: {msg.get('id')}")
                    pass
            
            existing_chat.sender_messages = existing_sender_messages
            existing_chat.receiver_messages = existing_receiver_messages
            existing_chat.updated_at = datetime.utcnow()
            
            # Mark JSON fields as modified
            flag_modified(existing_chat, "sender_messages")
            flag_modified(existing_chat, "receiver_messages")
            
            await db.commit()
            await db.refresh(existing_chat)
            
            return StandardResponse(
                status_code=200,
                message="Existing chat record updated successfully",
                data={
                    "id": str(existing_chat.id),
                    "booking_id": str(existing_chat.booking_id),
                    "sender_id": str(existing_chat.sender_id),
                    "receiver_id": str(existing_chat.receiver_id),
                    "action": "updated_existing",
                    "sender_messages_count": len(existing_chat.sender_messages),
                    "receiver_messages_count": len(existing_chat.receiver_messages)
                }
            )
        
        # Create new chat record
        new_chat = Chat(
            booking_id=booking_id,
            sender_id=request.sender_id,
            receiver_id=request.receiver_id,
            sender_messages=sender_messages,
            receiver_messages=receiver_messages
        )
        
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)
        
        return StandardResponse(
            status_code=201,
            message="Chat record created successfully",
            data={
                "id": str(new_chat.id),
                "booking_id": str(new_chat.booking_id),
                "sender_id": str(new_chat.sender_id),
                "receiver_id": str(new_chat.receiver_id),
                "action": "created_new",
                "sender_messages_count": len(new_chat.sender_messages),
                "receiver_messages_count": len(new_chat.receiver_messages)
            }
        )
                
    except HTTPException:
        raise
    except Exception as e:
        return ErrorResponse(status_code=500, message="Failed to create chat records", error=str(e))


@router.patch("/chat/message/{message_id}")
async def update_message(
    message_id: str,
    request: UpdateMessageRequest,
    Authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """Update any fields in a message object"""
    try:
        # Validate authorization
        if not Authorization:
            return ErrorResponse(status_code=401, message="Authorization header is required")
        
        auth_response = await get_id_header(Authorization)
        if not auth_response or auth_response.status_code != 200:
            return ErrorResponse(status_code=401, message="Unauthorized")
        
        auth_data = auth_response.json()
        user_account_id = auth_data.get("account_id")
        
        if not user_account_id:
            return ErrorResponse(status_code=401, message="Invalid token - account_id not found")
        
        # Get account_id from request payload (sender_id or receiver_id)
        account_id = request.sender_id or request.receiver_id or user_account_id
        
        if not account_id:
            return ErrorResponse(status_code=400, message="Either sender_id or receiver_id is required")
        
        success = await update_message_fields(db, message_id, account_id, request.updates)
        if not success:
            return ErrorResponse(status_code=404, message="Message not found or access denied")
        
        return StandardResponse(
            status_code=200,
            message="Message updated successfully",
            data={
                "message_id": message_id, 
                "updates": request.updates, 
                "account_id": account_id
            }
        )
                
    except HTTPException:
        raise
    except Exception as e:
        return ErrorResponse(status_code=500, message="Failed to update message",error=str(e))


async def update_message_fields(db: AsyncSession, message_id: str, account_id: str, updates: dict) -> bool:
    """Update any fields in a message object"""
    try:
        # Query chat records for this user
        stmt = select(Chat).where(
            (Chat.sender_id == account_id) | (Chat.receiver_id == account_id)
        )
        result = await db.execute(stmt)
        chats = result.scalars().all()

        for chat in chats:
            updated = False
            
            # Check sender messages
            if chat.sender_messages:
                for msg in chat.sender_messages:
                    if msg.get("id") == message_id:
                        # Update all provided fields
                        for key, value in updates.items():
                            msg[key] = value
                        
                        # Add audit fields
                        # msg["updated_at"] = datetime.utcnow().isoformat()
                        # msg["updated_by"] = account_id
                        updated = True
                        break
            
            # Check receiver messages
            if not updated and chat.receiver_messages:
                for msg in chat.receiver_messages:
                    if msg.get("id") == message_id:
                        # Update all provided fields
                        for key, value in updates.items():
                            msg[key] = value
                        
                        # Add audit fields
                        # msg["updated_at"] = datetime.utcnow().isoformat()
                        # msg["updated_by"] = account_id
                        updated = True
                        break

            if updated:
                flag_modified(chat, "sender_messages")
                flag_modified(chat, "receiver_messages")
                await db.commit()
                return True

        return False

    except Exception as e:
        return False



@router.get("/chat/history/{booking_id}")
async def get_chat_history_by_booking_id(
    booking_id: str,
    Authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a booking ID"""
    try:
        # Validate authorization
        auth_response = await get_id_header(Authorization)
        if not auth_response or auth_response.status_code != 200:
            return ErrorResponse(status_code=401, message="Unauthorized")
        
        auth_data = auth_response.json()
        user_account_id = auth_data.get("account_id")
        
        if not user_account_id:
            return ErrorResponse(status_code=401, message="Invalid token - account_id not found")
        
        stmt = select(Chat).where(
            Chat.booking_id == booking_id
        ).order_by(Chat.created_at.desc())
        
        result = await db.execute(stmt)
        chat_records = result.scalars().all()
        
        if not chat_records:
            return StandardResponse(
                status_code=200,
                message="No chat data found for this booking",
                data=[]
            )
        
        # Process all chat records
        all_chat_data = []
        for record in chat_records:

            # Get participant names
            sender_name = "Unknown"
            receiver_name = "Unknown"
            
            # Get sender name
            if record.sender_id:
                stmt = select(Users).where(Users.id == record.sender_id)
                user_result = await db.execute(stmt)
                user = user_result.scalar_one_or_none()
                if user:
                    sender_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email
                
                # If not found in Users, check ServiceProvider
                if not user:
                    stmt = select(ServiceProvider).where(ServiceProvider.id == record.sender_id)
                    sp_result = await db.execute(stmt)
                    sp = sp_result.scalar_one_or_none()
                    if sp:
                        sender_name = f"{sp.first_name} {sp.last_name}" if sp.first_name and sp.last_name else sp.email
                        print(f"🔍 Debug: Found sender service provider: {sender_name}")
                    else: 
                        sender_name = "Unknown"
            
            # Get receiver name
            if record.receiver_id:
                stmt = select(Users).where(Users.id == record.receiver_id)
                user_result = await db.execute(stmt)
                user = user_result.scalar_one_or_none()
                if user:
                    receiver_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email
                
                # If not found in Users, check ServiceProvider
                if not user:
                    stmt = select(ServiceProvider).where(ServiceProvider.id == record.receiver_id)
                    sp_result = await db.execute(stmt)
                    sp = sp_result.scalar_one_or_none()
                    if sp:
                        receiver_name = f"{sp.first_name} {sp.last_name}" if sp.first_name and sp.last_name else sp.email
                    else:
                        receiver_name = "Unknown"
            
            # Collect all messages and merge them
            all_messages = []
            
            # Add sender messages
            if record.sender_messages:
                for msg in record.sender_messages:
                    if not msg.get("is_deleted", False):
                        message_with_metadata = {
                            **msg,
                            # "sender_id": str(record.sender_id),
                            # "sender_name": sender_name,
                            # "receiver_id": str(record.receiver_id),
                            # "receiver_name": receiver_name,
                            "message_type": "sent"
                        }
                        all_messages.append(message_with_metadata)
            
            # Add receiver messages
            if record.receiver_messages:
                for msg in record.receiver_messages:
                    if not msg.get("is_deleted", False):
                        message_with_metadata = {
                            **msg,
                            # "sender_id": str(record.sender_id),
                            # "sender_name": receiver_name,
                            # "receiver_id": str(record.receiver_id),
                            # "receiver_name": sender_name,
                            "message_type": "received"
                        }
                        all_messages.append(message_with_metadata)
            
            # Sort messages by timestamp
            all_messages.sort(key=lambda x: x.get("timestamp", ""))
            
            # Prepare complete chat record data
            chat_data = {
                "id": str(record.id),
                "booking_id": str(record.booking_id),
                "sender_id": str(record.sender_id),
                "sender_name": sender_name,
                "receiver_id": str(record.receiver_id),
                "receiver_name": receiver_name,
                "messages": all_messages,  # Merged and sorted messages
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            }
            
            all_chat_data.append(chat_data)
        
        return StandardResponse(
            status_code=200,
            message="Chat history retrieved successfully",
            data=all_chat_data
        )
            
    except Exception as e:
        return ErrorResponse(status_code=500, message="Failed to retrieve chat history",error=str(e))
