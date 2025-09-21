"""
threaded - a personal project to digitalise my wardrobe
main entry point for the application
"""

from src.preprocessing.preprocessor import batch_preprocess

def main():
    print("[STARTING] preprocessing...")
    
    # process all raw images
    batch_preprocess("data/raw_images", "data/processed_images")
    
    print("[FINISHED] preprocessing...")

if __name__ == "__main__":
    main()