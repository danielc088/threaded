"""
displays clothing item images and outfit combinations
supports both background-removed and processed versions
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import math
from pathlib import Path


def display_outfit(shirt_id, pants_id, shoes_id, image_type="bg_removed", figsize=(6, 12)):
    """
    display an outfit combination with images vertically stacked
    
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
    
    # create the plot - vertical layout like a real outfit
    fig, axes = plt.subplots(3, 1, figsize=figsize)
    
    # load and display each image
    items = [
        (shirt_path, "shirt", shirt_id),
        (pants_path, "pants", pants_id), 
        (shoes_path, "shoes", shoes_id)
    ]
    
    for i, (path, title, item_id) in enumerate(items):
        try:
            img = mpimg.imread(str(path))
            axes[i].imshow(img)
            axes[i].set_title(f"{title}")
            axes[i].axis('off')
        except Exception as e:
            axes[i].text(0.5, 0.5, f"error loading\n{item_id}", 
                        ha='center', va='center', transform=axes[i].transAxes)
            axes[i].set_title(f"{title}")
            axes[i].axis('off')
    
    plt.suptitle(f"recommended outfit", fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

def show_items_grid(item_type, items, image_dir="data/wardrobe/bg_removed", suffix="_bg_removed.png", columns=5):
    """
    display clothing items in a grid with numbers for selection
    """
    items = sorted(items)
    n_items = len(items)
    rows = math.ceil(n_items / columns)
    
    fig, axes = plt.subplots(rows, columns, figsize=(columns*2, rows*2))
    axes = axes.flatten()
    
    for i, item_id in enumerate(items):
        img_path = Path(image_dir) / f"{item_id}{suffix}"
        if img_path.exists():
            img = plt.imread(str(img_path))
            axes[i].imshow(img)
            axes[i].axis('off')
            axes[i].set_title(f"{i+1}", fontsize=8)
        else:
            axes[i].axis('off')
            axes[i].set_title(f"missing\n{i+1}", fontsize=8)
    
    # hide empty subplots
    for j in range(i+1, len(axes)):
        axes[j].axis('off')
    
    plt.suptitle(f"Select a {item_type} by number", fontsize=12)
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
        print("no outfit to display")
        return
    
    # extract IDs from the outfit dict
    shirt_id = outfit_dict.get('shirt', '')
    pants_id = outfit_dict.get('pants', '')  
    shoes_id = outfit_dict.get('shoes', '')
    
    # display score and any fixed item info
    if 'score' in outfit_dict:
        print(f"outfit score: {outfit_dict['score']*100:.1f}%")

    if 'fixed_item' in outfit_dict:
        print(f"built around: {outfit_dict['fixed_item']}")
    
    display_outfit(shirt_id, pants_id, shoes_id, image_type)
    
def get_outfit_choice(generator):
    """handle user input for outfit recommendation type"""
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
    print("\nchoose an outfit creation option:")
    print("  • 1. Random outfit")
    print("  • 2. Outfit with chosen item")
    
    while True:
        choice = input("enter option (1 or 2): ").strip()
        
        if choice == "1":
            return generator.get_random_outfit()
        
        elif choice == "2":
            # get item type
            while True:
                item_type = input("pick item type (shirt/pants/shoes): ").strip().lower()
                if item_type in ['shirt', 'pants', 'shoes']:
                    break
                print("please enter 'shirt', 'pants', or 'shoes' only")
            
            # ensure wardrobe items are loaded
            if generator.wardrobe_items is None:
                generator.load_wardrobe_items()
            
            available_items = sorted(generator.wardrobe_items[f"{item_type}"])
            
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
            
            return generator.complete_outfit(item_type, item_id)
        
        else:
            print("please enter 1 or 2 only")
