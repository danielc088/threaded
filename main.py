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
    """run the full wardrobe digitization pipeline"""
    
    # toggle these to run optional components
    TRAIN_MODEL = False
    UPDATE_PALETTES = False
    SHOW_OUTFITS = True  # set to True to see outfit recommendations
    
    if UPDATE_PALETTES:
        print("[STARTING] updating color palettes...")
        update_palette_database("data/supporting/palettes.json", max_palettes=100)
        print("[FINISHED] updating color palettes...")
    
    # process raw clothing images    
    print("\n[STARTING] preprocessing wardrobe...")
    batch_preprocess("data/wardrobe/raw_images", "data/wardrobe/bg_removed", "data/wardrobe/processed_images")
    print("[FINISHED] preprocessing wardrobe...")

    # extract clothing features from processed images
    print("\n[STARTING] feature extraction...")
    process_wardrobe_features("data/wardrobe/processed_images", "data/supporting/clothing_features.csv")
    print("[FINISHED] feature extraction...")

    # extract GenAI-based clothing features
    print("\n[STARTING] genai feature extraction...")
    process_wardrobe_genai("data/wardrobe/processed_images","data/supporting/genai_features.csv")
    print("[FINISHED] genai feature extraction...")

    # optional: train recommendation model
    if True:
        print("\n[STARTING] preparing training data...")
        prepare_training_data(
            ratings_file="data/supporting/outfit_ratings.csv",
            cv_features_file="data/supporting/clothing_features.csv", 
            genai_features_file="data/supporting/genai_features.csv",
            palettes_file="data/supporting/palettes.json",
            output_dir="data/training"
        )
        print("[FINISHED] preparing training data...")
        
        print("\n[STARTING] training recommendation model...")
        train_outfit_model(data_dir="data/training", save_path="models/outfit_recommender.pkl")
        print("[FINISHED] training recommendation model...")

    # optional: show outfit recommendations and browse wardrobe
    if SHOW_OUTFITS:
        print("\n" + "="*50)
        print("OUTFIT RECOMMENDATION")
        print("="*50)
        
        try:
            from src.utils.outfit_viewer import display_recommended_outfit
            
            # show recommended outfits if model exists
            try:
                print("recommended outfit...")
                display_recommended_outfit()
            except Exception as e:
                print(f"could not generate outfit recommendations: {e}")
                print("make sure you have a trained model (set TRAIN_MODEL=True)")
                
        except ImportError as e:
            print(f"could not import outfit viewer: {e}")


if __name__ == "__main__":
    main()