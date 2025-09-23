"""
threaded - a personal project to digitalise my wardrobe
main entry point for the application
"""

from src.preprocessing.preprocessor import batch_preprocess
from src.utils.palette_scraper import update_palette_database
from src.feature_extraction.features import process_wardrobe_features

def main():

    # process raw clothing images    
    print("[STARTING] preprocessing wardrobe...")
    batch_preprocess("data/wardrobe/raw_images", "data/wardrobe/bg_removed", "data/wardrobe/processed_images")
    print("[FINISHED] preprocessing wardrobe...")

    # extract clothing features from processed images
    print("[STARTING] feature extraction...")
    process_wardrobe_features("data/wardrobe/processed_images", "data/supporting/clothing_features.csv")
    print("[FINISHED] feature extraction...")

if __name__ == "__main__":
    main()