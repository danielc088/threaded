"""
threaded - a personal project to digitalise my wardrobe
main entry point for the application
"""

from src.preprocessing.preprocessor import batch_preprocess
from src.utils.palette_scraper import update_palette_database

def main():

    # process raw clothing images    
    print("[STARTING] preprocessing wardrobe...")
    batch_preprocess("data/raw_images", "data/bg_removed", "data/processed_images")
    print("[FINISHED] preprocessing wardrobe...")

    
    # scrape for colour palettes to work with
    print("[STARTING] colour palette scraping...")
    update_palette_database("data/palettes.json", max_palettes=100)
    print("[FINISHED] colour palette scraping...")

if __name__ == "__main__":
    main()