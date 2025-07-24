import os
import requests
from fastapi import Depends, HTTPException, Header, status
from typing import Annotated, List, Optional
from pydantic import BaseModel
from app.config import settings


async def get_id_header(Authorization):
    if not Authorization:
        return {"error": "Token required"}
    try:
        # print(Authorization, "auth")
        print("Validating JWT token...")
        # Extract the JWT token from the Authorization header
        jwt_token = Authorization.split(" ")[1]
        baseurl = os.getenv("BE_AUTH_API_URL")
        response = requests.post(
            f"{baseurl}/validate-token/", json={"token": jwt_token}
        )
        return response
    except Exception as e:
        print(e, "error")
        return {"error": f"Error: {e}"}


async def validate_token_with_auth_service(jwt_token: str) -> tuple[str | None, str | None]:
    """Validate token using the auth service"""
    try:
        print("🔐 Validating token with auth service...")
        baseurl = settings.BE_AUTH_API_URL
        if not baseurl:
            print("❌ BE_AUTH_API_URL not configured")
            return None, None
            
        response = requests.post(
            f"{baseurl}/validate-token/", 
            json={"token": jwt_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token validation successful: {data}")
            # Extract user_id and user_role from the response
            user_id = data.get("account_id")
            user_role = data.get("user_role")
            return user_id, user_role
        else:
            print(f"❌ Token validation failed: {response.status_code} - {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error validating token: {e}")
        return None, None
