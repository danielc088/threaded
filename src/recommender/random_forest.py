"""
user-aware random forest model for outfit recommendation system
each user gets their own personalised model based on their ratings
learns what you like and gets better over time
"""

import pandas as pd
import numpy as np
import os
import glob
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from src.feature_extraction.feature_engineering import create_training_features

class UserOutfitRecommendationModel:
    """user-specific random forest classifier for predicting outfit ratings"""
    
    def __init__(self, user_id, n_estimators=500, max_depth=5, class_weight={0: 1, 1: 2}, random_state=42):
        """initialise with user id and optimised hyperparameters"""
        self.user_id = user_id
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight=class_weight,
            random_state=random_state,
            n_jobs=-1
        )
        self.threshold = 0.45 
        self.feature_names = None
        self.is_fitted = False
        self.training_history = []
    
    def get_model_path(self, version=None):
        """get user-specific model file path"""
        if version:
            return f"models/user_{self.user_id}/outfit_recommender_{version}.pkl"
        else:
            return f"models/user_{self.user_id}/outfit_recommender_latest.pkl"
    
    def train(self, X_train, y_train, version=None):
        """train the random forest model on user's outfit combinations"""
        
        self.feature_names = X_train.columns.tolist() if hasattr(X_train, 'columns') else None
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        
        # record training info
        training_info = {
            'version': version,
            'samples': len(X_train),
            'positive_samples': int(y_train.sum()),
            'features': len(self.feature_names) if self.feature_names else X_train.shape[1]
        }
        self.training_history.append(training_info)
        
        return self
    
    def predict_proba(self, X):
        """get probability scores for outfit combinations"""
        if not self.is_fitted:
            raise ValueError(f"model for user {self.user_id} must be trained before making predictions")
        
        return self.model.predict_proba(X)[:, 1]  # probability of high rating
    
    def predict(self, X, use_threshold=True):
        """predict whether outfits will be rated highly"""
        if not self.is_fitted:
            raise ValueError(f"model for user {self.user_id} must be trained before making predictions")
        
        if use_threshold:
            probas = self.predict_proba(X)
            return (probas >= self.threshold).astype(int)
        else:
            return self.model.predict(X)
    
    def evaluate(self, X_train, y_train, X_test, y_test, show_details=True):
        """evaluate model performance on train and test sets"""

        y_train_pred = self.predict(X_train)
        y_test_pred = self.predict(X_test)

        train_accuracy = accuracy_score(y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)

        results = {
            'user_id': self.user_id,
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'threshold_used': self.threshold,
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }

        if show_details:
            print(f"model evaluation for user {self.user_id} (threshold = {self.threshold})")
            print(f"train accuracy: {train_accuracy:.3f} ({len(X_train)} samples)")
            print(f"test accuracy:  {test_accuracy:.3f} ({len(X_test)} samples)")
            print()
            print(classification_report(y_test, y_test_pred))
            print()
            print("test set confusion matrix:")

            # handle confusion matrix more robustly
            cm = confusion_matrix(y_test, y_test_pred)
            unique_labels = sorted(list(set(y_test) | set(y_test_pred)))

            if len(unique_labels) == 1:
                # only one class present
                label = unique_labels[0]
                print(f"predicted:  {label}")
                print(f"actual {label}: [{cm[0,0]:3d}]")
                print("(note: only one class present in test set)")
            elif len(unique_labels) == 2:
                # both classes present - normal case
                print("predicted:  0   1")
                if cm.shape == (2, 2):
                    print(f"actual 0: [{cm[0,0]:3d} {cm[0,1]:3d}]")
                    print(f"actual 1: [{cm[1,0]:3d} {cm[1,1]:3d}]")
                elif cm.shape == (1, 1):
                    # edge case: only one class in actual data
                    actual_class = unique_labels[0] if len(set(y_test)) == 1 else 0
                    print(f"actual {actual_class}: [{cm[0,0]:3d}]")
                else:
                    print(f"confusion matrix shape: {cm.shape}")
                    print(cm)
            else:
                # more than 2 classes (shouldn't happen with binary classification)
                print("predicted:", "  ".join(map(str, unique_labels)))
                for i, actual_label in enumerate(unique_labels):
                    row = "  ".join(f"{cm[i,j]:3d}" if j < cm.shape[1] else "  0" for j in range(len(unique_labels)))
                    print(f"actual {actual_label}: [{row}]")

        return results
    
    def get_feature_importance(self, top_n=10):
        """analyse which features are most important for this user's outfit preferences"""
        
        if not self.is_fitted:
            raise ValueError(f"model for user {self.user_id} must be trained before analysing features")
        
        if self.feature_names is None:
            print("feature names not available")
            return None
        
        importances = pd.Series(
            self.model.feature_importances_, 
            index=self.feature_names
        ).sort_values(ascending=False)
        
        print(f"top {top_n} features for user {self.user_id}:")
        for i, (feature, importance) in enumerate(importances.head(top_n).items(), 1):
            print(f"{i:2d}. {feature:35s} {importance:.4f}")
        
        return importances
    
    def save_model(self, version=None):
        """save user's trained model to disk"""
        
        if not self.is_fitted:
            raise ValueError(f"model for user {self.user_id} must be trained before saving")
        
        model_path = Path(self.get_model_path(version))
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'user_id': self.user_id,
            'model': self.model,
            'threshold': self.threshold,
            'feature_names': self.feature_names,
            'training_history': self.training_history,
            'version': version
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        # also save as latest
        latest_path = self.get_model_path()
        with open(latest_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"model for user {self.user_id} saved to {model_path}")
        return str(model_path)
    
    def load_model(self, version=None):
        """load user's trained model from disk"""
        
        model_path = self.get_model_path(version)
        
        if not Path(model_path).exists():
            raise FileNotFoundError(f"no saved model found for user {self.user_id} at {model_path}")
        
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        # verify this is the right user's model
        if model_data.get('user_id') != self.user_id:
            raise ValueError(f"model file is for user {model_data.get('user_id')}, not {self.user_id}")
        
        self.model = model_data['model']
        self.threshold = model_data['threshold']
        self.feature_names = model_data['feature_names']
        self.training_history = model_data.get('training_history', [])
        self.is_fitted = True
        
        return model_data.get('version')
    
    def model_exists(self, version=None):
        """check if a saved model exists for this user"""
        return Path(self.get_model_path(version)).exists()


