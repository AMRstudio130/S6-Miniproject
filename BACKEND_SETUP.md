# Diabetic Retinopathy AI - Backend Setup Guide

## Project Overview
This is an Explainable AI-Based Django Web Application for Diabetic Retinopathy (DR) Classification using ResNet50 CNN with Grad-CAM visualization.

## Backend Components

### 1. **Models** (`dr_app/models.py`)
- `PredictionResult`: Stores DR detection results with heatmaps
- `PatientRecord`: Manages patient information and their predictions

### 2. **ML Utils** (`dr_app/ml_utils.py`)
- `DRClassifier`: ResNet50-based DR classification model
- `GradCAM`: Explainable AI visualization using Grad-CAM technique
- Helper functions for image preprocessing

### 3. **Views** (`dr_app/views.py`)
- Web views for dashboard
- RESTful API endpoints for predictions, history, and patient management

### 4. **Settings** (`ai_project/settings.py`)
- Media file configuration
- Logging setup
- ML model configuration

## Installation & Setup

### Prerequisites
```bash
Python 3.8+
pip package manager
```

### 1. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create Logs Directory
```bash
mkdir logs
```

### 4. Make Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (for Admin)
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

Access the application:
- Dashboard: [http://localhost:8000/](http://localhost:8000/)
- Admin Panel: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## API Endpoints

### 1. **Predict DR Stage**
- **Endpoint**: `POST /api/predict/`
- **Description**: Upload a fundus image and get DR prediction with Grad-CAM
- **Request**:
  ```
  Form-data:
  - image: <image_file>
  - patient_id: (optional) <patient_identifier>
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "prediction_id": 1,
    "stage": 2,
    "stage_name": "Moderate",
    "confidence": 95.5,
    "heatmap_url": "/media/heatmaps/heatmap_image.png",
    "probabilities": {
      "No Diabetic Retinopathy": 0.5,
      "Mild": 15.2,
      "Moderate": 95.5,
      "Severe": 2.1,
      "Proliferative DR": 0.1
    }
  }
  ```

### 2. **Get Prediction Result**
- **Endpoint**: `GET /api/result/<prediction_id>/`
- **Description**: Retrieve details of a specific prediction
- **Response**:
  ```json
  {
    "status": "success",
    "prediction_id": 1,
    "stage": 2,
    "stage_name": "Moderate",
    "confidence": 95.5,
    "image_url": "/media/retinal_scans/image.jpg",
    "heatmap_url": "/media/heatmaps/heatmap_image.png",
    "created_at": "2024-02-14T10:30:00Z"
  }
  ```

### 3. **Get Prediction History**
- **Endpoint**: `GET /api/history/`
- **Description**: Get all predictions (last 50)
- **Response**:
  ```json
  {
    "status": "success",
    "count": 10,
    "predictions": [
      {
        "id": 1,
        "stage": 2,
        "stage_name": "Moderate",
        "confidence": 95.5,
        "created_at": "2024-02-14T10:30:00Z"
      }
    ]
  }
  ```

### 4. **Get Patient History**
- **Endpoint**: `GET /api/history/<patient_id>/`
- **Description**: Get all predictions for a specific patient
- **Response**: Same as above

### 5. **Register Patient**
- **Endpoint**: `POST /api/register-patient/`
- **Description**: Register a new patient
- **Request**:
  ```json
  {
    "patient_id": "PAT001",
    "name": "John Doe",
    "age": 45,
    "email": "john@example.com"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Patient registered",
    "patient_id": "PAT001",
    "created": true
  }
  ```

---

## DR Classification Stages

| Stage | Name | Description |
|-------|------|-------------|
| 0 | No Diabetic Retinopathy | No signs of DR detected |
| 1 | Mild | Microaneurysms detected |
| 2 | Moderate | Retinal hemorrhages, hard exudates |
| 3 | Severe | Widespread retinal damage |
| 4 | Proliferative DR | Abnormal blood vessel growth |

---

## Key Features

### 1. **Explainable AI (Grad-CAM)**
- Visualizes which regions of the retina influenced the prediction
- Builds trust in AI system for clinical use
- Highlights areas of concern

### 2. **Automated Image Preprocessing**
- Automatic resizing to 224x224
- Normalization using ResNet50 preprocessing
- Handles various image formats (JPG, PNG)

### 3. **Patient Management**
- Store patient information
- Track multiple predictions per patient
- Historical analysis

### 4. **Robust Error Handling**
- Input validation
- Comprehensive logging
- Graceful error responses

---

## Directory Structure

```
ai_project/
├── manage.py
├── db.sqlite3
├── requirements.txt
├── logs/                    # Application logs
│   └── django.log
├── media/                   # User uploads
│   ├── retinal_scans/      # Original fundus images
│   ├── heatmaps/           # Grad-CAM visualizations
│   └── temp/               # Temporary files
├── ai_project/             # Main project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── dr_app/                 # Main application
│   ├── models.py           # Database models
│   ├── views.py            # Views & API endpoints
│   ├── urls.py             # URL routing
│   ├── admin.py            # Django admin config
│   ├── apps.py
│   ├── ml_utils.py         # ML & Grad-CAM code
│   ├── migrations/
│   └── __pycache__/
├── templates/              # HTML templates
│   └── home.html           # Dashboard
└── static/                 # Static files
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

---

## Database Models

### PredictionResult
```python
- id (AutoField)
- image (ImageField) - Original fundus image
- prediction (IntegerField) - DR stage (0-4)
- confidence (FloatField) - Prediction confidence (0-100)
- heatmap (ImageField) - Grad-CAM visualization
- created_at (DateTimeField) - Prediction timestamp
```

### PatientRecord
```python
- id (AutoField)
- patient_id (CharField) - Unique identifier
- name (CharField)
- age (IntegerField)
- email (EmailField)
- predictions (ManyToManyField) - Related predictions
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

---

## Configuration

### Media Files
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### ML Model
```python
ML_CONFIG = {
    'img_size': (224, 224),
    'batch_size': 32,
    'model_name': 'ResNet50',
}
```

### Logging
- Logs are saved to `logs/django.log`
- Console output for development
- File output for production

---

## Deployment Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Update `ALLOWED_HOSTS` with domain
- [ ] Use environment variables for secrets
- [ ] Configure proper database (PostgreSQL)
- [ ] Set up proper media file serving (AWS S3, etc.)
- [ ] Use Gunicorn as WSGI server
- [ ] Set up CORS if frontend is separate
- [ ] Configure SSL/HTTPS
- [ ] Set up monitoring and alerts

---

## Common Issues & Solutions

### Issue: Model Loading Failed
**Solution**: Ensure TensorFlow/Keras is properly installed
```bash
pip install tensorflow==2.14.0 keras==2.14.0
```

### Issue: CUDA/GPU not detected
**Solution**: Install TensorFlow CPU version or configure GPU drivers

### Issue: Media files not serving
**Solution**: Ensure `DEBUG = True` or configure web server

### Issue: Database migration errors
**Solution**: 
```bash
python manage.py migrate --fake dr_app zero
python manage.py migrate
```

---

## Backend Development Roadmap

✅ **Completed**
- Database models for predictions and patients
- ResNet50 ML model integration
- Grad-CAM explainability
- API endpoints for prediction and management
- Django admin interface
- Image preprocessing and validation

🔄 **Next Steps**
- Model training with actual DR dataset
- Batch prediction for bulk uploads
- Advanced analytics dashboard
- PDF report generation
- Integration with healthcare systems (HL7)
- Performance optimization
- Unit & integration tests

---

## Contact & Support
For issues or questions, please contact the development team.

---

**Last Updated**: February 14, 2026
**Version**: 1.0.0
