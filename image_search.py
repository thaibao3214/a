from tensorflow.keras.applications import EfficientNetB2
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.efficientnet import preprocess_input
import tensorflow as tf
import numpy as np
from pathlib import Path
import pickle
from scipy.spatial.distance import cosine, euclidean
import time

class ImageSearchEngine:
    def __init__(self):
        """Initialize EfficientNetB2 model for better accuracy"""
        print("Initializing model...")
        # Standard image size for quick testing
        self.img_size = (300, 300)
        self.model = EfficientNetB2(
            weights='imagenet',
            include_top=False,
            pooling='avg',
            input_shape=(self.img_size[0], self.img_size[1], 3)
        )
        self.features_file = 'data/features/image_features.pkl'
        self.batch_size = 8  # Batch size for quick processing
        self.max_images_per_class = 2000  # Images per class for testing
        
    def extract_features(self, img_path):
        """Extract features with enhanced augmentation"""
        try:
            # Load and augment image
            img = image.load_img(img_path, target_size=self.img_size)
            x = image.img_to_array(img)
            
            # Enhanced augmentation pipeline
            x = tf.image.random_flip_left_right(x)
            x = tf.image.random_flip_up_down(x)
            x = tf.image.random_brightness(x, 0.3)
            x = tf.image.random_contrast(x, 0.7, 1.3)
            x = tf.image.random_saturation(x, 0.7, 1.3)
            x = tf.image.random_hue(x, 0.2)
            
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)
            features = self.model.predict(x, verbose=0)
            
            # L2 normalization
            features = features / (np.linalg.norm(features) + 1e-7)
            return features.flatten()
        except Exception as e:
            print(f"Error extracting features from {img_path}: {e}")
            return None
    
    def process_batch(self, image_batch, paths_batch):
        """Process batch with enhanced normalization"""
        try:
            batch_array = np.array(image_batch)
            features = self.model.predict(batch_array, verbose=0)
            # Enhanced normalization
            features = features / (np.linalg.norm(features, axis=1, keepdims=True) + 1e-7)
            return features
        except Exception as e:
            print(f"Error processing batch: {e}")
            return None
    
    def build_features_database(self):
        """Build features database with enhanced processing"""
        features_db = {}
        processed_dir = Path('data/processed/train')
        
        print("Starting feature extraction...")
        start_time = time.time()
        
        total_processed = 0
        batch_images = []
        batch_paths = []
        
        for class_dir in processed_dir.iterdir():
            if not class_dir.is_dir():
                continue
                
            print(f"\nProcessing class: {class_dir.name}")
            count = 0
            
            for img_path in class_dir.glob('*.[jp][pn][eg]*'):
                if count >= self.max_images_per_class:
                    break
                    
                try:
                    # Load and preprocess image
                    img = image.load_img(img_path, target_size=self.img_size)
                    x = image.img_to_array(img)
                    x = preprocess_input(x)
                    
                    # Enhanced augmentation
                    x = tf.image.random_flip_left_right(x)
                    x = tf.image.random_flip_up_down(x)
                    x = tf.image.random_brightness(x, 0.3)
                    x = tf.image.random_contrast(x, 0.7, 1.3)
                    x = tf.image.random_saturation(x, 0.7, 1.3)
                    
                    batch_images.append(x)
                    batch_paths.append(img_path)
                    count += 1
                    
                    if len(batch_images) >= self.batch_size:
                        batch_features = self.process_batch(batch_images, batch_paths)
                        if batch_features is not None:
                            for idx, path in enumerate(batch_paths):
                                features_db[str(path)] = {
                                    'features': batch_features[idx],
                                    'class': path.parent.name
                                }
                                total_processed += 1
                        
                        batch_images = []
                        batch_paths = []
                        print(f"Processed {total_processed} images...")
                        
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
                    continue
        
        # Process remaining images
        if batch_images:
            batch_features = self.process_batch(batch_images, batch_paths)
            if batch_features is not None:
                for idx, path in enumerate(batch_paths):
                    features_db[str(path)] = {
                        'features': batch_features[idx],
                        'class': path.parent.name
                    }
                    total_processed += 1
        
        elapsed_time = time.time() - start_time
        print(f"\nFeature extraction completed:")
        print(f"- Total images processed: {total_processed}")
        print(f"- Time taken: {elapsed_time:.2f} seconds")
        print(f"- Average time per image: {elapsed_time/total_processed:.2f} seconds")
        
        print("\nSaving features database...")
        with open(self.features_file, 'wb') as f:
            pickle.dump(features_db, f)
        print("Features database saved successfully!")
    
    def search(self, query_image, top_k=5):
        """Search with enhanced similarity metrics"""
        print("Extracting features from query image...")
        query_features = self.extract_features(query_image)
        
        if query_features is None:
            return []
        
        print("Loading features database...")
        try:
            with open(self.features_file, 'rb') as f:
                features_db = pickle.load(f)
        except Exception as e:
            print(f"Error loading features database: {e}")
            return []
        
        print("Calculating similarities...")
        similarities = []
        for path, data in features_db.items():
            # Multiple similarity metrics
            cosine_sim = 1 - cosine(query_features, data['features'])
            euclidean_sim = 1 / (1 + euclidean(query_features, data['features']))
            correlation = np.corrcoef(query_features, data['features'])[0,1]
            
            # Weighted combination of metrics
            weighted_sim = (0.5 * cosine_sim + 
                          0.3 * euclidean_sim + 
                          0.2 * correlation)
            
            similarities.append({
                'path': path,
                'similarity': weighted_sim,
                'class': data['class']
            })
        
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

if __name__ == "__main__":
    engine = ImageSearchEngine()
    print("Building features database...")
    engine.build_features_database()
    print("\nFeature extraction completed!")