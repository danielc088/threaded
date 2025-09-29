"""
wardrobe management utilities for crud operations on clothing items
handles viewing, uploading, and deleting wardrobe items from database
"""

from pathlib import Path
import shutil
from src.preprocessing.image_processor import batch_preprocess
from src.feature_extraction.cv_features import process_wardrobe_features
from src.feature_extraction.genai_features import process_wardrobe_genai


def view_wardrobe_items(user_id, db, item_type=None):
    """display user's wardrobe items by category"""
    
    items = db.get_wardrobe_items(user_id, item_type)
    
    if not items:
        if item_type:
            print(f"no {item_type}s found in wardrobe")
        else:
            print("no items found in wardrobe")
        return
    
    # group by item type for display
    grouped_items = {}
    for item in items:
        category = item['item_type']
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item)
    
    # display by category
    for category, category_items in grouped_items.items():
        print(f"\n{category.upper()}S ({len(category_items)} items):")
        for item in category_items:
            print(f"  - {item['clothing_id']} (uploaded: {item['uploaded_at'][:10]})")
    
    total_items = len(items)
    print(f"\ntotal wardrobe items: {total_items}")


def upload_new_images(user_id, db, raw_images_dir):
    """process and upload new clothing images to wardrobe"""
    
    raw_path = Path(raw_images_dir)
    if not raw_path.exists():
        print(f"directory not found: {raw_images_dir}")
        return
    
    # check for new images
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png']:
        image_files.extend(raw_path.glob(f"*{ext}"))
    
    if not image_files:
        print("no image files found in directory")
        return
    
    print(f"found {len(image_files)} images to process")
    
    # create user-specific directories
    user_dir = f"data/wardrobe/{user_id}"
    bg_removed_dir = f"{user_dir}/bg_removed"
    processed_dir = f"{user_dir}/processed_images"
    
    Path(bg_removed_dir).mkdir(parents=True, exist_ok=True)
    Path(processed_dir).mkdir(parents=True, exist_ok=True)
    
    # process images through the pipeline
    print("preprocessing images...")
    batch_preprocess(raw_images_dir, bg_removed_dir, processed_dir)
    
    # extract features and add to database
    print("extracting cv features...")
    cv_count = process_wardrobe_features(processed_dir, user_id, db)
    
    print("extracting genai features...")
    genai_count = process_wardrobe_genai(processed_dir, user_id, db)
    
    print(f"successfully uploaded {cv_count} new clothing items")


def delete_wardrobe_item(user_id, db, clothing_id):
    """remove clothing item from wardrobe (soft delete in database)"""
    
    # check if item exists
    items = db.get_wardrobe_items(user_id)
    item = next((i for i in items if i['clothing_id'] == clothing_id), None)
    
    if not item:
        print(f"clothing item '{clothing_id}' not found in wardrobe")
        return False
    
    # soft delete from database
    db.delete_wardrobe_item(user_id, clothing_id)
    
    print(f"deleted '{clothing_id}' from wardrobe")
    print("note: image files are kept on disk but item is inactive in database")
    
    return True


def get_wardrobe_stats(user_id, db):
    """get statistics about user's wardrobe"""
    
    items = db.get_wardrobe_items(user_id)
    genai_features = db.get_genai_features(user_id)
    ratings = db.get_all_ratings(user_id)
    
    stats = {
        'total_items': len(items),
        'shirts': len([i for i in items if i['item_type'] == 'shirt']),
        'pants': len([i for i in items if i['item_type'] == 'pants']),
        'shoes': len([i for i in items if i['item_type'] == 'shoes']),
        'items_with_genai': len(genai_features),
        'total_ratings': len(ratings),
        'avg_rating': sum(r['rating'] for r in ratings) / len(ratings) if ratings else 0
    }
    
    return stats


