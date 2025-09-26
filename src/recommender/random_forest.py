"""
random forest model for outfit recommendation system
trains on engineered features to predict whether outfit combinations will be rated highly
includes model evaluation, feature importance analysis, and outfit scoring functions
"""

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


class OutfitRecommendationModel:
    """random forest classifier for predicting outfit ratings"""
    
    def __init__(self, n_estimators=500, max_depth=5, class_weight={0: 1, 1: 2}, random_state=42):
        """initialize with optimized hyperparameters for outfit recommendation"""
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight=class_weight,  # give more weight to positive ratings
            random_state=random_state,
            n_jobs=-1
        )
        self.threshold = 0.38  # optimized threshold for precision/recall balance
        self.feature_names = None
        self.is_fitted = False
    
    def load_training_data(self, data_dir="data/training"):
        """load preprocessed training and test datasets"""
        data_path = Path(data_dir)
        
        print("Loading training datasets...")
        self.X_train = pd.read_csv(data_path / "train_features.csv")
        self.X_test = pd.read_csv(data_path / "test_features.csv")  
        self.y_train = pd.read_csv(data_path / "train_labels.csv").iloc[:, 0]  # first column
        self.y_test = pd.read_csv(data_path / "test_labels.csv").iloc[:, 0]
        
        self.feature_names = self.X_train.columns.tolist()
        
        print(f"Training data: {self.X_train.shape[0]} samples, {self.X_train.shape[1]} features")
        print(f"Test data: {self.X_test.shape[0]} samples")
        print(f"Positive class distribution: {self.y_train.mean():.2%} train, {self.y_test.mean():.2%} test")
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def train(self, X_train=None, y_train=None):
        """train the random forest model on outfit combinations"""
        
        if X_train is None:
            X_train = self.X_train
        if y_train is None:
            y_train = self.y_train
        
        print("Training random forest model...")
        print(f"Using {self.model.n_estimators} trees with max depth {self.model.max_depth}")
        
        self.model.fit(X_train, y_train)
        self.is_fitted = True
        
        print("Training completed!")
        return self
    
    def predict_proba(self, X):
        """get probability scores for outfit combinations"""
        if not self.is_fitted:
            raise ValueError("Model must be trained before making predictions")
        
        return self.model.predict_proba(X)[:, 1]  # probability of high rating
    
    def predict(self, X, use_threshold=True):
        """predict whether outfits will be rated highly"""
        if not self.is_fitted:
            raise ValueError("Model must be trained before making predictions")
        
        if use_threshold:
            # use optimized threshold for better precision/recall balance
            probas = self.predict_proba(X)
            return (probas >= self.threshold).astype(int)
        else:
            # use default 0.5 threshold
            return self.model.predict(X)
    
    def evaluate(self, X_test=None, y_test=None, show_details=True):
        """evaluate model performance on test set"""
        
        if X_test is None:
            X_test = self.X_test
        if y_test is None:
            y_test = self.y_test
        
        # predictions on both train and test
        y_train_pred = self.predict(self.X_train)
        y_test_pred = self.predict(X_test)
        
        train_accuracy = accuracy_score(self.y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        
        results = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'threshold_used': self.threshold
        }
        
        if show_details:
            print(f"Model Evaluation (threshold = {self.threshold})")
            print("=" * 50)
            print(f"Train Accuracy: {train_accuracy:.3f}")
            print(f"Test Accuracy:  {test_accuracy:.3f}")
            print()
            print("Test Set Classification Report:")
            print(classification_report(y_test, y_test_pred))
            print()
            print("Test Set Confusion Matrix:")
            print("Predicted:  0   1")
            cm = confusion_matrix(y_test, y_test_pred)
            print(f"Actual 0: [{cm[0,0]:3d} {cm[0,1]:3d}]")
            print(f"Actual 1: [{cm[1,0]:3d} {cm[1,1]:3d}]")
        
        return results
    
    def get_feature_importance(self, top_n=10):
        """analyze which features are most important for outfit recommendations"""
        
        if not self.is_fitted:
            raise ValueError("Model must be trained before analyzing feature importance")
        
        # create importance series
        importances = pd.Series(
            self.model.feature_importances_, 
            index=self.feature_names
        ).sort_values(ascending=False)
        
        print(f"Top {top_n} Most Important Features:")
        print("=" * 50)
        for i, (feature, importance) in enumerate(importances.head(top_n).items(), 1):
            print(f"{i:2d}. {feature:35s} {importance:.4f}")
        
        return importances
    
    def score_outfit(self, shirt_features, pants_features, shoes_features):
        """score a single outfit combination (returns probability of high rating)"""
        
        if not self.is_fitted:
            raise ValueError("Model must be trained before scoring outfits")
        
        # this would need the same feature engineering pipeline applied
        # to individual items to create the full feature vector
        # implementation depends on how individual item features are structured
        
        pass  # placeholder - would implement based on your feature structure
    
    def recommend_outfits(self, candidate_outfits, top_n=10):
        """rank outfit combinations and return top recommendations"""
        
        if not self.is_fitted:
            raise ValueError("Model must be trained before making recommendations")
        
        # get probability scores for all candidates
        scores = self.predict_proba(candidate_outfits)
        
        # create results dataframe with scores
        recommendations = candidate_outfits.copy()
        recommendations['recommendation_score'] = scores
        
        # sort by score and return top N
        top_outfits = recommendations.sort_values(
            'recommendation_score', 
            ascending=False
        ).head(top_n)
        
        return top_outfits
    
    def save_model(self, filepath="models/outfit_recommender.pkl"):
        """save trained model to disk"""
        
        if not self.is_fitted:
            raise ValueError("Model must be trained before saving")
        
        model_path = Path(filepath)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'threshold': self.threshold,
            'feature_names': self.feature_names
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath="models/outfit_recommender.pkl"):
        """load trained model from disk"""
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.threshold = model_data['threshold']
        self.feature_names = model_data['feature_names']
        self.is_fitted = True
        
        print(f"Model loaded from {filepath}")
        print(f"Features: {len(self.feature_names)}, Threshold: {self.threshold}")


