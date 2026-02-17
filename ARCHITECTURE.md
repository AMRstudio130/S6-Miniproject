# DR AI Vision - Architecture & System Design

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser / Client                    │
│                      (Frontend UI / API)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      Django Web Framework          │
        │                                    │
        │  ┌──────────────────────────────┐  │
        │  │    URL Routing               │  │
        │  │  (ai_project/urls.py)        │  │
        │  └──────────────────────────────┘  │
        │           │                        │
        ├───────────┼───────────────────────┤
        │           ▼                       │
        │  ┌──────────────────────────────┐  │
        │  │    Views (API Endpoints)     │  │
        │  │  (dr_app/views.py)           │  │
        │  │  - /api/predict/             │  │
        │  │  - /api/result/<id>/         │  │
        │  │  - /api/history/             │  │
        │  │  - /api/register-patient/    │  │
        │  └──────────────────────────────┘  │
        │           │                        │
        │           ▼                        │
        │  ┌──────────────────────────────┐  │
        │  │  ML/AI Module                │  │
        │  │  (dr_app/ml_utils.py)        │  │
        │  │  - DRClassifier              │  │
        │  │  - GradCAM                   │  │
        │  └──────────────────────────────┘  │
        │           │                        │
        │           ▼                        │
        │  ┌──────────────────────────────┐  │
        │  │  Database Models             │  │
        │  │  (dr_app/models.py)          │  │
        │  │  - PredictionResult          │  │
        │  │  - PatientRecord             │  │
        │  └──────────────────────────────┘  │
        └────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │      Data Storage Layer            │
        │                                    │
        │  ┌──────────────────────────────┐  │
        │  │  SQLite Database             │  │
        │  │  (db.sqlite3)                │  │
        │  │  - Predictions               │  │
        │  │  - Patients                  │  │
        │  └──────────────────────────────┘  │
        │                                    │
        │  ┌──────────────────────────────┐  │
        │  │  File Storage                │  │
        │  │  (media/)                    │  │
        │  │  - Fundus images             │  │
        │  │  - Heatmaps                  │  │
        │  └──────────────────────────────┘  │
        └────────────────────────────────────┘
```

---

## Component Architecture

### 1. **Presentation Layer** (Frontend)
- **Location**: `/templates/` and `/static/`
- **Files**: `home.html`, `style.css`, `script.js`
- **Responsibilities**:
  - Display web interface
  - Handle file uploads
  - Display predictions
  - Show Grad-CAM heatmaps

### 2. **API Layer** (Views)
- **Location**: `dr_app/views.py`
- **Endpoints**:
  ```python
  home()                    # Web dashboard
  api_predict()             # Prediction endpoint
  api_result()              # Get specific result
  api_history()             # Get prediction history
  api_register_patient()    # Patient registration
  ```

### 3. **Business Logic Layer** (ML Utils)
- **Location**: `dr_app/ml_utils.py`
- **Classes**:
  ```python
  DRClassifier              # ResNet50 model
  GradCAM                   # Grad-CAM visualization
  ```

### 4. **Data Layer** (Models & Database)
- **Location**: `dr_app/models.py`
- **Models**:
  ```python
  PredictionResult          # Prediction records
  PatientRecord             # Patient information
  ```

### 5. **Configuration Layer**
- **Location**: `ai_project/settings.py`
- **Handles**:
  - Database configuration
  - Media files
  - Static files
  - Logging
  - Security settings

---

## Data Flow Diagram

### Prediction Flow
```
User Upload Image
       │
       ▼
Validate Image Format & Size
       │
       ▼
Save Temporary Image File
       │
       ▼
┌──────────────────────────────┐
│  ML Processing Pipeline      │
│                              │
│ 1. Load Image (CV2)          │
│ 2. Resize (224×224)          │
│ 3. Normalize                 │
│ 4. Preprocess (ResNet50)     │
└──────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  ResNet50 Model              │
│  - Forward Pass              │
│  - Get Predictions           │
│  - Get Confidence            │
└──────────────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Grad-CAM Generation         │
│  - Extract Conv Layer Output │
│  - Compute Gradients         │
│  - Generate Heatmap          │
│  - Overlay on Original Image │
└──────────────────────────────┘
       │
       ▼
Save Results to Database
       │
       ├─ Save Image
       ├─ Save Heatmap
       ├─ Save Prediction
       └─ Save Confidence
       │
       ▼
Return JSON Response
       │
       ▼
Display to User
```

---

## Database Schema

### PredictionResult Table
```sql
CREATE TABLE dr_app_predictionresult (
    id INTEGER PRIMARY KEY,
    image VARCHAR(100),
    prediction INTEGER,
    confidence FLOAT,
    heatmap VARCHAR(100),
    created_at DATETIME
);

