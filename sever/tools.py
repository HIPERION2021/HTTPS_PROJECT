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

def save_keys(private_key, public_key, private_filename="private_key.pem", public_filename="public_key.pem"):
    # Save private key
    with open(private_filename, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    os.chmod(private_filename, 0o600)
    
    with open(public_filename, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

def load_private_key(filename="private_key.pem", password=None):
    with open(filename, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=password)

def load_public_key(filename="public_key.pem"):
    with open(filename, "rb") as f:
        return serialization.load_pem_public_key(f.read())

if __name__ == "__main__":
    #Run the file to generate the keys. They will be saved in teh current folder. The prived goes to client the public to server.
    private_key, public_key = generate_key_pair()
    save_keys(private_key, public_key)
    print("Keys generated and saved to private_key.pem and public_key.pem")