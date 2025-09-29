"""
database-enabled feature engineering pipeline for outfit recommendation
creates ml-ready features from wardrobe items and color palettes
"""

import pandas as pd
import numpy as np
import warnings
import pickle
from pathlib import Path
from matplotlib.colors import to_rgb
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from sklearn.preprocessing import PolynomialFeatures

# suppress pandas future warnings
warnings.filterwarnings('ignore', category=FutureWarning)


class OutfitFeatureEngine:
    """database-enabled feature engineering for outfit combinations"""
    
    def __init__(self, user_id, db):
        """initialize with user id and database connection"""
        self.user_id = user_id
        self.db = db
        self.poly_transformer = None
        self.feature_names = None
    
    def get_clothing_features_from_db(self, outfit_df):
        """merge cv and genai features for each clothing item from database"""
        
        # get wardrobe items from database
        wardrobe_items = self.db.get_wardrobe_items(self.user_id)
        items_df = pd.DataFrame(wardrobe_items)
        
        # get genai features from database
        genai_data = self.db.get_genai_features(self.user_id)
        genai_df = pd.DataFrame(genai_data) if genai_data else pd.DataFrame()
        
        # merge cv features for each item type
        result_df = outfit_df.copy()
        
        for item_type in ["shirt", "pants", "shoes"]:
            item_col = f"{item_type}_id"
            
            # merge cv features (from wardrobe_items table)
            cv_cols = [
                'clothing_id', 'dominant_color', 'secondary_color', 'avg_brightness',
                'avg_saturation', 'avg_hue', 'color_variance', 'edge_density', 'texture_contrast'
            ]
            
            item_cv = items_df[items_df['item_type'] == item_type][cv_cols].copy()
            item_cv = item_cv.add_prefix(f"{item_type}_")
            
            result_df = result_df.merge(
                item_cv,
                left_on=item_col,
                right_on=f"{item_type}_clothing_id",
                how="left"
            ).drop(columns=[f"{item_type}_clothing_id"])
            
            # merge genai features if available
            if not genai_df.empty:
                genai_cols = [
                    'clothing_id', 'pattern_type', 'has_graphic', 'style', 'fit_type',
                    'formality_score', 'versatility_score', 'season_suitability', 'color_description'
                ]
                
                item_genai = genai_df[genai_cols].copy()
                item_genai = item_genai.add_prefix(f"{item_type}_")
                
                result_df = result_df.merge(
                    item_genai,
                    left_on=item_col,
                    right_on=f"{item_type}_clothing_id",
                    how="left"
                ).drop(columns=[f"{item_type}_clothing_id"])
        
        # ensure color columns stay as strings to prevent pandas conversion errors
        color_cols = [
            'shirt_dominant_color', 'shirt_secondary_color',
            'pants_dominant_color', 'pants_secondary_color', 
            'shoes_dominant_color', 'shoes_secondary_color'
        ]
        
        for col in color_cols:
            if col in result_df.columns:
                result_df[col] = result_df[col].astype(str)
        
        return result_df
    
    def create_categorical_features(self, df):
        """one-hot encode categorical genai features"""
        
        categorical_cols = []
        for item in ["shirt", "pants", "shoes"]:
            for col in ["pattern_type", "style", "fit_type", "season_suitability"]:
                cat_col = f"{item}_{col}"
                if cat_col in df.columns:
                    categorical_cols.append(cat_col)
        
        if categorical_cols:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=FutureWarning)
                df = pd.get_dummies(df, columns=categorical_cols, dummy_na=True)
        
        return df
    
    def hex_to_lab(self, hex_code):
        """convert hex color to lab color space"""
        if pd.isna(hex_code) or not hex_code or hex_code == 'nan':
            return None
        try:
            rgb = sRGBColor(*to_rgb(hex_code), is_upscaled=False)
            return convert_color(rgb, LabColor)
        except:
            return None
    
    def create_color_harmony_features(self, df):
        """calculate color harmony metrics using dominant colors from database"""
        
        def calculate_color_distance(row):
            """measure color similarity between shirt, pants, shoes"""
            colors = []
            
            for item in ['shirt', 'pants', 'shoes']:
                color_col = f'{item}_dominant_color'
                
                if color_col in row and pd.notna(row[color_col]) and row[color_col] != 'nan':
                    try:
                        lab_color = self.hex_to_lab(row[color_col])
                        if lab_color:
                            colors.append(lab_color)
                    except Exception:
                        continue
            
            if len(colors) < 2:
                return 0.0
            
            # calculate all pairwise distances
            distances = []
            for i in range(len(colors)):
                for j in range(i+1, len(colors)):
                    try:
                        dist = delta_e_cie2000(colors[i], colors[j])
                        distances.append(float(dist))
                    except Exception:
                        continue
            
            return np.mean(distances) if distances else 0.0
        
        df['overall_color_harmony'] = df.apply(calculate_color_distance, axis=1)
        return df
    
    def create_lab_color_features(self, df):
        """extract lab color values for dominant colors from database"""
        
        def extract_lab_values(hex_color):
            """get l*a*b* values for hex color"""
            try:
                lab_color = self.hex_to_lab(hex_color)
                if lab_color:
                    return pd.Series([lab_color.lab_l, lab_color.lab_a, lab_color.lab_b])
                else:
                    return pd.Series([50.0, 0.0, 0.0])
            except:
                return pd.Series([50.0, 0.0, 0.0])
        
        for item in ["shirt", "pants", "shoes"]:
            color_col = f"{item}_dominant_color"
            if color_col in df.columns:
                df[[f"{item}_L", f"{item}_a", f"{item}_b"]] = \
                    df[color_col].apply(extract_lab_values)
        
        return df
    
    def create_style_compatibility_features(self, df):
        """create features based on style compatibility from genai data"""
        
        # average formality score across outfit
        formality_cols = [f"{item}_formality_score" for item in ["shirt", "pants", "shoes"]]
        existing_formality = [col for col in formality_cols if col in df.columns]
        if existing_formality:
            df['avg_formality'] = df[existing_formality].mean(axis=1)
            df['formality_variance'] = df[existing_formality].var(axis=1)
        
        # average versatility score
        versatility_cols = [f"{item}_versatility_score" for item in ["shirt", "pants", "shoes"]]
        existing_versatility = [col for col in versatility_cols if col in df.columns]
        if existing_versatility:
            df['avg_versatility'] = df[existing_versatility].mean(axis=1)
        
        return df
    
    def create_palette_features(self, df):
        """find closest color palette for each outfit using database colors"""
        
        # get color palettes from database
        palettes = self.db.get_color_palettes()
        
        if not palettes:
            df['palette_distance'] = 0.0
            return df
        
        def find_closest_palette(row):
            """find best matching palette for this outfit"""
            outfit_colors = []
            
            for item in ['shirt', 'pants', 'shoes']:
                color_col = f"{item}_dominant_color"
                if color_col in row and pd.notna(row[color_col]) and row[color_col] != 'nan':
                    outfit_colors.append(row[color_col])
            
            if not outfit_colors:
                return pd.Series([None, 0.0])
            
            best_palette, best_distance = None, float('inf')
            
            for palette in palettes:
                # extract palette colors (skip none values)
                palette_colors = []
                for i in range(1, 6):
                    color = palette.get(f'color_{i}')
                    if color:
                        palette_colors.append(color)
                
                if not palette_colors:
                    continue
                
                # calculate average distance from outfit colors to palette
                distances = []
                for outfit_color in outfit_colors:
                    outfit_lab = self.hex_to_lab(outfit_color)
                    if outfit_lab:
                        palette_distances = []
                        for palette_color in palette_colors:
                            palette_lab = self.hex_to_lab(palette_color)
                            if palette_lab:
                                try:
                                    dist = float(delta_e_cie2000(outfit_lab, palette_lab))
                                    palette_distances.append(dist)
                                except:
                                    continue
                        if palette_distances:
                            distances.append(min(palette_distances))
                
                if distances:
                    avg_distance = np.mean(distances)
                    if avg_distance < best_distance:
                        best_distance = avg_distance
                        best_palette = palette['name']
            
            return pd.Series([best_palette, best_distance if best_distance != float('inf') else 0.0])
        
        df[['closest_palette', 'palette_distance']] = df.apply(find_closest_palette, axis=1)
        
        # create one-hot encoded palette features
        if 'closest_palette' in df.columns:
            palette_dummies = pd.get_dummies(df['closest_palette'], prefix='palette')
            df = pd.concat([df, palette_dummies], axis=1)
        
        return df
    
    def create_polynomial_features(self, X_train, X_test=None, degree=3, fit=True):
        """create polynomial interaction features"""

        # identify numeric columns
        numeric_cols = X_train.select_dtypes(include=['int64', 'float64']).columns

        if fit or self.poly_transformer is None:
            # fit new transformer
            self.poly_transformer = PolynomialFeatures(
                degree=degree, interaction_only=False, include_bias=False
            )

            X_train_poly = pd.DataFrame(
                self.poly_transformer.fit_transform(X_train[numeric_cols]),
                columns=self.poly_transformer.get_feature_names_out(numeric_cols),
                index=X_train.index
            )

            # combine with categorical features
            flag_cols = [c for c in X_train.columns if c not in numeric_cols]
            X_train_final = pd.concat([X_train[flag_cols], X_train_poly], axis=1)

            # ONLY set feature_names when fitting
            self.feature_names = X_train_final.columns.tolist()

        else:
            # use existing transformer - don't overwrite feature_names
            X_train_poly = pd.DataFrame(
                self.poly_transformer.transform(X_train[numeric_cols]),
                columns=self.poly_transformer.get_feature_names_out(numeric_cols),
                index=X_train.index
            )

            # combine with categorical features
            flag_cols = [c for c in X_train.columns if c not in numeric_cols]
            X_train_final = pd.concat([X_train[flag_cols], X_train_poly], axis=1)

        # handle test set
        if X_test is not None:
            X_test_poly = pd.DataFrame(
                self.poly_transformer.transform(X_test[numeric_cols]),
                columns=self.poly_transformer.get_feature_names_out(numeric_cols),
                index=X_test.index
            )
            flag_cols = [c for c in X_test.columns if c not in numeric_cols]
            X_test_final = pd.concat([X_test[flag_cols], X_test_poly], axis=1)
            return X_train_final, X_test_final

        return X_train_final
    
    def align_prediction_columns(self, X_pred, expected_columns):
        """Ensure prediction features match training features exactly"""
        
        # Get current columns
        current_columns = set(X_pred.columns)
        expected_columns_set = set(expected_columns)
        
        # Add missing columns with zeros
        missing_columns = expected_columns_set - current_columns
        for col in missing_columns:
            X_pred[col] = 0.0
        
        # Remove extra columns
        extra_columns = current_columns - expected_columns_set
        if extra_columns:
            X_pred = X_pred.drop(columns=list(extra_columns))
        
        # Reorder columns to match training order
        X_pred = X_pred[expected_columns]
        
        print(f"Aligned features: {len(X_pred.columns)} columns (added {len(missing_columns)}, removed {len(extra_columns)})")
        
        return X_pred
    
    def prepare_outfit_features(self, df, for_training=True):
        """full feature engineering pipeline with robust column handling"""

        # Add outfit hashes for caching
        if 'outfit_hash' not in df.columns:
            df['outfit_hash'] = (df['shirt_id'] + '_' + df['pants_id'] + '_' + df['shoes_id'])

        # Check for cached features (only for prediction, not training)
        cached_features = {}
        missing_hashes = df['outfit_hash'].tolist()

        if not for_training:
            cached_data = self.db.get_outfit_features(self.user_id, df['outfit_hash'].tolist())

            for item in cached_data:
                cached_features[item['outfit_hash']] = pickle.loads(item['feature_blob'])

            missing_hashes = [h for h in df['outfit_hash'] if h not in cached_features]

            if cached_features:
                None
            if missing_hashes:
                print(f"Need to compute features for {len(missing_hashes)} combinations")

        # Compute features for missing combinations
        if missing_hashes:
            if not for_training:
                print("Computing missing features...")

            # Filter to outfits that need computation
            missing_df = df[df['outfit_hash'].isin(missing_hashes)].copy()

            # STEP 1: get clothing features from database
            missing_df = self.get_clothing_features_from_db(missing_df)

            # STEP 2: categorical features
            missing_df = self.create_categorical_features(missing_df)

            # STEP 3: color harmony features
            missing_df = self.create_color_harmony_features(missing_df)

            # STEP 4: lab color features
            missing_df = self.create_lab_color_features(missing_df)

            # STEP 5: style compatibility features
            missing_df = self.create_style_compatibility_features(missing_df)

            # STEP 6: palette features
            missing_df = self.create_palette_features(missing_df)

            # STEP 7: prepare for ml
            drop_cols = [
                "shirt_id", "pants_id", "shoes_id", "rating", "outfit_hash",
                "closest_palette", "rating_binary",
                # Color hex columns
                "shirt_dominant_color", "shirt_secondary_color",
                "pants_dominant_color", "pants_secondary_color", 
                "shoes_dominant_color", "shoes_secondary_color",
                # Text description columns
                "shirt_color_description", "pants_color_description", "shoes_color_description"
            ]       

            # only drop columns that exist
            drop_cols = [col for col in drop_cols if col in missing_df.columns]
            X_missing = missing_df.drop(columns=drop_cols)

            # STEP 8: handle any remaining NaN values before polynomial features
            X_missing = X_missing.fillna(0.0)

            # STEP 9: polynomial features with column alignment
            if for_training:
                X_missing_final = self.create_polynomial_features(X_missing, fit=True)
            else:
                X_missing_final = self.create_polynomial_features(X_missing, fit=False)

                # CRITICAL: Align columns with training features
                if hasattr(self, 'feature_names') and self.feature_names:
                    X_missing_final = self.align_prediction_columns(X_missing_final, self.feature_names)

            # Cache the computed features (only for prediction)
            if not for_training:
                print("Caching computed features...")
                for idx, outfit_hash in enumerate(missing_hashes):
                    features = X_missing_final.iloc[idx].values
                    self.db.save_outfit_features(self.user_id, outfit_hash, features)
                    cached_features[outfit_hash] = features
            else:
                # For training, just add to our working set
                for idx, outfit_hash in enumerate(missing_hashes):
                    cached_features[outfit_hash] = X_missing_final.iloc[idx].values

        # Reconstruct full feature matrix from cached + computed features
        if not for_training and len(cached_features) < len(df):
            print("Warning: Some features still missing after computation")

        # Build final feature matrix in original order
        feature_matrix = []
        for outfit_hash in df['outfit_hash']:
            if outfit_hash in cached_features:
                feature_matrix.append(cached_features[outfit_hash])
            else:
                # This shouldn't happen, but provide fallback
                print(f"Warning: No features found for {outfit_hash}")
                # Create zero vector as fallback
                if hasattr(self, 'feature_names') and self.feature_names:
                    feature_matrix.append(np.zeros(len(self.feature_names)))
                else:
                    feature_matrix.append(np.zeros(100))  # fallback size

        # Convert to DataFrame with proper column handling
        if hasattr(self, 'feature_names') and self.feature_names:
            # We have a saved transformer - need to align all features to it
            feature_names = self.feature_names
            
            # Check if feature dimensions match
            if len(feature_matrix[0]) != len(feature_names):
                print(f"Feature dimension mismatch detected: computed={len(feature_matrix[0])}, expected={len(feature_names)}")
                
                # Create temporary DataFrame to align
                if missing_hashes and 'X_missing_final' in locals():
                    temp_feature_names = X_missing_final.columns.tolist()
                else:
                    temp_feature_names = [f"feat_{i}" for i in range(len(feature_matrix[0]))]
                
                temp_df = pd.DataFrame(feature_matrix, columns=temp_feature_names, index=df.index)
                
                # Align to expected features
                temp_df = self.align_prediction_columns(temp_df, feature_names)
                X_final = temp_df
            else:
                X_final = pd.DataFrame(feature_matrix, columns=feature_names, index=df.index)
                
        elif missing_hashes and 'X_missing_final' in locals():
            # First time computing - use computed feature names
            feature_names = X_missing_final.columns.tolist()
            self.feature_names = feature_names
            X_final = pd.DataFrame(feature_matrix, columns=feature_names, index=df.index)
        else:
            # Fallback
            feature_names = [f"feat_{i}" for i in range(len(feature_matrix[0]))]
            self.feature_names = feature_names
            X_final = pd.DataFrame(feature_matrix, columns=feature_names, index=df.index)

        return X_final
    
    def save_transformer(self, filepath):
       """save the feature transformer for reuse"""
       
       Path(filepath).parent.mkdir(parents=True, exist_ok=True)
       
       transformer_data = {
           'poly_transformer': self.poly_transformer,
           'feature_names': self.feature_names,
           'user_id': self.user_id
       }
       
       with open(filepath, 'wb') as f:
           pickle.dump(transformer_data, f)
       
       print(f"Saved transformer with {len(self.feature_names)} features")

    def load_transformer(self, filepath):
       """load saved feature transformer"""
       
       with open(filepath, 'rb') as f:
           transformer_data = pickle.load(f)
       
       self.poly_transformer = transformer_data['poly_transformer']
       self.feature_names = transformer_data['feature_names']
       
       print(f"Loaded transformer with {len(self.feature_names)} features")


