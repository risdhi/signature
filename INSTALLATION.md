# Installation Guide - Signature Verification AI

## System Requirements

### Minimum
- Python 3.8 or higher
- MySQL 5.7 or higher
- 2GB RAM
- 1GB disk space

### Recommended
- Python 3.10 or higher
- MySQL 8.0 or higher
- 8GB RAM
- NVIDIA GPU (optional, for faster processing)
- 5GB disk space

### Supported Platforms
- macOS 10.14+
- Ubuntu 18.04+ / Debian 10+
- Windows 10/11
- CentOS 7+

---

## Step-by-Step Installation

### 1. Install Python

#### macOS
```bash
# Using Homebrew
brew install python3

# Verify
python3 --version
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Verify
python3 --version
```

#### Windows
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. Check "Add Python to PATH"
4. Verify in Command Prompt:
```cmd
python --version
```

### 2. Install MySQL

#### macOS
```bash
# Using Homebrew
brew install mysql

# Start MySQL
brew services start mysql

# Secure installation
mysql_secure_installation
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install mysql-server

# Secure installation
sudo mysql_secure_installation

# Start MySQL
sudo service mysql start
```

#### Windows
1. Download MySQL Community Server from [mysql.com](https://dev.mysql.com/downloads/mysql/)
2. Run installer
3. Follow setup wizard
4. Configure MySQL as service

#### Verify Installation
```bash
mysql --version
mysql -u root -p -e "SELECT VERSION();"
```

### 3. Create Project Directory

```bash
cd /Users/fadhil/Documents/project_gw/signature
pwd  # Verify you're in the right directory
```

### 4. Create & Activate Virtual Environment

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate

# You should see (venv) in your prompt
```

#### Windows
```cmd
python -m venv venv
venv\Scripts\activate

# You should see (venv) in your prompt
```

### 5. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

This will install:
- Flask 3.0
- TensorFlow 2.14
- OpenCV 4.8
- MySQL drivers
- And all dependencies

### 6. Configure MySQL Database

#### Create Database User

```sql
-- Login to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE signature_verification 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'sigadmin'@'localhost' IDENTIFIED BY 'your_secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON signature_verification.* 
  TO 'sigadmin'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Verify
SHOW GRANTS FOR 'sigadmin'@'localhost';

-- Exit
EXIT;
```

#### For Remote Database

If using a remote MySQL server:

```sql
-- Create user accessible from any host
CREATE USER 'sigadmin'@'%' IDENTIFIED BY 'your_secure_password';

GRANT ALL PRIVILEGES ON signature_verification.* 
  TO 'sigadmin'@'%';

FLUSH PRIVILEGES;
```

### 7. Configure Environment Variables

Edit `.env` file in project root:

```bash
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Security
SECRET_KEY=your-secret-key-change-in-production

# Database Configuration
DATABASE_URL=mysql+pymysql://sigadmin:your_secure_password@localhost:3306/signature_verification

# Model Configuration
MODEL_PATH=model/siamese_signature_model.keras
SIMILARITY_THRESHOLD=0.82
DISTANCE_THRESHOLD=0.25
VOTING_THRESHOLD=0.7

# Upload Configuration
MAX_CONTENT_LENGTH=16777216
MIN_REFERENCE_SIGNATURES=2
MAX_REFERENCE_SIGNATURES=5

# Logging
LOG_LEVEL=INFO
```

**Important**: Replace `your_secure_password` with your actual MySQL password.

### 8. Verify Model Files

Ensure pre-trained model files are in the `model/` directory:

```bash
ls -la model/

# Output should show:
# siamese_signature_model.h5
# and/or
# siamese_signature_model.keras
```

If files are missing, copy them:

```bash
cp /path/to/siamese_signature_model.keras model/
# or
cp /path/to/siamese_signature_model.h5 model/
```

### 9. Initialize Database

Create tables in the database:

```bash
python init_db.py --init
```

Expected output:
```
Creating database tables...
✓ Database tables created successfully!

Database URI: mysql+pymysql://sigadmin:***@localhost:3306/signature_verification
Upload folder: /path/to/app/static/uploads
Model path: /path/to/model/siamese_signature_model.keras
```

### 10. Test Configuration

```bash
python -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    print('✓ App created successfully')
    print(f'✓ Database URI: {app.config[\"SQLALCHEMY_DATABASE_URI\"]}')
    print(f'✓ Model path: {app.config[\"MODEL_PATH\"]}')
    print(f'✓ Upload folder: {app.config[\"UPLOAD_FOLDER\"]}')
    db.engine.execute('SELECT 1')
    print('✓ Database connection successful')
"
```

---

## Running the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Run application
python run.py
```

Server starts at: **http://127.0.0.1:5000**

### Production Mode

#### Using Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

#### Using uWSGI

```bash
# Install uWSGI
pip install uwsgi

# Run with uWSGI
uwsgi --http :5000 --wsgi-file run.py --callable app --processes 4 --threads 2
```

#### Using Docker (Optional)

```bash
# Build image
docker build -t signature-ai .

# Run container
docker run -d \
  -e DATABASE_URL=mysql+pymysql://sigadmin:password@host:3306/signature_verification \
  -p 5000:5000 \
  signature-ai
```

---

## Verification Checklist

After installation, verify everything works:

```bash
# 1. Check Python environment
python --version

# 2. Check virtual environment
which python  # Should show venv path

# 3. Check MySQL connection
mysql -u sigadmin -p -e "SELECT VERSION();"

# 4. Check Flask app
python run.py

# 5. Open browser
# http://localhost:5000

# 6. Check database
python -c "from app import create_app; app = create_app(); db.engine.execute('SELECT COUNT(*) FROM users')"
```

---

## Troubleshooting

### "No module named 'app'"
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Install requirements again
pip install -r requirements.txt
```

### "Access denied for MySQL user"
```bash
# Verify credentials in .env
cat .env | grep DATABASE_URL

# Test MySQL connection manually
mysql -u sigadmin -p -h localhost

# Check user privileges
mysql -u root -p -e "SHOW GRANTS FOR 'sigadmin'@'localhost';"
```

### "Port 5000 already in use"
```bash
# Change port in .env
FLASK_PORT=5001

# Or kill process using port
lsof -ti:5000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5000   # Windows
```

### "Model file not found"
```bash
# Check if file exists
ls -la model/siamese_signature_model.keras

# Check config path
python -c "from app.config import config; print(config['development'].MODEL_PATH)"

# Verify file permissions
chmod 644 model/siamese_signature_model.keras
```

### "Out of memory"
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS
Get-ComputerInfo -Property TotalPhysicalMemory  # Windows

# Reduce image size in app/config.py
IMG_SIZE = (224, 224)  # Instead of (299, 299)
```

### "TensorFlow GPU issues"
```bash
# Install TensorFlow CPU version
pip uninstall tensorflow
pip install tensorflow-cpu

# Or install CUDA/cuDNN for GPU support
# See: https://www.tensorflow.org/install/source
```

---

## Database Backup & Restore

### Backup

```bash
# Full database backup
mysqldump -u sigadmin -p signature_verification > backup.sql

# With compression
mysqldump -u sigadmin -p signature_verification | gzip > backup.sql.gz
```

### Restore

```bash
# From SQL file
mysql -u sigadmin -p signature_verification < backup.sql

# From compressed file
gunzip < backup.sql.gz | mysql -u sigadmin -p signature_verification
```

---

## Development Environment Setup

### Install Development Tools

```bash
# Linting
pip install flake8 black pylint

# Testing
pip install pytest pytest-cov pytest-flask

# Debugging
pip install ipdb

# Hot reload
pip install python-dotenv
```

### VS Code Setup

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/.pytest_cache": true
    }
}
```

---

## Next Steps

1. **Read QUICKSTART.md** for immediate start
2. **Review README.md** for comprehensive documentation
3. **Check API examples** in documentation
4. **Customize thresholds** in `.env`
5. **Test with sample data**
6. **Deploy to production**

---

## Support & Resources

- **TensorFlow Docs**: https://www.tensorflow.org/
- **Flask Docs**: https://flask.palletsprojects.com/
- **OpenCV Docs**: https://docs.opencv.org/
- **MySQL Docs**: https://dev.mysql.com/doc/
- **Python Docs**: https://docs.python.org/

---

**Need Help?**
- Check logs: `tail -f logs/signature_verification.log`
- Review error messages carefully
- Verify all prerequisites are installed
- Ensure file permissions are correct
- Check firewall/network settings
