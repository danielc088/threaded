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
    save results to a CSV file.
    """
    input_path = Path(input_dir)
    image_files = list(input_path.glob("*_processed.png"))

    if not image_files:
        print("No processed images found in", input_dir)
        return

    wardrobe_data = []
    for img_file in image_files:
        clothing_id = img_file.name.replace("_processed.png", "")
        features = extract_genai_features(str(img_file))
        row = {"clothing_id": clothing_id, **features}
        wardrobe_data.append(row)

    # convert to df
    df = pd.DataFrame(wardrobe_data)

    # save
    df.to_csv(output_csv, index=False)

    print(f"\nGenAI features extracted and saved to {output_csv}")
    print(f"Processed {len(df)} clothing items")
    print("\nPreview:")
    print(df.head())

    return df


if __name__ == "__main__":
    # Example usage
    process_wardrobe_genai("data/processed_images", "genai_features.csv")
