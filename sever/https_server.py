# https_server.py - Implementing a secure server with HTTPS

import os
import json
import base64
import time
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import mysql.connector
from tools import load_public_key, generate_key_pair, generate_token, hash_token
from datetime import date
from dateutil.relativedelta import relativedelta

app = Flask(__name__)

# Directory for storing malformed messages (kind of a log to avoid losing data if something fails)
UPLOAD_FOLDER = 'received_messages'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Server ECDH key
server_private_key, server_public_key = generate_key_pair()

verify_key = load_public_key("public_key.pem")
client_sessions = {}

@app.route('/api/key_exchange', methods=['POST'])
def key_exchange():
    try:
        data = request.json
        client_id = data.get('client_id')
        client_public_key_pem = data.get('public_key')
        
        if not client_id or not client_public_key_pem:
            return jsonify('Missing client ID or public key'), 400
        
        # Load client public key
        client_public_key = serialization.load_pem_public_key(client_public_key_pem.encode())
        
        # Generate shared key
        shared_key = server_private_key.exchange(ec.ECDH(), client_public_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data'
        ).derive(shared_key)
        
        # Store session info
        client_sessions[client_id] = {
            'key': derived_key,
            'public_key': client_public_key,
            'created_at': time.time()
        }
        
        # Return server public key
        return jsonify({
            'public_key': server_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_data():
    try:
        client_id = request.headers.get('X-Client-ID')
        if not client_id or client_id not in client_sessions:
            return jsonify({'error': 'Invalid or missing client ID'}), 401
        #check if the clinet id exists and have a token to validate access
        try:
            #connection configurations is hard coded for now, is best to make configuration files. for this prototype we are mre interested in encryption and authentication...
            conn = mysql.connector.connect(user='root', password='',
                    host='127.0.0.1',
                    database='project_CSS',
                    use_pure=False)
            cursor = conn.cursor(dictionary=True)
            sql = f"SELECT * from users WHERE userid = %s AND valid = 1"
            cursor.execute(sql, (client_id,))
            users = cursor.fetchall()

            if len(users) == 1:
                user = users[0]
                #authenticate token, use client_id first part as salt (not a good idea, but just testing is ok...)
                client_token = hash_token(request.headers.get('token'), client_id[:16])
                db_token = user['token']
                current_date = date.today()
                revoke_date = user['until']
                if client_token != db_token:
                    if conn.is_connected():
                        conn.close()
                        cursor.close()
                    return jsonify('Connection refused...'), 401
                if current_date >= revoke_date: #check the validity of the presented token
                    sql = f"UPDATE users SET valid = 0 WHERE ID = %s"
                    cursor.execute(sql, (user['ID'],))
                    conn.commit()
                    if conn.is_connected():
                        conn.close()
                        cursor.close()
                    return jsonify('Invalid token, please contact your administrator...'), 401
            else:
                #no token, we make the entry and generate a token for the client 
                print("Connection refused, please contact your administrator and ask for a valid authentication code\n")
                token = generate_token()
                #add a part of teh client id as salt (I know... not optimal) and calculate the hash for the database.
                #we NEVER save teh token in the server, we generate the file here, but the dea is to give the only copy to the client.
                #We could use a symmetric key to encrypt it for extra security. Maybe if we have time...
                token_db = hash_token(token, client_id[:16])
                today = date.today()
                until = today + relativedelta(years=1)
                sql = f"INSERT INTO users (userid, token, created, until) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (client_id, token_db, today, until))
                conn.commit()
                with open(str(client_id) + '.json', 'w') as f:
                    json.dump({'token': token}, f)
                    f.close()
                if conn.is_connected():
                    conn.close()
                    cursor.close()
                return jsonify('Request accepted.\nplease contact the administrator to receive a valid authentication token'), 401 # terminate the connection
        except mysql.connector.Error as e:
            return jsonify('Connection refused, please contact your administrator'), 401

        if conn.is_connected():
            conn.close()
            cursor.close()

        
        # Get client session
        session = client_sessions[client_id]
        
        # Get encrypted data parts
        nonce = base64.b64decode(request.json.get('nonce', ''))
        ciphertext = base64.b64decode(request.json.get('ciphertext', ''))
        signature = base64.b64decode(request.json.get('signature', ''))
        
        if not nonce or not ciphertext:
            return jsonify('Missing encryption data'), 400
        
        # Decrypt the data
        try:
            aesgcm = AESGCM(session['key'])
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            return jsonify(str(e)), 400
        
        # Verify signature 
        if signature:
            try:
                verify_key.verify(signature, plaintext, ec.ECDSA(hashes.SHA256()))
            except InvalidSignature:
                return jsonify('Invalid signature'), 400
        
        # Process the decrypted data
        try:
            data = json.loads(plaintext)
            try:
                link = mysql.connector.connect(user='root', password='',
                        host='127.0.0.1',
                        database='project_CSS',
                        use_pure=False)
                cursor = link.cursor(dictionary=True)

            except mysql.connector.Error as e:
                filename = f'data_{int(time.time())}.bin'
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                with open(filepath, 'wb') as f:
                    f.write(plaintext)
                #I had these as json in the beggining but the client side is showing the entire thing.. so it looks ugly but it works
                return jsonify('Something went wrong, please contact the network administrator'), 401  

            #some columns have no default value and are NEEDED for teh insert to work, this is in purpose...
            try:
                columns = [x for x in data.keys() if x !='type']
                query = f"INSERT INTO data ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
                cursor.execute(query, [data[column] for column in columns])
                link.commit()
                
                if link.is_connected():
                    link.close()
                    cursor.close()
                    
                return jsonify({
                    'status': 'success',
                    'message': f'Data saved'
                })
            except Exception as e:
                filename = f'data_{int(time.time())}.bin'
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                with open(filepath, 'wb') as f:
                    f.write(plaintext)
                
                return jsonify('Malformed data... please try again...'), 401
                
        except json.JSONDecodeError:
            # Handle non-JSON data
            filename = f'data_{int(time.time())}.bin'
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            with open(filepath, 'wb') as f:
                f.write(plaintext)
            
            return jsonify({
                'status': 'success',
                'message': f'Raw data saved as {filename}',
                'size': len(plaintext)
            })
            
    except Exception as e:
        return jsonify(str(e)), 500


@app.route('/api/session_cleanup', methods=['POST'])
def cleanup_sessions():
    """Admin endpoint to cleanup old sessions"""
    # Simple auth check - in production use better auth
    if request.headers.get('X-Admin-Token') != os.environ.get('ADMIN_TOKEN', 'admin_secret'):
        return jsonify('error : Unauthorized'), 401
    
    # Current time
    now = time.time()
    # Max session age (2 hours)
    max_age = 7200
    
    # Find expired sessions
    expired = [client_id for client_id, session in client_sessions.items() 
               if now - session['created_at'] > max_age]
    
    # Remove expired sessions
    for client_id in expired:
        del client_sessions[client_id]
    
    return jsonify({
        'status': 'success',
        'removed': len(expired),
        'remaining': len(client_sessions)
    })

if __name__ == "__main__":
    
    # SSL context for HTTPS
    ssl_context = ('cert.pem', 'key.pem')
    
    # If cert files don't exist, inform user they need to create them
    if not os.path.exists('cert.pem') or not os.path.exists('key.pem'):
        print("SSL certificates not found. Create them with:")
        print("openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
        print("The server is not secure, please create the SSL certificates and start again\n")
    
    app.run(host='0.0.0.0', port=5000, ssl_context=ssl_context, debug=False)
