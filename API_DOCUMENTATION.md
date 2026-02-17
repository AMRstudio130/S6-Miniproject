# DR AI Vision - Complete API Documentation

## Base URL
```
http://localhost:8000/
```

## Authentication
Currently, no authentication is required for API endpoints. Implement token-based authentication (JWT) for production.

---

## Endpoints Overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/predict/` | Upload image and get DR prediction |
| GET | `/api/result/<id>/` | Get prediction details |
| GET | `/api/history/` | Get all predictions |
| GET | `/api/history/<patient_id>/` | Get patient's predictions |
| POST | `/api/register-patient/` | Register new patient |

---

## Detailed Endpoint Documentation

### 1. Upload and Predict DR Stage

#### **POST** `/api/predict/`

**Description**: Upload a retinal fundus image and receive DR stage prediction with Grad-CAM heatmap

**Authentication**: None (implement JWT in production)

**Request Format**:
- Content-Type: `multipart/form-data`

**Parameters**:
```
image: File (required)
  - Formats: JPEG, PNG, JPG
  - Max Size: Recommended < 5MB
  - Resolution: High-resolution recommended (2000x2000+)

patient_id: String (optional)
  - Format: Any unique identifier
  - Used to link prediction to patient record
```

**Example Request** (using curl):
```bash
curl -X POST http://localhost:8000/api/predict/ \
  -F "image=@fundus_image.jpg" \
  -F "patient_id=PAT001"
```

**Success Response** (200):
```json
{
  "status": "success",
  "prediction_id": 42,
  "stage": 2,
  "stage_name": "Moderate",
  "confidence": 94.75,
  "heatmap_url": "/media/heatmaps/heatmap_fundus_image.png",
  "probabilities": {
    "No Diabetic Retinopathy": 2.15,
    "Mild": 0.98,
    "Moderate": 94.75,
    "Severe": 1.87,
    "Proliferative DR": 0.25
  }
}
```

**Error Response** (400):
```json
{
  "status": "error",
  "message": "Invalid image format. Please use JPG or PNG"
}
```

**Error Response** (500):
```json
{
  "status": "error",
  "message": "Model inference failed: [error details]"
}
```

---

### 2. Get Prediction Result Details

#### **GET** `/api/result/<prediction_id>/`

**Description**: Retrieve complete details of a specific prediction result

**Authentication**: None

**Parameters** (URL):
```
prediction_id: Integer (required)
  - The ID returned from prediction endpoint
```

**Example Request**:
```bash
curl http://localhost:8000/api/result/42/
```

**Success Response** (200):
```json
{
  "status": "success",
  "prediction_id": 42,
  "stage": 2,
  "stage_name": "Moderate",
  "confidence": 94.75,
  "image_url": "/media/retinal_scans/fundus_image.jpg",
  "heatmap_url": "/media/heatmaps/heatmap_fundus_image.png",
  "created_at": "2024-02-14T14:30:45.123456Z"
}
```

**Error Response** (404):
```json
{
  "status": "error",
  "message": "Prediction not found"
}
```

---

### 3. Get All Predictions

#### **GET** `/api/history/`

**Description**: Retrieve all predictions (latest 50)

**Authentication**: None

**Parameters**: None

**Example Request**:
```bash
curl http://localhost:8000/api/history/
```

**Success Response** (200):
```json
{
  "status": "success",
  "count": 10,
  "predictions": [
    {
      "id": 42,
      "stage": 2,
      "stage_name": "Moderate",
      "confidence": 94.75,
      "created_at": "2024-02-14T14:30:45.123456Z"
    },
    {
      "id": 41,
      "stage": 0,
      "stage_name": "No Diabetic Retinopathy",
      "confidence": 98.45,
      "created_at": "2024-02-14T13:15:20.456789Z"
    }
  ]
}
```

---

### 4. Get Patient's Prediction History

#### **GET** `/api/history/<patient_id>/`

**Description**: Retrieve all predictions for a specific patient

**Authentication**: None

**Parameters** (URL):
```
patient_id: String (required)
  - Patient identifier
```

**Example Request**:
```bash
curl http://localhost:8000/api/history/PAT001/
```

**Success Response** (200):
```json
{
  "status": "success",
  "count": 5,
  "predictions": [
    {
      "id": 42,
      "stage": 2,
      "stage_name": "Moderate",
      "confidence": 94.75,
      "created_at": "2024-02-14T14:30:45.123456Z"
    },
    {
      "id": 41,
      "stage": 2,
      "stage_name": "Moderate",
      "confidence": 92.15,
      "created_at": "2024-02-10T10:20:30.789123Z"
    }
  ]
}
```

**Error Response** (404):
```json
{
  "status": "error",
  "message": "Patient not found"
}
```

---

### 5. Register New Patient

#### **POST** `/api/register-patient/`

**Description**: Register a new patient in the system

**Authentication**: None

**Request Format**:
- Content-Type: `application/json`

