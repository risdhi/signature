# Quick Start Guide - Signature Verification AI

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- Existing `.keras` or `.h5` model in `model/` directory

### Step 1: Clone & Setup Virtual Environment
```bash
cd /Users/fadhil/Documents/project_gw/signature

# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Database

**Create MySQL Database:**
```sql
CREATE DATABASE signature_verification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sigadmin'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON signature_verification.* TO 'sigadmin'@'localhost';
FLUSH PRIVILEGES;
```

**Update `.env` file:**
```env
DATABASE_URL=mysql+pymysql://sigadmin:password123@localhost:3306/signature_verification
SIMILARITY_THRESHOLD=0.82
DISTANCE_THRESHOLD=0.25
```

### Step 4: Place Pre-trained Model
```bash
# Your model files are already in place:
ls model/
# Output: siamese_signature_model.h5 siamese_signature_model.keras
```

### Step 5: Initialize Database
```bash
python init_db.py --init
```

Expected output:
```
Creating database tables...
✓ Database tables created successfully!
```

### Step 6: Run Application
```bash
python run.py
```

Expected output:
```
WARNING in app.run_helpers: This is a development server. Do not use it in production. Use a production WSGI server instead.
Running on http://127.0.0.1:5000
```

### Step 7: Open Web Browser
Visit: **`http://localhost:5000`**

## 📋 First Time Users

### 1. Create a User
- Click **"Register"** button
- Enter:
  - Username: `john_doe`
  - Email: `john@example.com`
  - Full Name: `John Doe` (optional)
- Click **"Create User"**

### 2. Register Signatures
- Upload 3-5 genuine signatures
- Formats: PNG, JPG, BMP, GIF
- Click **"Upload"**

### 3. Verify Signature
- Select user
- Upload test signature
- Wait for result
- View GENUINE or FORGED with confidence score

### 4. View History
- Check all past verifications
- View detailed metrics
- Track accuracy

## 🔌 API Usage Examples

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Create User
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jane_smith",
    "email": "jane@example.com",
    "full_name": "Jane Smith"
  }'
```

### Register Signatures
```bash
curl -X POST http://localhost:5000/api/users/1/register \
  -F "files=@signature1.png" \
  -F "files=@signature2.png" \
  -F "files=@signature3.png"
```

### Verify Signature
```bash
curl -X POST http://localhost:5000/api/users/1/verify \
  -F "file=@test_signature.png"
```

Response:
```json
{
  "prediction": "GENUINE",
  "confidence": 97.5,
  "average_similarity": 0.945,
  "max_similarity": 0.975,
  "matched_signatures": 4,
  "total_signatures": 5
}
```

## 🎯 Important Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/register` | GET/POST | Register new user |
| `/upload-signatures/<id>` | GET/POST | Upload signatures |
| `/verify/<id>` | GET/POST | Verify signature |
| `/result/<user_id>/<history_id>` | GET | View result |
| `/history/<id>` | GET | Verification history |
| `/api/health` | GET | API health check |
| `/api/users` | GET/POST | User management |
| `/api/users/<id>/verify` | POST | API verification |

## ⚠️ Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
**Solution**: Verify you're in correct directory and virtual environment is activated

### "Access denied for user 'root'@'localhost'"
**Solution**: Check MySQL username/password in `.env`

### "Model file not found"
**Solution**: Ensure model files are in `model/` directory:
```bash
ls -la model/
# Should show: siamese_signature_model.h5 or .keras
```

### "Port 5000 already in use"
**Solution**: Change port in `.env`:
```env
FLASK_PORT=5001
```

### "CUDA not found"
**Solution**: CPU version works fine, just slower. GPU optional.

## 📊 System Information

After running, you can check:

**Database Status:**
```bash
python -c "
from app import create_app
from app.extensions import db
from app.database.models import User
app = create_app()
with app.app_context():
    print(f'Total users: {User.query.count()}')
"
```

**Model Info:**
```bash
python -c "
from app.config import config
cfg = config['development']
print(f'Model: {cfg.MODEL_PATH}')
print(f'Input size: {cfg.IMG_SIZE}')
print(f'Similarity threshold: {cfg.SIMILARITY_THRESHOLD}')
"
```

## 🎨 Customization Examples

### Change Similarity Threshold
Edit `.env`:
```env
SIMILARITY_THRESHOLD=0.75  # More lenient
# or
SIMILARITY_THRESHOLD=0.90  # More strict
```

### Change Input Image Size
Edit `app/config.py`:
```python
IMG_SIZE = (224, 224)  # Default: (299, 299)
```

### Change Database
Edit `.env`:
```env
DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname
```

## 📚 Directory Guide

```
Project Root
├── app/                    # Flask application
│   ├── ai/                # AI/ML modules
│   ├── database/          # Database models
│   ├── routes/            # Flask routes
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, uploads
├── model/                 # Pre-trained models ← Your .h5/.keras
├── logs/                  # Application logs
├── .env                   # Configuration ← UPDATE THIS
├── requirements.txt       # Dependencies
├── run.py                 # Entry point
└── init_db.py            # DB initialization
```

## ✅ Verification Checklist

Before using in production:

- [ ] Database configured and initialized
- [ ] Model files placed in `model/` directory
- [ ] `.env` file configured with correct values
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Application starts without errors
- [ ] Dashboard loads at http://localhost:5000
- [ ] Can create user
- [ ] Can upload signatures
- [ ] Can verify signatures
- [ ] Can view history

## 🔐 Before Production

1. **Change SECRET_KEY** in `.env`
2. **Use HTTPS** and set `SESSION_COOKIE_SECURE=True`
3. **Update database password**
4. **Use production WSGI server** (Gunicorn, uWSGI)
5. **Set FLASK_ENV=production**
6. **Enable proper error logging**
7. **Setup SSL certificates**
8. **Regular backups**

## 📞 Support

For issues:
1. Check logs in `logs/` folder
2. Review error message in terminal
3. Check `.env` configuration
4. Verify database connection
5. Review README.md for detailed info

---

**Next Step**: Check README.md for comprehensive documentation
