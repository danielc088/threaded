"""
feature extraction pipeline for the processed clothing images
extracts colour, pattern, brightness, and symmetry data for the recommendation system
"""

import pandas as pd
import numpy as np
import cv2
from sklearn.cluster import KMeans
from pathlib import Path
import matplotlib.pyplot as plt


def rgb_to_hex(rgb):
    """convert RGB values (0-1 range) to hex codes for storage"""
    r, g, b = (rgb * 255).astype(int)
    return f"#{r:02X}{g:02X}{b:02X}"


def extract_dominant_colours(img, n_clusters=10, top_n=5):
    """get the top 5 most dominant colours from the clothing item using k-means"""
    
    # reshape image to get all pixels with RGBA values
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
    
    # take top N colours and calculate their weights
    top_centers = sorted_centers[:top_n]
    top_counts = sorted_counts[:top_n]
    total_top = sum(top_counts)
    weights = top_counts / total_top
    
    # convert to hex codes and create final format
    dominant_colours = []
    for center, weight in zip(top_centers, weights):
        hex_code = rgb_to_hex(center)
        dominant_colours.append([hex_code, float(weight)])
    
    return dominant_colours


def calculate_texture_variance(img):
    """measure how patterned vs solid the clothing item is using texture variance"""
    
    # get mask for clothing pixels only (high alpha)
    mask = img[:, :, 3] > 0.95
    
    if not mask.any():
        return 0  # no clothing pixels found
    
    # create a masked grayscale image for texture analysis
    height, width = img.shape[:2]
    gray_img = np.zeros((height, width), dtype=np.uint8)
    
    # fill in the clothing areas with grayscale values
    rgb_255 = (img[:, :, :3] * 255).astype(np.uint8)
    gray_full = cv2.cvtColor(rgb_255, cv2.COLOR_RGB2GRAY)
    gray_img[mask] = gray_full[mask]
    
    # calculate variance only on clothing pixels
    clothing_gray = gray_img[mask]
    variance = float(np.var(clothing_gray))
    
    return variance


def calculate_brightness_level(img):
    """measure overall lightness of the clothing item"""
    mask = img[:, :, 3] > 0.95
    
    if mask.any():
        clothing_rgb = img[mask][:, :3]
        avg_brightness = float(np.mean(clothing_rgb))
        return avg_brightness
    
    return 0.0


def calculate_symmetry(img):
    """calculate vertical and horizontal symmetry scores"""
    
    # get mask for clothing pixels only
    mask = img[:, :, 3] > 0.95
    
    if not mask.any():
        return (0.0, 0.0)
    
    # convert to grayscale for symmetry analysis
    rgb_255 = (img[:, :, :3] * 255).astype(np.uint8)
    gray = cv2.cvtColor(rgb_255, cv2.COLOR_RGB2GRAY)
    
    # apply mask to focus only on clothing
    gray_masked = gray.copy()
    gray_masked[~mask] = 0
    
    height, width = gray_masked.shape
    
    # vertical symmetry (left vs right)
    mid_x = width // 2
    left_half = gray_masked[:, :mid_x]
    right_half = gray_masked[:, mid_x:]
    
    # flip right half to compare
    right_flipped = np.fliplr(right_half)
    
    # handle odd widths by taking minimum size
    min_width = min(left_half.shape[1], right_flipped.shape[1])
    left_crop = left_half[:, -min_width:]
    right_crop = right_flipped[:, :min_width]
    
    # calculate vertical symmetry score (higher = more symmetric)
    vertical_diff = np.mean(np.abs(left_crop.astype(int) - right_crop.astype(int)))
    vertical_symmetry = max(0, 255 - vertical_diff) / 255
    
    # horizontal symmetry (top vs bottom)
    mid_y = height // 2
    top_half = gray_masked[:mid_y, :]
    bottom_half = gray_masked[mid_y:, :]
    
    # flip bottom half to compare
    bottom_flipped = np.flipud(bottom_half)
    
    # handle odd heights
    min_height = min(top_half.shape[0], bottom_flipped.shape[0])
    top_crop = top_half[-min_height:, :]
    bottom_crop = bottom_flipped[:min_height, :]
    
    # calculate horizontal symmetry score
    horizontal_diff = np.mean(np.abs(top_crop.astype(int) - bottom_crop.astype(int)))
    horizontal_symmetry = max(0, 255 - horizontal_diff) / 255
    
    return (float(vertical_symmetry), float(horizontal_symmetry))


def extract_all_features(image_path):
    """run the full feature extraction pipeline on a single clothing item"""
    
    img = plt.imread(str(image_path))
    
    # extract all features
    dominant_colours = extract_dominant_colours(img)
    texture_variance = calculate_texture_variance(img)
    brightness = calculate_brightness_level(img)
    vertical_symmetry, horizontal_symmetry = calculate_symmetry(img)
    
    # package everything up
    features = {
        'dominant_colours': dominant_colours,
        'texture_variance': texture_variance,
        'brightness': brightness,
        'vertical_symmetry': vertical_symmetry,
        'horizontal_symmetry': horizontal_symmetry
    }
    
    return features


def process_wardrobe_features(input_dir, output_csv):
    """extract features from all processed clothing images and save to CSV.
    Skips items that are already in the output CSV.
    """
    input_path = Path(input_dir)
    image_files = list(input_path.glob("*_processed.png"))

    print(f"Found {len(image_files)} processed clothes to analyse")

    # load existing CSV if it exists
    if Path(output_csv).exists():
        existing_df = pd.read_csv(output_csv)
        existing_ids = set(existing_df["clothing_id"].astype(str).tolist())
        wardrobe_data = existing_df.to_dict("records")
    else:
        existing_ids = set()
        wardrobe_data = []

    # process new images only
    new_rows = []
    for img_file in image_files:
        clothing_id = img_file.name.replace("_processed.png", "")

        if clothing_id in existing_ids:
            continue

        features = extract_all_features(img_file)

        row = {
            "clothing_id": clothing_id,
            "dominant_colours": str(features["dominant_colours"]),
            "texture_variance": features["texture_variance"],
            "brightness": features["brightness"],
            "vertical_symmetry": features["vertical_symmetry"],
            "horizontal_symmetry": features["horizontal_symmetry"],
        }
        new_rows.append(row)

    # append new rows
    if new_rows:
        wardrobe_data.extend(new_rows)
        df = pd.DataFrame(wardrobe_data)
        df.to_csv(output_csv, index=False)
        #print(f"\nAdded {len(new_rows)} new clothes")
    else:
        df = pd.DataFrame(wardrobe_data)
        #print("\nNo new clothes to process")

    print(f"processed: {len(new_rows)} new clothes")
    print(f"skipped: {len(image_files)} clothes already done")

    return df