def show_wardrobe_stats(user_id, db):
    """display wardrobe statistics"""
    
    stats = get_wardrobe_stats(user_id, db)
    
    print("\nwardrobe statistics:")
    print(f"  total items: {stats['total_items']}")
    print(f"  shirts: {stats['shirts']}")
    print(f"  pants: {stats['pants']}")
    print(f"  shoes: {stats['shoes']}")
    print(f"  items with ai analysis: {stats['items_with_genai']}")
    print(f"  total outfit ratings: {stats['total_ratings']}")
    
    if stats['avg_rating'] > 0:
        print(f"  average rating: {stats['avg_rating']:.1f}/5")


def interactive_wardrobe_management(user_id, db):
    """interactive menu for wardrobe management operations"""
    
    while True:
        print("\nwardrobe management:")
        print("  1. view all items")
        print("  2. view by category")
        print("  3. upload new images")
        print("  4. delete item")
        print("  5. show statistics")
        print("  6. back to main menu")
        
        choice = input("choose option (1-6): ").strip()
        
        if choice == "1":
            view_wardrobe_items(user_id, db)
            
        elif choice == "2":
            while True:
                item_type = input("category (shirt/pants/shoes): ").strip().lower()
                if item_type in ['shirt', 'pants', 'shoes']:
                    view_wardrobe_items(user_id, db, item_type)
                    break
                print("please enter 'shirt', 'pants', or 'shoes'")
                
        elif choice == "3":
            raw_dir = input("path to raw images directory: ").strip()
            if raw_dir:
                upload_new_images(user_id, db, raw_dir)
            else:
                default_dir = f"data/wardrobe/{user_id}/raw_images"
                print(f"using default directory: {default_dir}")
                upload_new_images(user_id, db, default_dir)
                
        elif choice == "4":
            clothing_id = input("clothing id to delete: ").strip()
            if clothing_id:
                delete_wardrobe_item(user_id, db, clothing_id)
                
        elif choice == "5":
            show_wardrobe_stats(user_id, db)
            
        elif choice == "6":
            break
            
        else:
            print("invalid choice. please enter 1-6.")


def bulk_upload_from_directory(user_id, db, base_directory):
    """bulk upload all images from a directory structure"""
    
    base_path = Path(base_directory)
    if not base_path.exists():
        print(f"directory not found: {base_directory}")
        return
    
    # look for raw_images subdirectory
    raw_images_path = base_path / "raw_images"
    if raw_images_path.exists():
        upload_new_images(user_id, db, str(raw_images_path))
    else:
        # use the base directory directly
        upload_new_images(user_id, db, str(base_path))


def cleanup_orphaned_files(user_id, db):
    """remove image files for items that are no longer in database"""
    
    # get active items from database
    active_items = db.get_wardrobe_items(user_id)
    active_ids = {item['clothing_id'] for item in active_items}
    
    # check image directories
    user_dir = Path(f"data/wardrobe/{user_id}")
    
    for subdir in ['bg_removed', 'processed_images']:
        img_dir = user_dir / subdir
        if not img_dir.exists():
            continue
            
        # find image files
        image_files = []
        for pattern in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(img_dir.glob(pattern))
        
        removed_count = 0
        for img_file in image_files:
            # extract clothing_id from filename
            stem = img_file.stem
            if stem.endswith('_bg_removed'):
                clothing_id = stem.replace('_bg_removed', '')
            elif stem.endswith('_processed'):
                clothing_id = stem.replace('_processed', '')
            else:
                clothing_id = stem
            
            # remove if not in active database items
            if clothing_id not in active_ids:
                img_file.unlink()
                removed_count += 1
                print(f"removed orphaned file: {img_file}")
        
        if removed_count > 0:
            print(f"cleaned up {removed_count} orphaned files from {subdir}")
        else:
            print(f"no orphaned files found in {subdir}")


if __name__ == "__main__":
    # for testing
    from data.database.models import WardrobeDB
    db = WardrobeDB()
    interactive_wardrobe_management(1, db)