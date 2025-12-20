# app.py - Flask Backend with AWS S3 Integration and Authentication
from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
import io  # ADD THIS LINE if not already there
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
from datetime import timedelta

import hashlib
import uuid
from dotenv import load_dotenv
import json
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey123')

# Session configuration for production
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app, supports_credentials=True, origins=['https://clouddrive-secure-file-storage-system.onrender.com'])

# AWS S3 Configuration
S3_BUCKET = os.environ.get('S3_BUCKET_NAME', 'your-bucket-name')
S3_REGION = os.environ.get('AWS_REGION', 'ap-south-1')
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

# Debug: Check if environment variables are loaded
print("=" * 60)
print("AWS CONFIGURATION CHECK:")
print(f"Bucket: {S3_BUCKET}")
print(f"Region: {S3_REGION}")
print(f"Access Key: {AWS_ACCESS_KEY[:10] + '...' if AWS_ACCESS_KEY else 'None'}")
print(f"Secret Key: {'Loaded ✓' if AWS_SECRET_KEY else 'None ✗'}")
print("=" * 60)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)

# Test S3 connection
try:
    s3_client.list_buckets()
    print("S3 TEST: Connected Successfully ✓")
except Exception as e:
    print("S3 TEST FAILED:", e)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# User storage in S3
USERS_FILE_KEY = 'app-data/users.json'

def load_users():
    """Load users from S3"""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=USERS_FILE_KEY)
        return json.loads(response['Body'].read().decode('utf-8'))
    except ClientError:
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    """Save users to S3"""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=USERS_FILE_KEY,
            Body=json.dumps(users, indent=4),
            ContentType='application/json'
        )
    except Exception as e:
        print(f"Error saving users: {e}")

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_file_hash(file_content):
    return hashlib.sha256(file_content).hexdigest()

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/login')
def login_page():
    if 'user_email' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    if 'user_email' in session:
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('login.html', error='Please provide email and password')
        
        users = load_users()
        
        if email not in users:
            return render_template('login.html', error='Invalid email or password')
        
        if not check_password_hash(users[email]['password'], password):
            return render_template('login.html', error='Invalid email or password')
        
        session['user_email'] = email
        session['user_id'] = users[email]['user_id']
        return redirect(url_for('index'))
        
    except Exception as e:
        return render_template('login.html', error=str(e))

@app.route('/signup', methods=['POST'])
def signup():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return render_template('signup.html', error='Please provide email and password')
        
        if len(password) < 6:
            return render_template('signup.html', error='Password must be at least 6 characters')
        
        users = load_users()
        
        if email in users:
            return render_template('signup.html', error='Email already registered')
        
        users[email] = {
            'user_id': str(uuid.uuid4()),
            'password': generate_password_hash(password),
            'created_at': datetime.now().isoformat()
        }
        
        save_users(users)
        
        session['user_email'] = email
        session['user_id'] = users[email]['user_id']
        return redirect(url_for('index'))
        
    except Exception as e:
        return render_template('signup.html', error=str(e))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ==================== FILE MANAGEMENT ROUTES ====================

@app.route('/')
@login_required
def index():
    return render_template('index.html', user_email=session.get('user_email'))

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Read file content
        file_content = file.read()
        if len(file_content) > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds limit'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_hash = generate_file_hash(file_content)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        
        # Upload to S3 with user information
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=unique_filename,
            Body=file_content,
            Metadata={
                'original-filename': original_filename,
                'file-hash': file_hash,
                'upload-date': datetime.now().isoformat(),
                'user-id': session.get('user_id', 'unknown'),
                'user-email': session.get('user_email', 'unknown')
            }
        )
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': original_filename,
            's3_key': unique_filename,
            'file_hash': file_hash
        }), 200
        
    except ClientError as e:
        return jsonify({'error': f'AWS Error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
@login_required
def list_files():
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        
        if 'Contents' not in response:
            return jsonify({'files': []}), 200
        
        files = []
        user_id = session.get('user_id')
        
        for obj in response['Contents']:
            # Skip the users.json file
            if obj['Key'] == USERS_FILE_KEY:
                continue
                
            try:
                metadata = s3_client.head_object(Bucket=S3_BUCKET, Key=obj['Key'])
                
                # Only show files uploaded by current user
                if metadata['Metadata'].get('user-id') == user_id:
                    files.append({
                        'key': obj['Key'],
                        'filename': metadata['Metadata'].get('original-filename', obj['Key']),
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'file_hash': metadata['Metadata'].get('file-hash', 'N/A')
                    })
            except:
                pass
        
        return jsonify({'files': files}), 200
        
    except ClientError as e:
        return jsonify({'error': f'AWS Error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<key>', methods=['GET'])
@login_required
def download_file(key):
    try:
        # Verify file belongs to user
        metadata = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        if metadata['Metadata'].get('user-id') != session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 403
        
        file_obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
        return send_file(
            file_obj['Body'],
            as_attachment=True,
            download_name=file_obj['Metadata'].get('original-filename', key)
        )
    except ClientError as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<key>', methods=['DELETE'])
@login_required
def delete_file(key):
    try:
        # Verify file belongs to user
        metadata = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        if metadata['Metadata'].get('user-id') != session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 403
        
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        return jsonify({'message': 'File deleted successfully'}), 200
    except ClientError as e:
        return jsonify({'error': f'AWS Error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# File Sharing - Generate Share Link
@app.route('/api/share/<key>', methods=['POST'])
@login_required
def share_file(key):
    try:
        # Verify file belongs to user
        metadata = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        if metadata['Metadata'].get('user-id') != session.get('user_id'):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Generate share token
        share_token = str(uuid.uuid4())
        expiry_hours = request.json.get('expiry_hours', 24)
        expiry_time = datetime.now() + timedelta(hours=expiry_hours)
        
        # Store share info in metadata
        share_data = {
            'token': share_token,
            'key': key,
            'filename': metadata['Metadata'].get('original-filename', key),
            'expiry': expiry_time.isoformat(),
            'owner_id': session.get('user_id')
        }
        
        # Save to S3 as JSON
        share_key = f'shares/{share_token}.json'
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=share_key,
            Body=json.dumps(share_data),
            ContentType='application/json'
        )
        
        share_link = f"{request.host_url}shared/{share_token}"
        return jsonify({'share_link': share_link, 'expiry': expiry_time.isoformat()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Download Shared File
@app.route('/shared/<token>')
def shared_file(token):
    try:
        # Get share data
        share_key = f'shares/{token}.json'
        share_obj = s3_client.get_object(Bucket=S3_BUCKET, Key=share_key)
        share_data = json.loads(share_obj['Body'].read().decode('utf-8'))
        
        # Check expiry
        expiry_time = datetime.fromisoformat(share_data['expiry'])
        if datetime.now() > expiry_time:
            return "This link has expired", 410
        
        # Get the actual file
        file_obj = s3_client.get_object(Bucket=S3_BUCKET, Key=share_data['key'])
        return send_file(
            io.BytesIO(file_obj['Body'].read()),
            as_attachment=True,
            download_name=share_data['filename']
        )
        
    except ClientError:
        return "Invalid or expired link", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
