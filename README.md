# Signature Verification AI System

Complete fullstack AI-powered signature verification system using Siamese Network architecture with a pre-trained neural network backbone.

## 🎯 Features

- **User Registration**: Register multiple reference signatures for each user
- **Signature Verification**: Compare test signatures against registered ones
- **Siamese Network**: Uses pre-trained model for embedding-based comparison
- **Similarity Metrics**: Cosine similarity and Euclidean distance calculations
- **Voting Mechanism**: Multiple reference signature voting for robust verification
- **Modern Web UI**: Responsive, intuitive interface with real-time feedback
- **REST API**: Complete API for integration with other systems
- **Database**: MySQL backend for persistent storage
- **Image Preprocessing**: Advanced OpenCV-based preprocessing pipeline

## 🏗️ Project Structure

```
signature-ai/
├── app/
│   ├── static/              # Static assets (CSS, JS)
│   ├── templates/           # HTML templates
│   ├── preprocessing/       # Image preprocessing
│   ├── ai/                  # AI/ML modules
│   ├── database/            # Database models
│   ├── routes/              # Flask routes
│   ├── utils/               # Utilities
│   ├── config.py            # Configuration
│   ├── extensions.py        # Flask extensions
│   └── __init__.py          # App factory
├── model/                   # Pre-trained model files
├── checkpoints/             # Model checkpoints
├── logs/                    # Application logs
├── run.py                   # Entry point
├── init_db.py               # Database initialization
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md                # This file
```

## 📋 Requirements

- Python 3.8+
- MySQL 5.7+
- CUDA 11.x (optional, for GPU acceleration)

## 🚀 Installation & Setup

### 1. Clone Repository & Navigate

```bash
cd /Users/fadhil/Documents/project_gw/signature
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. MySQL Setup

#### Create Database

```sql
CREATE DATABASE signature_verification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sigadmin'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON signature_verification.* TO 'sigadmin'@'localhost';
FLUSH PRIVILEGES;
```

#### Update `.env` file

```env
DATABASE_URL=mysql+pymysql://sigadmin:your_secure_password@localhost:3306/signature_verification
```

### 5. Place Pre-trained Model

Copy your model files to the `model/` directory:

```bash
# Using existing model files
cp /path/to/siamese_signature_model.keras model/
# or
cp /path/to/siamese_signature_model.h5 model/
```

### 6. Initialize Database

```bash
python init_db.py --init
```

This creates all necessary tables:
- `users` - User profiles
- `reference_signatures` - Registered signatures
- `verification_history` - Verification records

## ▶️ Running the Application

### Start Flask Development Server

```bash
python run.py
```

The application will start at `http://127.0.0.1:5000`

### Access the Web Interface

1. **Dashboard**: `http://localhost:5000/`
2. **Register User**: `http://localhost:5000/register`
3. **Verify Signature**: `http://localhost:5000/verify/<user_id>`

## 📱 Web Interface

### Dashboard
- System statistics
- Recent verifications
- User management

### Register User
1. Enter username and email
2. Upload 3-5 genuine signatures
3. System generates embeddings and stores reference data

### Verify Signature
1. Select registered user
2. Upload test signature
3. View instant verification result with confidence score

### Verification History
- View past verifications
- Track accuracy metrics
- Export results

## 🔌 API Endpoints

### Health Check
```bash
GET /api/health
```

### Users
```bash
GET    /api/users                    # List all users
POST   /api/users                    # Create new user
GET    /api/users/<id>              # Get user details
```

### Registration
```bash
POST /api/users/<id>/register        # Register signatures
GET  /api/users/<id>/reference-signatures
```

### Verification
```bash
POST /api/users/<id>/verify          # Verify signature
GET  /api/users/<id>/verification-history
GET  /api/verification/<id>          # Get verification result
```

### Statistics
```bash
GET /api/stats                       # System statistics
```

## 🧠 AI/ML Architecture

### Model Pipeline

```
Original Image
    ↓
Preprocessing (OpenCV)
    ├─ Grayscale conversion
    ├─ Adaptive thresholding
    ├─ Denoising
    ├─ Background removal
    ├─ Auto-crop
    └─ Resize with padding
    ↓
Pre-trained Model (Feature Extractor)
    ├─ Load existing .h5/.keras model
    ├─ Remove classification layer
    └─ Use penultimate layer as embedding extractor
    ↓
Embedding Vector (N-dimensional)
    ↓
Siamese Network Verification
    ├─ Compare with reference embeddings
    ├─ Cosine Similarity: ≥ 0.82
    ├─ Euclidean Distance: ≤ 0.25
    └─ Voting mechanism (70% threshold)
    ↓
Result: GENUINE or FORGED
```

### Preprocessing Pipeline

#### OpenCV Operations
- **Grayscale Conversion**: Reduce to 1 channel
- **Adaptive Thresholding**: Binary image generation
- **Denoising**: Fast non-local means denoising
- **Background Removal**: Morphological operations
- **Contour Extraction**: Signature boundaries
- **Auto-crop**: Focus on signature area
- **Padding Alignment**: Consistent size (299×299)

#### Output
Normalized, preprocessed image ready for model input

### Similarity Metrics

#### Cosine Similarity
- Range: [0, 1]
- 1 = identical, 0 = orthogonal
- Default threshold: ≥ 0.82

