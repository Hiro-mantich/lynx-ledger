import secrets

SECRET_KEY = secrets.token_urlsafe(32)  # Секретный ключ для JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней