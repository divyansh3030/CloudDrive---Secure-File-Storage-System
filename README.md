# CloudDrive - Secure File Storage System

A full-stack cloud-based file storage application with AWS S3 integration.

## 🚀 Features

- **Secure File Upload**: Upload files directly to AWS S3 with validation
- **File Management**: List, download, and delete files
- **Drag & Drop Interface**: User-friendly drag-and-drop upload
- **File Integrity**: SHA-256 hash verification
- **RESTful API**: Clean API architecture
- **Responsive Design**: Works on desktop and mobile

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS) → Flask Backend → AWS S3
                       ↓
                    Metadata Storage
```

## 📋 Prerequisites

- Python 3.8+
- AWS Account with S3 access
- AWS Access Key and Secret Key

## ⚙️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/clouddrive.git
cd clouddrive
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

4. Run the application:
```bash
python app.py
```

5. Open browser: `http://localhost:5000`

## 📁 Project Structure

```
clouddrive/
├── app.py                 # Flask backend
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── templates/
│   └── index.html        # Frontend HTML
├── static/
│   ├── style.css         # Styling
│   └── script.js         # Frontend logic
└── README.md
```

## 🔒 Security Features

- File type validation
- Size limit enforcement (16MB)
- Secure filename handling
- SHA-256 file hashing
- CORS protection

## 🛠️ Technologies Used

- **Backend**: Python, Flask
- **Cloud**: AWS S3, Boto3
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: Werkzeug, CORS

## 📊 API Endpoints

- `POST /api/upload` - Upload file
- `GET /api/files` - List all files
- `GET /api/download/<key>` - Download file
- `DELETE /api/delete/<key>` - Delete file

## 🎓 Academic Project

This project demonstrates:
- Cloud computing concepts (AWS S3)
- RESTful API design
- Secure file handling
- Full-stack development
- Modern web technologies

## 👨‍💻 Author

[Divyansh kakkar] 
    [divyanshkakkar30@gmail.com]

## 📄 License

MIT License - See LICENSE file for details