# app.py - Flask Backend with AWS S3 Integration
from flask import Flask, request, jsonify, render_template, send_file, session, redirect
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
import hashlib
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey123"   # needed for login sessions
CORS(app)

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
# 🔍 Test S3 connection
try:
    s3_client.list_buckets()
    print("S3 TEST: Connected Successfully ✓")
except Exception as e:
    print("S3 TEST FAILED:", e)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_file_hash(file_content):
    return hashlib.sha256(file_content).hexdigest()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
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
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=unique_filename,
            Body=file_content,
            Metadata={
                'original-filename': original_filename,
                'file-hash': file_hash,
                'upload-date': datetime.now().isoformat()
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
def list_files():
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET)
        
        if 'Contents' not in response:
            return jsonify({'files': []}), 200
        
        files = []
        for obj in response['Contents']:
            try:
                metadata = s3_client.head_object(Bucket=S3_BUCKET, Key=obj['Key'])
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
def download_file(key):
    try:
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
def delete_file(key):
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
        return jsonify({'message': 'File deleted successfully'}), 200
    except ClientError as e:
        return jsonify({'error': f'AWS Error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)