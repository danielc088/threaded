"""
data preparation pipeline for outfit recommendation training
combines CV features, GenAI features, and outfit ratings into ML-ready datasets
creates train/test splits with engineered features for the random forest model
"""

import pandas as pd
import numpy as np
import json
import warnings
from pathlib import Path
from matplotlib.colors import to_rgb
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures

# suppress pandas future warnings
warnings.filterwarnings('ignore', category=FutureWarning)


def load_and_merge_data(ratings_file, cv_features_file, genai_features_file):
    """load outfit ratings and merge with both CV and GenAI features for each clothing item"""
    
    df = pd.read_csv(ratings_file)
    print(f"found: {len(df)} outfit combinations")
    
    # merge CV features (dominant colours, texture, brightness, symmetry)
    cv_features = pd.read_csv(cv_features_file)
    
    for item in ["shirt", "pants", "shoes"]:
        df = df.merge(
            cv_features.add_prefix(f"{item}_"),
            left_on=f"{item}_id",
            right_on=f"{item}_clothing_id",
            how="left"
        ).drop(columns=[f"{item}_clothing_id"])
    
    # merge GenAI features (pattern, style, fit, graphics)
    genai_features = pd.read_csv(genai_features_file)
    
    for item in ["shirt", "pants", "shoes"]:
        df = df.merge(
            genai_features.add_prefix(f"{item}_"),
            left_on=f"{item}_id",
            right_on=f"{item}_clothing_id",
            how="left"
        ).drop(columns=[f"{item}_clothing_id"])
    
    # convert boolean graphic flags to integers for ML
    for item in ["shirt", "pants", "shoes"]:
        col = f"{item}_has_graphic"
        if col in df.columns:
            df[col] = df[col].astype(int)
    
    return df


def create_categorical_features(df):
    """one-hot encode categorical GenAI features like pattern_type, style, fit_type"""
    
    categorical_cols = []
    for item in ["shirt", "pants", "shoes"]:
        for col in ["pattern_type", "style", "fit_type"]:
            cat_col = f"{item}_{col}"
            if cat_col in df.columns:
                categorical_cols.append(cat_col)
    
    if categorical_cols:
        # Use the new pandas syntax to avoid future warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=FutureWarning)
            df = pd.get_dummies(df, columns=categorical_cols, dummy_na=True)
    
    return df


def hex_to_lab(hex_code):
    """convert hex colour codes to LAB colour space for better distance calculations"""
    rgb = sRGBColor(*to_rgb(hex_code), is_upscaled=False)
    return convert_color(rgb, LabColor)


def parse_top_colours(col_str, top_n=3):
    """extract dominant colours and weights from the stored string format"""
    try:
        parsed = eval(col_str)  # convert string back to list
        return [(h, w) for h, w in parsed[:top_n]]
    except:
        return []


def weighted_palette_distance(outfit_colours, palette_colours):
    """calculate how well an outfit matches a colour palette using weighted LAB distance"""
    
    # convert outfit colours to LAB space with weights
    outfit_lab = [(hex_to_lab(h), w) for h, w in outfit_colours]
    palette_lab = [hex_to_lab(c) for c in palette_colours]
    
    # find minimum distance to palette for each outfit colour, weight by dominance
    dists = []
    for lab, w in outfit_lab:
        min_dist = min(float(delta_e_cie2000(lab, p)) for p in palette_lab)
        dists.append(min_dist * w)
    
    # return weighted average distance
    return np.sum(dists) / (np.sum([w for _, w in outfit_lab]) + 1e-8)


def create_palette_features(df, palettes_file):
    """find closest trendy colour palette for each outfit and create palette features"""
    
    with open(palettes_file, "r") as f:
        palettes = json.load(f)
    
    print(f"found: {len(palettes)} colour palettes")
    
    def closest_palette_weighted(row):
        """find the best matching palette for this outfit combination"""
        outfit_colours = []
        
        # collect dominant colours from all three clothing items
        for item in ['shirt', 'pants', 'shoes']:
            outfit_colours.extend(parse_top_colours(row[f"{item}_dominant_colours"], top_n=5))
        
        if not outfit_colours:
            return pd.Series([None, np.nan])
        
        # test against all palettes to find best match
        best_palette, best_dist = None, float('inf')
        for name, cols in palettes.items():
            d = weighted_palette_distance(outfit_colours, cols)
            if d < best_dist:
                best_dist = d
                best_palette = name
        
        return pd.Series([best_palette, best_dist])
    
    df[['closest_palette', 'palette_distance']] = df.apply(closest_palette_weighted, axis=1)
    
    # create one-hot encoded palette features
    palette_dummies = pd.get_dummies(df['closest_palette'], prefix='palette')
    df = pd.concat([df, palette_dummies], axis=1)
    
    return df


