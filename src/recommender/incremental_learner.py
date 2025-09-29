"""
Incremental learning system for outfit recommendations
Handles both initial model training and continuous improvement
"""

import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from datetime import datetime
from sklearn.metrics import accuracy_score


class IncrementalOutfitLearner:
    """Manages incremental model training and prediction caching"""
    
    def __init__(self, user_id, db):
        self.user_id = user_id
        self.db = db
        self.current_model_version = None
        self.feature_version = "v1.0"
        self.min_ratings_for_training = 5
        self.retrain_threshold = 10  # retrain after N new ratings
        
    def get_current_model_version(self):
        """Get the active model version for this user"""
        model_info = self.db.get_active_model_version(self.user_id)
        return model_info['version'] if model_info else None
    
    def should_retrain_model(self):
        """Determine if model needs retraining based on new ratings"""
        current_version = self.get_current_model_version()
        if not current_version:
            return True  # No model exists
            
        # Count ratings since last model training
        last_training = self.db.execute_query("""
            SELECT trained_at FROM model_versions 
            WHERE user_id = ? AND version = ?
        """, (self.user_id, current_version))
        
        if not last_training:
            return True
            
        new_ratings = self.db.execute_query("""
            SELECT COUNT(*) as count FROM outfit_ratings 
            WHERE user_id = ? AND rated_at > ?
        """, (self.user_id, last_training[0]['trained_at']))
        
        return new_ratings[0]['count'] >= self.retrain_threshold
    
    def get_cached_features(self, outfit_hashes):
        """Retrieve cached engineered features for outfit combinations"""
        if not outfit_hashes:
            return {}
            
        # Convert list to comma-separated placeholders
        placeholders = ','.join(['?'] * len(outfit_hashes))
        
        cached = self.db.execute_query(f"""
            SELECT outfit_hash, feature_blob FROM outfit_features
            WHERE user_id = ? AND feature_version = ? 
            AND outfit_hash IN ({placeholders})
        """, [self.user_id, self.feature_version] + outfit_hashes)
        
        # Deserialize features
        cache_dict = {}
        for row in cached:
            cache_dict[row['outfit_hash']] = pickle.loads(row['feature_blob'])
            
        return cache_dict
    
    def cache_features(self, outfit_hash, features):
        """Store engineered features for future use"""
        feature_blob = pickle.dumps(features)
        
        self.db.execute_query("""
            INSERT OR REPLACE INTO outfit_features 
            (user_id, outfit_hash, feature_blob, feature_version)
            VALUES (?, ?, ?, ?)
        """, (self.user_id, outfit_hash, feature_blob, self.feature_version))
    
    def get_cached_predictions(self, outfit_hashes, model_version=None):
        """Retrieve cached model predictions"""
        if not model_version:
            model_version = self.get_current_model_version()
        if not model_version or not outfit_hashes:
            return {}
            
        placeholders = ','.join(['?'] * len(outfit_hashes))
        
        cached = self.db.execute_query(f"""
            SELECT outfit_hash, predicted_rating FROM outfit_predictions
            WHERE user_id = ? AND model_version = ?
            AND outfit_hash IN ({placeholders})
        """, [self.user_id, model_version] + outfit_hashes)
        
        return {row['outfit_hash']: row['predicted_rating'] for row in cached}
    
    def cache_predictions(self, predictions_dict, model_version):
        """Store model predictions for future use"""
        for outfit_hash, prediction in predictions_dict.items():
            self.db.execute_query("""
                INSERT OR REPLACE INTO outfit_predictions
                (user_id, outfit_hash, model_version, predicted_rating)
                VALUES (?, ?, ?, ?)
            """, (self.user_id, outfit_hash, model_version, float(prediction)))
    
    def train_or_update_model(self, force_retrain=False):
        """Train new model or update existing one based on available ratings"""
        ratings = self.db.get_all_ratings(self.user_id)
        
        if len(ratings) < self.min_ratings_for_training:
            print(f"Need at least {self.min_ratings_for_training} ratings to train model")
            return None
            
        if not force_retrain and not self.should_retrain_model():
            print("Model is up to date, no retraining needed")
            return self.get_current_model_version()
        
        print(f"Training model with {len(ratings)} ratings...")
        
        # Prepare training data
        training_data = pd.DataFrame([{
            'shirt_id': r['shirt_id'],
            'pants_id': r['pants_id'], 
            'shoes_id': r['shoes_id'],
            'rating': r['rating']
        } for r in ratings])
        
        training_data['rating_binary'] = (training_data['rating'] >= 4).astype(int)
        
        # Feature engineering with caching
        X = self.prepare_features_with_cache(training_data)
        y = training_data['rating_binary']
        
        # Train model
        from src.recommender.random_forest import OutfitRecommendationModel
        model = OutfitRecommendationModel()
        model.train(X, y)
        
        # Create new model version
        model_version = f"v{len(ratings)}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        model_path = f"models/outfit_recommender_{self.user_id}_{model_version}.pkl"
        model.save_model(model_path)
        
        # Calculate accuracy (simple holdout)
        if len(ratings) >= 10:
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model_eval = OutfitRecommendationModel()
            model_eval.train(X_train, y_train)
            y_pred = model_eval.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
        else:
            accuracy = None
        
        # Save model metadata
        self.db.execute_query("""
            INSERT INTO model_versions 
            (user_id, version, training_samples, accuracy_score, feature_count, model_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (self.user_id, model_version, len(ratings), accuracy, len(X.columns), model_path))
        
        # Deactivate old models
        self.db.execute_query("""
            UPDATE model_versions SET is_active = FALSE 
            WHERE user_id = ? AND version != ?
        """, (self.user_id, model_version))
        
        # Clear old predictions cache since model changed
        self.clear_prediction_cache()
        
        self.current_model_version = model_version
        print(f"Trained new model: {model_version}")
        if accuracy:
            print(f"Model accuracy: {accuracy:.3f}")
            
        return model_version
    
    def prepare_features_with_cache(self, outfit_df):
        """Prepare features using cache when possible"""
        # Generate outfit hashes
        outfit_df['outfit_hash'] = (outfit_df['shirt_id'] + '_' + 
                                  outfit_df['pants_id'] + '_' + 
                                  outfit_df['shoes_id'])
        
        # Check cache for existing features
        cached_features = self.get_cached_features(outfit_df['outfit_hash'].tolist())
        
        # Identify which outfits need feature computation
        missing_hashes = [h for h in outfit_df['outfit_hash'] if h not in cached_features]
        
        if missing_hashes:
            print(f"Computing features for {len(missing_hashes)} new outfit combinations...")
            
            # Compute features for missing outfits
            missing_df = outfit_df[outfit_df['outfit_hash'].isin(missing_hashes)].copy()
            
            from src.feature_extraction.feature_engineering import OutfitFeatureEngine
            engine = OutfitFeatureEngine(self.user_id, self.db)
            X_missing = engine.prepare_outfit_features(missing_df, for_training=True)
            
            # Cache the new features
            for hash_val, features in zip(missing_hashes, X_missing.values):
                self.cache_features(hash_val, features)
                cached_features[hash_val] = features
        
        # Reconstruct full feature matrix
        feature_matrix = []
        for hash_val in outfit_df['outfit_hash']:
            feature_matrix.append(cached_features[hash_val])
        
        # Convert to DataFrame
        if missing_hashes:
            # Use column names from recent computation
            feature_names = X_missing.columns.tolist()
        else:
            # Fallback feature names
            feature_names = [f"feat_{i}" for i in range(len(feature_matrix[0]))]
        
        X = pd.DataFrame(feature_matrix, columns=feature_names, index=outfit_df.index)
        return X
    
    def predict_with_cache(self, outfit_combinations):
        """Get predictions using cache when possible"""
        # Generate hashes
        outfit_hashes = []
        for _, row in outfit_combinations.iterrows():
            hash_val = f"{row['shirt_id']}_{row['pants_id']}_{row['shoes_id']}"
            outfit_hashes.append(hash_val)
        
        model_version = self.get_current_model_version()
        if not model_version:
            print("No trained model available")
            return np.random.uniform(0.3, 0.7, len(outfit_combinations))
        
        # Check prediction cache
        cached_predictions = self.get_cached_predictions(outfit_hashes, model_version)
        
        # Identify outfits needing prediction
        missing_hashes = [h for h in outfit_hashes if h not in cached_predictions]
        
        if missing_hashes:
            print(f"Computing predictions for {len(missing_hashes)} outfit combinations...")
            
            # Load model
            from src.recommender.random_forest import OutfitRecommendationModel
            model = OutfitRecommendationModel()
            model_path = f"models/outfit_recommender_{self.user_id}_{model_version}.pkl"
            model.load_model(model_path)
            
            # Get features for missing predictions
            missing_df = outfit_combinations[
                [f"{h.split('_')[0]}_{h.split('_')[1]}_{h.split('_')[2]}" in missing_hashes 
                 for h in outfit_hashes]
            ].copy()
            
            # This is a bit tricky - need to reconstruct the missing_df properly
            missing_indices = [i for i, h in enumerate(outfit_hashes) if h in missing_hashes]
            missing_df = outfit_combinations.iloc[missing_indices].copy()
            
            X_missing = self.prepare_features_with_cache(missing_df)
            predictions_missing = model.predict_proba(X_missing)
            
            # Cache new predictions
            new_predictions = dict(zip(missing_hashes, predictions_missing))
            self.cache_predictions(new_predictions, model_version)
            cached_predictions.update(new_predictions)
        
        # Return predictions in original order
        return [cached_predictions[h] for h in outfit_hashes]
    
    def clear_prediction_cache(self, model_version=None):
        """Clear cached predictions (e.g., when model is retrained)"""
        if model_version:
            self.db.execute_query("""
                DELETE FROM outfit_predictions 
                WHERE user_id = ? AND model_version = ?
            """, (self.user_id, model_version))
        else:
            self.db.execute_query("""
                DELETE FROM outfit_predictions WHERE user_id = ?
            """, (self.user_id,))
        
    def clear_feature_cache(self):
        """Clear feature cache (e.g., when feature engineering changes)"""
        self.db.execute_query("""
            DELETE FROM outfit_features WHERE user_id = ? AND feature_version = ?
        """, (self.user_id, self.feature_version))