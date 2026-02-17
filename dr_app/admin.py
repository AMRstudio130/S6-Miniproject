from django.contrib import admin
from .models import PredictionResult, PatientRecord


@admin.register(PredictionResult)
class PredictionResultAdmin(admin.ModelAdmin):
    """Admin interface for prediction results"""
    
    list_display = ('id', 'prediction', 'confidence', 'created_at')
    list_filter = ('prediction', 'created_at')
    search_fields = ('id',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Image & Prediction', {
            'fields': ('image', 'prediction', 'confidence')
        }),
        ('Visualization', {
            'fields': ('heatmap',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):
    """Admin interface for patient records"""
    
    list_display = ('patient_id', 'name', 'age', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient_id', 'name', 'email')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('predictions',)
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_id', 'name', 'age', 'email')
        }),
        ('Predictions', {
            'fields': ('predictions',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
