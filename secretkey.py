import os
import secrets

KEY_FILE = os.path.join(os.path.dirname(__file__), '.secret_key')

def get_secret_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'r') as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(KEY_FILE, 'w') as f:
        f.write(key)
    return key

secret_key = get_secret_key()