def create_pairwise_features(df):
    """create features for specific clothing item combinations (shirt-pants, etc.)"""
    
    
    # create ID pairs for common combinations
    df['pair_shirt_pants'] = df['shirt_id'] + '_' + df['pants_id']
    df['pair_shirt_shoes'] = df['shirt_id'] + '_' + df['shoes_id']
    df['pair_pants_shoes'] = df['pants_id'] + '_' + df['shoes_id']
    
    # one-hot encode the pairwise combinations
    pair_dummies = pd.get_dummies(
        df[['pair_shirt_pants', 'pair_shirt_shoes', 'pair_pants_shoes']],
        prefix=['sp', 'ss', 'ps']
    )
    
    df = pd.concat([df, pair_dummies], axis=1)
    
    return df


def extract_first_hex(s):
    """helper to get the most dominant colour from the stored format"""
    try:
        return eval(s)[0][0]  # first colour's hex code
    except:
        return None


def create_colour_similarity_features(df):
    """calculate overall colour harmony metrics across the outfit"""
    
    def dominant_colour_similarity(row):
        """measure how similar the dominant colours are across shirt, pants, shoes"""
        hexes = [extract_first_hex(row[f'{i}_dominant_colours']) for i in ['shirt', 'pants', 'shoes']]
        
        if None in hexes:
            return np.nan
        
        # convert to LAB and calculate average pairwise distance
        lab_colors = [hex_to_lab(h) for h in hexes]
        distances = [delta_e_cie2000(lab_colors[i], lab_colors[j]) 
                    for i in range(3) for j in range(i+1, 3)]
        
        return np.mean(distances)
    
    df['overall_colour_similarity'] = df.apply(dominant_colour_similarity, axis=1)
    
    return df


def create_lab_colour_features(df):
    """extract LAB colour values for the most dominant colour of each item"""
    
    def extract_first_colour_lab(dominant_colours_str):
        """get L*a*b* values for the most dominant colour"""
        try:
            parsed = eval(dominant_colours_str)
            if not parsed:
                return pd.Series([np.nan, np.nan, np.nan])
            
            hex_code = parsed[0][0]
            lab = hex_to_lab(hex_code)
            return pd.Series([lab.lab_l, lab.lab_a, lab.lab_b])
        except:
            return pd.Series([np.nan, np.nan, np.nan])
    
    for item in ["shirt", "pants", "shoes"]:
        df[[f"{item}_L", f"{item}_a", f"{item}_b"]] = \
            df[f"{item}_dominant_colours"].apply(extract_first_colour_lab)
    
    return df


def create_polynomial_features(X_train, X_test):
    """create interaction features between numeric variables"""
    
    
    # identify numeric columns for interactions
    numeric_cols = X_train.select_dtypes(include=['int64', 'float64']).columns
    
    # create degree-2 interactions (no bias term)
    poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
    
    X_train_poly = pd.DataFrame(
        poly.fit_transform(X_train[numeric_cols]),
        columns=poly.get_feature_names_out(numeric_cols),
        index=X_train.index
    )
    
    X_test_poly = pd.DataFrame(
        poly.transform(X_test[numeric_cols]),
        columns=poly.get_feature_names_out(numeric_cols),
        index=X_test.index
    )
    
    # combine with categorical/binary flags
    flag_cols = [c for c in X_train.columns if c not in numeric_cols]
    X_train_final = pd.concat([X_train[flag_cols], X_train_poly], axis=1)
    X_test_final = pd.concat([X_test[flag_cols], X_test_poly], axis=1)
    
    
    return X_train_final, X_test_final


def prepare_training_data(
    ratings_file="data/supporting/outfit_ratings.csv",
    cv_features_file="data/supporting/clothing_features.csv", 
    genai_features_file="data/supporting/genai_features.csv",
    palettes_file="data/supporting/palettes.json",
    output_dir="data/training",
    test_size=0.2,
    random_state=42
):
    """full pipeline to prepare train/test datasets with engineered features"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # step 1: load outfit ratings
    df = pd.read_csv(ratings_file)
    
    # step 2: use the modular feature engine
    from src.feature_extraction.engineered_features import OutfitFeatureEngine

    df_features = df.drop(columns=['rating'])
    engine = OutfitFeatureEngine(palettes_file)
    
    # prepare features using the modular pipeline
    X = engine.prepare_outfit_features(
        df_features, cv_features_file, genai_features_file, for_training=True
    )
    
    # step 3: prepare labels (4+ stars = good outfit)
    y = (df['rating'] >= 4).astype(int)
    
    # step 4: train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    # step 5: save everything
    X_train.to_csv(output_path / "train_features.csv", index=False)
    X_test.to_csv(output_path / "test_features.csv", index=False)
    y_train.to_csv(output_path / "train_labels.csv", index=False)
    y_test.to_csv(output_path / "test_labels.csv", index=False)
    
    # also save the raw data with train/test split for reference
    train_indices, test_indices = train_test_split(df.index, test_size=test_size, random_state=random_state)
    df.loc[train_indices].to_csv(output_path / "train_raw.csv", index=False)
    df.loc[test_indices].to_csv(output_path / "test_raw.csv", index=False)
    
    # save the feature transformer
    engine.save_transformer("models/feature_transformer.pkl")
    
    print(f"features: {X_train.shape[1]} columns")
    print(f"positive samples: {y_train.sum()}/{len(y_train)} train, {y_test.sum()}/{len(y_test)} test")
    
    return X_train, X_test, y_train, y_test