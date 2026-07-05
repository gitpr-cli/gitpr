from cryptography.fernet import Fernet
from pathlib import Path

# Path where the master encryption key will be stored
KEY_PATH = Path.home() / ".gitpr" / "secret.key"

def get_or_create_key():
    """
    Retrieves the master key from disk or generates a new one if it doesn't exist.
    """
    if not KEY_PATH.exists():
        KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key()
        with open(KEY_PATH, "wb") as key_file:
            key_file.write(key)
    return open(KEY_PATH, "rb").read()

def encrypt_data(data: str) -> str:
    """
    Transforms a string into an encrypted hash.
    """
    if not data:
        return ""
    key = get_or_create_key()
    f = Fernet(key)
    # Encrypts the string (converted to bytes) and returns as a readable string
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Transforms the encrypted hash back into the original string.
    """
    if not encrypted_data:
        return ""
    try:
        key = get_or_create_key()
        f = Fernet(key)
        # Decrypts and converts back to string (utf-8)
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception:
        # In case the key is invalid or the data is corrupted
        return ""