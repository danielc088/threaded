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
from src.utils.outfit_viewer import display_outfit_from_dict, get_outfit_choice
from src.recommender.outfit_generator import OutfitGenerator



def main():
    """run the full wardrobe digitization pipeline"""
    
    # toggle these to run different parts of the pipeline
    UPDATE_PALETTES = False
    TRAIN_MODEL = False
    PROCESSING = False
    SHOW_OUTFITS = True
    
    # scrape colour palettes
    if UPDATE_PALETTES:
        print("[STARTING] updating color palettes...")
        update_palette_database("data/supporting/palettes.json", max_palettes=100)
        print("[FINISHED] updating color palettes...")
    
    # image processing and feature extraction
    if PROCESSING:
        print("[STARTING] preprocessing wardrobe...")
        batch_preprocess(
            "data/wardrobe/raw_images",
            "data/wardrobe/bg_removed", 
            "data/wardrobe/processed_images"
        )
        print("[FINISHED] preprocessing wardrobe...")

        print("[STARTING] cv feature extraction...")
        process_wardrobe_features(
            "data/wardrobe/processed_images",
            "data/supporting/clothing_features.csv"
        )
        print("[FINISHED] cv feature extraction...")

        print("[STARTING] genai feature extraction...")
        process_wardrobe_genai(
            "data/wardrobe/processed_images",
            "data/supporting/genai_features.csv"
        )
        print("[FINISHED] genai feature extraction...")

    # train recommendation model
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
        train_outfit_model(
            data_dir="data/training",
            save_path="models/outfit_recommender.pkl"
        )
        print("[FINISHED] training recommendation model...")

    # show outfit recommendations
    if SHOW_OUTFITS:
        try:
            generator = OutfitGenerator()
            outfit = get_outfit_choice(generator)
            
            if outfit:
                display_outfit_from_dict(outfit, image_type="bg_removed")
            else:
                print("no outfit could be generated")
                
        except Exception as e:
            print(f"error generating outfit: {e}")
            print("make sure you have a trained model (set TRAIN_MODEL=True)")


if __name__ == "__main__":
    main()