"""
threaded - database-enabled wardrobe digitization and outfit recommendation system
main entry point for the application
"""

import sys
from pathlib import Path

# add current directory to path
sys.path.append(str(Path(__file__).parent))

from data.database.schema import create_database
from data.database.models import WardrobeDB
from src.utils.outfit_viewer import main_menu


def main():
    """run the threaded wardrobe system"""
    
    # setup database and user
    db_path = create_database("data/database/threaded.db")
    db = WardrobeDB(db_path)
    user_id = 1 

    # create user directories
    user_dirs = [
        f"data/wardrobe/{user_id}/raw_images",
        f"data/wardrobe/{user_id}/bg_removed", 
        f"data/wardrobe/{user_id}/processed_images"
    ]
    
    for dir_path in user_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    Path("models").mkdir(exist_ok=True)
    
    # launch main menu
    main_menu(db, user_id)


if __name__ == "__main__":
    main()