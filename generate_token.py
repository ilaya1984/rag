import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "yd4057895-4d0c"
ALGORITHM = "HS256"

def generate_token(account_id: str, expires_in_minutes: int = 60):
    payload = {
        "account_id": account_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# Example usage
print(generate_token("jc-2352"))
print(generate_token("jc-2353"))
