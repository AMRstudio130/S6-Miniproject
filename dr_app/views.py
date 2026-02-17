from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import json
from PIL import Image
import numpy as np

from .models import PredictionResult, PatientRecord
from .ml_utils import get_classifier, GradCAM, preprocess_and_predict
import logging

logger = logging.getLogger(__name__)


def home(request):
    """Main dashboard view"""
    if request.method == 'POST':
        # Handle image upload and prediction
        if 'image' not in request.FILES:
            return render(request, "home.html", {
                'error': 'Please select an image file'
            })
        
        image_file = request.FILES['image']
        
        try:
            # Save uploaded image temporarily
            temp_path = default_storage.save(
                f'temp/{image_file.name}',
                ContentFile(image_file.read())
            )
            full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
            
            # Get prediction
            classifier = get_classifier()
            result = classifier.predict(full_path)
            
            # Generate Grad-CAM visualization
            processed_img, _ = classifier.preprocess_image(full_path)
            grad_cam = GradCAM(classifier.model)
            heatmap = grad_cam.generate_heatmap(processed_img, pred_index=result['stage'])
            
            # Save heatmap
            heatmap_path = os.path.join(
                settings.MEDIA_ROOT,
                'heatmaps',
                f'heatmap_{image_file.name.split(".")[0]}.png'
            )
            os.makedirs(os.path.dirname(heatmap_path), exist_ok=True)
            grad_cam.save_heatmap(heatmap, full_path, heatmap_path)
            
            # Store in database
            prediction_obj = PredictionResult.objects.create(
                image=temp_path,
                prediction=result['stage'],
                confidence=result['confidence'],
                heatmap=f'heatmaps/heatmap_{image_file.name.split(".")[0]}.png'
            )
            
            # Clean up temp file
            default_storage.delete(temp_path)
            
            context = {
                'prediction': result['stage_name'],
                'stage_number': result['stage'],
                'confidence': result['confidence'],
                'heatmap_url': f'{settings.MEDIA_URL}heatmaps/heatmap_{image_file.name.split(".")[0]}.png',
                'probabilities': result['probabilities'],
                'prediction_id': prediction_obj.id
            }
            
            return render(request, "home.html", context)
            
        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            return render(request, "home.html", {
                'error': f'Prediction failed: {str(e)}'
            })
    
    return render(request, "home.html")


@csrf_exempt
@require_http_methods(["POST"])
def api_predict(request):
    """
    API endpoint for DR prediction
    
    Expected POST data:
    - image: Image file
    - patient_id: (optional) Patient identifier
    
    Returns JSON with prediction results
    """
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'status': 'error',
                'message': 'No image provided'
            }, status=400)
        
        image_file = request.FILES['image']
        patient_id = request.POST.get('patient_id', None)
        
        # Validate image format
        valid_formats = ['JPEG', 'PNG', 'JPG']
        img = Image.open(image_file)
        if img.format not in valid_formats:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid image format. Please use JPG or PNG'
            }, status=400)
        
        # Save uploaded image
        temp_path = default_storage.save(
            f'temp/{image_file.name}',
            ContentFile(image_file.read())
        )
        full_path = os.path.join(settings.MEDIA_ROOT, temp_path)
        
        # Get prediction
        classifier = get_classifier()
        result = classifier.predict(full_path)
        
        # Generate Grad-CAM
        processed_img, _ = classifier.preprocess_image(full_path)
        grad_cam = GradCAM(classifier.model)
        heatmap = grad_cam.generate_heatmap(processed_img, pred_index=result['stage'])
        
        # Save heatmap
        heatmap_filename = f'heatmap_{image_file.name.split(".")[0]}.png'
        heatmap_path = os.path.join(
            settings.MEDIA_ROOT,
            'heatmaps',
            heatmap_filename
        )
        os.makedirs(os.path.dirname(heatmap_path), exist_ok=True)
        grad_cam.save_heatmap(heatmap, full_path, heatmap_path)
        
        # Store prediction
        prediction_obj = PredictionResult.objects.create(
            image=temp_path,
            prediction=result['stage'],
            confidence=result['confidence'],
            heatmap=f'heatmaps/{heatmap_filename}'
        )
        
        # Link to patient if provided
        if patient_id:
            try:
                patient = PatientRecord.objects.get(patient_id=patient_id)
                patient.predictions.add(prediction_obj)
            except PatientRecord.DoesNotExist:
                logger.warning(f"Patient {patient_id} not found")
        
        # Clean up temp file
        default_storage.delete(temp_path)
        
        return JsonResponse({
            'status': 'success',
            'prediction_id': prediction_obj.id,
            'stage': result['stage'],
            'stage_name': result['stage_name'],
            'confidence': result['confidence'],
            'heatmap_url': f'{settings.MEDIA_URL}heatmaps/{heatmap_filename}',
            'probabilities': result['probabilities']
        }, status=200)
        
    except Exception as e:
        logger.error(f"API prediction error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_result(request, prediction_id):
    """Get prediction result by ID"""
    try:
        prediction = PredictionResult.objects.get(id=prediction_id)
        
        return JsonResponse({
            'status': 'success',
            'prediction_id': prediction.id,
            'stage': prediction.prediction,
            'stage_name': prediction.get_prediction_display(),
            'confidence': prediction.confidence,
            'image_url': f'{settings.MEDIA_URL}{prediction.image}',
            'heatmap_url': f'{settings.MEDIA_URL}{prediction.heatmap}' if prediction.heatmap else None,
            'created_at': prediction.created_at.isoformat()
        }, status=200)
        
    except PredictionResult.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Prediction not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error retrieving result: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_history(request, patient_id=None):
    """Get prediction history for a patient"""
    try:
        if patient_id:
            patient = PatientRecord.objects.get(patient_id=patient_id)
            predictions = patient.predictions.all()
        else:
            predictions = PredictionResult.objects.all()[:50]  # Last 50
        
        data = []
        for pred in predictions:
            data.append({
                'id': pred.id,
                'stage': pred.prediction,
                'stage_name': pred.get_prediction_display(),
                'confidence': pred.confidence,
                'created_at': pred.created_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(data),
            'predictions': data
        }, status=200)
        
    except PatientRecord.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Patient not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_register_patient(request):
    """Register a new patient"""
    try:
        data = json.loads(request.body)
        
        patient, created = PatientRecord.objects.get_or_create(
            patient_id=data['patient_id'],
            defaults={
                'name': data.get('name', ''),
                'age': data.get('age', 0),
                'email': data.get('email', '')
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Patient registered' if created else 'Patient already exists',
            'patient_id': patient.patient_id,
            'created': created
        }, status=201 if created else 200)
        
    except Exception as e:
        logger.error(f"Error registering patient: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