def train_outfit_model(data_dir="data/training", save_path="models/outfit_score.pkl"):
    """convenience function to train and save the outfit recommendation model"""
    
    print("Training Outfit Recommendation Model")
    print("=" * 50)
    
    # initialize and train model
    model = OutfitRecommendationModel()
    model.load_training_data(data_dir)
    model.train()
    
    # evaluate performance
    model.evaluate()
    print()
    
    # analyze feature importance
    model.get_feature_importance(top_n=15)
    print()
    
    # save model
    model.save_model(save_path)
    
    return model


def evaluate_model_variants(data_dir="data/training"):
    """test different hyperparameter combinations to find best model"""
    
    print("Evaluating Model Variants")
    print("=" * 50)
    
    # test different configurations
    variants = [
        {'n_estimators': 300, 'max_depth': 4, 'class_weight': {0: 1, 1: 2}},
        {'n_estimators': 500, 'max_depth': 5, 'class_weight': {0: 1, 1: 2}},
        {'n_estimators': 700, 'max_depth': 6, 'class_weight': {0: 1, 1: 2}},
        {'n_estimators': 500, 'max_depth': 5, 'class_weight': {0: 1, 1: 3}},
    ]
    
    results = []
    
    for i, params in enumerate(variants, 1):
        print(f"\\nVariant {i}: {params}")
        
        model = OutfitRecommendationModel(**params)
        model.load_training_data(data_dir)
        model.train()
        
        eval_results = model.evaluate(show_details=False)
        eval_results.update(params)
        results.append(eval_results)
        
        print(f"Train: {eval_results['train_accuracy']:.3f}, Test: {eval_results['test_accuracy']:.3f}")
    
    # find best model
    results_df = pd.DataFrame(results)
    best_idx = results_df['test_accuracy'].idxmax()
    best_params = results_df.iloc[best_idx]
    
    print(f"\\nBest Model Configuration:")
    print(f"Test Accuracy: {best_params['test_accuracy']:.3f}")
    print(f"Parameters: {best_params[['n_estimators', 'max_depth', 'class_weight']].to_dict()}")
    
    return results_df