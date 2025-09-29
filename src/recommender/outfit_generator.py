"""
database-enabled outfit generation pipeline with caching
uses cached features and predictions for faster recommendations
basically the main engine that picks what you should wear today
"""

import pandas as pd
import itertools
import numpy as np
from pathlib import Path
import sys
import os

# add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.recommender.random_forest import get_user_model

class CachedOutfitGenerator:
    """generates and scores outfit combinations with caching for speed"""

    def __init__(self, user_id, db):
        """initialise with user id and database connection"""
        self.user_id = user_id
        self.db = db
        self.wardrobe_items = None
        self.all_combinations = None
        self.scored_combinations = None
        self.good_outfits = None
        
        # get user preferences from database
        prefs = self.db.get_user_preferences(user_id)
        self.score_threshold = prefs.get('score_threshold', 0.5) if prefs else 0.5
        
        # load user's model
        self.model = get_user_model(user_id, db, auto_train=True)
        if not self.model:
            print(f"warning: no model available for user {user_id}")

    def load_wardrobe_items(self):
        """load available clothing items from database"""
        
        # get items from database
        shirts = self.db.get_wardrobe_items(self.user_id, 'shirt')
        pants = self.db.get_wardrobe_items(self.user_id, 'pants')  
        shoes = self.db.get_wardrobe_items(self.user_id, 'shoes')

        # extract clothing ids
        self.wardrobe_items = {
            'shirt': [item['clothing_id'] for item in shirts],
            'pants': [item['clothing_id'] for item in pants],
            'shoes': [item['clothing_id'] for item in shoes]
        }
        
        return self.wardrobe_items

    def generate_all_combinations(self):
        """create all possible outfit combinations"""
        if self.wardrobe_items is None:
            self.load_wardrobe_items()

        if not all(self.wardrobe_items.values()):
            print("warning: missing items in some categories")
            return pd.DataFrame()

        combinations = list(itertools.product(
            self.wardrobe_items['shirt'],
            self.wardrobe_items['pants'],
            self.wardrobe_items['shoes']
        ))
        
        self.all_combinations = pd.DataFrame(combinations, columns=['shirt_id', 'pants_id', 'shoes_id'])
        
        # add outfit hashes for caching
        self.all_combinations['outfit_hash'] = (
            self.all_combinations['shirt_id'] + '_' + 
            self.all_combinations['pants_id'] + '_' + 
            self.all_combinations['shoes_id']
        )
                
        return self.all_combinations

    def score_all_combinations_cached(self, use_existing_ratings=True):
        """score all outfit combinations using coalesce: user_rating > cached_prediction > new_ml_prediction > random"""
        if self.all_combinations is None:
            self.generate_all_combinations()

        if len(self.all_combinations) == 0:
            print("no outfit combinations to score")
            return pd.DataFrame()

        # initialise scored combinations
        self.scored_combinations = self.all_combinations.copy()
        self.scored_combinations['recommendation_score'] = 0.0
        self.scored_combinations['score_source'] = 'none'

        # priority 1: user ratings (highest priority - ground truth)
        user_rated_count = 0
        if use_existing_ratings:

            for idx, row in self.scored_combinations.iterrows():
                existing_rating = self.db.get_outfit_rating(
                    self.user_id, row['shirt_id'], row['pants_id'], row['shoes_id']
                )

                if existing_rating:
                    # convert 1-5 scale to 0-1 probability
                    user_score = existing_rating['rating'] / 5.0
                    self.scored_combinations.loc[idx, 'recommendation_score'] = user_score
                    self.scored_combinations.loc[idx, 'score_source'] = f"user_rating_{existing_rating['rating']}"
                    user_rated_count += 1

            print(f"found {user_rated_count} user ratings")

        # priority 2: cached ml predictions (for unrated items)
        unrated_mask = self.scored_combinations['score_source'] == 'none'
        unrated_hashes = self.scored_combinations[unrated_mask]['outfit_hash'].tolist()

        cached_predictions_count = 0
        if unrated_hashes and self.model and hasattr(self.model, 'training_history'):
            # get current model version
            model_info = self.db.get_active_model_version(self.user_id)
            if model_info:
                model_version = model_info['version']

                # get cached predictions
                cached_preds = self.db.get_outfit_predictions(self.user_id, unrated_hashes, model_version)
                cached_dict = {pred['outfit_hash']: pred['predicted_rating'] for pred in cached_preds}

                # apply cached predictions
                for idx, row in self.scored_combinations.iterrows():
                    if row['outfit_hash'] in cached_dict and self.scored_combinations.loc[idx, 'score_source'] == 'none':
                        self.scored_combinations.loc[idx, 'recommendation_score'] = cached_dict[row['outfit_hash']]
                        self.scored_combinations.loc[idx, 'score_source'] = 'cached_ml'
                        cached_predictions_count += 1

        # priority 3: compute new ml predictions (for remaining unrated/uncached items)
        still_unrated_mask = self.scored_combinations['score_source'] == 'none'
        still_unrated_count = still_unrated_mask.sum()

        if still_unrated_count > 0:
            if self.model and self.model.is_fitted:
                try:
                    unrated_combinations = self.scored_combinations[still_unrated_mask][
                        ['shirt_id', 'pants_id', 'shoes_id']
                    ].copy()

                    # use the feature engine directly to compute missing features on-demand
                    from src.feature_extraction.feature_engineering import OutfitFeatureEngine
                    engine = OutfitFeatureEngine(self.user_id, self.db)
                    
                    # load transformer if it exists
                    transformer_path = Path(f"models/user_{self.user_id}/feature_transformer.pkl")
                    if transformer_path.exists():
                        engine.load_transformer(str(transformer_path))
                    
                    # this will use cached features when available and compute missing ones
                    X = engine.prepare_outfit_features(unrated_combinations, for_training=False)

                    # get ml predictions
                    ml_scores = self.model.predict_proba(X)

                    # assign ml scores
                    self.scored_combinations.loc[still_unrated_mask, 'recommendation_score'] = ml_scores
                    self.scored_combinations.loc[still_unrated_mask, 'score_source'] = 'new_ml'

                    # cache the new predictions
                    if hasattr(self.model, 'training_history'):
                        model_info = self.db.get_active_model_version(self.user_id)
                        if model_info:
                            model_version = model_info['version']
                            new_predictions = {}

                            for idx, score in zip(self.scored_combinations[still_unrated_mask].index, ml_scores):
                                outfit_hash = self.scored_combinations.loc[idx, 'outfit_hash']
                                new_predictions[outfit_hash] = float(score)

                            # batch save predictions
                            self.db.save_outfit_predictions_batch(self.user_id, new_predictions, model_version)

                except Exception as e:
                    print(f"error generating ml features: {e}")
                    print("using random scores as fallback")
                    random_scores = np.random.uniform(0.3, 0.7, still_unrated_count)
                    self.scored_combinations.loc[still_unrated_mask, 'recommendation_score'] = random_scores
                    self.scored_combinations.loc[still_unrated_mask, 'score_source'] = 'random'
            else:
                print(f"no trained model available, using random scores for {still_unrated_count} combinations")
                random_scores = np.random.uniform(0.3, 0.7, still_unrated_count)
                self.scored_combinations.loc[still_unrated_mask, 'recommendation_score'] = random_scores
                self.scored_combinations.loc[still_unrated_mask, 'score_source'] = 'random'

        # filter for good outfits based on score and source
        threshold_prob = getattr(self.model, 'threshold', self.score_threshold) if self.model else self.score_threshold

        # be more lenient with user ratings since they're ground truth
        def is_good_outfit(row):
            score = row['recommendation_score']
            source = row['score_source']

            if source.startswith('user_rating'):
                # user rated 4 or 5 stars (≥0.8 on 0-1 scale)
                return score >= 0.8
            else:
                # use model threshold for ml predictions
                return score >= threshold_prob

        self.good_outfits = self.scored_combinations[
            self.scored_combinations.apply(is_good_outfit, axis=1)
        ].sort_values('recommendation_score', ascending=False)

        # print scoring summary
        source_counts = self.scored_combinations['score_source'].value_counts()
        for source, count in source_counts.items():
            if source.startswith('user_rating'):
                rating = source.split('_')[-1]
            else:
                None

        return self.scored_combinations

    def get_random_outfit(self, use_existing_ratings=False, exploration_rate=0.05):
        """get outfit recommendation with optional random exploration"""
        import random

        # 5% chance for completely random exploration
        if random.random() < exploration_rate:
            return self.get_exploration_outfit()

        # 95% chance for normal ml-based recommendation
        return self.get_ml_recommended_outfit(use_existing_ratings)

    def get_exploration_outfit(self):
        """get completely random outfit for exploration (breaking filter bubble)"""
        if not hasattr(self, 'wardrobe_items') or self.wardrobe_items is None:
            self.load_wardrobe_items()

        if not all(self.wardrobe_items.values()):
            print("warning: missing items in some categories")
            return None

        # pick completely random items
        import random
        random_shirt = random.choice(self.wardrobe_items['shirt'])
        random_pants = random.choice(self.wardrobe_items['pants'])  
        random_shoes = random.choice(self.wardrobe_items['shoes'])

        return {
            'shirt': random_shirt,
            'pants': random_pants,
            'shoes': random_shoes,
            'score': 0.5,  # neutral score since it's random
            'score_source': 'exploration_random'
        }

    def get_ml_recommended_outfit(self, use_existing_ratings=False):
        """get ml-based recommendation (original logic)"""
        if self.good_outfits is None or len(self.good_outfits) == 0:
            self.score_all_combinations_cached(use_existing_ratings=use_existing_ratings)

        if len(self.good_outfits) == 0:
            print("no high-scoring outfits found - try lowering the threshold")
            # return a random combination as fallback
            if len(self.scored_combinations) > 0:
                random_outfit = self.scored_combinations.sample(n=1).iloc[0]
                print(f"returning random outfit with score {random_outfit['recommendation_score']:.2f}")
            else:
                return None
        else:
            # pick a random outfit from the good ones
            random_outfit = self.good_outfits.sample(n=1).iloc[0]

        return {
            'shirt': random_outfit['shirt_id'],
            'pants': random_outfit['pants_id'],
            'shoes': random_outfit['shoes_id'],
            'score': random_outfit['recommendation_score'],
            'score_source': random_outfit['score_source']
        }

    def complete_outfit(self, item_type, item_id, use_existing_ratings=False, exploration_rate=0.05):
        """find best outfit combinations that include the specified item with exploration"""
        import random

        # 5% chance for exploration even with fixed item
        if random.random() < exploration_rate:
            return self.get_exploration_outfit_with_fixed_item(item_type, item_id)

        # 95% chance for normal ml-based completion
        return self.get_ml_outfit_completion(item_type, item_id, use_existing_ratings)

    def get_exploration_outfit_with_fixed_item(self, item_type, item_id):
        """random exploration while keeping one item fixed"""
        if not hasattr(self, 'wardrobe_items') or self.wardrobe_items is None:
            self.load_wardrobe_items()

        import random

        # start with the fixed item
        outfit = {'shirt': None, 'pants': None, 'shoes': None}
        outfit[item_type] = item_id

        # randomly pick the other items
        for other_type in ['shirt', 'pants', 'shoes']:
            if other_type != item_type:
                outfit[other_type] = random.choice(self.wardrobe_items[other_type])

        return {
            'shirt': outfit['shirt'],
            'pants': outfit['pants'],
            'shoes': outfit['shoes'],
            'score': 0.5,
            'score_source': 'exploration_with_fixed',
            'fixed_item': f"{item_id}"
        }

    def get_ml_outfit_completion(self, item_type, item_id, use_existing_ratings=False):
        """ml-based outfit completion (original logic)"""
        if self.scored_combinations is None:
            self.score_all_combinations_cached(use_existing_ratings=use_existing_ratings)

        if len(self.scored_combinations) == 0:
            return None

        # filter combinations that include the specified item
        item_column = f"{item_type}_id"
        if item_column not in self.scored_combinations.columns:
            raise ValueError(f"invalid item type: {item_type}. must be 'shirt', 'pants', or 'shoes'")

        threshold_prob = getattr(self.model, 'threshold', self.score_threshold) if self.model else self.score_threshold

        matching_outfits = self.scored_combinations[
            (self.scored_combinations[item_column] == item_id) &
            (self.scored_combinations['recommendation_score'] >= threshold_prob)
        ]

        if len(matching_outfits) == 0:
            print(f"no high-scoring outfits found including {item_id}")
            # try with all combinations including this item
            all_matching = self.scored_combinations[
                self.scored_combinations[item_column] == item_id
            ]
            if len(all_matching) > 0:
                best_outfit = all_matching.nlargest(1, 'recommendation_score').iloc[0]
                print(f"returning best available option with score {best_outfit['recommendation_score']:.2f}")
            else:
                return None
        else:
            # return random outfit from high-scoring matches
            best_outfit = matching_outfits.sample(n=1).iloc[0]

        return {
            'shirt': best_outfit['shirt_id'],
            'pants': best_outfit['pants_id'],
            'shoes': best_outfit['shoes_id'],
            'score': best_outfit['recommendation_score'],
            'score_source': best_outfit['score_source'],
            'fixed_item': f"{item_id}"
        }

    def save_outfit_rating(self, outfit_dict, rating, source='manual', notes=None):
        """save user rating for an outfit to database"""
        self.db.save_outfit_rating(
            self.user_id,
            outfit_dict['shirt'],
            outfit_dict['pants'], 
            outfit_dict['shoes'],
            rating,
            source,
            notes
        )

        # invalidate cached scores so they get recalculated
        self.invalidate_cache()

        # also clear prediction cache since ratings changed
        self.db.clear_outfit_predictions(self.user_id)

    def invalidate_cache(self):
        """clear cached combinations and scores to force regeneration"""
        self.scored_combinations = None
        self.good_outfits = None
        # note: we keep database caches - those are managed by the incremental learner
    
    def clear_all_caches(self):
        """clear both memory and database caches (for debugging)"""
        self.invalidate_cache()
        self.db.clear_outfit_predictions(self.user_id)
        self.db.clear_outfit_features(self.user_id)
        print("cleared all caches including database caches")

    def get_cache_stats(self):
        """get statistics about cached data"""
        stats = self.db.get_database_stats(self.user_id)
        return {
            'cached_features': stats['cached_features'],
            'cached_predictions': stats['cached_predictions'], 
            'active_model': stats['active_model'],
            'total_combinations': len(self.all_combinations) if self.all_combinations is not None else 0,
            'scored_combinations': len(self.scored_combinations) if self.scored_combinations is not None else 0,
            'good_outfits': len(self.good_outfits) if self.good_outfits is not None else 0
        }

    def get_user_stats(self):
        """get statistics about user's wardrobe and ratings"""
        return self.db.get_database_stats(self.user_id)

    def save_daily_outfit(self, outfit_dict, date_str):
        """save outfit choice as daily outfit"""
        self.db.save_daily_outfit(
            self.user_id,
            date_str,
            outfit_dict['shirt'],
            outfit_dict['pants'],
            outfit_dict['shoes'],
            outfit_dict['score']
        )
        
        print(f"saved daily outfit for {date_str}")

    def get_daily_outfit(self, date_str):
        """get daily outfit for specific date"""
        daily_outfit = self.db.get_daily_outfit(self.user_id, date_str)
        
        if daily_outfit:
            return {
                'shirt': daily_outfit['shirt_id'],
                'pants': daily_outfit['pants_id'],
                'shoes': daily_outfit['shoes_id'],
                'score': daily_outfit['ml_score'],
                'user_rating': daily_outfit['user_rating'],
                'date': daily_outfit['outfit_date']
            }
        
        return None


# keep backward compatibility
OutfitGenerator = CachedOutfitGenerator