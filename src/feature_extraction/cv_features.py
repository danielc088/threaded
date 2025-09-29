"""
computer vision feature extraction for clothing images
pulls out colour, texture, and pattern data so we can recommend outfits that actually work together
"""

import pandas as pd
import numpy as np
import cv2
from sklearn.cluster import KMeans
from pathlib import Path
import matplotlib.pyplot as plt


def rgb_to_hex(rgb):
    """convert rgb values (0-1 range) to hex codes"""
    r, g, b = (rgb * 255).astype(int)
    return f"#{r:02X}{g:02X}{b:02X}"


def extract_dominant_colors(img, n_clusters=10, top_n=5):
    """get the top dominant colours from clothing item using k-means clustering"""
    
    # reshape image to get all pixels with rgba values
    color_tbl = pd.DataFrame(
        img.reshape(-1, 4), 
        columns=["red", "green", "blue", "alpha"]
    )
    
    # only keep solid clothing pixels (high alpha)
    color_tbl = color_tbl[color_tbl['alpha'] > 0.95]
    color_tbl = color_tbl.drop('alpha', axis=1)
    
    if len(color_tbl) < n_clusters:
        # not enough pixels for clustering
        return []
    
    # run k-means clustering to find dominant colours
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    km.fit(color_tbl)
    
    # get cluster sizes to find most dominant
    unique, counts = np.unique(km.labels_, return_counts=True)
    cluster_sizes = dict(zip(unique, counts))
    
    # sort clusters by size (most dominant first)
    sorted_indices = np.argsort(counts)[::-1]
    sorted_centers = km.cluster_centers_[sorted_indices]
    sorted_counts = counts[sorted_indices]
    
    # take top n colours and calculate their weights
    top_centers = sorted_centers[:top_n]
    top_counts = sorted_counts[:top_n]
    total_top = sum(top_counts)
    weights = top_counts / total_top
    
    # convert to hex codes and create final format
    dominant_colors = []
    for center, weight in zip(top_centers, weights):
        hex_code = rgb_to_hex(center)
        dominant_colors.append([hex_code, float(weight)])
    
    return dominant_colors


def calculate_texture_variance(img):
    """measure how patterned vs solid the clothing item is"""
    
    # get mask for clothing pixels only (high alpha)
    mask = img[:, :, 3] > 0.95
    
    if not mask.any():
        return 0  # no clothing pixels found
    
    # create a masked greyscale image for texture analysis
    height, width = img.shape[:2]
    gray_img = np.zeros((height, width), dtype=np.uint8)
    
    # fill in the clothing areas with greyscale values
    rgb_255 = (img[:, :, :3] * 255).astype(np.uint8)
    gray_full = cv2.cvtColor(rgb_255, cv2.COLOR_RGB2GRAY)
    gray_img[mask] = gray_full[mask]
    
    # calculate variance only on clothing pixels
    clothing_gray = gray_img[mask]
    variance = float(np.var(clothing_gray))
    
    return variance


def calculate_brightness_level(img):
    """measure overall lightness of clothing item"""
    mask = img[:, :, 3] > 0.95
    
    if mask.any():
        clothing_rgb = img[mask][:, :3]
        avg_brightness = float(np.mean(clothing_rgb))
        return avg_brightness
    
    return 0.0


def calculate_color_statistics(img):
    """calculate colour statistics (saturation, hue, variance)"""
    mask = img[:, :, 3] > 0.95
    
    if not mask.any():
        return 0.0, 0.0, 0.0
    
    # convert to hsv for better colour analysis
    rgb_255 = (img[:, :, :3] * 255).astype(np.uint8)
    hsv = cv2.cvtColor(rgb_255, cv2.COLOR_RGB2HSV)
    
    # get clothing pixels only
    clothing_hsv = hsv[mask]
    
    # calculate statistics
    avg_saturation = float(np.mean(clothing_hsv[:, 1]) / 255.0)  # normalise to 0-1
    avg_hue = float(np.mean(clothing_hsv[:, 0]) / 179.0)  # normalise to 0-1
    color_variance = float(np.var(clothing_hsv, axis=0).mean())
    
    return avg_saturation, avg_hue, color_variance


def calculate_edge_density(img):
    """measure edge density for texture analysis"""
    mask = img[:, :, 3] > 0.95
    
    if not mask.any():
        return 0.0
    
    # convert to greyscale
    rgb_255 = (img[:, :, :3] * 255).astype(np.uint8)
    gray = cv2.cvtColor(rgb_255, cv2.COLOR_RGB2GRAY)
    
    # apply edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # calculate edge density only on clothing pixels
    clothing_edges = edges[mask]
    edge_density = float(np.sum(clothing_edges > 0) / len(clothing_edges))
    
    return edge_density


def extract_all_features(image_path):
    """run the full cv feature extraction pipeline on a clothing item"""
    
    img = plt.imread(str(image_path))
    
    # extract dominant colours
    dominant_colors = extract_dominant_colors(img)
    
    # get primary and secondary colours
    dominant_color = dominant_colors[0][0] if dominant_colors else None
    secondary_color = dominant_colors[1][0] if len(dominant_colors) > 1 else None
    
    # extract other features
    texture_variance = calculate_texture_variance(img)
    brightness = calculate_brightness_level(img)
    avg_saturation, avg_hue, color_variance = calculate_color_statistics(img)
    edge_density = calculate_edge_density(img)
    
    # package everything up
    features = {
        'dominant_color': dominant_color,
        'secondary_color': secondary_color,
        'avg_brightness': brightness,
        'avg_saturation': avg_saturation,
        'avg_hue': avg_hue,
        'color_variance': color_variance,
        'edge_density': edge_density,
        'texture_contrast': texture_variance
    }
    
    return features


def process_wardrobe_features(input_dir, user_id, db):
    """extract cv features from processed images and save to database"""
    input_path = Path(input_dir)
    image_files = list(input_path.glob("*_processed.png"))

    print(f"found {len(image_files)} processed images to analyse")

    processed_count = 0
    
    for img_file in image_files:
        clothing_id = img_file.name.replace("_processed.png", "")
        
        # check if item already exists in database
        existing_items = db.get_wardrobe_items(user_id)
        if any(item['clothing_id'] == clothing_id for item in existing_items):
            continue
        
        # determine item type
        if clothing_id.startswith('shirt_'):
            item_type = 'shirt'
        elif clothing_id.startswith('pants_'):
            item_type = 'pants'
        elif clothing_id.startswith('shoes_'):
            item_type = 'shoes'
        else:
            continue
        
        # extract features
        features = extract_all_features(img_file)
        
        # construct file path relative to wardrobe folder
        file_path = f"data/wardrobe/{user_id}/bg_removed/{clothing_id}_bg_removed.png"
        
        # add to database
        db.add_wardrobe_item(user_id, clothing_id, item_type, file_path, features)
        processed_count += 1
        print(f"added {clothing_id} to database")

    print(f"processed {processed_count} new clothing items")
    return processed_count