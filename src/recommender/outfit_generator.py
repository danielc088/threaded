"""
outfit generation pipeline for the wardrobe recommendation system
generates all possible outfit combinations and scores them using the trained model
provides random high-scoring outfits and targeted recommendations based on user selection
"""

import pandas as pd
import itertools
from pathlib import Path
from src.recommender.random_forest import OutfitRecommendationModel
from src.feature_extraction.engineered_features import create_prediction_features


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
        self.score_threshold = 0.5

        if self.model_path.exists():
            self.model.load_model(str(self.model_path))
        else:
            print(f"no trained model found at {model_path}")
            print("run main.py with TRAIN_MODEL=True first")

    def load_wardrobe_items(self):
        """load available clothing items from feature files"""
        cv_features = pd.read_csv("data/supporting/clothing_features.csv")
        genai_features = pd.read_csv("data/supporting/genai_features.csv")

        shirts = [item for item in cv_features['clothing_id'] if item.startswith('shirt_')]
        pants = [item for item in cv_features['clothing_id'] if item.startswith('pants_')]
        shoes = [item for item in cv_features['clothing_id'] if item.startswith('shoes_')]

        self.wardrobe_items = {'shirts': shirts, 'pants': pants, 'shoes': shoes}
        return self.wardrobe_items

    def generate_all_combinations(self):
        """create all possible shirt-pants-shoes combinations"""
        if self.wardrobe_items is None:
            self.load_wardrobe_items()

        combinations = list(itertools.product(
            self.wardrobe_items['shirts'],
            self.wardrobe_items['pants'],
            self.wardrobe_items['shoes']
        ))
        
        self.all_combinations = pd.DataFrame(combinations, columns=['shirt_id', 'pants_id', 'shoes_id'])
        return self.all_combinations

    def score_all_combinations(self):
        """score all outfit combinations using the trained model"""
        if not self.model.is_fitted:
            raise ValueError("model must be trained before scoring outfits")

        if self.all_combinations is None:
            self.generate_all_combinations()
        
        # use the modular feature pipeline to create features
        X = create_prediction_features(self.all_combinations)
        
        # get probability scores from model
        scores = self.model.predict_proba(X)

        # combine with outfit IDs and scores
        self.scored_combinations = self.all_combinations.copy()
        self.scored_combinations['recommendation_score'] = scores

        # filter for good outfits using model's threshold
        threshold_prob = self.model.threshold if hasattr(self.model, 'threshold') else self.score_threshold
        self.good_outfits = self.scored_combinations[
            self.scored_combinations['recommendation_score'] >= threshold_prob
        ].sort_values('recommendation_score', ascending=False)

        return self.scored_combinations

    def get_random_outfit(self):
        """get a random high-scoring outfit recommendation"""
        if self.good_outfits is None or len(self.good_outfits) == 0:
            self.score_all_combinations()

        if len(self.good_outfits) == 0:
            print("no high-scoring outfits found - try lowering the threshold")
            return None

        # pick a random outfit from the good ones
        random_outfit = self.good_outfits.sample(n=1).iloc[0]
        
        return {
            'shirt': random_outfit['shirt_id'],
            'pants': random_outfit['pants_id'],
            'shoes': random_outfit['shoes_id'],
            'score': random_outfit['recommendation_score']
        }

    def complete_outfit(self, item_type, item_id):
        """find best outfit combinations that include the specified item"""
        if self.scored_combinations is None:
            self.score_all_combinations()

        # filter combinations that include the specified item
        item_column = f"{item_type}_id"
        if item_column not in self.scored_combinations.columns:
            raise ValueError(f"invalid item type: {item_type}. must be 'shirt', 'pants', or 'shoes'")

        matching_outfits = self.scored_combinations[
            self.scored_combinations[item_column] == item_id
        ].sort_values('recommendation_score', ascending=False)

        if len(matching_outfits) == 0:
            print(f"no outfits found including {item_id}")
            return None

        # return top-scoring outfit with this item
        best_outfit = matching_outfits.iloc[0]
        
        return {
            'shirt': best_outfit['shirt_id'],
            'pants': best_outfit['pants_id'],
            'shoes': best_outfit['shoes_id'],
            'score': best_outfit['recommendation_score'],
            'fixed_item': f"{item_type}: {item_id}"
        }