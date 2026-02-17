# DR AI Vision - Implementation & Developer Guide

## Code Walkthrough & Implementation Details

This guide explains how each component works and how to extend the system.

---

## 1. Database Models (`dr_app/models.py`)

### PredictionResult Model

```python
class PredictionResult(models.Model):
    """Stores individual DR prediction results"""
    
    # Choice tuples for DR stages
    DR_STAGES = [
        (0, 'No Diabetic Retinopathy'),
        (1, 'Mild'),
        (2, 'Moderate'),
        (3, 'Severe'),
        (4, 'Proliferative DR'),
    ]
    
    # Fields
    image = models.ImageField(
        upload_to='retinal_scans/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    
    prediction = models.IntegerField(
        choices=DR_STAGES,
        help_text="Diabetic Retinopathy Stage"
    )
    
    confidence = models.FloatField(
        help_text="Confidence score (0-100)",
        default=0.0
    )
    
    heatmap = models.ImageField(
        upload_to='heatmaps/',
        null=True,
        blank=True,
        help_text="Grad-CAM heatmap visualization"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
```

**Key Features**:
- `auto_now_add=True` - Automatically sets creation time
- `choices` - Restricts prediction to valid stages
- `FileExtensionValidator` - Ensures valid image formats
- `upload_to` - Separates images into different directories

**Usage Example**:
```python
# Create prediction
prediction = PredictionResult.objects.create(
    image='temp/image.jpg',
    prediction=2,
    confidence=94.75,
    heatmap='heatmaps/heatmap.png'
)

# Query predictions
moderates = PredictionResult.objects.filter(prediction=2)
recent = PredictionResult.objects.all().order_by('-created_at')[:10]

# Get prediction details
print(prediction.get_prediction_display())  # 'Moderate'
```

### PatientRecord Model

```python
class PatientRecord(models.Model):
    """Stores patient information and prediction history"""
    
    patient_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField()
    
    predictions = models.ManyToManyField(PredictionResult, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Features**:
- `unique=True` - Prevents duplicate patient IDs
- `ManyToManyField` - Links multiple predictions to one patient
- `auto_now=True` - Updates timestamp on every save

**Usage Example**:
```python
# Create patient
patient = PatientRecord.objects.create(
    patient_id='PAT001',
    name='John Doe',
    age=45,
    email='john@example.com'
)

# Add prediction to patient
patient.predictions.add(prediction_obj)

# Get patient's predictions
patient_preds = patient.predictions.all()

# Advanced queries
aging_patients = PatientRecord.objects.filter(age__gte=60)
recent_patients = PatientRecord.objects.all().order_by('-created_at')
patients_with_predictions = PatientRecord.objects.filter(
    predictions__isnull=False
).distinct()
```

---

## 2. ML Utils (`dr_app/ml_utils.py`)

### DRClassifier Class

#### Model Loading
```python
def __init__(self):
    self.model = None
    self.base_model = None
    self.img_size = (224, 224)
    self.load_model()

