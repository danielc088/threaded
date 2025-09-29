"""
database models and operations for threaded wardrobe system
handles all database crud operations including caching functionality
"""
import sqlite3
import hashlib
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class WardrobeDB:
    def __init__(self, db_path="data/database/threaded.db"):
        self.db_path = db_path
        
    def get_connection(self):
        """get database connection with foreign key support"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # enable column access by name
        return conn
    
    def create_outfit_hash(self, shirt_id: str, pants_id: str, shoes_id: str) -> str:
        """create unique hash for outfit combination"""
        outfit_str = f"{shirt_id}_{pants_id}_{shoes_id}"
        return hashlib.md5(outfit_str.encode()).hexdigest()
    
    # user operations
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = TRUE", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_users(self) -> List[Dict]:
        """get all active users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE is_active = TRUE ORDER BY display_name")
            return [dict(row) for row in cursor.fetchall()]
    
    # wardrobe operations
    def get_wardrobe_items(self, user_id: int, item_type: str = None) -> List[Dict]:
        """get wardrobe items for user, optionally filtered by type"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if item_type:
                cursor.execute("""
                    SELECT * FROM wardrobe_items 
                    WHERE user_id = ? AND item_type = ? AND is_active = TRUE
                    ORDER BY clothing_id
                """, (user_id, item_type))
            else:
                cursor.execute("""
                    SELECT * FROM wardrobe_items 
                    WHERE user_id = ? AND is_active = TRUE
                    ORDER BY item_type, clothing_id
                """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_wardrobe_item(self, user_id: int, clothing_id: str, item_type: str, 
                     file_path: str, cv_features: Dict = None) -> int:
        """add new wardrobe item or reactivate soft-deleted one"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # prepare cv features
            cv_data = cv_features or {}
            
            # check if item already exists (soft-deleted)
            cursor.execute("""
                SELECT id FROM wardrobe_items 
                WHERE user_id = ? AND clothing_id = ?
            """, (user_id, clothing_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # reactivate and update the existing item
                cursor.execute("""
                    UPDATE wardrobe_items 
                    SET is_active = TRUE,
                        item_type = ?,
                        file_path = ?,
                        dominant_color = ?,
                        secondary_color = ?,
                        avg_brightness = ?,
                        avg_saturation = ?,
                        avg_hue = ?,
                        color_variance = ?,
                        edge_density = ?,
                        texture_contrast = ?,
                        uploaded_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND clothing_id = ?
                """, (
                    item_type, file_path,
                    cv_data.get('dominant_color'),
                    cv_data.get('secondary_color'), 
                    cv_data.get('avg_brightness'),
                    cv_data.get('avg_saturation'),
                    cv_data.get('avg_hue'),
                    cv_data.get('color_variance'),
                    cv_data.get('edge_density'),
                    cv_data.get('texture_contrast'),
                    user_id, clothing_id
                ))
                return existing['id']
            else:
                # insert new item
                cursor.execute("""
                    INSERT INTO wardrobe_items 
                    (user_id, clothing_id, item_type, file_path, dominant_color, 
                     secondary_color, avg_brightness, avg_saturation, avg_hue, 
                     color_variance, edge_density, texture_contrast)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, clothing_id, item_type, file_path,
                    cv_data.get('dominant_color'),
                    cv_data.get('secondary_color'), 
                    cv_data.get('avg_brightness'),
                    cv_data.get('avg_saturation'),
                    cv_data.get('avg_hue'),
                    cv_data.get('color_variance'),
                    cv_data.get('edge_density'),
                    cv_data.get('texture_contrast')
                ))
                
                return cursor.lastrowid
    
    def delete_wardrobe_item(self, user_id: int, clothing_id: str):
        """mark wardrobe item as inactive (soft delete)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE wardrobe_items 
                SET is_active = FALSE 
                WHERE user_id = ? AND clothing_id = ?
            """, (user_id, clothing_id))
    
    # outfit rating operations
    def save_outfit_rating(self, user_id: int, shirt_id: str, pants_id: str, 
                          shoes_id: str, rating: int, source: str = 'manual', 
                          notes: str = None):
        """save or update outfit rating"""
        outfit_hash = self.create_outfit_hash(shirt_id, pants_id, shoes_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO outfit_ratings 
                (user_id, shirt_id, pants_id, shoes_id, outfit_hash, 
                 rating, rating_source, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, shirt_id, pants_id, shoes_id, outfit_hash, 
                  rating, source, notes))
    
    def get_outfit_rating(self, user_id: int, shirt_id: str, pants_id: str, 
                         shoes_id: str) -> Optional[Dict]:
        """get existing rating for outfit"""
        outfit_hash = self.create_outfit_hash(shirt_id, pants_id, shoes_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM outfit_ratings 
                WHERE user_id = ? AND outfit_hash = ?
            """, (user_id, outfit_hash))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_ratings(self, user_id: int) -> List[Dict]:
        """get all outfit ratings for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM outfit_ratings 
                WHERE user_id = ?
                ORDER BY rated_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # daily outfit operations
    def save_daily_outfit(self, user_id: int, outfit_date: str, shirt_id: str, 
                         pants_id: str, shoes_id: str, ml_score: float):
        """save daily outfit choice"""
        outfit_hash = self.create_outfit_hash(shirt_id, pants_id, shoes_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO daily_outfits 
                (user_id, outfit_date, shirt_id, pants_id, shoes_id, 
                 outfit_hash, ml_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, outfit_date, shirt_id, pants_id, shoes_id, 
                  outfit_hash, ml_score))
    
    def get_daily_outfit(self, user_id: int, outfit_date: str) -> Optional[Dict]:
        """get daily outfit for specific date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM daily_outfits 
                WHERE user_id = ? AND outfit_date = ?
            """, (user_id, outfit_date))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # user preferences
    def get_user_preferences(self, user_id: int) -> Dict:
        """get user preferences"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM user_preferences WHERE user_id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}
    
    def update_user_preferences(self, user_id: int, **preferences):
        """update user preferences"""
        if not preferences:
            return
        
        # build dynamic update query
        set_clause = ", ".join([f"{key} = ?" for key in preferences.keys()])
        values = list(preferences.values()) + [user_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE user_preferences 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, values)
    
    # colour palette operations
    def get_color_palettes(self, active_only: bool = True) -> List[Dict]:
        """get all colour palettes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("""
                    SELECT * FROM color_palettes 
                    WHERE is_active = TRUE
                    ORDER BY name
                """)
            else:
                cursor.execute("SELECT * FROM color_palettes ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def add_color_palette(self, name: str, colors: List[str], source: str = None):
        """add new colour palette"""
        # pad colours list to 5 items
        colors_padded = colors + [None] * (5 - len(colors))
        colors_padded = colors_padded[:5]  # take only first 5
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO color_palettes 
                (name, color_1, color_2, color_3, color_4, color_5, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, colors_padded[0], colors_padded[1], colors_padded[2], 
                  colors_padded[3], colors_padded[4], source))
    
    # genai features operations
    def add_genai_features(self, wardrobe_item_id: int, features: Dict):
        """add genai features for wardrobe item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO genai_features
                (wardrobe_item_id, pattern_type, has_graphic, style, fit_type,
                 formality_score, versatility_score, season_suitability, color_description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wardrobe_item_id,
                features.get('pattern_type'),
                features.get('has_graphic'),
                features.get('style'),
                features.get('fit_type'),
                features.get('formality_score'),
                features.get('versatility_score'),
                features.get('season_suitability'),
                features.get('color_description')
            ))
    
    def get_genai_features(self, user_id: int) -> List[Dict]:
        """get all genai features for user's items"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wi.clothing_id, gf.*
                FROM wardrobe_items wi
                JOIN genai_features gf ON wi.id = gf.wardrobe_item_id
                WHERE wi.user_id = ? AND wi.is_active = TRUE
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # outfit features caching operations
    def get_outfit_features(self, user_id: int, outfit_hashes: List[str], feature_version: str = "v1.0") -> List[Dict]:
        """get cached outfit features"""
        if not outfit_hashes:
            return []
            
        placeholders = ','.join(['?'] * len(outfit_hashes))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT outfit_hash, feature_blob FROM outfit_features
                WHERE user_id = ? AND feature_version = ?
                AND outfit_hash IN ({placeholders})
            """, [user_id, feature_version] + outfit_hashes)
            return [dict(row) for row in cursor.fetchall()]
    
    def save_outfit_features(self, user_id: int, outfit_hash: str, features, feature_version: str = "v1.0"):
        """cache outfit features"""
        feature_blob = pickle.dumps(features)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO outfit_features
                (user_id, outfit_hash, feature_blob, feature_version)
                VALUES (?, ?, ?, ?)
            """, (user_id, outfit_hash, feature_blob, feature_version))
    
    def clear_outfit_features(self, user_id: int, feature_version: str = None):
        """clear cached outfit features"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if feature_version:
                cursor.execute("""
                    DELETE FROM outfit_features 
                    WHERE user_id = ? AND feature_version = ?
                """, (user_id, feature_version))
            else:
                cursor.execute("""
                    DELETE FROM outfit_features WHERE user_id = ?
                """, (user_id,))
    
    # outfit predictions caching operations
    def get_outfit_predictions(self, user_id: int, outfit_hashes: List[str], model_version: str) -> List[Dict]:
        """get cached model predictions"""
        if not outfit_hashes:
            return []
            
        placeholders = ','.join(['?'] * len(outfit_hashes))
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT outfit_hash, predicted_rating FROM outfit_predictions
                WHERE user_id = ? AND model_version = ?
                AND outfit_hash IN ({placeholders})
            """, [user_id, model_version] + outfit_hashes)
            return [dict(row) for row in cursor.fetchall()]
    
    def save_outfit_prediction(self, user_id: int, outfit_hash: str, prediction: float, model_version: str):
        """cache model prediction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO outfit_predictions
                (user_id, outfit_hash, model_version, predicted_rating)
                VALUES (?, ?, ?, ?)
            """, (user_id, outfit_hash, model_version, prediction))
    
    def save_outfit_predictions_batch(self, user_id: int, predictions_dict: Dict[str, float], model_version: str):
        """cache multiple predictions efficiently"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            data = [(user_id, outfit_hash, model_version, float(prediction)) 
                   for outfit_hash, prediction in predictions_dict.items()]
            cursor.executemany("""
                INSERT OR REPLACE INTO outfit_predictions
                (user_id, outfit_hash, model_version, predicted_rating)
                VALUES (?, ?, ?, ?)
            """, data)
    
    def clear_outfit_predictions(self, user_id: int, model_version: str = None):
        """clear cached predictions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if model_version:
                cursor.execute("""
                    DELETE FROM outfit_predictions
                    WHERE user_id = ? AND model_version = ?
                """, (user_id, model_version))
            else:
                cursor.execute("""
                    DELETE FROM outfit_predictions WHERE user_id = ?
                """, (user_id,))
    
    # model version management operations
    def save_model_version(self, user_id: int, version: str, training_samples: int, 
                          accuracy_score: float = None, feature_count: int = None, 
                          model_path: str = None):
        """record new model training"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO model_versions
                (user_id, version, training_samples, accuracy_score, feature_count, model_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, version, training_samples, accuracy_score, feature_count, model_path))
    
    def get_active_model_version(self, user_id: int) -> Optional[Dict]:
        """get current active model version for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version, model_path, trained_at, training_samples, accuracy_score 
                FROM model_versions
                WHERE user_id = ? AND is_active = TRUE
                ORDER BY trained_at DESC LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_model_versions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """get model training history for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM model_versions
                WHERE user_id = ?
                ORDER BY trained_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def deactivate_old_models(self, user_id: int, keep_version: str):
        """deactivate all models except the specified version"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE model_versions SET is_active = FALSE
                WHERE user_id = ? AND version != ?
            """, (user_id, keep_version))
    
    def count_ratings_since_model(self, user_id: int, model_version: str) -> int:
        """count new ratings since a specific model was trained"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM outfit_ratings r
                JOIN model_versions m ON m.user_id = r.user_id
                WHERE r.user_id = ? AND m.version = ? AND r.rated_at > m.trained_at
            """, (user_id, model_version))
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    # utility methods
    def get_database_stats(self, user_id: int) -> Dict:
        """get comprehensive database statistics for user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # wardrobe items
            cursor.execute("""
                SELECT item_type, COUNT(*) as count 
                FROM wardrobe_items 
                WHERE user_id = ? AND is_active = TRUE
                GROUP BY item_type
            """, (user_id,))
            item_counts = {row['item_type']: row['count'] for row in cursor.fetchall()}
            
            # ratings
            cursor.execute("""
                SELECT COUNT(*) as total_ratings, AVG(rating) as avg_rating
                FROM outfit_ratings WHERE user_id = ?
            """, (user_id,))
            rating_stats = dict(cursor.fetchone())
            
            # cached features
            cursor.execute("""
                SELECT COUNT(*) as cached_features FROM outfit_features WHERE user_id = ?
            """, (user_id,))
            feature_cache = cursor.fetchone()['cached_features']
            
            # cached predictions
            cursor.execute("""
                SELECT COUNT(*) as cached_predictions FROM outfit_predictions WHERE user_id = ?
            """, (user_id,))
            prediction_cache = cursor.fetchone()['cached_predictions']
            
            # model info
            model_info = self.get_active_model_version(user_id)
            
            return {
                'wardrobe_items': item_counts,
                'total_items': sum(item_counts.values()),
                'total_ratings': int(rating_stats['total_ratings'] or 0),
                'avg_rating': float(rating_stats['avg_rating'] or 0),
                'cached_features': feature_cache,
                'cached_predictions': prediction_cache,
                'active_model': model_info['version'] if model_info else None,
                'model_accuracy': model_info['accuracy_score'] if model_info else None
            }
    
    def cleanup_old_cache(self, user_id: int, days_old: int = 30):
        """clean up old cached data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # clean old feature cache
            cursor.execute("""
                DELETE FROM outfit_features 
                WHERE user_id = ? AND created_at < datetime('now', '-{} days')
            """.format(days_old), (user_id,))
            features_deleted = cursor.rowcount
            
            # clean old prediction cache (keep only latest model)
            active_model = self.get_active_model_version(user_id)
            if active_model:
                cursor.execute("""
                    DELETE FROM outfit_predictions 
                    WHERE user_id = ? AND model_version != ?
                """, (user_id, active_model['version']))
                predictions_deleted = cursor.rowcount
            else:
                predictions_deleted = 0
            
            return {
                'features_deleted': features_deleted,
                'predictions_deleted': predictions_deleted
            }
        
    def reset_user_ratings_keep_cache(self, user_id: int):
        """one-time reset: delete ratings and models, keep feature cache for speed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM outfit_ratings WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM model_versions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM daily_outfits WHERE user_id = ?", (user_id,))
            # keep outfit_features and outfit_predictions for speed
            print(f"reset ratings for user {user_id}. kept feature cache for performance.")

    def precompute_all_outfit_features(self, user_id):
        """pre-compute features for all possible outfit combinations for this user"""

        # get all user's clothing items
        shirts = [item['clothing_id'] for item in self.get_wardrobe_items(user_id, 'shirt')]
        pants = [item['clothing_id'] for item in self.get_wardrobe_items(user_id, 'pants')]
        shoes = [item['clothing_id'] for item in self.get_wardrobe_items(user_id, 'shoes')]

        if not all([shirts, pants, shoes]):
            print("cannot precompute - missing items in some categories")
            return

        # generate all possible combinations
        import itertools
        all_combinations = list(itertools.product(shirts, pants, shoes))
        total_combinations = len(all_combinations)

        print(f"pre-computing features for {total_combinations} outfit combinations...")

        # create dataframe of all combinations
        combo_df = pd.DataFrame(all_combinations, columns=['shirt_id', 'pants_id', 'shoes_id'])
        combo_df['outfit_hash'] = (combo_df['shirt_id'] + '_' + combo_df['pants_id'] + '_' + combo_df['shoes_id'])

        # check which combinations already have cached features
        existing_hashes = set()
        cached_data = self.get_outfit_features(user_id, combo_df['outfit_hash'].tolist())
        for item in cached_data:
            existing_hashes.add(item['outfit_hash'])

        # only compute features for new combinations
        new_combos = combo_df[~combo_df['outfit_hash'].isin(existing_hashes)]

        if len(new_combos) == 0:
            print("all outfit features already cached")
            return

        print(f"computing features for {len(new_combos)} new combinations...")

        # use feature engine to compute features
        from src.feature_extraction.feature_engineering import OutfitFeatureEngine
        from pathlib import Path

        engine = OutfitFeatureEngine(user_id, self)

        # load existing transformer if it exists, otherwise create new one
        transformer_path = Path(f"models/user_{user_id}/feature_transformer.pkl")
        if transformer_path.exists():
            print("loading existing transformer...")
            engine.load_transformer(str(transformer_path))
            use_training_mode = False
        else:
            print("creating new transformer from all combinations...")
            use_training_mode = True

        # process all at once instead of batching
        try:
            if use_training_mode:
                # first time - create transformer from all combinations
                features_df = engine.prepare_outfit_features(new_combos, for_training=True)
                # save the transformer for reuse
                engine.save_transformer(str(transformer_path))
            else:
                # use existing transformer
                features_df = engine.prepare_outfit_features(new_combos, for_training=False)

            # cache all features
            print(f"caching {len(new_combos)} feature sets...")
            for idx, (_, row) in enumerate(new_combos.iterrows()):
                outfit_hash = row['outfit_hash']
                features = features_df.iloc[idx].values
                self.save_outfit_features(user_id, outfit_hash, features)

                if (idx + 1) % 100 == 0:
                    print(f"cached {idx + 1}/{len(new_combos)} combinations")

            print(f"pre-computed and cached features for all {total_combinations} outfit combinations")

        except Exception as e:
            print(f"error processing combinations: {e}")
            import traceback
            traceback.print_exc()

    def rebuild_user_feature_cache(self, user_id):
        """rebuild entire feature cache for user (use when feature engineering changes)"""

        # clear existing cache
        self.clear_outfit_features(user_id)

        # recompute all features
        self.precompute_all_outfit_features(user_id)