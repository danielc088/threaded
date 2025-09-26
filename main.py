"""
threaded - a personal project to digitalise my wardrobe
main entry point for the application
"""

from src.preprocessing.image_processor import batch_preprocess
from src.utils.palette_scraper import update_palette_database
from src.feature_extraction.cv_features import process_wardrobe_features
from src.feature_extraction.genai_features import process_wardrobe_genai
from src.recommender.test_train_prep import prepare_training_data
from src.recommender.random_forest import train_outfit_model

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

    TRAIN_MODEL = True
    if TRAIN_MODEL:
        print("[STARTING] preparing training data...")
        prepare_training_data(
            ratings_file="data/supporting/outfit_ratings.csv",
            cv_features_file="data/supporting/clothing_features.csv", 
            genai_features_file="data/supporting/genai_features.csv",
            palettes_file="data/supporting/palettes.json",
            output_dir="data/training"
        )
        print("[FINISHED] preparing training data...")
        
        print("[STARTING] training recommendation model...")
        train_outfit_model(data_dir="data/training", save_path="models/outfit_recommender.pkl")
        print("[FINISHED] training recommendation model...")

if __name__ == "__main__":
    main()