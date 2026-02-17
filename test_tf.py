import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_project.settings')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

django.setup()

try:
    from dr_app.ml_utils import DRClassifier
    classifier = DRClassifier()
    
    if classifier.model:
        print('✓ Trained ResNet50 model loaded successfully!')
        print(f'✓ Model type: {type(classifier.model).__name__}')
        print('→ Efficiency improved - using pre-trained fine-tuned model')
    else:
        print('✗ Model failed to load')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
