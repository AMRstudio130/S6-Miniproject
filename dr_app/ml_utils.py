"""
Machine Learning utilities for Diabetic Retinopathy detection
Includes ResNet50 model loading and Grad-CAM visualization
"""

import numpy as np
import cv2
from PIL import Image
import os
from django.conf import settings
import logging

try:
    import tensorflow as tf  # type: ignore
    from tensorflow.keras.applications import ResNet50  # type: ignore
    from tensorflow.keras.applications.resnet50 import preprocess_input  # type: ignore
    from tensorflow.keras.layers import GlobalAveragePooling2D, Dense  # type: ignore
    from tensorflow.keras import Model  # type: ignore
    try:
        from tensorflow.keras import load_model  # type: ignore
    except ImportError:
        from keras.saving import load_model  # type: ignore
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    
logger = logging.getLogger(__name__)

# DR Stage mapping
DR_STAGES = {
    0: 'No Diabetic Retinopathy',
    1: 'Mild',
    2: 'Moderate',
    3: 'Severe',
    4: 'Proliferative DR'
}


class DRClassifier:
    """ResNet50-based Diabetic Retinopathy Classifier"""
    
    def __init__(self):
        self.model = None
        self.base_model = None
        self.img_size = (224, 224)
        self.load_model()
    
    def load_model(self):
        """Load pre-trained ResNet50 model"""
        try:
            if not TENSORFLOW_AVAILABLE:
                logger.warning("TensorFlow not available. Install with: pip install tensorflow==2.14.0")
                self.model = None
                return
            
            # Load trained model from file
            model_path = os.path.join(settings.BASE_DIR, 'dr_app', 'model', 'dr_model.h5')
            
            if os.path.exists(model_path):
                try:
                    # Load the pre-trained, fine-tuned model
                    self.model = load_model(model_path)
                    logger.info(f"Trained model loaded successfully from {model_path}")
                except Exception as model_load_error:
                    # Fallback: Build model from scratch if trained model has compatibility issues
                    logger.warning(f"Could not load trained model: {str(model_load_error)}. Building from scratch...")
                    self._build_model_from_scratch()
            else:
                # Fallback: Build model from scratch if trained model not found
                logger.warning(f"Trained model not found at {model_path}. Building model from scratch...")
                self._build_model_from_scratch()
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def _build_model_from_scratch(self):
        """Build ResNet50 model from scratch for compatibility"""
        try:
            self.base_model = ResNet50(
                weights='imagenet',
                include_top=False,
                input_shape=(224, 224, 3)
            )
            
            # Add custom classification layers
            x = self.base_model.output
            x = GlobalAveragePooling2D()(x)
            x = Dense(256, activation='relu')(x)
            x = Dense(128, activation='relu')(x)
            predictions = Dense(5, activation='softmax', name='dr_predictions')(x)
            
            self.model = Model(
                inputs=self.base_model.input,
                outputs=predictions
            )
            logger.info("Model built from scratch with ResNet50")
        except Exception as e:
            logger.error(f"Error building model from scratch: {str(e)}")
            raise
    
    def preprocess_image(self, image_path):
        """Preprocess image for model input"""
        try:
            # Read image
            img = cv2.imread(str(image_path))
            if img is None:
                raise ValueError("Could not read image")
            
            # Convert BGR to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize
            img = cv2.resize(img, self.img_size)
            
            # Normalize
            img = img.astype('float32')
            img = preprocess_input(img)
            
            return np.expand_dims(img, axis=0), cv2.imread(str(image_path))
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise
    
    def predict(self, image_path):
        """Predict DR stage from fundus image"""
        try:
            if not self.model or not TENSORFLOW_AVAILABLE:
                raise Exception("Model not loaded. Please install TensorFlow: pip install tensorflow==2.14.0")
            
            processed_img, original_img = self.preprocess_image(image_path)
            
            # Make prediction
            predictions = self.model.predict(processed_img, verbose=0)
            pred_class = np.argmax(predictions[0])
            confidence = float(predictions[0][pred_class]) * 100
            
            return {
                'stage': int(pred_class),
                'stage_name': DR_STAGES[pred_class],
                'confidence': round(confidence, 2),
                'probabilities': {
                    DR_STAGES[i]: float(predictions[0][i]) * 100
                    for i in range(5)
                }
            }
            
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            raise


