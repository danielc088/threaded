"""
modular feature engineering pipeline for outfit recommendation
provides reusable functions for creating ML features from outfit combinations
used by both training pipeline and live outfit generation
"""

import pandas as pd
import numpy as np
if not hasattr(np, "asscalar"):
    np.asscalar = lambda x: x.item()
import json
import warnings
from pathlib import Path
from matplotlib.colors import to_rgb
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from sklearn.preprocessing import PolynomialFeatures

# suppress pandas future warnings
warnings.filterwarnings('ignore', category=FutureWarning)


class OutfitFeatureEngine:
    """handles all feature engineering for outfit combinations"""
    
    def __init__(self, palettes_file="data/supporting/palettes.json"):
        """initialize with color palette data"""
        self.palettes_file = Path(palettes_file)
        self.palettes = None
        self.poly_transformer = None
        self.feature_names = None
        
        # load palettes if file exists
        if self.palettes_file.exists():
            with open(self.palettes_file, "r") as f:
                self.palettes = json.load(f)
            print(f"Loaded {len(self.palettes)} color palettes")
    
    def merge_clothing_features(self, df, cv_features_file, genai_features_file):
        """merge CV and GenAI features for each clothing item in the outfit"""
        
        # load feature datasets
        cv_features = pd.read_csv(cv_features_file)
        genai_features = pd.read_csv(genai_features_file)
        
        # merge CV features for each item
        for item in ["shirt", "pants", "shoes"]:
            df = df.merge(
                cv_features.add_prefix(f"{item}_"),
                left_on=f"{item}_id",
                right_on=f"{item}_clothing_id",
                how="left"
            ).drop(columns=[f"{item}_clothing_id"])
        
        # merge GenAI features for each item
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
    
    def create_categorical_features(self, df):
        """one-hot encode categorical GenAI features"""
        
        categorical_cols = []
        for item in ["shirt", "pants", "shoes"]:
            for col in ["pattern_type", "style", "fit_type"]:
                cat_col = f"{item}_{col}"
                if cat_col in df.columns:
                    categorical_cols.append(cat_col)
        
        if categorical_cols:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=FutureWarning)
                df = pd.get_dummies(df, columns=categorical_cols, dummy_na=True)
        
        return df
    
    def hex_to_lab(self, hex_code):
        """convert hex color to LAB color space"""
        rgb = sRGBColor(*to_rgb(hex_code), is_upscaled=False)
        return convert_color(rgb, LabColor)
    
    def parse_top_colours(self, col_str, top_n=3):
        """extract dominant colors from stored string format"""
        try:
            parsed = eval(col_str)
            return [(h, w) for h, w in parsed[:top_n]]
        except:
            return []
    
    def weighted_palette_distance(self, outfit_colours, palette_colours):
        """calculate weighted distance to a color palette"""
        
        outfit_lab = [(self.hex_to_lab(h), w) for h, w in outfit_colours]
        palette_lab = [self.hex_to_lab(c) for c in palette_colours]
        
        dists = []
        for lab, w in outfit_lab:
            min_dist = min(float(delta_e_cie2000(lab, p)) for p in palette_lab)
            dists.append(min_dist * w)
        
        return np.sum(dists) / (np.sum([w for _, w in outfit_lab]) + 1e-8)
    
    def create_palette_features(self, df):
        """find closest color palette for each outfit"""
        
        if self.palettes is None:
            print("No color palettes loaded - skipping palette features")
            return df
        
        def closest_palette_weighted(row):
            """find best matching palette for this outfit"""
            outfit_colours = []
            
            for item in ['shirt', 'pants', 'shoes']:
                col_name = f"{item}_dominant_colours"
                if col_name in row:
                    outfit_colours.extend(self.parse_top_colours(row[col_name], top_n=5))
            
            if not outfit_colours:
                return pd.Series([None, np.nan])
            
            best_palette, best_dist = None, float('inf')
            for name, cols in self.palettes.items():
                d = self.weighted_palette_distance(outfit_colours, cols)
                if d < best_dist:
                    best_dist = d
                    best_palette = name
            
            return pd.Series([best_palette, best_dist])
        
        df[['closest_palette', 'palette_distance']] = df.apply(closest_palette_weighted, axis=1)
        
        # create one-hot encoded palette features
        palette_dummies = pd.get_dummies(df['closest_palette'], prefix='palette')
        df = pd.concat([df, palette_dummies], axis=1)
        
        return df
    
    def create_pairwise_features(self, df):
        """create features for clothing item combinations"""
        
        df['pair_shirt_pants'] = df['shirt_id'] + '_' + df['pants_id']
        df['pair_shirt_shoes'] = df['shirt_id'] + '_' + df['shoes_id']
        df['pair_pants_shoes'] = df['pants_id'] + '_' + df['shoes_id']
        
        pair_dummies = pd.get_dummies(
            df[['pair_shirt_pants', 'pair_shirt_shoes', 'pair_pants_shoes']],
            prefix=['sp', 'ss', 'ps']
        )
        
        df = pd.concat([df, pair_dummies], axis=1)
        return df
    
    def extract_first_hex(self, s):
        """get most dominant color hex code"""
        try:
            return eval(s)[0][0]
        except:
            return None
    
    def create_colour_similarity_features(self, df):
        """calculate color harmony metrics across the outfit"""
        
        def dominant_colour_similarity(row):
            """measure color similarity between shirt, pants, shoes"""
            hexes = [self.extract_first_hex(row[f'{i}_dominant_colours']) 
                    for i in ['shirt', 'pants', 'shoes']]
            
            if None in hexes:
                return np.nan
            
            lab_colors = [self.hex_to_lab(h) for h in hexes]
            distances = [delta_e_cie2000(lab_colors[i], lab_colors[j])
                        for i in range(3) for j in range(i+1, 3)]
            
            return np.mean(distances)
        
        df['overall_colour_similarity'] = df.apply(dominant_colour_similarity, axis=1)
        return df
    
    def create_lab_colour_features(self, df):
        """extract LAB color values for dominant colors"""
        
        def extract_first_colour_lab(dominant_colours_str):
            """get L*a*b* values for most dominant color"""
            try:
                parsed = eval(dominant_colours_str)
                if not parsed:
                    return pd.Series([np.nan, np.nan, np.nan])
                
                hex_code = parsed[0][0]
                lab = self.hex_to_lab(hex_code)
                return pd.Series([lab.lab_l, lab.lab_a, lab.lab_b])
            except:
                return pd.Series([np.nan, np.nan, np.nan])
        
        for item in ["shirt", "pants", "shoes"]:
            col_name = f"{item}_dominant_colours"
            if col_name in df.columns:
                df[[f"{item}_L", f"{item}_a", f"{item}_b"]] = \
                    df[col_name].apply(extract_first_colour_lab)
        
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
        else:
            # use existing transformer
            X_train_poly = pd.DataFrame(
                self.poly_transformer.transform(X_train[numeric_cols]),
                columns=self.poly_transformer.get_feature_names_out(numeric_cols),
                index=X_train.index
            )
        
        # handle test set
        X_test_poly = None
        if X_test is not None:
            X_test_poly = pd.DataFrame(
                self.poly_transformer.transform(X_test[numeric_cols]),
                columns=self.poly_transformer.get_feature_names_out(numeric_cols),
                index=X_test.index
            )
        
        # combine with categorical features
        flag_cols = [c for c in X_train.columns if c not in numeric_cols]
        X_train_final = pd.concat([X_train[flag_cols], X_train_poly], axis=1)
        
        if X_test_poly is not None:
            X_test_final = pd.concat([X_test[flag_cols], X_test_poly], axis=1)
            return X_train_final, X_test_final
        
        # store feature names for later use
        self.feature_names = X_train_final.columns.tolist()
        return X_train_final
    
    def prepare_outfit_features(self, df, cv_features_file="data/supporting/clothing_features.csv",
                               genai_features_file="data/supporting/genai_features.csv", 
                               for_training=True, use_cache=True, cache_file=None):
        """full feature engineering pipeline for outfit combinations with caching"""
        
        if cache_file is None:
            cache_file = "data/cache/engineered_features.csv"
        
        cache_path = Path(cache_file)
        
        # try to load from cache first
        if use_cache and cache_path.exists():
            print(f"Loading cached engineered features from {cache_file}")
            cached_df = pd.read_csv(cache_file)
            
            # check if we have the same outfit combinations
            required_cols = ['shirt_id', 'pants_id', 'shoes_id']
            if all(col in cached_df.columns for col in required_cols):
                # merge with current outfit combinations
                df_merged = df.merge(cached_df, on=required_cols, how='left')
                
                # check if we have all the features we need
                feature_cols = [col for col in cached_df.columns if col not in required_cols]
                missing_features = df_merged[feature_cols].isnull().any(axis=1).sum()
                
                if missing_features == 0:
                    print(f"Using cached features for {len(df_merged)} outfit combinations")
                    
                    # prepare for ML (drop ID columns, etc.)
                    drop_cols = [
                        "shirt_id", "pants_id", "shoes_id", "rating",
                        "shirt_dominant_colours", "pants_dominant_colours", "shoes_dominant_colours",
                        "closest_palette", "pair_shirt_pants", "pair_shirt_shoes", "pair_pants_shoes"
                    ]
                    
                    drop_cols = [col for col in drop_cols if col in df_merged.columns]
                    X = df_merged.drop(columns=drop_cols)
                    
                    # polynomial features
                    if for_training:
                        X_final = self.create_polynomial_features(X, fit=True)
                    else:
                        X_final = self.create_polynomial_features(X, fit=False)
                    
                    print(f"Loaded cached features: {len(X_final.columns)} features")
                    return X_final
                else:
                    print(f"Cache incomplete - {missing_features} combinations missing features, recomputing...")
        
        # run full feature engineering pipeline
        print("Computing engineered features (this may take a while)...")
        
        # step 1: merge clothing features
        df = self.merge_clothing_features(df, cv_features_file, genai_features_file)
        
        # step 2: categorical features
        df = self.create_categorical_features(df)
        
        # step 3: palette features
        df = self.create_palette_features(df)
        
        # step 4: pairwise features  
        df = self.create_pairwise_features(df)
        
        # step 5: color similarity
        df = self.create_colour_similarity_features(df)
        
        # step 6: LAB color features
        df = self.create_lab_colour_features(df)
        
        # save to cache before final ML prep
        if use_cache:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(cache_file, index=False)
            print(f"Cached engineered features to {cache_file}")
        
        # step 7: prepare for ML
        drop_cols = [
            "shirt_id", "pants_id", "shoes_id", "rating",
            "shirt_dominant_colours", "pants_dominant_colours", "shoes_dominant_colours",
            "closest_palette", "pair_shirt_pants", "pair_shirt_shoes", "pair_pants_shoes"
        ]
        
        # only drop columns that exist
        drop_cols = [col for col in drop_cols if col in df.columns]
        X = df.drop(columns=drop_cols)
        
        # step 8: polynomial features
        if for_training:
            X_final = self.create_polynomial_features(X, fit=True)
        else:
            X_final = self.create_polynomial_features(X, fit=False)
        
        print(f"Feature engineering complete: {len(X_final.columns)} features")
        return X_final
    
    def save_transformer(self, filepath="models/feature_transformer.pkl"):
        """save the feature transformer for reuse"""
        import pickle
        
        transformer_data = {
            'poly_transformer': self.poly_transformer,
            'feature_names': self.feature_names,
            'palettes': self.palettes
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(transformer_data, f)
        
        print(f"Feature transformer saved to {filepath}")
    
    def load_transformer(self, filepath="models/feature_transformer.pkl"):
        """load saved feature transformer"""
        import pickle
        
        with open(filepath, 'rb') as f:
            transformer_data = pickle.load(f)
        
        self.poly_transformer = transformer_data['poly_transformer']
        self.feature_names = transformer_data['feature_names']
        if 'palettes' in transformer_data:
            self.palettes = transformer_data['palettes']
        
        print(f"Feature transformer loaded from {filepath}")


# convenience functions for easy import
def create_training_features(outfit_df, save_transformer=True):
    """create features for training data and save transformer"""
    
    
    engine = OutfitFeatureEngine()
    X = engine.prepare_outfit_features(outfit_df, for_training=True)
    
    if save_transformer:
        engine.save_transformer()
    
    return X, engine


def create_prediction_features(outfit_df, transformer_path="models/feature_transformer.pkl"):
    """create features for new outfits using saved transformer"""
    
    engine = OutfitFeatureEngine()
    engine.load_transformer(transformer_path)
    X = engine.prepare_outfit_features(outfit_df, for_training=False)
    
    return X