Indexes:
- prediction (for filtering by stage)
- created_at (for sorting)
```

### PatientRecord Table
```sql
CREATE TABLE dr_app_patientrecord (
    id INTEGER PRIMARY KEY,
    patient_id VARCHAR(50) UNIQUE,
    name VARCHAR(100),
    age INTEGER,
    email VARCHAR(254),
    created_at DATETIME,
    updated_at DATETIME
);

Indexes:
- patient_id (unique, for lookups)
- created_at (for sorting)
```

### PatientRecord_predictions Through Table
```sql
CREATE TABLE dr_app_patientrecord_predictions (
    id INTEGER PRIMARY KEY,
    patientrecord_id INTEGER,
    predictionresult_id INTEGER,
    FOREIGN KEY (patientrecord_id) REFERENCES dr_app_patientrecord(id),
    FOREIGN KEY (predictionresult_id) REFERENCES dr_app_predictionresult(id)
);
```

---

## ML Model Architecture

### ResNet50 Customization
```
Pre-trained ResNet50 (ImageNet)
         │
         ├─ Remove Classification Head
         │
         ▼
    Conv5_block3_out (2048 features)
         │
         ├─ GlobalAveragePooling2D
         │  Output: (2048,)
         │
         ├─ Dense(256, relu)
         │  Output: (256,)
         │
         ├─ Dense(128, relu)
         │  Output: (128,)
         │
         ├─ Dense(5, softmax)
         │  Output: (5,) - DR Stages
         │
         ▼
    Final Prediction
```

### Grad-CAM Implementation
```
Input Image (224×224×3)
     │
     ▼
ResNet50 Forward Pass
     │
     ├─ Extract Conv5_block3_out features
     │
     ├─ Compute class score gradients
     │
     ├─ Calculate channel importance weights
     │
     ├─ Generate weighted average
     │
     ├─ Normalize (0 to 1)
     │
     ├─ Upsample to image size (224×224)
     │
     ├─ Apply colormap (JET)
     │
     ├─ Blend with original (α=0.6)
     │
     ▼
Final Heatmap (Visualization)
```

---

## Request-Response Flow

### Prediction Endpoint (POST /api/predict/)

#### Request
```
┌─────────────────────────────┐
│   multipart/form-data       │
├─────────────────────────────┤
│ image: <binary file>        │
│ patient_id: PAT001 (opt)    │
└─────────────────────────────┘
```

#### Processing
```python
1. Extract image and patient_id
2. Validate image format (JPEG, PNG)
3. Save to temporary storage
4. Load classifier model
5. Preprocess image
6. Generate prediction
7. Compute confidence
8. Generate Grad-CAM heatmap
9. Save heatmap file
10. Store in database
11. Link to patient (if provided)
12. Clean temp files
13. Return results
```

#### Response
```json
{
  "status": "success",
  "prediction_id": 42,
  "stage": 2,
  "stage_name": "Moderate",
  "confidence": 94.75,
  "heatmap_url": "/media/heatmaps/heatmap_...",
  "probabilities": {
    "No Diabetic Retinopathy": 2.15,
    "Mild": 0.98,
    "Moderate": 94.75,
    "Severe": 1.87,
    "Proliferative DR": 0.25
  }
}
```

---

## File Organization

### Static Files
```
static/
├── css/
│   └── style.css        (Dashboard styling)
├── js/
│   └── script.js        (Frontend interactions)
└── img/                 (Icons, logos)
```

### Media Files (User Uploads)
```
media/
├── retinal_scans/       (Original fundus images)
│   ├── image_001.jpg
│   ├── image_002.png
│   └── ...
├── heatmaps/            (Grad-CAM visualizations)
│   ├── heatmap_001.png
│   ├── heatmap_002.png
│   └── ...
└── temp/                (Temporary processing)
    ├── temp_*.jpg
    └── temp_*.png
```

### Logs
```
logs/
└── django.log           (Application logs)
    ├── INFO messages
    ├── WARNING messages
    └── ERROR messages
```

---

## Error Handling Flow

```
User Request
     │
     ▼
Input Validation
     │
     ├─ Valid      ✓ Process
     │
     └─ Invalid    ✗ Return 400 Error
                      {
                        "status": "error",
                        "message": "Invalid..."
                      }
     │
     ▼
Business Logic
     │
     ├─ Success    ✓ Generate Response
     │
     └─ Failure    ✗ Return 500 Error
                      Log exception
                      {
                        "status": "error",
                        "message": "Server error"
                      }
     │
     ▼
JSON Response to Client
```

---

## Security Architecture

### Input Validation
```
User Input
    │
    ├─ File Format Check (extensions)
    │
    ├─ File Size Check (< 5MB)
    │
    ├─ Image Format Validation (PIL)
    │
    ├─ Patient ID Validation (exists in DB)
    │
    └─ Sanitization
