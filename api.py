"""
api.py - REST API wrapper for existing threaded functionality
exposes all your existing code as API endpoints for React Native
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path
import shutil
import json
import traceback

# add project root to path (same as before)
sys.path.append(str(Path(__file__).parent))

# import all your existing code (zero changes needed!)
from data.database.schema import create_database
from data.database.models import WardrobeDB
from src.recommender.outfit_generator import CachedOutfitGenerator
from src.preprocessing.image_processor import preprocess_clothing_image_stages
from src.feature_extraction.cv_features import extract_all_features
from src.feature_extraction.genai_features import extract_genai_features

app = FastAPI(title="Threaded API", version="1.0.0")

# enable CORS for React Native
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# setup database (same as your main.py)
db_path = create_database("data/database/threaded.db")
db = WardrobeDB(db_path)
user_id = 1

# create directories (same as before)
user_dirs = [
    f"data/wardrobe/{user_id}/raw_images",
    f"data/wardrobe/{user_id}/bg_removed", 
    f"data/wardrobe/{user_id}/processed_images"
]

for dir_path in user_dirs:
    Path(dir_path).mkdir(parents=True, exist_ok=True)

Path("models").mkdir(exist_ok=True)

# STARTUP - Only train model if needed, don't pre-compute features
print("\n=== STARTUP: Checking system ===")
try:
    model_path = Path(f"models/user_{user_id}/outfit_recommender_latest.pkl")
    ratings = db.get_all_ratings(user_id)
    
    if not model_path.exists() and len(ratings) >= 5:
        print(f"No model found but {len(ratings)} ratings available - training initial model...")
        from src.recommender.random_forest import train_user_model_from_ratings
        train_user_model_from_ratings(user_id, db, min_ratings=5)
        print("✓ Initial model trained successfully")
    elif model_path.exists():
        print(f"✓ Model exists")
    else:
        print("No trained model yet - rate 5 outfits to train your first model!")
    
    # Check if transformer exists
    transformer_path = Path(f"models/user_{user_id}/feature_transformer.pkl")
    if transformer_path.exists():
        print(f"✓ Feature transformer exists")
    else:
        print("⚠ No feature transformer - will be created on first outfit request")
        
except Exception as e:
    print(f"✗ Startup check failed: {e}")
    import traceback
    traceback.print_exc()
print("=== STARTUP COMPLETE ===\n")

# pydantic models for API
class OutfitRating(BaseModel):
    shirt_id: str
    pants_id: str
    shoes_id: str
    rating: int
    notes: Optional[str] = None

class OutfitRequest(BaseModel):
    item_type: str
    item_id: str

# === API ENDPOINTS ===

@app.get("/")
def root():
    return {"message": "Threaded API is running"}

@app.get("/wardrobe/stats")
def get_wardrobe_stats():
    """get wardrobe statistics - uses your existing db.get_database_stats()"""
    stats = db.get_database_stats(user_id)
    return stats

@app.get("/wardrobe/items")
def get_wardrobe_items(item_type: Optional[str] = None):
    """get wardrobe items - uses your existing db.get_wardrobe_items()"""
    items = db.get_wardrobe_items(user_id, item_type)
    
    # add natural sorting
    def natural_sort_key(item):
        import re
        parts = re.split(r'(\d+)', item['clothing_id'])
        return [int(part) if part.isdigit() else part for part in parts]
    
    return sorted(items, key=natural_sort_key)

@app.post("/wardrobe/items")
async def add_wardrobe_item(
    item_type: str,
    file: UploadFile = File(...)
):
    """add new wardrobe item - uses all your existing processing code"""
    
    print(f"\n=== UPLOAD DEBUG ===")
    print(f"Received: filename={file.filename}, content_type={file.content_type}, item_type={item_type}")
    
    try:
        # generate clothing id (same logic as your add_new_item function)
        existing_items = db.get_wardrobe_items(user_id, item_type)
        existing_ids = [item['clothing_id'] for item in existing_items]
        
        next_num = 1
        while f"{item_type}_{next_num}" in existing_ids:
            next_num += 1
        
        clothing_id = f"{item_type}_{next_num}"
        print(f"Generated clothing_id: {clothing_id}")
        
        # save uploaded file
        raw_dir = Path(f"data/wardrobe/{user_id}/raw_images")
        file_ext = Path(file.filename).suffix if file.filename else '.jpg'
        if not file_ext:
            file_ext = '.jpg'
        raw_file = raw_dir / f"{clothing_id}{file_ext}"
        
        print(f"Saving to: {raw_file}")
        
        with open(raw_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"File saved - exists: {raw_file.exists()}, size: {raw_file.stat().st_size if raw_file.exists() else 'N/A'} bytes")
        
        # process image (uses your existing preprocessing)
        bg_dir = Path(f"data/wardrobe/{user_id}/bg_removed")
        processed_dir = Path(f"data/wardrobe/{user_id}/processed_images")
        
        bg_removed_file = bg_dir / f"{clothing_id}_bg_removed.png"
        processed_file = processed_dir / f"{clothing_id}_processed.png"
        
        print(f"Starting image preprocessing...")
        print(f"  Input: {raw_file}")
        print(f"  BG removed output: {bg_removed_file}")
        print(f"  Processed output: {processed_file}")
        
        # call your existing preprocessing function
        bg_removed_img, processed_img = preprocess_clothing_image_stages(
            raw_file, bg_removed_file, processed_file
        )
        
        print(f"Preprocessing complete!")
        print(f"  BG removed exists: {bg_removed_file.exists()}")
        print(f"  Processed exists: {processed_file.exists()}")
        
        # extract features (uses your existing feature extraction)
        print(f"Extracting CV features...")
        cv_features = extract_all_features(processed_file)
        print(f"CV features extracted: {list(cv_features.keys())}")
        
        # add to database (uses your existing database methods)
        file_path = f"data/wardrobe/{user_id}/bg_removed/{clothing_id}_bg_removed.png"
        print(f"Adding to database...")
        wardrobe_item_id = db.add_wardrobe_item(user_id, clothing_id, item_type, file_path, cv_features)
        print(f"Added to database with ID: {wardrobe_item_id}")
        
        # extract genai features (uses your existing genai extraction)
        try:
            print(f"Extracting GenAI features...")
            genai_features = extract_genai_features(processed_file)
            db.add_genai_features(wardrobe_item_id, genai_features)
            print(f"GenAI features added")
        except Exception as e:
            print(f"GenAI feature extraction failed (non-critical): {e}")
        
        # ONLY clear predictions (not features or transformer)
        print(f"Clearing prediction cache...")
        db.clear_outfit_predictions(user_id)
        
        # DON'T rebuild transformer or pre-compute features
        # They will be computed lazily as outfits are requested
        
        # Retrain model if enough ratings
        ratings = db.get_all_ratings(user_id)
        if len(ratings) >= 5:
            print(f"Retraining model...")
            try:
                from src.recommender.random_forest import train_user_model_from_ratings
                train_user_model_from_ratings(user_id, db, min_ratings=5)
                print(f"Model retrained successfully")
            except Exception as e:
                print(f"Model retraining failed: {e}")
        
        print(f"=== UPLOAD SUCCESS ===\n")
        
        return {
            "success": True,
            "clothing_id": clothing_id,
            "message": f"successfully added {clothing_id}"
        }
        
    except Exception as e:
        print(f"\n=== UPLOAD ERROR ===")
        print(f"Error: {e}")
        traceback.print_exc()
        print(f"===================\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/wardrobe/items/{clothing_id}")
def delete_wardrobe_item(clothing_id: str):
    """delete wardrobe item - uses your existing db.delete_wardrobe_item()"""
    
    try:
        # check if item exists
        items = db.get_wardrobe_items(user_id)
        item = next((i for i in items if i['clothing_id'] == clothing_id), None)
        
        if not item:
            raise HTTPException(status_code=404, detail="clothing item not found")
        
        print(f"\n=== DELETING {clothing_id} ===")
        
        # delete using your existing method
        db.delete_wardrobe_item(user_id, clothing_id)
        print(f"Item soft-deleted from database")
        
        # ONLY clear predictions (not features or transformer)
        db.clear_outfit_predictions(user_id)
        print(f"Cleared prediction cache")
        
        # DON'T rebuild transformer or pre-compute features
        # Old cached features will just be ignored
        
        # Retrain model with updated data
        ratings = db.get_all_ratings(user_id)
        if len(ratings) >= 5:
            print(f"Retraining model...")
            try:
                from src.recommender.random_forest import train_user_model_from_ratings
                train_user_model_from_ratings(user_id, db, min_ratings=5)
                print(f"Model retrained successfully")
            except Exception as e:
                print(f"Model retraining failed: {e}")
        
        print(f"=== DELETE SUCCESS ===\n")
        
        return {
            "success": True,
            "message": f"deleted {clothing_id}"
        }
        
    except Exception as e:
        print(f"\n=== DELETE ERROR ===")
        print(f"Error: {e}")
        traceback.print_exc()
        print(f"===================\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/outfits/random")
def get_random_outfit():
    """generate random outfit - uses your existing CachedOutfitGenerator"""
    
    try:
        # use your existing outfit generator
        generator = CachedOutfitGenerator(user_id, db)
        outfit = generator.get_random_outfit()
        
        if outfit:
            return outfit
        else:
            raise HTTPException(status_code=404, detail="no outfit could be generated")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/outfits/complete")
def complete_outfit(request: OutfitRequest):
    """generate outfit with chosen item - uses your existing CachedOutfitGenerator"""
    
    try:
        # use your existing outfit generator
        generator = CachedOutfitGenerator(user_id, db)
        outfit = generator.complete_outfit(request.item_type, request.item_id)
        
        if outfit:
            return outfit
        else:
            raise HTTPException(status_code=404, detail="no outfit could be generated with that item")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/outfits/rate")
def rate_outfit(rating: OutfitRating):
    """save outfit rating - uses your existing db.save_outfit_rating()"""
    
    try:
        # use your existing rating save method
        db.save_outfit_rating(
            user_id,
            rating.shirt_id,
            rating.pants_id,
            rating.shoes_id,
            rating.rating,
            source='mobile',
            notes=rating.notes
        )
        
        # check for model retraining (uses your existing logic)
        ratings = db.get_all_ratings(user_id)
        rating_count = len(ratings)
        
        should_retrain = rating_count >= 5 and rating_count % 5 == 0
        
        return {
            "success": True,
            "message": f"rated {rating.rating}/5 stars",
            "rating_count": rating_count,
            "should_retrain": should_retrain
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/model/retrain")
def retrain_model():
    """retrain ML model - uses your existing train_user_model_from_ratings()"""
    
    try:
        from src.recommender.random_forest import train_user_model_from_ratings
        
        result = train_user_model_from_ratings(user_id, db, min_ratings=5)
        
        if result:
            model, training_results = result
            accuracy = training_results.get('test_accuracy', 0)
            
            # clear cache so new model is used
            generator = CachedOutfitGenerator(user_id, db)
            generator.invalidate_cache()
            
            return {
                "success": True,
                "message": "model retrained successfully",
                "accuracy": accuracy
            }
        else:
            return {
                "success": False,
                "message": "not enough ratings for training"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ratings")
def get_ratings():
    """get all user ratings - uses your existing db.get_all_ratings()"""
    ratings = db.get_all_ratings(user_id)
    return ratings

# serve images for the mobile app
@app.get("/images/{clothing_id}")
def get_clothing_image(clothing_id: str):
    """serve clothing images to mobile app"""
    from fastapi.responses import FileResponse
    
    image_path = f"data/wardrobe/{user_id}/bg_removed/{clothing_id}_bg_removed.png"
    
    if Path(image_path).exists():
        return FileResponse(image_path)
    else:
        raise HTTPException(status_code=404, detail="image not found")

@app.get("/wardrobe/items/{clothing_id}/features")
def get_item_features(clothing_id: str):
    """Get detailed features for a specific clothing item"""
    
    try:
        # Get wardrobe item
        items = db.get_wardrobe_items(user_id)
        item = next((i for i in items if i['clothing_id'] == clothing_id), None)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get GenAI features
        genai_data = db.get_genai_features(user_id)
        genai_item = next((g for g in genai_data if g['clothing_id'] == clothing_id), None)
        
        # Combine CV and GenAI features
        features = {
            'clothing_id': clothing_id,
            'item_type': item['item_type'],
            'dominant_color': item.get('dominant_color'),
            'secondary_color': item.get('secondary_color'),
        }
        
        if genai_item:
            features.update({
                'style': genai_item.get('style'),
                'fit_type': genai_item.get('fit_type'),
            })
        
        # Calculate closest palette for this single item
        from src.feature_extraction.feature_engineering import OutfitFeatureEngine
        import pandas as pd
        
        engine = OutfitFeatureEngine(user_id, db)
        
        # Create a minimal dataframe with just this item's colors
        item_df = pd.DataFrame([{
            'shirt_id': clothing_id if item['item_type'] == 'shirt' else 'dummy_shirt',
            'pants_id': clothing_id if item['item_type'] == 'pants' else 'dummy_pants',
            'shoes_id': clothing_id if item['item_type'] == 'shoes' else 'dummy_shoes',
        }])
        
        # Get clothing features (which includes colors)
        item_with_features = engine.get_clothing_features_from_db(item_df)
        
        # Find closest palette using the engine's method
        palettes = db.get_color_palettes()
        
        if palettes and item.get('dominant_color'):
            best_palette = None
            best_distance = float('inf')
            
            outfit_color = item.get('dominant_color')
            outfit_lab = engine.hex_to_lab(outfit_color)
            
            if outfit_lab:
                for palette in palettes:
                    palette_colors = []
                    for i in range(1, 6):
                        color = palette.get(f'color_{i}')
                        if color:
                            palette_colors.append(color)
                    
                    if not palette_colors:
                        continue
                    
                    palette_distances = []
                    for palette_color in palette_colors:
                        palette_lab = engine.hex_to_lab(palette_color)
                        if palette_lab:
                            try:
                                from colormath.color_diff import delta_e_cie2000
                                dist = float(delta_e_cie2000(outfit_lab, palette_lab))
                                palette_distances.append(dist)
                            except:
                                continue
                    
                    if palette_distances:
                        min_dist = min(palette_distances)
                        if min_dist < best_distance:
                            best_distance = min_dist
                            best_palette = palette['name']
                
                if best_palette:
                    features['closest_palette'] = best_palette
        
        return features
        
    except Exception as e:
        print(f"Error fetching features: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
