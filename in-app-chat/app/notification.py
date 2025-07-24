from enum import Enum
import re
import logging
from typing import Optional
from pydantic import BaseModel, field_validator
import requests
from app.config import get_settings 
from app.models import Users,ServiceProvider
from app.database import get_db_session
from sqlalchemy import select

# Initialize settings and logger
settings = get_settings()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NotificationType(str, Enum):
    SMS = "sms"
    OTP = "otp"
    EMAIL = "email"
    PUSH = "push"


class CustomBaseModel(BaseModel):
    class Config:
        from_attributes = True
        use_enum_values = True

    @field_validator("phone_number", mode="before", check_fields=False)
    @classmethod
    def phone_validation(cls, v):
        if not v:
            return v
        regex = r"^\+?[1-9]{1,4}-?[0-9]{9,15}$"
        if not re.fullmatch(regex, v):
            raise ValueError(
                "Phone number is invalid. It should start with '+' followed by the country code, "
                "optionally include '-', and contain 9-15 digits."
            )
        return v


class NotificationRequest(CustomBaseModel):
    phone_number: Optional[str] = None
    email: Optional[str] = None
    sender_id: Optional[str] = None
    message: str
    notification_type: NotificationType
    title: Optional[str] = None
    data: Optional[dict] = None


async def get_user_by_id(user_id: str):
    """
    Fetches user details by ID.

    :param user_id: ID of the user to fetch
    :return: notification_uuid or None if not found
    """
    logger.info(f"Fetching user details for user_id: {user_id}")
    try:
        db = await get_db_session()
        query = select(Users).where(Users.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            notification_uuid = user.notification_uuid
            if not notification_uuid:
                logger.warning(f"User {user_id} does not have a notification_uuid.")
                return None
            logger.info(f"Successfully retrieved notification_uuid for user {user_id}: {notification_uuid}")
            return notification_uuid
        else:
            logger.warning(f"No user found with id: {user_id}") 
            return None
    except Exception as e:
        logger.error(f"Exception in get_user_by_id for user {user_id}: {str(e)}", exc_info=True)
        return None
    finally:
        await db.close()


async def get_service_provider_by_id(sp_id: str):
    """
    Fetches service provider details by ID.

    :param sp_id: ID of the service provider to fetch (UUID format)
    :return: notification_uuid or None if not found
    """
    try:
        db = await get_db_session()
        query = select(ServiceProvider).where(ServiceProvider.id == sp_id)
        result = await db.execute(query)
        service_provider = result.scalar_one_or_none()
        
        if service_provider:
            return service_provider.notification_uuid
        else:
            return None
    except Exception as e:
        logger.error(f"Exception in get_service_provider_by_id: {str(e)}", exc_info=True)
        return None
    finally:
        await db.close()

# Function to send push notification
async def send_push_notification(
    auth_token: str,
    title: str,
    message: str,
    sender_id: str,
    type: str,
    data: dict = {},
):
    """
    Sends a push notification using the API.

    :param auth_token: The authorization token (JWT or other)
    :param message: The message for the notification
    :param sender_id: The ID of the sender
    :return: Response from the API
    """
    logger.info(f"Sending push notification - Sender ID: {sender_id}, Type: {type}, Title: {title}, Message: {message}")
    if type == "user":
        sender_id = await get_user_by_id(user_id=sender_id)
    if type == "service_provider":
        sender_id = await get_service_provider_by_id(sp_id=sender_id)
        logger.info(f"Service provider sender_id: {sender_id}")
    # Get API URL from settings
    BASE_URL = settings.BE_NOTIFICATION_API_URL
    ENDPOINT = "/send_notification"
    API_URL = f"{BASE_URL}{ENDPOINT}"

    # Prepare notification request
    notification_data = NotificationRequest(
        message=message,
        title=title,
        notification_type=NotificationType.PUSH,
        sender_id=str(sender_id),
        data=data,
    )

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    }
    logger.info(f"Notification details - Title: {title}, Message: {message}, Sender ID: {sender_id}")

    # Make API request
    try:
        response = requests.post(
            API_URL, headers=headers, json=notification_data.dict()
        )  # ✅ Fix JSON payload
        response_data = response.json()  # ✅ Ensure response.json() is properly called

        logger.info(f"Response Code: {response.status_code}")
        logger.info(f"Response Data: {response_data}")

        return response.status_code, response_data

    except requests.RequestException as e:
        logger.error(f"Error sending notification: {str(e)}")
        return 500, {"error": "Failed to send notification"}
