"""
outfit visualisation module
displays clothing item images and outfit combinations
supports both background-removed and processed versions
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path
import os


def display_outfit(shirt_id, pants_id, shoes_id, image_type="bg_removed", figsize=(6, 12)):
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
        print("missing image files:")
        for missing in missing_files:
            print(f"  - {missing}")
        return
    
    # create the plot
    fig, axes = plt.subplots(3, 1, figsize=figsize)
    
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
            axes[i].set_title(f"{title}")
            axes[i].axis('off')
        except Exception as e:
            axes[i].text(0.5, 0.5, f"Error loading\n{item_id}", 
                        ha='center', va='center', transform=axes[i].transAxes)
            axes[i].set_title(f"{title}")
            axes[i].axis('off')
    
    plt.suptitle(f"Reccomended outfit", fontsize=14, fontweight='bold')
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
        print(f"outfit score: {outfit_dict['score']:.3f}")
    
    display_outfit(shirt_id, pants_id, shoes_id, image_type)


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
        print("no outfit recommendations available")
        return
    
    # display it
    display_outfit_from_dict(outfit, image_type="bg_removed")
    
    return outfit