# convenience functions for easy import
def create_training_features(user_id, outfit_df, db, save_transformer=True):
    """create features for training data using database and save transformer"""
    
    engine = OutfitFeatureEngine(user_id, db)
    X = engine.prepare_outfit_features(outfit_df, for_training=True)
    
    if save_transformer:
        transformer_path = f"models/user_{user_id}/feature_transformer.pkl"
        engine.save_transformer(transformer_path)
    
    return X, engine


def create_prediction_features(user_id, outfit_df, db, use_saved_transformer=True):
    """create features for prediction using ONLY cached features"""
    
    # Add outfit hashes
    if 'outfit_hash' not in outfit_df.columns:
        outfit_df = outfit_df.copy()  # Don't modify original
        outfit_df['outfit_hash'] = (outfit_df['shirt_id'] + '_' + outfit_df['pants_id'] + '_' + outfit_df['shoes_id'])
        
    # Get cached features
    cached_data = db.get_outfit_features(user_id, outfit_df['outfit_hash'].tolist())
    
    if len(cached_data) == 0:
        raise ValueError("No cached features found! Run precompute_all_outfit_features() first.")
    
    if len(cached_data) != len(outfit_df):
        print(f"WARNING: Only {len(cached_data)}/{len(outfit_df)} features cached")
        # Show which ones are missing
        cached_hashes = {item['outfit_hash'] for item in cached_data}
        missing_hashes = [h for h in outfit_df['outfit_hash'] if h not in cached_hashes]
        print(f"Missing combinations: {missing_hashes[:5]}...")
        raise ValueError("Some outfit combinations not cached! Run precompute_all_outfit_features() again.")
        
    # Build feature matrix from cached data
    cached_dict = {item['outfit_hash']: pickle.loads(item['feature_blob']) for item in cached_data}
    
    # Reconstruct features in original order
    feature_matrix = []
    for outfit_hash in outfit_df['outfit_hash']:
        if outfit_hash in cached_dict:
            feature_matrix.append(cached_dict[outfit_hash])
        else:
            raise ValueError(f"Missing cached features for {outfit_hash}")
    
    # Get feature names from transformer
    transformer_path = f"models/user_{user_id}/feature_transformer.pkl"
    if Path(transformer_path).exists():
        with open(transformer_path, 'rb') as f:
            transformer_data = pickle.load(f)
            feature_names = transformer_data.get('feature_names')
    else:
        raise FileNotFoundError(f"No transformer found at {transformer_path}")
    
    if not feature_names:
        raise ValueError("Transformer missing feature names")
    
    # Create DataFrame with correct feature names
    if len(feature_matrix[0]) != len(feature_names):
        raise ValueError(f"Feature dimension mismatch: cached={len(feature_matrix[0])}, expected={len(feature_names)}")
    
    X = pd.DataFrame(feature_matrix, columns=feature_names, index=outfit_df.index)
    
    return X