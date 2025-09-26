"""
outfit generation pipeline for the wardrobe recommendation system
generates all possible outfit combinations and scores them using the trained model
provides random high-scoring outfits and targeted recommendations based on user selection
"""

import pandas as pd
import numpy as np
import itertools
import pickle
from pathlib import Path
from src.recommender.random_forest import OutfitRecommendationModel
from src.recommender.test_train_prep import prepare_training_data


class OutfitGenerator:
    """generates and scores outfit combinations from available wardrobe items"""
    
    def __init__(self, model_path="models/outfit_recommender.pkl"):
        """initialize with trained recommendation model"""
        self.model = OutfitRecommendationModel()
        self.model_path = Path(model_path)
        self.wardrobe_items = None
        self.all_combinations = None
        self.scored_combinations = None
        self.good_outfits = None
        self.score_threshold = 4.0
        
        # load model if it exists
        if self.model_path.exists():
            self.model.load_model(str(self.model_path))
            print(f"Loaded trained model from {model_path}")
        else:
            print(f"No trained model found at {model_path}")
            print("Run main.py with TRAIN_MODEL=True first")
    
    def load_wardrobe_items(self):
        """load available clothing items from the feature files"""
        
        cv_features = pd.read_csv("data/supporting/clothing_features.csv")
        genai_features = pd.read_csv("data/supporting/genai_features.csv")
        
        # get unique clothing IDs by category
        shirts = [item for item in cv_features['clothing_id'] if item.startswith('shirt_')]
        pants = [item for item in cv_features['clothing_id'] if item.startswith('pants_')]
        shoes = [item for item in cv_features['clothing_id'] if item.startswith('shoes_')]
        
        self.wardrobe_items = {
            'shirts': shirts,
            'pants': pants, 
            'shoes': shoes
        }
        
        print(f"Loaded wardrobe: {len(shirts)} shirts, {len(pants)} pants, {len(shoes)} shoes")
        return self.wardrobe_items
    
    def generate_all_combinations(self):
        """create all possible shirt-pants-shoes combinations"""
        
        if self.wardrobe_items is None:
            self.load_wardrobe_items()
        
        # generate all combinations
        combinations = list(itertools.product(
            self.wardrobe_items['shirts'],
            self.wardrobe_items['pants'], 
            self.wardrobe_items['shoes']
        ))
        
        # convert to dataframe format expected by the model
        self.all_combinations = pd.DataFrame(combinations, columns=['shirt_id', 'pants_id', 'shoes_id'])
        
        print(f"Generated {len(self.all_combinations)} possible outfit combinations")
        return self.all_combinations
    
    def prepare_combinations_for_scoring(self):
        """apply the same feature engineering pipeline used in training"""
        
        if self.all_combinations is None:
            self.generate_all_combinations()
        
        print("Preparing combinations for scoring...")
        
        # load feature data
        cv_features = pd.read_csv("data/supporting/clothing_features.csv")
        genai_features = pd.read_csv("data/supporting/genai_features.csv")
        
        # merge features for each clothing item
        df = self.all_combinations.copy()
        
        # merge CV features
        for item in ["shirt", "pants", "shoes"]:
            df = df.merge(
                cv_features.add_prefix(f"{item}_"),
                left_on=f"{item}_id",
                right_on=f"{item}_clothing_id",
                how="left"
            ).drop(columns=[f"{item}_clothing_id"])
        
        # merge GenAI features
        for item in ["shirt", "pants", "shoes"]:
            df = df.merge(
                genai_features.add_prefix(f"{item}_"),
                left_on=f"{item}_id",
                right_on=f"{item}_clothing_id",
                how="left"
            ).drop(columns=[f"{item}_clothing_id"])
        
        # convert boolean graphics to int
        for item in ["shirt", "pants", "shoes"]:
            col = f"{item}_has_graphic"
            if col in df.columns:
                df[col] = df[col].astype(int)
        
        return df
    
    def apply_feature_engineering(self, df):
        """apply the same feature engineering used during training"""
        
        # this is complex - we need to recreate the exact same features
        # for now, we'll use a simpler approach and just use the core features
        # in a production system, you'd want to modularize the feature engineering
        
        print("Applying feature engineering...")
        
        # for now, let's create a minimal feature set that matches training
        # drop ID columns and dominant colour strings
        feature_cols = [col for col in df.columns if not col.endswith('_id') and 
                       not col.endswith('dominant_colours')]
        
        return df[feature_cols]
    
    def score_all_combinations(self):
        """score all outfit combinations using the trained model"""
        
        if not self.model.is_fitted:
            raise ValueError("Model must be trained before scoring outfits")
        
        if self.all_combinations is None:
            self.generate_all_combinations()
        
        print("Scoring outfit combinations using trained model...")
        
        # use the modular feature pipeline
        from src.feature_extraction.engineered_features import create_prediction_features        
        
        # create features using the same pipeline as training
        X = create_prediction_features(self.all_combinations)
        
        # get probability scores from the model
        scores = self.model.predict_proba(X)
        
        # combine with outfit IDs and scores
        self.scored_combinations = self.all_combinations.copy()
        self.scored_combinations['recommendation_score'] = scores
        
        # filter for good outfits using model's threshold
        threshold_prob = self.model.threshold if hasattr(self.model, 'threshold') else 0.5
        self.good_outfits = self.scored_combinations[
            self.scored_combinations['recommendation_score'] >= threshold_prob
        ].sort_values('recommendation_score', ascending=False)
        
        print(f"Found {len(self.good_outfits)} high-scoring outfit combinations (threshold: {threshold_prob})")
        return self.scored_combinations
    
    def get_random_outfit(self):
        """get a random high-scoring outfit recommendation"""
        
        if self.good_outfits is None or len(self.good_outfits) == 0:
            self.score_all_combinations()
        
        if len(self.good_outfits) == 0:
            print("No high-scoring outfits found. Try lowering the threshold.")
            return None
        
        # pick a random outfit from the good ones
        random_outfit = self.good_outfits.sample(n=1).iloc[0]
        
        result = {
            'shirt': random_outfit['shirt_id'],
            'pants': random_outfit['pants_id'], 
            'shoes': random_outfit['shoes_id'],
            'score': random_outfit['recommendation_score']
        }
        
        return result
    
    def complete_outfit(self, item_type, item_id):
        """find best outfit combinations that include the specified item"""
        
        if self.scored_combinations is None:
            self.score_all_combinations()
        
        # filter combinations that include the specified item
        item_column = f"{item_type}_id"
        if item_column not in self.scored_combinations.columns:
            raise ValueError(f"Invalid item type: {item_type}. Must be 'shirt', 'pants', or 'shoes'")
        
        matching_outfits = self.scored_combinations[
            self.scored_combinations[item_column] == item_id
        ].sort_values('recommendation_score', ascending=False)
        
        if len(matching_outfits) == 0:
            print(f"No outfits found including {item_id}")
            return None
        
        # return top-scoring outfit with this item
        best_outfit = matching_outfits.iloc[0]
        
        result = {
            'shirt': best_outfit['shirt_id'],
            'pants': best_outfit['pants_id'],
            'shoes': best_outfit['shoes_id'],
            'score': best_outfit['recommendation_score'],
            'fixed_item': f"{item_type}: {item_id}"
        }
        
        return result
    
    def get_top_outfits(self, n=10):
        """get the top N highest-scoring outfit recommendations"""
        
        if self.scored_combinations is None:
            self.score_all_combinations()
        
        top_outfits = self.scored_combinations.nlargest(n, 'recommendation_score')
        
        results = []
        for _, outfit in top_outfits.iterrows():
            results.append({
                'shirt': outfit['shirt_id'],
                'pants': outfit['pants_id'],
                'shoes': outfit['shoes_id'],
                'score': outfit['recommendation_score']
            })
        
        return results
    
    def print_outfit(self, outfit_dict):
        """nicely format an outfit recommendation for display"""
        
        if outfit_dict is None:
            print("No outfit to display")
            return
        
        print("=" * 50)
        print("OUTFIT RECOMMENDATION")
        print("=" * 50)
        print(f"Shirt: {outfit_dict['shirt']}")
        print(f"Pants: {outfit_dict['pants']}")
        print(f"Shoes: {outfit_dict['shoes']}")
        print(f"Confidence Score: {outfit_dict['score']:.3f}")
        
        if 'fixed_item' in outfit_dict:
            print(f"Built around: {outfit_dict['fixed_item']}")
        
        print("=" * 50)


def demo_outfit_generator():
    """demonstrate the outfit generator functionality"""
    
    print("Initializing Outfit Generator...")
    generator = OutfitGenerator()
    
    # test random outfit
    print("\n1. Random High-Scoring Outfit:")
    random_outfit = generator.get_random_outfit()
    generator.print_outfit(random_outfit)
    
    # test outfit completion
    print("\n2. Complete Outfit with Specific Item:")
    if generator.wardrobe_items and len(generator.wardrobe_items['shirts']) > 0:
        first_shirt = generator.wardrobe_items['shirts'][0]
        shirt_outfit = generator.complete_outfit('shirt', first_shirt)
        generator.print_outfit(shirt_outfit)
    
    # test top outfits
    print("\n3. Top 5 Outfit Recommendations:")
    top_outfits = generator.get_top_outfits(n=5)
    for i, outfit in enumerate(top_outfits, 1):
        print(f"\n#{i}: {outfit['shirt']} + {outfit['pants']} + {outfit['shoes']} (Score: {outfit['score']:.3f})")