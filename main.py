"""
threaded - a personal project to digitalise my wardrobe
main entry point for the application
"""

from src.preprocessing.image_processor import batch_preprocess
from src.utils.palette_scraper import update_palette_database
from src.feature_extraction.cv_features import process_wardrobe_features
from src.feature_extraction.genai_features import process_wardrobe_genai

def main():

    # process raw clothing images    
    print("[STARTING] preprocessing wardrobe...")
    batch_preprocess("data/wardrobe/raw_images", "data/wardrobe/bg_removed", "data/wardrobe/processed_images")
    print("[FINISHED] preprocessing wardrobe...")

    # extract clothing features from processed images
    print("[STARTING] feature extraction...")
    process_wardrobe_features("data/wardrobe/processed_images", "data/supporting/clothing_features.csv")
    print("[FINISHED] feature extraction...")

    # extract GenAI-based clothing features
    print("[STARTING] genai feature extraction...")
    process_wardrobe_genai("data/wardrobe/processed_images","data/supporting/genai_features.csv")
    print("[FINISHED] genai feature extraction...")

if __name__ == "__main__":
    main()