from django.urls import path
from . import views

urlpatterns = [
    # Web Views
    path('', views.home, name='home'),
    
    # API Endpoints - Prediction
    path('api/predict/', views.api_predict, name='api_predict'),
    path('api/result/<int:prediction_id>/', views.api_result, name='api_result'),
    
    # API Endpoints - History
    path('api/history/', views.api_history, name='api_history_all'),
    path('api/history/<str:patient_id>/', views.api_history, name='api_history_patient'),
    
    # API Endpoints - Patient Management
    path('api/register-patient/', views.api_register_patient, name='api_register_patient'),
]
