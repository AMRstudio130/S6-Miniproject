from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class PredictionResult(models.Model):
    """Model to store DR prediction results"""
    
    DR_STAGES = [
        (0, 'No Diabetic Retinopathy'),
        (1, 'Mild'),
        (2, 'Moderate'),
        (3, 'Severe'),
        (4, 'Proliferative DR'),
    ]
    
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
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Prediction Results"
    
    def __str__(self):
        return f"DR {self.get_prediction_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class PatientRecord(models.Model):
    """Model to store patient information"""
    
    patient_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField()
    
    predictions = models.ManyToManyField(PredictionResult, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.patient_id})"