class GradCAM:
    """Grad-CAM visualization for model explainability"""
    
    def __init__(self, model, layer_name='conv5_block3_out'):
        """
        Initialize Grad-CAM
        
        Args:
            model: Keras model
            layer_name: Name of the layer to visualize
        """
        self.model = model
        self.layer_name = layer_name
        self.grad_model = None
        self.build_grad_model()
    
    def build_grad_model(self):
        """Build gradient model for Grad-CAM computation"""
        try:
            # Get the last conv layer and output layer
            last_conv_layer = self.model.get_layer(self.layer_name)
            
            self.grad_model = Model(
                [self.model.inputs],
                [last_conv_layer.output, self.model.output]
            )
            
        except Exception as e:
            logger.error(f"Error building grad model: {str(e)}")
            # Fallback to ResNet50's last conv layer
            try:
                self.grad_model = Model(
                    [self.model.inputs],
                    [self.model.get_layer('conv5_block3_out').output,
                     self.model.output]
                )
            except:
                logger.error("Could not build grad model with fallback")
                raise
    
    def generate_heatmap(self, img_array, pred_index=None):
        """
        Generate Grad-CAM heatmap
        
        Args:
            img_array: Preprocessed image array
            pred_index: Class index to visualize (None = top prediction)
        
        Returns:
            Heatmap as numpy array
        """
        try:
            with tf.GradientTape() as tape:
                conv_outputs, predictions = self.grad_model(img_array)
                
                if pred_index is None:
                    pred_index = tf.argmax(predictions[0])
                
                class_channel = predictions[:, pred_index]
            
            # Compute gradients
            grads = tape.gradient(class_channel, conv_outputs)
            
            # Compute weights
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
            
            # Generate heatmap
            conv_outputs = conv_outputs[0]
            heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
            heatmap = tf.squeeze(heatmap)
            
            # Normalize heatmap
            heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
            
            return heatmap.numpy()
            
        except Exception as e:
            logger.error(f"Error generating heatmap: {str(e)}")
            raise
    
    def save_heatmap(self, heatmap, original_image_path, output_path, alpha=0.6):
        """
        Save Grad-CAM heatmap overlaid on original image
        
        Args:
            heatmap: Grad-CAM heatmap
            original_image_path: Path to original image
            output_path: Path to save output
            alpha: Transparency of overlay
        """
        try:
            # Read original image
            img = cv2.imread(str(original_image_path))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize heatmap to match image
            heatmap = cv2.resize(heatmap, (img_rgb.shape[1], img_rgb.shape[0]))
            heatmap = np.uint8(255 * heatmap)
            
            # Apply colormap
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            heatmap_rgb = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
            
            # Overlay on original image
            overlay = cv2.addWeighted(img_rgb, 1 - alpha, heatmap_rgb, alpha, 0)
            
            # Save
            overlay_bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(output_path), overlay_bgr)
            
            logger.info(f"Heatmap saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving heatmap: {str(e)}")
            raise


def get_classifier():
    """Singleton function to get DR classifier instance"""
    if not hasattr(get_classifier, '_instance'):
        get_classifier._instance = DRClassifier()
    return get_classifier._instance


def preprocess_and_predict(image_path):
    """
    Main function to preprocess image and get prediction with explanation
    
    Args:
        image_path: Path to fundus image
    
    Returns:
        Dictionary with prediction results and metadata
    """
    try:
        classifier = get_classifier()
        result = classifier.predict(image_path)
        return result
    except Exception as e:
        logger.error(f"Error in preprocess_and_predict: {str(e)}")
        raise