def load_model(self):
    """Loads ResNet50 and adds custom layers"""
    
    # Load base model (pre-trained on ImageNet)
    self.base_model = ResNet50(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    # Add classification layers
    x = self.base_model.output
    x = GlobalAveragePooling2D()(x)        # (2048,) → scalar pool
    x = Dense(256, activation='relu')(x)   # 256 features
    x = Dense(128, activation='relu')(x)   # 128 features
    predictions = Dense(5, activation='softmax', name='dr_predictions')(x)
    
    # Create final model
    self.model = Model(inputs=self.base_model.input, outputs=predictions)
```

**Architecture Explanation**:
- ResNet50 extracts image features (2048 filters)
- GlobalAveragePooling reduces spatial dimensions
- Dense(256) and Dense(128) provide non-linear combinations
- Dense(5, softmax) outputs class probabilities

#### Image Preprocessing
```python
def preprocess_image(self, image_path):
    """Prepares image for model input"""
    
    # Read image using OpenCV
    img = cv2.imread(str(image_path))
    
    # Convert BGR to RGB (OpenCV uses BGR by default)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize to model input size
    img = cv2.resize(img, self.img_size)
    
    # Normalize to float32
    img = img.astype('float32')
    
    # Apply ResNet50 preprocessing
    # Subtracts ImageNet mean values from each channel
    img = preprocess_input(img)
    
    # Add batch dimension (required for model)
    return np.expand_dims(img, axis=0), cv2.imread(str(image_path))
```

**Preprocessing Steps**:
1. Convert BGR→RGB (OpenCV format correction)
2. Resize to 224×224 (ResNet50 input size)
3. Normalize pixel values
4. Apply ResNet50-specific preprocessing
5. Add batch dimension [1, 224, 224, 3]

#### Prediction
```python
def predict(self, image_path):
    """Generates prediction with confidence"""
    
    # Preprocess image
    processed_img, original_img = self.preprocess_image(image_path)
    
    # Get model predictions
    predictions = self.model.predict(processed_img, verbose=0)
    # predictions shape: (1, 5) - batch size 1, 5 classes
    
    # Get predicted class (highest probability)
    pred_class = np.argmax(predictions[0])
    
    # Get confidence as percentage
    confidence = float(predictions[0][pred_class]) * 100
    
    return {
        'stage': int(pred_class),                    # 0-4
        'stage_name': DR_STAGES[pred_class],         # 'Moderate'
        'confidence': round(confidence, 2),          # 94.75
        'probabilities': {
            DR_STAGES[i]: float(predictions[0][i]) * 100
            for i in range(5)
        }
    }
```

**Return Format**:
```python
{
    'stage': 2,
    'stage_name': 'Moderate',
    'confidence': 94.75,
    'probabilities': {
        'No Diabetic Retinopathy': 2.15,
        'Mild': 0.98,
        'Moderate': 94.75,
        'Severe': 1.87,
        'Proliferative DR': 0.25
    }
}
```

### GradCAM Class

#### Initialization
```python
def __init__(self, model, layer_name='conv5_block3_out'):
    """
    Initializes Grad-CAM
    
    Parameters:
    - model: Keras model for visualization
    - layer_name: Conv layer to visualize (default: last conv layer)
    """
    self.model = model
    self.layer_name = layer_name
    self.build_grad_model()

def build_grad_model(self):
    """Creates model for gradient computation"""
    
    # Get the last convolutional layer
    last_conv_layer = self.model.get_layer(self.layer_name)
    
    # Build model that outputs:
    # 1. Last conv layer features
    # 2. Final predictions
    self.grad_model = Model(
        [self.model.inputs],
        [last_conv_layer.output, self.model.output]
    )
```

**Why This Works**:
- Last conv layer captures spatial information
- Final output shows class activations
- Gradient between them tells us spatial importance

#### Heatmap Generation
```python
def generate_heatmap(self, img_array, pred_index=None):
    """Computes Grad-CAM visualization"""
    
    # Enable gradient tracking
    with tf.GradientTape() as tape:
        # Forward pass
        conv_outputs, predictions = self.grad_model(img_array)
        
        # Get predicted class index
        if pred_index is None:
            pred_index = tf.argmax(predictions[0])
        
        # Get class probability
        class_channel = predictions[:, pred_index]
    
    # Compute gradients of class w.r.t. conv layer
    grads = tape.gradient(class_channel, conv_outputs)
    
    # Global average pooling of gradients
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    
    # Weight feature maps by gradients
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    
    # Normalize to 0-1 range
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    
    return heatmap.numpy()
```

**Mathematical Explanation**:
```
Grad-CAM Formula:
Lc = ReLU(Σ(αk * Ak))

Where:
- Lc is the class activation map
- αk = (1/N) * Σ(∂yc/∂Ak) are gradient weights
- Ak are feature maps from conv layer
- N is spatial dimensions (H×W)
- yc is score for class c
```

**Process**:
1. Compute gradients of class score w.r.t. feature maps
2. Average gradients over spatial dimensions (importance)
3. Weight each feature map by its importance
4. Sum weighted feature maps
5. Apply ReLU to get only positive contributions
6. Normalize to 0-1 range

#### Heatmap Visualization
```python
def save_heatmap(self, heatmap, original_image_path, output_path, alpha=0.6):
    """Saves Grad-CAM overlaid on original image"""
    
    # Read original image
    img = cv2.imread(str(original_image_path))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize heatmap to match image dimensions
    heatmap = cv2.resize(heatmap, (img_rgb.shape[1], img_rgb.shape[0]))
    
    # Scale to 0-255 (uint8)
    heatmap = np.uint8(255 * heatmap)
    
    # Apply JET colormap (red=hot, blue=cold)
    heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
    
    # Blend heatmap with original image
    # alpha=0.6 means 60% heatmap, 40% original
    overlay = cv2.addWeighted(img_rgb, 1-alpha, heatmap_rgb, alpha, 0)
    
    # Save result
    overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(output_path), overlay_bgr)
```

**Blending**:
```
Result = (1-α) * Original + α * Heatmap
       = (1-0.6) * Original + 0.6 * Heatmap
       = 0.4 * Original + 0.6 * Heatmap