def train_user_model_from_data(user_id, X, y, version=None, test_size=0.2):
    """train and save a user-specific model from data"""
    
    # split into train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)
    
    # initialise and train user model
    model = UserOutfitRecommendationModel(user_id)
    model.train(X_train, y_train, version=version)
    
    # evaluate performance
    results = model.evaluate(X_train, y_train, X_test, y_test)
    print()
    
    # analyse feature importance
    model.get_feature_importance(top_n=15)
    print()
    
    # save model
    model_path = model.save_model(version=version)
    
    return model, results


def train_user_model_from_ratings(user_id, db, min_ratings=5, version=None):
    """train user-specific model directly from their ratings in database"""
    
    # get user ratings
    ratings = db.get_all_ratings(user_id)
    
    if len(ratings) < min_ratings:
        print(f"user {user_id}: not enough ratings for training (need at least {min_ratings}, have {len(ratings)})")
        return None
    
    # generate version if not provided
    if version is None:
        from datetime import datetime
        version = f"v{len(ratings)}_{datetime.now().strftime('%Y%m%d_%H%M')}"
    
    # create training data from ratings
    training_data = []
    for rating in ratings:
        training_data.append({
            'shirt_id': rating['shirt_id'],
            'pants_id': rating['pants_id'],
            'shoes_id': rating['shoes_id'],
            'rating': rating['rating']
        })
    
    # convert to dataframe and binary ratings (4-5 = good, 1-3 = bad)
    df = pd.DataFrame(training_data)
    df['rating_binary'] = (df['rating'] >= 4).astype(int)
    
    # load existing transformer if cached features exist
    transformer_path = f"models/user_{user_id}/feature_transformer.pkl"
    stats = db.get_database_stats(user_id)
    
    # always create fresh transformer for training to match rated outfits
    print("creating transformer from training data")
    X, engine = create_training_features(user_id, df, db, save_transformer=False)
    
    y = df['rating_binary']
    
    # train user model
    model, results = train_user_model_from_data(user_id, X, y, version=version)
    
    db.save_model_version(
        user_id=user_id,
        version=version,
        training_samples=len(ratings),
        accuracy_score=results.get('test_accuracy'),
        feature_count=len(X.columns),
        model_path=model.get_model_path(version)
    )
    
    print(f"model registered in database: {version}")
    
    return model, results


def get_user_model(user_id, db=None, auto_train=True, min_ratings=5):
    """get user's model, training it if necessary"""
    
    model = UserOutfitRecommendationModel(user_id)
    
    # try to load existing model
    if model.model_exists():
        try:
            model.load_model()
            return model
        except Exception as e:
            print(f"error loading model for user {user_id}: {e}")
    
    # if no model exists and auto_train is enabled
    if auto_train and db:
        print(f"no model found for user {user_id}, attempting to train...")
        result = train_user_model_from_ratings(user_id, db, min_ratings=min_ratings)
        if result:
            model, _ = result
            return model
    
    print(f"no trained model available for user {user_id}")
    return None


def list_user_models():
    """list all saved user models"""
    models_dir = Path("models")
    if not models_dir.exists():
        print("no models directory found")
        return []
    
    user_models = []
    for user_dir in models_dir.glob("user_*"):
        user_id = int(user_dir.name.replace("user_", ""))
        
        # check for latest model
        latest_model = user_dir / "outfit_recommender_latest.pkl"
        if latest_model.exists():
            user_models.append({
                'user_id': user_id,
                'latest_model': str(latest_model),
                'modified': latest_model.stat().st_mtime
            })
    
    return sorted(user_models, key=lambda x: x['user_id'])

def cleanup_old_models(user_id: str, keep_count: int = 3):
    """keep only the most recent N models, delete older ones"""
    model_dir = Path(f"models/{user_id}")
    
    if not model_dir.exists():
        return
    
    # get all model files for this user
    model_files = glob.glob(str(model_dir / "outfit_model_*.pkl"))
    
    if len(model_files) <= keep_count:
        return
    
    # sort by modification time (newest first)
    model_files.sort(key=os.path.getmtime, reverse=True)
    
    # delete old models (keep only the newest 'keep_count' models)
    for old_model in model_files[keep_count:]:
        try:
            os.remove(old_model)
            print(f"Deleted old model: {old_model}")
        except Exception as e:
            print(f"Error deleting {old_model}: {e}")

# keep backward compatibility
OutfitRecommendationModel = UserOutfitRecommendationModel
train_outfit_model_from_data = train_user_model_from_data
train_outfit_model_from_ratings = train_user_model_from_ratings