**Parameters** (JSON Body):
```json
{
  "patient_id": "PAT001",          // Required - unique identifier
  "name": "John Doe",              // Required
  "age": 45,                       // Required - integer
  "email": "john@example.com"      // Required - valid email
}
```

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/register-patient/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PAT001",
    "name": "John Doe",
    "age": 45,
    "email": "john@example.com"
  }'
```

**Success Response** (201 - New Patient):
```json
{
  "status": "success",
  "message": "Patient registered",
  "patient_id": "PAT001",
  "created": true
}
```

**Success Response** (200 - Existing Patient):
```json
{
  "status": "success",
  "message": "Patient already exists",
  "patient_id": "PAT001",
  "created": false
}
```

**Error Response** (400):
```json
{
  "status": "error",
  "message": "Missing required fields or invalid data"
}
```

---

## DR Classification Stages

| Code | Name | Clinical Description |
|------|------|----------------------|
| 0 | No Diabetic Retinopathy | No signs of DR detected in fundus image |
| 1 | Mild | Only microaneurysms present |
| 2 | Moderate | Retinal hemorrhages, hard exudates, microaneurysms in multiple quadrants |
| 3 | Severe | Extensive intraretinal microvascular abnormalities, multiple deep round hemorrhages |
| 4 | Proliferative DR | Abnormal new blood vessels on optic disc or retina |

---

## Frontend Integration Examples

### JavaScript/Fetch API

#### 1. Upload Image and Predict
```javascript
async function predictDR(imageFile, patientId = null) {
  const formData = new FormData();
  formData.append('image', imageFile);
  if (patientId) {
    formData.append('patient_id', patientId);
  }

  try {
    const response = await fetch('/api/predict/', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Prediction error:', error);
    return { status: 'error', message: error.message };
  }
}

// Usage
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const imageFile = document.getElementById('imageInput').files[0];
  const result = await predictDR(imageFile, 'PAT001');
  console.log(result);
});
```

#### 2. Get Prediction Result
```javascript
async function getPredictionResult(predictionId) {
  try {
    const response = await fetch(`/api/result/${predictionId}/`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching result:', error);
  }
}
```

#### 3. Get Prediction History
```javascript
async function getPatientHistory(patientId) {
  try {
    const response = await fetch(`/api/history/${patientId}/`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching history:', error);
  }
}
```

#### 4. Register Patient
```javascript
async function registerPatient(patientData) {
  try {
    const response = await fetch('/api/register-patient/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patientData)
    });

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error registering patient:', error);
  }
}

// Usage
registerPatient({
  patient_id: 'PAT001',
  name: 'John Doe',
  age: 45,
  email: 'john@example.com'
});
```

---

## Response Format Standards

### Success Response
```json
{
  "status": "success",
  "data": { /* endpoint-specific data */ }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Human-readable error message"
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource not found |
| 500 | Server Error - Internal error |

---

## Rate Limiting
Currently not implemented. Recommended for production:
- 100 requests per minute per IP
- 1000 predictions per day per patient

---

## CORS Configuration
For production with separate frontend:
```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ...
]

CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

---

## Security Recommendations

1. **Input Validation**
   - Image format validation ✓
   - File size limits recommended
   - Sanitize patient data

2. **Authentication** (Implement for production)
   - JWT token-based
   - Rate limiting per user
   - API key management

3. **Data Protection**
   - HTTPS/SSL for all endpoints
   - Database encryption
   - Secure patient data storage

4. **Error Handling**
   - Don't expose system errors to client
   - Log all errors server-side
   - Proper error codes and messages

---

## Testing the API

### Using Postman
1. Collection: DR AI Vision API
2. Endpoints:
   - POST: `{{base_url}}/api/predict/`
   - GET: `{{base_url}}/api/result/{{prediction_id}}/`
   - GET: `{{base_url}}/api/history/`
   - GET: `{{base_url}}/api/history/{{patient_id}}/`
   - POST: `{{base_url}}/api/register-patient/`

### CLI Testing
```bash
# Predict
curl -X POST http://localhost:8000/api/predict/ \
  -F "image=@test.jpg" \
  -F "patient_id=TEST001"

# Get result
curl http://localhost:8000/api/result/1/

# Get history
curl http://localhost:8000/api/history/

# Register patient
curl -X POST http://localhost:8000/api/register-patient/ \
  -H "Content-Type: application/json" \
  -d '{"patient_id":"TEST001","name":"Test","age":50,"email":"test@test.com"}'
```

---

## Troubleshooting

### 404 - Prediction not found
- Verify prediction ID is correct
- Check if prediction was successfully created

### 500 - Model inference error
- Check if image is properly formatted
- Verify TensorFlow/Keras installation
- Check server logs

### CORS errors
- Configure CORS middleware for frontend domain
- Check allowed origins in settings

---

**API Version**: 1.0.0  
**Last Updated**: February 14, 2026