```

---

## 3. Views & API Endpoints (`dr_app/views.py`)

### Home View (Web Interface)

```python
def home(request):
    """Renders dashboard and handles file uploads"""
    
    if request.method == 'POST':
        # Extract uploaded file
        if 'image' not in request.FILES:
            return render(request, "home.html", {'error': 'No image'})
        
        image_file = request.FILES['image']
        
        try:
            # Save temporarily
            temp_path = default_storage.save(
                f'temp/{image_file.name}',
                ContentFile(image_file.read())
            )
            full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
            
            # Predict
            classifier = get_classifier()
            result = classifier.predict(full_path)
            
            # Generate Grad-CAM
            processed_img, _ = classifier.preprocess_image(full_path)
            grad_cam = GradCAM(classifier.model)
            heatmap = grad_cam.generate_heatmap(processed_img, pred_index=result['stage'])
            
            # Save heatmap
            heatmap_path = os.path.join(settings.MEDIA_ROOT, 'heatmaps', ...)
            grad_cam.save_heatmap(heatmap, full_path, heatmap_path)
            
            # Store in database
            prediction_obj = PredictionResult.objects.create(
                image=temp_path,
                prediction=result['stage'],
                confidence=result['confidence'],
                heatmap='heatmaps/...'
            )
            
            # Cleanup temp file
            default_storage.delete(temp_path)
            
            # Render with results
            context = {
                'prediction': result['stage_name'],
                'confidence': result['confidence'],
                'heatmap_url': f'{settings.MEDIA_URL}...',
                'probabilities': result['probabilities'],
                'prediction_id': prediction_obj.id
            }
            return render(request, "home.html", context)
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return render(request, "home.html", {'error': str(e)})
    
    return render(request, "home.html")
```

**Flow**:
1. Check for POST with image
2. Save image temporarily
3. Run prediction
4. Generate Grad-CAM
5. Save results to database
6. Clean up temp files
7. Return rendered template with results

### API Endpoints

#### Predict Endpoint
```python
@csrf_exempt
@require_http_methods(["POST"])
def api_predict(request):
    """RESTful prediction endpoint"""
    
    # Parse multipart form data
    image_file = request.FILES.get('image')
    patient_id = request.POST.get('patient_id')
    
    # Validate
    if not image_file:
        return JsonResponse({'status': 'error', 'message': 'No image'}, status=400)
    
    try:
        # Save and process (same as home view)
        # ...
        
        # Link to patient
        if patient_id:
            patient = PatientRecord.objects.get(patient_id=patient_id)
            patient.predictions.add(prediction_obj)
        
        # Return JSON
        return JsonResponse({
            'status': 'success',
            'prediction_id': prediction_obj.id,
            'stage': result['stage'],
            'stage_name': result['stage_name'],
            'confidence': result['confidence'],
            'heatmap_url': f'{settings.MEDIA_URL}...',
            'probabilities': result['probabilities']
        }, status=200)
        
    except PatientRecord.DoesNotExist:
        logger.warning(f"Patient {patient_id} not found")
        return JsonResponse({'status': 'error'}, status=400)
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
```

**Key Features**:
- `@csrf_exempt` - Allows API calls without CSRF token
- `@require_http_methods` - Only accepts POST
- `request.FILES` - Access uploaded files
- `request.POST` - Access form data
- `JsonResponse` - Returns JSON instead of HTML

---

## 4. URL Routing

### App URLs (`dr_app/urls.py`)
```python
urlpatterns = [
    path('', views.home, name='home'),
    
    # API endpoints
    path('api/predict/', views.api_predict, name='api_predict'),
    path('api/result/<int:prediction_id>/', views.api_result, name='api_result'),
    path('api/history/', views.api_history, name='api_history_all'),
    path('api/history/<str:patient_id>/', views.api_history, name='api_history_patient'),
    path('api/register-patient/', views.api_register_patient, name='api_register_patient'),
]
```

**URL Patterns**:
- `<int:prediction_id>` - Integer URL parameter
- `<str:patient_id>` - String URL parameter
- `name='api_predict'` - URL name for reverse lookup

### Project URLs (`ai_project/urls.py`)
```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dr_app.urls')),  # Include app URLs
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 5. Settings Configuration (`ai_project/settings.py`)

### Media Files
```python
MEDIA_URL = '/media/'  # URL prefix for media
MEDIA_ROOT = BASE_DIR / 'media'  # File system path
```

**Usage**:
- `/media/retinal_scans/image.jpg` → accessed via MEDIA_URL
- Files saved to `media/retinal_scans/image.jpg`

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'dr_app': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

**Usage**:
```python
import logging
logger = logging.getLogger(__name__)  # Gets 'dr_app.views'

logger.info("Prediction successful")
logger.warning("Low confidence prediction")
logger.error("Model inference failed")
```

---

## 6. Extending the System

### Adding a New Feature

#### Example: Batch Prediction

**Step 1: Add View**
```python
@csrf_exempt
@require_http_methods(["POST"])
def api_batch_predict(request):
    """Predict for multiple images"""
    
    images = request.FILES.getlist('images')
    patient_id = request.POST.get('patient_id')
    
    results = []
    for image in images:
        # Process each image
        result = process_image(image, patient_id)
        results.append(result)
    
    return JsonResponse({
        'status': 'success',
        'count': len(results),
        'predictions': results
    })
```