#### Euclidean Distance
- Range: [0, ∞]
- 0 = identical, ∞ = maximum difference
- Default threshold: ≤ 0.25

#### Voting Mechanism
```
Match Count = signatures meeting BOTH cosine AND distance thresholds
Vote Score = Match Count / Total Reference Signatures
Decision = Vote Score ≥ 70% → GENUINE, else → FORGED
Confidence = Vote Score × 100
```

## 📊 Verification Flow

### Registration Flow
```
1. User uploads 3-5 genuine signatures
2. Each signature is preprocessed
3. Embeddings are extracted using pre-trained model
4. Embeddings and images are stored in database
5. User profile marked as registered
```

### Verification Flow
```
1. User uploads test signature
2. Test signature is preprocessed
3. Embedding extracted from test signature
4. Embeddings compared with all reference embeddings
5. Similarity scores calculated
6. Voting mechanism applied
7. Final prediction (GENUINE/FORGED) with confidence
8. Results saved to database and displayed
```

## 🎨 Customization

### Adjust Thresholds

Edit `.env` file:

```env
SIMILARITY_THRESHOLD=0.82        # Cosine similarity threshold
DISTANCE_THRESHOLD=0.25          # Euclidean distance threshold
VOTING_THRESHOLD=0.7             # Voting percentage (0-1)
```

### Change Model

Replace in `app/config.py`:

```python
MODEL_PATH = os.getenv('MODEL_PATH', 'path/to/your/model.h5')
IMG_SIZE = (299, 299)  # Update based on your model input
```

### Preprocessing Parameters

Edit `app/preprocessing/preprocess.py`:

```python
# Adaptive threshold parameters
block_size = 11
C = 2

# Denoise parameters
h = 10
template_size = 7
search_size = 21
```

## 🔐 Security Considerations

1. **Change SECRET_KEY** in `.env` for production
2. **Use HTTPS** in production (set `SESSION_COOKIE_SECURE=True`)
3. **Secure Database**: Use strong passwords
4. **Input Validation**: All inputs are validated
5. **Rate Limiting**: Implement in production
6. **Authentication**: Add user authentication for production

## 🚨 Troubleshooting

### Database Connection Error
```
Error: Access denied for user 'root'@'localhost'
```
**Solution**: Check MySQL credentials in `.env`

### Model Not Found
```
FileNotFoundError: Model file not found
```
**Solution**: Ensure model files are in `model/` directory

### Out of Memory
```
ResourceExhaustedError: OOM when allocating tensor
```
**Solution**: Reduce batch size or upgrade GPU memory

### Image Not Loaded
```
ValueError: Failed to load image
```
**Solution**: Check image format and path; ensure PNG/JPG/BMP

### Port Already in Use
```
Address already in use
```
**Solution**: Change port in `.env` or kill process on port 5000

## 📈 Performance Optimization

### For CPU
- Reduce image preprocessing quality
- Use smaller model if available
- Enable model quantization

### For GPU
- Install TensorFlow GPU version
- Use CUDA for acceleration
- Batch process multiple verifications

## 📚 API Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "timestamp": "2024-01-01T00:00:00"
}
```

### Verification Result
```json
{
  "prediction": "GENUINE",
  "confidence": 97.5,
  "average_similarity": 0.945,
  "max_similarity": 0.975,
  "min_similarity": 0.910,
  "euclidean_distance": 0.112,
  "matched_signatures": 4,
  "total_signatures": 5,
  "voting_score": 0.80,
  "cosine_similarities": [0.945, 0.975, 0.910, 0.935, 0.920],
  "euclidean_distances": [0.112, 0.089, 0.145, 0.125, 0.135]
}
```

## 🔄 Database Schema

### users
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `full_name` - Full name
- `is_registered` - Registration status
- `registration_date` - Account creation date

### reference_signatures
- `id` - Primary key
- `user_id` - Foreign key to users
- `image_path` - Original image path
- `processed_image_path` - Preprocessed image path
- `embedding_path` - Embedding file path
- `embedding` - JSON embedding vector
- `upload_date` - Upload timestamp

### verification_history
- `id` - Primary key
- `user_id` - Foreign key to users
- `test_image_path` - Test image path
- `prediction` - GENUINE/FORGED
- `confidence` - Confidence score
- `average_similarity` - Mean similarity
- `euclidean_distance` - Mean distance
- `matched_signatures` - Count of matched refs
- `similarity_scores` - JSON array of scores
- `verification_date` - Verification timestamp

## 🤝 Contributing

To contribute improvements:
1. Test thoroughly
2. Follow existing code style
3. Document changes
4. Submit pull request

## 📝 License

Proprietary - All rights reserved

## 👥 Support

For issues and questions:
- Check troubleshooting section
- Review logs in `logs/` directory
- Verify configuration in `.env`

## 🎓 Technical Stack

- **Backend**: Flask 3.0
- **Database**: MySQL 5.7+
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **AI/ML**: TensorFlow 2.14, Keras 3.0
- **Image Processing**: OpenCV 4.8
- **ORM**: SQLAlchemy 2.0
- **Task Queue**: Optional (Celery for async tasks)

---

**Created**: 2024
**Version**: 1.0.0
**Status**: Production Ready
