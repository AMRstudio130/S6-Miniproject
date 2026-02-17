# DR AI Vision - Quick Start Guide

## 5-Minute Setup

### Step 1: Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

Note: First installation may take 5-10 minutes due to TensorFlow

### Step 3: Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Create Admin User
```bash
python manage.py createsuperuser
```
Follow prompts to create username, email, and password

### Step 5: Create Logs Directory
```bash
mkdir logs
```

### Step 6: Run Server
```bash
python manage.py runserver
```

### Step 7: Access Application
- Dashboard: [http://localhost:8000](http://localhost:8000)
- Admin Panel: [http://localhost:8000/admin](http://localhost:8000/admin)

---

## Testing the Backend

### 1. Test via Dashboard (Web Interface)
1. Go to [http://localhost:8000](http://localhost:8000)
2. Click "Upload Retinal Fundus Image"
3. Select a test fundus image
4. Click "Analyze with AI"
5. View prediction and Grad-CAM heatmap

### 2. Test via API (Command Line)

#### Register a Patient
```bash
curl -X POST http://localhost:8000/api/register-patient/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "TEST001",
    "name": "Test Patient",
    "age": 45,
    "email": "test@example.com"
  }'
```

#### Make a Prediction
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -F "image=@path/to/fundus_image.jpg" \
  -F "patient_id=TEST001"
```

#### Get Prediction Result
```bash
curl http://localhost:8000/api/result/1/
```

#### Get Patient History
```bash
curl http://localhost:8000/api/history/TEST001/
```

### 3. Test via Django Admin
1. Go to [http://localhost:8000/admin](http://localhost:8000/admin)
2. Login with superuser credentials
3. Browse "Prediction Results" and "Patient Records"

---

## Project Structure Overview

```
ai_project/
├── manage.py                 # Django management commands
├── requirements.txt          # Python dependencies
├── db.sqlite3               # SQLite database
│
├── ai_project/              # Main project configuration
│   ├── settings.py          # Django settings (IMPORTANT)
│   ├── urls.py              # URL routing
│   ├── wsgi.py              # Production WSGI
│   └── asgi.py              # WebSocket support
│
├── dr_app/                  # Main application
│   ├── models.py            # Database models ✓
│   ├── views.py             # API endpoints ✓
│   ├── urls.py              # App URL routing ✓
│   ├── admin.py             # Django admin ✓
│   ├── ml_utils.py          # ML model & Grad-CAM ✓
│   └── migrations/          # Database migrations
│
├── templates/               # HTML templates
│   └── home.html            # Main dashboard
│
├── static/                  # Static files
│   ├── css/style.css
│   └── js/script.js
│
├── media/                   # User uploads (created at runtime)
│   ├── retinal_scans/
│   ├── heatmaps/
│   └── temp/
│
├── logs/                    # Application logs (created at runtime)
│   └── django.log
│
└── Documentation Files
    ├── README.md
    ├── BACKEND_SETUP.md     # Complete setup guide
    ├── API_DOCUMENTATION.md # API reference
    └── .env.example         # Environment template
```

---

## Key Files & Their Purpose

### Backend Core
- **[dr_app/models.py](dr_app/models.py)** - Database schemas for predictions & patients
- **[dr_app/views.py](dr_app/views.py)** - API endpoints and web views
- **[dr_app/ml_utils.py](dr_app/ml_utils.py)** - ResNet50 model & Grad-CAM implementation
- **[dr_app/admin.py](dr_app/admin.py)** - Django admin interface

### Configuration
- **[ai_project/settings.py](ai_project/settings.py)** - Django settings, media config, logging
- **[ai_project/urls.py](ai_project/urls.py)** - Main URL routing
- **[dr_app/urls.py](dr_app/urls.py)** - App-level URL routing

### Frontend
- **[templates/home.html](templates/home.html)** - Main dashboard UI
- **[static/css/style.css](static/css/style.css)** - Dashboard styling
- **[static/js/script.js](static/js/script.js)** - Frontend interactions

---

## Common Commands

### Django Management
```bash
# Create database tables
python manage.py migrate

# Make new database migration
python manage.py makemigrations

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run shell with Django context
python manage.py shell

# Create static files
python manage.py collectstatic

# Clear database
python manage.py flush
```

### Useful Python/Pip Commands
```bash
# List installed packages
pip list

# Check TensorFlow installation
python -c "import tensorflow as tf; print(tf.__version__)"

# Check CUDA/GPU support
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# Freeze dependencies
pip freeze > requirements.txt

# Clean pip cache
pip cache purge
```

---

## Available API Endpoints

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/` | Dashboard |
| POST | `/api/predict/` | Predict DR from image |
| GET | `/api/result/<id>/` | Get prediction details |
| GET | `/api/history/` | All predictions |
| GET | `/api/history/<patient_id>/` | Patient predictions |
| POST | `/api/register-patient/` | Register patient |
| GET | `/admin/` | Django admin |

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'tensorflow'"
**Solution**:
```bash
pip install tensorflow==2.14.0
```

### Issue: Port 8000 already in use
**Solution**:
```bash
python manage.py runserver 8001
```

### Issue: "No such table: dr_app_predictionresult"
**Solution**:
```bash
python manage.py migrate
```

### Issue: Images not displaying
**Solution**: Ensure `DEBUG = True` in settings.py or configure static/media server

### Issue: Grad-CAM not generating
**Solution**: Check TensorFlow version compatibility and GPU memory

---

## Next Steps

1. **Test the API** (see "Testing the Backend" section)
2. **Review Documentation**:
   - [BACKEND_SETUP.md](BACKEND_SETUP.md) - Comprehensive setup
   - [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Detailed API reference
3. **Train the Model** (Optional):
   - Use actual DR dataset (e.g., EyePACS, Messidor)
   - Fine-tune ResNet50 on your data
4. **Deploy** (When ready):
   - Configure PostgreSQL
   - Set up AWS S3 for media
   - Use Gunicorn/Nginx
   - Enable HTTPS

---

## Development Workflow

### Make a Prediction
```python
# In Python shell: python manage.py shell
from dr_app.ml_utils import get_classifier

classifier = get_classifier()
result = classifier.predict('path/to/image.jpg')
print(result)
```

### Add Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

### Query Database
```python
# In Python shell
from dr_app.models import PredictionResult, PatientRecord

# Get all predictions
predictions = PredictionResult.objects.all()

# Get by stage
moderates = PredictionResult.objects.filter(prediction=2)

# Count total
total = PredictionResult.objects.count()

# Get patient's predictions
patient = PatientRecord.objects.get(patient_id='PAT001')
predictions = patient.predictions.all()
```

---

## Performance Tips

1. **Image Size**: Pre-process images to 224x224 before upload
2. **Batch Processing**: Use batch predictions for multiple images
3. **Caching**: Cache model predictions when possible
4. **Database**: Use PostgreSQL for production instead of SQLite
5. **Static Files**: Serve CSS/JS from CDN in production

---

## Security Checklist

- [ ] Change Django SECRET_KEY in production
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS/SSL
- [ ] Set secure cookie flags
- [ ] Implement CORS properly
- [ ] Use environment variables for secrets
- [ ] Validate all user inputs
- [ ] Implement rate limiting
- [ ] Keep dependencies updated

---

## Support & Resources

- Django Documentation: https://docs.djangoproject.com/
- TensorFlow Documentation: https://www.tensorflow.org/api_docs
- ResNet50 Paper: https://arxiv.org/abs/1512.03385
- Grad-CAM Paper: https://arxiv.org/abs/1610.02055

---

## Quick Reference

| Task | Command |
|------|---------|
| Start Server | `python manage.py runserver` |
| Make Migrations | `python manage.py makemigrations` |
| Apply Migrations | `python manage.py migrate` |
| Access Admin | [http://localhost:8000/admin](http://localhost:8000/admin) |
| Upload Image | [http://localhost:8000](http://localhost:8000) |
| Predict via API | `POST /api/predict/` with image |
| Get History | `GET /api/history/<patient_id>/` |

---

**Version**: 1.0.0  
**Last Updated**: February 14, 2026

🎉 You're all set! Happy coding!
