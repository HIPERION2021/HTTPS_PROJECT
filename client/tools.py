import os
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import os
import json
import uuid

def load_or_create_client_id(path='client_id.json'):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)['client_id']
    else:
        client_id = str(uuid.uuid4())
        with open(path, 'w') as f:
            json.dump({'client_id': client_id}, f)
        return client_id
def load_token(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)['token']
    else:
        return ''


def generate_key_pair(curve=ec.SECP256R1):
    private_key = ec.generate_private_key(curve())
    public_key = private_key.public_key()
    return private_key, public_key

def save_keys(private_key, public_key, c_id, private_filename="private_key.pem"):
    # Save private key
    public_filename = c_id + '_public_key.pem'
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
    c_id = load_or_create_client_id()
    private_key, public_key = generate_key_pair()
    save_keys(private_key, public_key, c_id)
   
