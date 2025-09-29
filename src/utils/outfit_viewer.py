"""
[ARCHIVED]
display outfit combinations with images
shows clothing items side by side for visual review
main menu system for wardrobe management and outfit generation
"""

import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
import os
import shutil


def load_clothing_image(clothing_id, image_type="bg_removed", user_id=1):
    """load clothing image from wardrobe directory"""
    
    # construct file path based on image type
    if image_type == "bg_removed":
        file_path = f"data/wardrobe/{user_id}/bg_removed/{clothing_id}_bg_removed.png"
    elif image_type == "processed":
        file_path = f"data/wardrobe/{user_id}/processed_images/{clothing_id}_processed.png"
    elif image_type == "raw":
        # try different extensions for raw images
        for ext in ['.jpg', '.jpeg', '.png']:
            file_path = f"data/wardrobe/{user_id}/raw_images/{clothing_id}{ext}"
            if Path(file_path).exists():
                break
    else:
        raise ValueError(f"invalid image type: {image_type}")
    
    if not Path(file_path).exists():
        print(f"warning: image not found at {file_path}")
        return None
    
    try:
        img = Image.open(file_path)
        return img
    except Exception as e:
        print(f"error loading image {file_path}: {e}")
        return None


def display_outfit_from_dict(outfit_dict, image_type="bg_removed", user_id=1):
    """display outfit from dictionary containing shirt, pants, shoes ids"""
    
    # extract clothing ids from outfit dict
    shirt_id = outfit_dict.get('shirt')
    pants_id = outfit_dict.get('pants') 
    shoes_id = outfit_dict.get('shoes')
    
    # get score if available
    score = outfit_dict.get('score')
    score_source = outfit_dict.get('score_source', 'unknown')
    
    # create a more informative title based on score source
    title = "outfit combination"
    if score is not None:
        if score_source.startswith('user_rating'):
            rating = score_source.split('_')[-1]
            title += f" (your rating: {rating}/5)"
        elif score_source == 'cached_ml':
            title += f" (ml prediction: {score:.1%} )"
        elif score_source == 'new_ml':
            title += f" (ml prediction: {score:.1%})"
        elif score_source == 'exploration_random':
            title += f" (exploration mode: random discovery)"
        elif score_source == 'exploration_with_fixed':
            title += f" (exploration mode: random pairing)"
        elif score_source == 'random':
            title += f" (random score: {score:.1%})"
    
    # add exploration notice
    if score_source.startswith('exploration'):
        print("trying something completely different to discover new styles")
        print("this helps the system learn your taste boundaries.\n")
    
    display_outfit(shirt_id, pants_id, shoes_id, image_type, user_id, score, score_source, title)