```

### Data Protection
```
Database
    ├─ SQLite (dev only)
    ├─ Prepared statements (SQL injection prevention)
    └─ Model-level validation

File Storage
    ├─ Unique filenames (UUID-based)
    ├─ Temporary file cleanup
    └─ Access control (MEDIA_URL routing)

API
    ├─ CSRF protection (Django middleware)
    ├─ Error message sanitization
    └─ Logging of all errors
```

---

## Scalability Considerations

### Current (Development)
```
Single Django Server
    ├─ SQLite Database
    ├─ Local File Storage
    ├─ Single ML Model Instance
    └─ Development Server
```

### Production (Recommended)
```
Load Balancer
    │
    ├─ Django Server 1
    ├─ Django Server 2
    ├─ Django Server N
    │
    ├─ PostgreSQL Database (with replication)
    │
    ├─ AWS S3 (media storage)
    │
    ├─ Redis (caching & sessions)
    │
    └─ Celery (async tasks)
         ├─ ML predictions
         ├─ Heatmap generation
         └─ Email notifications
```

---

## Performance Optimization

### Caching Strategy
```python
# Cache model instance
get_classifier()  # Singleton pattern
    Returns cached ResNet50 model
    Avoids reloading on each request

# Database query optimization
    Use select_related() for foreign keys
    Use prefetch_related() for many-to-many
    Index frequently queried fields

# Image compression
    Store JPEGs at 85% quality
    Use progressive JPEG for web
    Cache heatmaps after generation
```

### Batch Processing
```
Future Enhancement:
    Accept multiple image uploads
    Queue for background processing (Celery)
    Return results via webhook or email
    Better resource utilization
```

---

## Deployment Architecture

### Development
```
Django Development Server (runserver)
    ├─ Single Process
    ├─ Auto-reload on changes
    ├─ SQLite Database
    └─ Local media storage
```

### Production
```
Internet
    │
    ▼
Nginx (Reverse Proxy)
    │
    ├─ Load balancing
    ├─ Static file serving
    ├─ SSL/TLS termination
    │
    ▼
Gunicorn (4-8 workers)
    │
    ├─ Django application
    ├─ Connection pooling
    │
    ▼
PostgreSQL Database
    ├─ Connection pooling
    ├─ Automatic backups
    └─ Replication setup

Shared Storage (AWS S3)
    ├─ Media files
    └─ Backups

Monitoring
    ├─ Application logs
    ├─ Database performance
    ├─ Server metrics
    └─ Error tracking
```

---

## Authentication Flow (Recommended Future)

```
User Login Request
    │
    ▼
Validate Credentials
    │
    ├─ Valid       Generate JWT Token
    └─ Invalid     Return 401 Unauthorized
    │
    ▼
Return Access & Refresh Tokens
    │
    ·
    ▼
API Request + Access Token
    │
    ▼
Verify Token (Middleware)
    │
    ├─ Valid       Proceed to endpoint
    └─ Invalid     Return 401 Unauthorized
    │
    ▼
Execute Endpoint Logic
```

---

## Testing Strategy

### Unit Tests
```python
test_models.py
    ├─ PredictionResult model
    ├─ PatientRecord model
    └─ Validation

test_views.py
    ├─ api_predict endpoint
    ├─ api_result endpoint
    ├─ api_history endpoint
    └─ Error handling

test_ml_utils.py
    ├─ DRClassifier model
    ├─ Image preprocessing
    ├─ GradCAM generation
    └─ Error cases
```

### Integration Tests
```python
test_integration.py
    ├─ Complete prediction flow
    ├─ Patient registration flow
    ├─ Database persistence
    └─ File handling
```

### Load Testing
```
tools: Apache JMeter, Locust
    ├─ API endpoints at 100+ req/sec
    ├─ Concurrent user simulation
    ├─ Response time analysis
    └─ Resource utilization
```

---

## Monitoring & Logging

### Application Logging
```
logs/django.log
    ├─ INFO
    │   ├─ Successful predictions
    │   ├─ Patient registration
    │   └─ API requests
    │
    ├─ WARNING
    │   ├─ Invalid input
    │   └─ Slow predictions
    │
    └─ ERROR
        ├─ Model inference failures
        ├─ Database errors
        └─ File handling issues
```

### Metrics to Track
```
- Prediction accuracy (vs. ground truth)
- Average inference time
- API response times
- Database query performance
- Error rates
- Storage usage
- API quota usage
```

---

## Conclusion

The DR AI Vision system is architected as a **layered, modular application** suitable for:
- Development and testing
- Academic research
- Clinical deployment (with proper modifications)
- Scaling to production

Each component is independent, well-documented, and follows Django best practices.

---

**Version**: 1.0.0  
**Last Updated**: February 14, 2026
