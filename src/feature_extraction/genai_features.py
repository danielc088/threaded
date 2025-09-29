"""
extracts semantic clothing features using anthropic's claude (multimodal)
analyses style, formality, and pattern information for wardrobe items
basically gets claude to look at your clothes and tell you what vibe they are
"""

import os
import base64
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# load api key
load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def encode_image(image_path: str) -> str:
    """encode image file into base64 for claude multimodal input"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_genai_features(image_path: str) -> dict:
    """
    send image to claude and extract semantic fashion features
    returns dict with pattern_type, formality_score, versatility_score, etc
    """
    base64_img = encode_image(image_path)

    prompt = """
    analyse this clothing image and classify the following fields in strict json:
    - pattern_type: one of [striped, checkered, plain, floral, graphic_pattern, other]
    - has_graphic: boolean (true if logos, text, or large graphic designs visible)
    - style: one of [casual, business, streetwear, vintage, formal, athletic]
    - fit_type: one of [slim, regular, oversized, loose]
    - formality_score: float 0-1 (0=very casual, 1=very formal)
    - versatility_score: float 0-1 (0=specific occasion only, 1=works anywhere)
    - season_suitability: one of [spring, summer, fall, winter, all_season]
    - color_description: brief description of main colours

    respond only with compact json. no explanations.
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt.strip()},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_img,
                        },
                    },
                ],
            }
        ],
    )

    raw_text = response.content[0].text.strip()

    try:
        # remove opening ``` or ```json
        raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
        # remove closing ```
        raw_text = re.sub(r"```$", "", raw_text).strip()
        features = json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"error parsing response: {raw_text}")
        features = {}

    # ensure required fields exist with defaults
    defaults = {
        'pattern_type': 'plain',
        'has_graphic': False,
        'style': 'casual',
        'fit_type': 'regular',
        'formality_score': 0.5,
        'versatility_score': 0.5,
        'season_suitability': 'all_season',
        'color_description': 'unknown'
    }
    
    for key, default_value in defaults.items():
        if key not in features:
            features[key] = default_value
    
    # handle shoes special case (no fit_type)
    clothing_id = Path(image_path).stem.replace("_processed", "")
    if clothing_id.startswith("shoe") or "shoe" in clothing_id.lower():
        features["fit_type"] = "N/A"
        features.setdefault("has_graphic", False)
    
    return features


def process_wardrobe_genai(input_dir: str, user_id: int, db):
    """
    extract genai features for all processed images and save to database
    skips items that already have genai features
    """
    input_path = Path(input_dir)
    image_files = list(input_path.glob("*_processed.png"))

    print(f"found {len(image_files)} processed images to analyse")

    # get existing genai features to avoid reprocessing
    existing_genai = db.get_genai_features(user_id)
    existing_clothing_ids = {item['clothing_id'] for item in existing_genai}

    processed_count = 0
    
    for img_file in image_files:
        clothing_id = img_file.name.replace("_processed.png", "")

        if clothing_id in existing_clothing_ids:
            continue

        # get wardrobe item id from database
        wardrobe_items = db.get_wardrobe_items(user_id)
        wardrobe_item = next((item for item in wardrobe_items if item['clothing_id'] == clothing_id), None)
        
        if not wardrobe_item:
            print(f"warning: {clothing_id} not found in wardrobe items")
            continue

        # extract genai features
        features = extract_genai_features(str(img_file))
        
        # add to database
        db.add_genai_features(wardrobe_item['id'], features)
        processed_count += 1
        print(f"added genai features for {clothing_id}")

    print(f"processed {processed_count} new genai features")
    return processed_count