import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# Директория для хранения токенов сброса пароля
RESET_TOKENS_DIR = os.path.join(settings.BASE_DIR, 'reset_tokens')
os.makedirs(RESET_TOKENS_DIR, exist_ok=True)


def generate_reset_token(email):
    """Генерация уникального токена для сброса пароля"""
    token = secrets.token_urlsafe(32)
    email_hash = hashlib.md5(email.encode()).hexdigest()

    token_data = {
        'token': token,
        'email': email,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(seconds=settings.PASSWORD_RESET_TIMEOUT)).isoformat()
    }

    file_path = os.path.join(RESET_TOKENS_DIR, f'{email_hash}.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)

    return token


def verify_reset_token(token):
    """Проверка токена и получение email пользователя"""
    for filename in os.listdir(RESET_TOKENS_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(RESET_TOKENS_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)

                if token_data.get('token') == token:
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if datetime.now() < expires_at:
                        return token_data['email']
                    else:
                        os.remove(file_path)
                        return None
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return None


def delete_reset_token(email):
    """Удаление токена после использования"""
    email_hash = hashlib.md5(email.encode()).hexdigest()
    file_path = os.path.join(RESET_TOKENS_DIR, f'{email_hash}.json')
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


def cleanup_expired_tokens():
    """Очистка просроченных токенов"""
    now = datetime.now()
    deleted = 0
    for filename in os.listdir(RESET_TOKENS_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(RESET_TOKENS_DIR, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if now >= expires_at:
                    os.remove(file_path)
                    deleted += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return deleted