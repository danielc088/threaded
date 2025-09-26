"""
extracts semantic clothing features using Anthropic's Claude (multimodal).
outputs a csv file with one row per clothing item.
"""

import os
import base64
import json
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# load API key
load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def encode_image(image_path: str) -> str:
    """Encode image file into base64 for Claude multimodal input."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_genai_features(image_path: str) -> dict:
    """
    send image to Claude and extract semantic fashion features.
    deturns a dict with pattern_type, has_graphic, style, fit_type.
    """
    base64_img = encode_image(image_path)

    prompt = """
    You are a fashion analysis assistant.
    Look at this clothing image and classify the following fields in strict JSON:
    - pattern_type: one of [striped, checkered, plain, floral, graphic pattern, other]
    - has_graphic: boolean (true if logos, text, or large graphic designs are visible)
    - style: one of [casual, business, streetwear, vintage, formal, athletic]
    - fit_type: one of [slim, regular, oversized, loose]

    Respond ONLY with a compact JSON object. No explanations.
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
        print("error, response was:", raw_text)
        features = {}

    clothing_id = Path(image_path).stem.replace("_processed", "")
    # shoes by default are set to N/A fit type and no graphic    
    if clothing_id.startswith("shoe") or "shoe" in clothing_id.lower():
        features.setdefault("has_graphic", False)
        features["fit_type"] = "N/A"
    
    return features


def process_wardrobe_genai(input_dir: str, output_csv: str):
    """
    extract generative ai features for all images in a folder.
    skips items that are already in the output CSV.
    """
    input_path = Path(input_dir)
    image_files = list(input_path.glob("*_processed.png"))

    if not image_files:
        print("No processed images found in", input_dir)
        return

    print(f"Found {len(image_files)} processed images to analyse")

    # load existing CSV if it exists
    if Path(output_csv).exists():
        existing_df = pd.read_csv(output_csv)
        existing_ids = set(existing_df["clothing_id"].astype(str).tolist())
        wardrobe_data = existing_df.to_dict("records")
        print(f"Loaded {len(existing_ids)} existing records from {output_csv}")
    else:
        existing_ids = set()
        wardrobe_data = []

    # process new images only
    new_rows = []
    for img_file in image_files:
        clothing_id = img_file.name.replace("_processed.png", "")

        if clothing_id in existing_ids:
            print(f"Skipping {clothing_id} (already in CSV)")
            continue

        print(f"Extracting GenAI features from {img_file.name}...")
        features = extract_genai_features(str(img_file))
        row = {"clothing_id": clothing_id, **features}
        new_rows.append(row)

    # append new rows
    if new_rows:
        wardrobe_data.extend(new_rows)
        df = pd.DataFrame(wardrobe_data)
        df.to_csv(output_csv, index=False)
        print(f"\nAdded {len(new_rows)} new items. Saved to {output_csv}")
    else:
        df = pd.DataFrame(wardrobe_data)
        print("\nNo new items to process, CSV left unchanged.")

    print(f"Total clothing items in CSV: {len(df)}")

    # preview
    print("\nPreview of GenAI features:")
    print(df.head())

    return df