def display_outfit(shirt_id, pants_id, shoes_id, image_type="bg_removed", user_id=1, score=None, score_source=None, title=None):
    """display three clothing items stacked vertically"""
    
    # load images
    shirt_img = load_clothing_image(shirt_id, image_type, user_id)
    pants_img = load_clothing_image(pants_id, image_type, user_id)
    shoes_img = load_clothing_image(shoes_id, image_type, user_id)
    
    # check if any images failed to load
    images = [shirt_img, pants_img, shoes_img]
    labels = [shirt_id, pants_id, shoes_id]
    item_types = ['shirt', 'pants', 'shoes']
    
    if not any(images):
        print("no images could be loaded for this outfit")
        return
    
    # create figure
    fig = plt.figure(figsize=(8, 15))
    
    # use provided title or create default
    if title is None:
        title = "outfit combination"
    
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # create each subplot explicitly
    for i, (img, label, item_type) in enumerate(zip(images, labels, item_types)):
        ax = plt.subplot(3, 1, i + 1)
        
        if img is not None:
            ax.imshow(img)
            ax.set_title(f"{label}", fontsize=12, fontweight='bold')
        else:
            # show placeholder for missing image
            ax.text(0.5, 0.5, f"{label}\n(image not found)", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax.set_title(f"{item_type}: {label}", fontsize=12, fontweight='bold')
        
        ax.axis('off')  # hide axes
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def display_outfit_grid(outfits_list, image_type="bg_removed", user_id=1, max_outfits=12):
    """display multiple outfits in a grid layout"""
    
    if not outfits_list:
        print("no outfits to display")
        return
    
    # limit number of outfits
    outfits_to_show = outfits_list[:max_outfits]
    num_outfits = len(outfits_to_show)
    
    # calculate grid dimensions
    cols = 3  # 3 columns (shirt, pants, shoes)
    rows = num_outfits
    
    # create figure
    fig = plt.figure(figsize=(12, 4 * rows))
    fig.suptitle(f"top {num_outfits} outfit recommendations", fontsize=16, fontweight='bold')
    
    for outfit_idx, outfit in enumerate(outfits_to_show):
        # extract clothing ids
        shirt_id = outfit.get('shirt')
        pants_id = outfit.get('pants')
        shoes_id = outfit.get('shoes')
        score = outfit.get('score')
        
        # load images
        clothing_ids = [shirt_id, pants_id, shoes_id]
        item_types = ['shirt', 'pants', 'shoes']
        
        for item_idx, (clothing_id, item_type) in enumerate(zip(clothing_ids, item_types)):
            ax = plt.subplot(rows, cols, outfit_idx * cols + item_idx + 1)
            
            img = load_clothing_image(clothing_id, image_type, user_id)
            
            if img is not None:
                ax.imshow(img)
            else:
                ax.text(0.5, 0.5, f"{clothing_id}\n(not found)", 
                       ha='center', va='center', transform=ax.transAxes,
                       fontsize=8, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            
            # add title with score for first item
            if item_idx == 0 and score is not None:
                ax.set_title(f"#{outfit_idx+1} - {score:.1%}\n{item_type}: {clothing_id}", 
                           fontsize=10, fontweight='bold')
            else:
                ax.set_title(f"{item_type}: {clothing_id}", fontsize=10)
            
            ax.axis('off')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def show_items_grid(item_type, available_items, image_type="bg_removed", user_id=1):
    """display available items in a grid for selection"""
    
    if not available_items:
        print(f"no {item_type} items available")
        return
    
    num_items = len(available_items)
    cols = min(5, num_items)  # max 5 columns
    rows = (num_items + cols - 1) // cols  # ceiling division
    
    fig = plt.figure(figsize=(3*cols, 3*rows))
    fig.suptitle(f"select {item_type}", fontsize=16, fontweight='bold')
    
    for i, clothing_id in enumerate(available_items):
        ax = plt.subplot(rows, cols, i + 1)
        
        img = load_clothing_image(clothing_id, image_type, user_id)
        
        if img is not None:
            ax.imshow(img)
        else:
            ax.text(0.5, 0.5, f"{clothing_id}\n(not found)", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=8, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        
        ax.set_title(f"{i+1}. {clothing_id}", fontsize=10, fontweight='bold')
        ax.axis('off')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()


def get_outfit_rating():
    """get user rating for displayed outfit"""
    while True:
        try:
            rating_input = input("\nhow much do you like this outfit? (1-5, or 'skip'): ").strip().lower()
            if rating_input in ['skip', 's', '']:
                return None
            rating = int(rating_input)
            if 1 <= rating <= 5:
                return rating
            print("please enter a number from 1 to 5")
        except ValueError:
            print("please enter a valid number or 'skip'")


def check_and_retrain_model(generator):
    """check if model should be retrained and do it with better error handling"""
    # get current rating count
    ratings = generator.db.get_all_ratings(generator.user_id)
    rating_count = len(ratings)
    
    # train model every 5 ratings
    if rating_count >= 5 and rating_count % 5 == 0:
        print(f"\ntraining new model with {rating_count} ratings...")
        
        try:
            # check if we have enough diverse data
            rating_values = [r['rating'] for r in ratings]
            unique_ratings = len(set(rating_values))
            
            if unique_ratings < 2:
                print("❌ need ratings of different values to train (all ratings are the same)")
                return
            
            from src.recommender.random_forest import train_user_model_from_ratings
            result = train_user_model_from_ratings(
                generator.user_id, 
                generator.db, 
                min_ratings=5
            )
            
            if result:
                model, training_results = result
                # update generator's model
                from src.recommender.random_forest import get_user_model
                generator.model = get_user_model(generator.user_id, generator.db)
                # clear cached predictions since model changed
                generator.invalidate_cache()
                
                accuracy = training_results.get('test_accuracy', 0)
                print(f"✅ model updated! accuracy: {accuracy:.1%}")
            else:
                print("❌ model training returned None")
                
        except Exception as e:
            print(f"❌ error training model: {e}")
            import traceback
            print("Debug traceback:")
            traceback.print_exc()
            
            # fallback: continue without model update
            print("🔄 continuing with existing model...")
            
    elif rating_count < 5:
        print(f"📊 {rating_count}/5 ratings collected (need 5 to train first model)")
    else:
        remaining = 5 - (rating_count % 5)
        print(f"📊 {remaining} more ratings until next model update")


def natural_sort_key(item_id):
    """helper for natural sorting (shirt_1, shirt_2, ..., shirt_10)"""
    import re
    parts = re.split(r'(\d+)', item_id)
    return [int(part) if part.isdigit() else part for part in parts]


# === MAIN MENU SYSTEM ===

def show_main_menu():
    """display the main menu"""
    width = 91
    print("\n" + "="*width)
    print(r"""
         _______  __   __  ______    _______  _______  ______   _______  ______  
        |       ||  | |  ||    _ |  |       ||   _   ||      | |       ||      | 
        |_     _||  |_|  ||   | ||  |    ___||  |_|  ||  _    ||    ___||  _    |
          |   |  |       ||   |_||_ |   |___ |       || | |   ||   |___ | | |   |
          |   |  |       ||    __  ||    ___||       || |_|   ||    ___|| |_|   |
          |   |  |   _   ||   |  | ||   |___ |   _   ||       ||   |___ |       |
          |___|  |__| |__||___|  |_||_______||__| |__||______| |_______||______| 
    """.center(width))
    print("smart wardrobe management system".center(width))
    print("="*width)
    
    print("\nmain menu:")
    print("  • 1. view wardrobe")
    print("  • 2. edit wardrobe") 
    print("  • 3. random outfit (outfit of the day)")
    print("  • 4. outfit with chosen item")
    print("  • 5. exit")


def view_wardrobe(db, user_id):
    """view wardrobe items by category with visual display"""
    print("\n" + "="*50)
    print("VIEW WARDROBE")
    print("="*50)
    
    while True:
        print("\nselect category to view:")
        print("  • 1. shirts")
        print("  • 2. pants") 
        print("  • 3. shoes")
        print("  • 4. back to main menu")
        
        choice = input("choose option (1-4): ").strip()
        
        if choice == "4":
            break
        elif choice in ["1", "2", "3"]:
            item_types = {"1": "shirt", "2": "pants", "3": "shoes"}
            item_type = item_types[choice]
            
            # get items from database
            items = db.get_wardrobe_items(user_id, item_type)
            
            if not items:
                print(f"\nno {item_type}s found in wardrobe")
                continue
            
            # extract clothing ids and sort them naturally
            clothing_ids = [item['clothing_id'] for item in items]
            clothing_ids = sorted(clothing_ids, key=natural_sort_key)
            
            print(f"\n{item_type.upper()}S ({len(clothing_ids)} items):")
            
            # show items visually in grid
            show_items_grid(item_type, clothing_ids, user_id=user_id)
            
            input("press enter to continue...")
        else:
            print("please enter 1, 2, 3, or 4")


def edit_wardrobe(db, user_id):
    """add or delete wardrobe items"""
    print("\n" + "="*50)
    print("EDIT WARDROBE")
    print("="*50)
    
    while True:
        print("\nedit options:")
        print("  • 1. add new item")
        print("  • 2. delete item")
        print("  • 3. back to main menu")
        
        choice = input("choose option (1-3): ").strip()
        
        if choice == "3":
            break
        elif choice == "1":
            add_new_item(db, user_id)
        elif choice == "2":
            delete_item(db, user_id)
        else:
            print("please enter 1, 2, or 3")


def add_new_item(db, user_id):
    """add a single new clothing item with full processing"""
    print("\n--- add new item ---")
    
    # get item type
    while True:
        item_type = input("item type (shirt/pants/shoes): ").strip().lower()
        if item_type in ['shirt', 'pants', 'shoes']:
            break
        print("please enter 'shirt', 'pants', or 'shoes'")
    
    # get image file path
    while True:
        image_path = input("path to image file: ").strip()
        if Path(image_path).exists():
            break
        print("file not found. please enter a valid path.")
    
    # generate clothing id
    existing_items = db.get_wardrobe_items(user_id, item_type)
    existing_ids = [item['clothing_id'] for item in existing_items]
    
    # find next available number
    next_num = 1
    while f"{item_type}_{next_num}" in existing_ids:
        next_num += 1
    
    clothing_id = f"{item_type}_{next_num}"
    
    print(f"\nprocessing {clothing_id}...")
    
    try:
        # setup paths
        raw_dir = Path(f"data/wardrobe/{user_id}/raw_images")
        bg_dir = Path(f"data/wardrobe/{user_id}/bg_removed")
        processed_dir = Path(f"data/wardrobe/{user_id}/processed_images")
        
        # determine file extension
        image_ext = Path(image_path).suffix
        raw_file = raw_dir / f"{clothing_id}{image_ext}"
        
        # copy to raw directory
        shutil.copy2(image_path, raw_file)
        print(f"✓ copied to {raw_file}")
        
        # process image
        bg_removed_file = bg_dir / f"{clothing_id}_bg_removed.png"
        processed_file = processed_dir / f"{clothing_id}_processed.png"
        
        from src.preprocessing.image_processor import preprocess_clothing_image_stages
        bg_removed_img, processed_img = preprocess_clothing_image_stages(
            raw_file,
            bg_removed_file,
            processed_file
        )
        print("✓ image preprocessing complete")
        
        # extract cv features
        from src.feature_extraction.cv_features import extract_all_features
        cv_features = extract_all_features(processed_file)
        print("✓ computer vision features extracted")
        
        # add to database
        file_path = f"data/wardrobe/{user_id}/bg_removed/{clothing_id}_bg_removed.png"
        wardrobe_item_id = db.add_wardrobe_item(user_id, clothing_id, item_type, file_path, cv_features)
        print("✓ added to database")
        
        # extract genai features
        try:
            from src.feature_extraction.genai_features import extract_genai_features
            genai_features = extract_genai_features(processed_file)
            db.add_genai_features(wardrobe_item_id, genai_features)
            print("✓ ai features extracted")
        except Exception as e:
            print(f"⚠ ai feature extraction failed: {e}")
            print("  (item still added, but without ai analysis)")
        
        # clear feature cache since wardrobe changed
        db.clear_outfit_features(user_id)
        print("✓ feature cache cleared")
        
        print(f"\n🎉 successfully added {clothing_id} to your wardrobe!")
        
    except Exception as e:
        print(f"❌ error adding item: {e}")
        # clean up any partial files
        for file_path in [raw_file, bg_removed_file, processed_file]:
            if file_path.exists():
                file_path.unlink()


def delete_item(db, user_id):
    """delete a clothing item and all references"""
    print("\n--- delete item ---")
    
    # get item type first
    while True:
        item_type = input("item type to delete from (shirt/pants/shoes): ").strip().lower()
        if item_type in ['shirt', 'pants', 'shoes']:
            break
        print("please enter 'shirt', 'pants', or 'shoes'")
    
    # get available items
    items = db.get_wardrobe_items(user_id, item_type)
    
    if not items:
        print(f"no {item_type}s found in wardrobe")
        return
    
    # sort and display options
    clothing_ids = [item['clothing_id'] for item in items]
    clothing_ids = sorted(clothing_ids, key=natural_sort_key)
    
    # show items visually
    show_items_grid(item_type, clothing_ids, user_id=user_id)
    
    # get selection
    print(f"\navailable {item_type}s:")
    for i, clothing_id in enumerate(clothing_ids, 1):
        print(f"  {i}. {clothing_id}")
    
    while True:
        try:
            selection = int(input(f"select {item_type} to delete (1-{len(clothing_ids)}): "))
            if 1 <= selection <= len(clothing_ids):
                clothing_id = clothing_ids[selection - 1]
                break
            else:
                print(f"please enter a number between 1 and {len(clothing_ids)}")
        except ValueError:
            print("please enter a valid number")
    
    # confirm deletion
    confirm = input(f"are you sure you want to delete {clothing_id}? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("deletion cancelled")
        return
    
    try:
        # soft delete from database (marks as inactive)
        db.delete_wardrobe_item(user_id, clothing_id)
        
        # delete any outfit ratings containing this item
        ratings = db.get_all_ratings(user_id)
        deleted_ratings = 0
        
        for rating in ratings:
            if (rating['shirt_id'] == clothing_id or 
                rating['pants_id'] == clothing_id or 
                rating['shoes_id'] == clothing_id):
                deleted_ratings += 1
        
        # clear all caches since wardrobe changed
        db.clear_outfit_features(user_id)
        db.clear_outfit_predictions(user_id)
        
        print(f"✓ {clothing_id} deleted from wardrobe")
        if deleted_ratings > 0:
            print(f"✓ {deleted_ratings} related outfit ratings removed")
        print("✓ caches cleared")
        
        print(f"\n🗑️ successfully deleted {clothing_id}")
        print("note: image files are kept on disk but item is inactive")
        
    except Exception as e:
        print(f"❌ error deleting item: {e}")


def random_outfit(db, user_id):
    """generate random outfit recommendation"""
    print("\n" + "="*50)
    print("OUTFIT OF THE DAY")
    print("="*50)
    
    try:
        from src.recommender.outfit_generator import CachedOutfitGenerator
        generator = CachedOutfitGenerator(user_id, db)
        outfit = generator.get_random_outfit()
        
        if outfit:
            display_outfit_from_dict(outfit, user_id=user_id)
            
            # get user rating
            rating = get_outfit_rating()
            if rating:
                generator.save_outfit_rating(outfit, rating)
                check_and_retrain_model(generator)
        else:
            print("❌ no outfit could be generated")
            
    except Exception as e:
        print(f"❌ error generating outfit: {e}")


def outfit_with_chosen_item(db, user_id):
    """generate outfit including a specific chosen item"""
    print("\n" + "="*50)
    print("OUTFIT WITH CHOSEN ITEM")
    print("="*50)
    
    try:
        from src.recommender.outfit_generator import CachedOutfitGenerator
        generator = CachedOutfitGenerator(user_id, db)
        
        # get item type
        while True:
            item_type = input("choose item type to keep (shirt/pants/shoes): ").strip().lower()
            if item_type in ['shirt', 'pants', 'shoes']:
                break
            print("please enter 'shirt', 'pants', or 'shoes'")
        
        # load wardrobe items
        generator.load_wardrobe_items()
        available_items = generator.wardrobe_items[item_type]
        
        if not available_items:
            print(f"no {item_type}s found in wardrobe")
            return
        
        # sort items naturally
        available_items = sorted(available_items, key=natural_sort_key)
        
        # show items visually
        show_items_grid(item_type, available_items, user_id=user_id)
        
        # get selection
        while True:
            try:
                selection = int(input(f"select {item_type} by number (1-{len(available_items)}): "))
                if 1 <= selection <= len(available_items):
                    item_id = available_items[selection - 1]
                    break
                else:
                    print(f"please enter a number between 1 and {len(available_items)}")
            except ValueError:
                print("please enter a valid number")
        
        # generate outfit
        outfit = generator.complete_outfit(item_type, item_id)
        
        if outfit:
            display_outfit_from_dict(outfit, user_id=user_id)
            
            # get user rating
            rating = get_outfit_rating()
            if rating:
                generator.save_outfit_rating(outfit, rating)
                check_and_retrain_model(generator)
        else:
            print("❌ no outfit could be generated with that item")
            
    except Exception as e:
        print(f"❌ error generating outfit: {e}")


def get_outfit_choice(generator):
    """handle user input for outfit recommendation type (legacy function for compatibility)"""
    width = 91
    print("\n" + "="*width)
    print(r"""
         _______  __   __  ______    _______  _______  ______   _______  ______  
        |       ||  | |  ||    _ |  |       ||   _   ||      | |       ||      | 
        |_     _||  |_|  ||   | ||  |    ___||  |_|  ||  _    ||    ___||  _    |
          |   |  |       ||   |_||_ |   |___ |       || | |   ||   |___ | | |   |
          |   |  |       ||    __  ||    ___||       || |_|   ||    ___|| |_|   |
          |   |  |   _   ||   |  | ||   |___ |   _   ||       ||   |___ |       |
          |___|  |__| |__||___|  |_||_______||__| |__||______| |_______||______| 
    """.center(width))
    print("a project by daniel cao".center(width))
    print("="*width)
    
    # show cache stats
    if hasattr(generator, 'get_cache_stats'):
        cache_stats = generator.get_cache_stats()
    
    print("\nchoose an outfit creation option:")
    print("  • 1. random outfit")
    print("  • 2. outfit with chosen item")
    
    while True:
        choice = input("enter option (1 or 2): ").strip()
        
        outfit = None
        if choice == "1":
            outfit = generator.get_random_outfit()
        
        elif choice == "2":
            # get item type
            while True:
                item_type = input("pick item type (shirt/pants/shoes): ").strip().lower()
                if item_type in ['shirt', 'pants', 'shoes']:
                    break
                print("please enter 'shirt', 'pants', or 'shoes' only")
            
            # ensure wardrobe items are loaded
            if not hasattr(generator, 'wardrobe_items') or generator.wardrobe_items is None:
                generator.load_wardrobe_items()
            
            # sort items by id (natural sorting for numbered ids)
            available_items = generator.wardrobe_items[f"{item_type}"]
            available_items = sorted(available_items, key=natural_sort_key)
            
            if not available_items:
                print(f"no {item_type} items found in wardrobe")
                continue
            
            # show items visually in grid
            show_items_grid(item_type, available_items)
            
            # get selection by number
            while True:
                try:
                    selection = int(input(f"select {item_type} by number (1-{len(available_items)}): "))
                    if 1 <= selection <= len(available_items):
                        item_id = available_items[selection - 1]
                        break
                    else:
                        print(f"please enter a number between 1 and {len(available_items)}")
                except ValueError:
                    print("please enter a valid number")
            
            outfit = generator.complete_outfit(item_type, item_id)
        
        else:
            print("please enter 1 or 2 only")
            continue
        
        # display outfit and get rating
        if outfit:
            display_outfit_from_dict(outfit, image_type="bg_removed", user_id=generator.user_id)
            
            # get user rating
            rating = get_outfit_rating()
            if rating:
                generator.save_outfit_rating(outfit, rating)
                
                # check if we should retrain
                check_and_retrain_model(generator)
        else:
            print("no outfit could be generated")
        
        return outfit


def main_menu(db, user_id):
    """main application loop"""
    
    while True:
        show_main_menu()
        
        choice = input("\nchoose option (1-5): ").strip()
        
        if choice == "1":
            view_wardrobe(db, user_id)
        elif choice == "2":
            edit_wardrobe(db, user_id)
        elif choice == "3":
            random_outfit(db, user_id)
        elif choice == "4":
            outfit_with_chosen_item(db, user_id)
        elif choice == "5":
            print("\nthank you for using threaded!")
            break
        else:
            print("please enter a number from 1-5")