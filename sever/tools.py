import os
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import os

def generate_token(length=32):
    token_bytes = os.urandom(length)
    return base64.urlsafe_b64encode(token_bytes).decode()

def hash_token(token, salt, iterations= 10000):

    if isinstance(token, str):
        token = token.encode('utf-8')
    if isinstance(salt, str):
        salt = salt.encode('utf-8')
    digest = hashlib.pbkdf2_hmac('sha256', token, salt, iterations)
    return digest.hex()

def generate_key_pair(curve=ec.SECP256R1):
    private_key = ec.generate_private_key(curve())
    public_key = private_key.public_key()
    return private_key, public_key

def load_public_key(filename="public_key.pem"):
    with open(filename, "rb") as f:
        return serialization.load_pem_public_key(f.read())

