

from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "LLM-TUTOR1234"
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 600  # 10 hours

def generate_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def verify_token(token: str) -> dict:
    try:
        # Decode will automatically verify signature and exp claim
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise