"""
outfit visualisation module
displays clothing item images and outfit combinations
supports both background-removed and processed versions
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path
import os


def display_outfit(shirt_id, pants_id, shoes_id, image_type="bg_removed", figsize=(12, 4)):
    """
    display an outfit combination with images side by side
    
    Args:
        shirt_id: shirt identifier (e.g. "shirt_1")
        pants_id: pants identifier (e.g. "pants_1") 
        shoes_id: shoes identifier (e.g. "shoes_1")
        image_type: "bg_removed" or "processed" - which image version to show
        figsize: figure size for the display
    """
    
    # determine image directory and file extension
    if image_type == "bg_removed":
        img_dir = "data/wardrobe/bg_removed"
        suffix = "_bg_removed.png"
    elif image_type == "processed":
        img_dir = "data/wardrobe/processed_images" 
        suffix = "_processed.png"
    else:
        raise ValueError("image_type must be 'bg_removed' or 'processed'")
    
    # build file paths
    shirt_path = Path(img_dir) / f"{shirt_id}{suffix}"
    pants_path = Path(img_dir) / f"{pants_id}{suffix}"
    shoes_path = Path(img_dir) / f"{shoes_id}{suffix}"
    
    # check if files exist
    missing_files = []
    for item, path in [("shirt", shirt_path), ("pants", pants_path), ("shoes", shoes_path)]:
        if not path.exists():
            missing_files.append(f"{item}: {path}")
    
    if missing_files:
        print("Missing image files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return
    
    # create the plot
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    # load and display each image
    items = [
        (shirt_path, "Shirt", shirt_id),
        (pants_path, "Pants", pants_id), 
        (shoes_path, "Shoes", shoes_id)
    ]
    
    for i, (path, title, item_id) in enumerate(items):
        try:
            img = mpimg.imread(str(path))
            axes[i].imshow(img)
            axes[i].set_title(f"{title}\n{item_id}")
            axes[i].axis('off')
        except Exception as e:
            axes[i].text(0.5, 0.5, f"Error loading\n{item_id}", 
                        ha='center', va='center', transform=axes[i].transAxes)
            axes[i].set_title(f"{title}\n{item_id}")
            axes[i].axis('off')
    
    plt.suptitle(f"Outfit: {shirt_id} + {pants_id} + {shoes_id}", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()


def display_outfit_from_dict(outfit_dict, image_type="bg_removed"):
    """
    display outfit from dictionary format (from outfit generator)
    
    Args:
        outfit_dict: dict with keys 'shirt', 'pants', 'shoes' and optionally 'score'
        image_type: "bg_removed" or "processed"
    """
    
    if outfit_dict is None:
        print("No outfit to display")
        return
    
    # extract IDs from the outfit dict
    shirt_id = outfit_dict.get('shirt', '')
    pants_id = outfit_dict.get('pants', '')  
    shoes_id = outfit_dict.get('shoes', '')
    
    # display with score in title if available
    if 'score' in outfit_dict:
        print(f"Outfit Score: {outfit_dict['score']:.3f}")
    
    display_outfit(shirt_id, pants_id, shoes_id, image_type)


def compare_outfit_versions(shirt_id, pants_id, shoes_id):
    """
    show both background-removed and processed versions side by side
    """
    
    print("Background Removed Version:")
    display_outfit(shirt_id, pants_id, shoes_id, image_type="bg_removed")
    
    print("\nProcessed Version:")
    display_outfit(shirt_id, pants_id, shoes_id, image_type="processed")


def browse_wardrobe(image_type="bg_removed", items_per_row=5):
    """
    display all available clothing items in a grid
    
    Args:
        image_type: "bg_removed" or "processed" 
        items_per_row: how many items to show per row
    """
    
    # determine image directory and pattern
    if image_type == "bg_removed":
        img_dir = Path("data/wardrobe/bg_removed")
        pattern = "*_bg_removed.png"
    else:
        img_dir = Path("data/wardrobe/processed_images")
        pattern = "*_processed.png"
    
    # find all image files
    if not img_dir.exists():
        print(f"Directory not found: {img_dir}")
        return
    
    image_files = sorted(list(img_dir.glob(pattern)))
    
    if not image_files:
        print(f"No images found in {img_dir}")
        return
    
    print(f"Found {len(image_files)} clothing items")
    
    # calculate grid dimensions
    n_items = len(image_files)
    n_rows = (n_items + items_per_row - 1) // items_per_row  # ceiling division
    
    # create the plot
    fig, axes = plt.subplots(n_rows, items_per_row, figsize=(items_per_row * 3, n_rows * 4))
    
    # handle single row case
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    elif items_per_row == 1:
        axes = axes.reshape(-1, 1)
    
    # display each image
    for i, img_file in enumerate(image_files):
        row = i // items_per_row
        col = i % items_per_row
        
        try:
            img = mpimg.imread(str(img_file))
            axes[row, col].imshow(img)
            
            # clean up filename for title
            item_name = img_file.stem.replace("_bg_removed", "").replace("_processed", "")
            axes[row, col].set_title(item_name)
            axes[row, col].axis('off')
            
        except Exception as e:
            axes[row, col].text(0.5, 0.5, f"Error\n{img_file.name}", 
                               ha='center', va='center', transform=axes[row, col].transAxes)
            axes[row, col].axis('off')
    
    # hide unused subplots
    for i in range(len(image_files), n_rows * items_per_row):
        row = i // items_per_row
        col = i % items_per_row
        axes[row, col].axis('off')
    
    plt.suptitle(f"Wardrobe Items ({image_type} version)", fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()


def display_recommended_outfit(outfit_generator=None):
    """
    get and display a recommended outfit using the outfit generator
    """
    
    if outfit_generator is None:
        from src.recommender.outfit_generator import OutfitGenerator
        outfit_generator = OutfitGenerator()
    
    # get a random high-scoring outfit
    outfit = outfit_generator.get_random_outfit()
    
    if outfit is None:
        print("No outfit recommendations available")
        return
    
    # display it
    print("Recommended Outfit:")
    display_outfit_from_dict(outfit, image_type="bg_removed")
    
    return outfit