**Step 2: Add URL**
```python
path('api/batch-predict/', views.api_batch_predict, name='api_batch_predict'),
```

**Step 3: Update Frontend**
```javascript
async function batchPredict(formData) {
    const response = await fetch('/api/batch-predict/', {
        method: 'POST',
        body: formData
    });
    return response.json();
}
```

### Adding Model Fine-tuning

**Step 1: Create Training Script**
```python
# dr_app/train.py
from tensorflow.keras.applications import ResNet50

def fine_tune_model(dataset_path):
    # Load pre-trained model
    model = ResNet50(weights='imagenet')
    
    # Freeze base layers
    for layer in model.layers[:-1]:
        layer.trainable = False
    
    # Add custom layers
    x = model.output
    x = Dense(256, activation='relu')(x)
    predictions = Dense(5, activation='softmax')(x)
    
    # Compile
    model.compile(
        optimizer=Adam(lr=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Train on your dataset
    # ...
    
    # Save weights
    model.save_weights('model_weights.h5')
```

**Step 2: Load Custom Weights**
```python
# In ml_utils.py
def load_model(self):
    # ... existing code ...
    
    # Load custom weights if available
    weights_path = settings.BASE_DIR / 'model_weights.h5'
    if weights_path.exists():
        self.model.load_weights(str(weights_path))
```

### Adding Database Statistics

**Step 1: Create Model Method**
```python
# In models.py
class PredictionResult(models.Model):
    @staticmethod
    def get_stage_statistics():
        """Returns count of predictions by stage"""
        from django.db.models import Count
        
        return PredictionResult.objects.values('prediction') \
            .annotate(count=Count('id')) \
            .order_by('prediction')

    @staticmethod
    def average_confidence_by_stage():
        """Returns average confidence for each stage"""
        from django.db.models import Avg
        
        return PredictionResult.objects.values('prediction') \
            .annotate(avg_confidence=Avg('confidence')) \
            .order_by('prediction')
```

**Step 2: Use in View**
```python
def api_statistics(request):
    stats = {
        'by_stage': PredictionResult.get_stage_statistics(),
        'avg_confidence': PredictionResult.average_confidence_by_stage(),
        'total_predictions': PredictionResult.objects.count(),
        'total_patients': PatientRecord.objects.count(),
    }
    return JsonResponse(stats)
```

---

## 7. Testing Examples

### Test a View
```python
# tests.py
from django.test import TestCase
from django.test import Client
from .models import PredictionResult

class PredictionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_api_history(self):
        # Create test prediction
        PredictionResult.objects.create(
            prediction=2,
            confidence=95.0
        )
        
        # Test API
        response = self.client.get('/api/history/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
```

### Test Model
```python
def test_prediction_creation(self):
    pred = PredictionResult.objects.create(
        prediction=2,
        confidence=94.75
    )
    self.assertEqual(pred.get_prediction_display(), 'Moderate')
```

---

## 8. Debugging Tips

### Print Model Structure
```python
classifier = get_classifier()
classifier.model.summary()
```

### Check Layer Output Shapes
```python
from keras import backend as K

# Create a function that returns layer output
get_layer_output = K.function(
    [classifier.model.inputs[0]],
    [classifier.model.get_layer('conv5_block3_out').output]
)

layer_output = get_layer_output([processed_img])[0]
print(f"Layer output shape: {layer_output.shape}")
```

### Database Debugging
```python
# In Django shell: python manage.py shell
from dr_app.models import PredictionResult

# Check all predictions
PredictionResult.objects.all().values()

# Check specific stage
moderates = PredictionResult.objects.filter(prediction=2)
print(moderates.count())

# SQL query
print(str(moderates.query))  # See actual SQL
```

---

## 9. Performance Optimization

### Cache Model Instance
```python
def get_classifier():
    """Singleton pattern - loads model once"""
    if not hasattr(get_classifier, '_instance'):
        get_classifier._instance = DRClassifier()
    return get_classifier._instance

# Usage
classifier = get_classifier()  # Reuses same instance
```

### Optimize Database Queries
```python
# Bad
patients = PatientRecord.objects.all()
for patient in patients:
    predictions = patient.predictions.all()  # N+1 problem!

# Good
patients = PatientRecord.objects.prefetch_related('predictions')
for patient in patients:
    predictions = patient.predictions.all()  # Already loaded
```

---

## Conclusion

This guide covers the core implementation details. Use it to:
- Understand how the system works
- Extend functionality
- Debug issues
- Optimize performance
- Implement new features

---

**Version**: 1.0.0  
**Last Updated**: February 14, 2026
