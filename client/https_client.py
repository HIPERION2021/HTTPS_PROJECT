# https_client.py - Client implementation for the HTTPS server

import os
import json
import base64
import uuid
import requests
import argparse
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from tools import load_private_key

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

class SecureHTTPSClient:
    def __init__(self, server_url, verify_ssl=True, signing_key_path="private_key.pem", ca_cert_path=None):
        # Server URL (e.g., https://example.com:5000)
        self.server_url = server_url.rstrip('/')
        self.verify_ssl = ca_cert_path if ca_cert_path else verify_ssl
        
        if not verify_ssl:
            # Suppress insecure request warnings when verify_ssl is False
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Generate client ID
        self.client_id = load_or_create_client_id()
        self.token = load_token(str(self.client_id) + '.json')
        
        # Generate ECDH key pair
        self.ecdh_private_key = ec.generate_private_key(ec.SECP256R1())
        self.ecdh_public_key = self.ecdh_private_key.public_key()
        
        # Load signing key if provided
        self.signing_key = None
        if signing_key_path and os.path.exists(signing_key_path):
            self.signing_key = load_private_key(signing_key_path)
        
        self.server_public_key = None
        self.derived_key = None

    def perform_key_exchange(self):
        try:
            public_key_pem = self.ecdh_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            
            # Send key exchange request
            response = requests.post(
                f"{self.server_url}/api/key_exchange",
                json={
                    'client_id': self.client_id,
                    'public_key': public_key_pem
                },
                verify=self.verify_ssl
            )
            
            # Check response
            if response.status_code != 200:
                print(f"Key exchange failed: {response.text}")
                return False
            
            data = response.json()
            server_public_key_pem = data.get('public_key')
            
            self.server_public_key = serialization.load_pem_public_key(
                server_public_key_pem.encode()
            )
            
            # Derive shared secret
            shared_key = self.ecdh_private_key.exchange(ec.ECDH(), self.server_public_key)
            self.derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'handshake data'
            ).derive(shared_key)
            
            print(" Key exchange successful")
            return True
            
        except Exception as e:
            print(f"Error during key exchange: {e}")
            return False

    def send_data(self, data, sign=True):
        if not self.derived_key:
            if not self.perform_key_exchange():
                return False
        
        try:
            if isinstance(data, dict):
                plaintext = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                plaintext = data.encode('utf-8')
            else:
                plaintext = data
            
            # Generate nonce for AES-GCM
            nonce = os.urandom(12)
            # Encrypt the data
            aesgcm = AESGCM(self.derived_key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            
            # Prepare request data
            request_data = {
                'nonce': base64.b64encode(nonce).decode(),
                'ciphertext': base64.b64encode(ciphertext).decode()
            }
            
            # Sign the plaintext if requested and signing key is available
            if sign and self.signing_key:
                signature = self.signing_key.sign(
                    plaintext,
                    ec.ECDSA(hashes.SHA256())
                )
                request_data['signature'] = base64.b64encode(signature).decode()
            
            # Send the request
            response = requests.post(
                f"{self.server_url}/api/upload",
                json=request_data,
                headers={'X-Client-ID': self.client_id, 'token' : self.token},
                verify=self.verify_ssl
            )
            
            # Check response
            if response.status_code != 200:
                print(f"Upload failed: {response.text}")
                return False
            
            print("Data sent successfully")
            return response.json()
            
        except Exception as e:
            print(f"Error sending data: {e}")
            return False

    

def main():
    
    parser = argparse.ArgumentParser(description='Secure HTTPS client for file transfer')
    parser.add_argument('--server', default='https://localhost:5000', help='Server URL')
    parser.add_argument('--no-verify', action='store_true', help='Disable SSL verification')
    parser.add_argument('message', help='JSON message to send')
    args = parser.parse_args()
    
    ca_cert_path = 'cert.pem' if not args.no_verify else False
    client = SecureHTTPSClient(args.server, verify_ssl=ca_cert_path)
    
    try:
        message = json.loads(args.message)
    except json.JSONDecodeError:
        message = args.message
    
    client.send_data(message)
    

if __name__ == "__main__":
    main()
