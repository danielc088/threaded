"""
Preprocessing pipeline for the uploaded clothing images (my wardrobe for now)
Takes the raw ios jpg photos and makes them consistent for feature extraction later
"""

import cv2
from PIL import Image
import rembg as rb
from pathlib import Path


def load_image(image_path):
    """load image and convert to the format such that it is all consistent to work with"""
    img = cv2.imread(str(image_path))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)


def remove_background(img):
    """apply an open source rembg library. this gets rid of that orange bedsheet (or any background really...)"""
    return rb.remove(img)


def crop_transparent_space(img):
    """get rid of all the empty transparent space around the clothes"""
    bbox = img.getbbox()
    
    if bbox:
        return img.crop(bbox)
    else:
        # edge case, if something goes wrong, just return what we have
        return img


def center_and_resize(img, target_size=(800, 1000), padding=50):
    """we want to standardise everything we work with, this makes all images the same size and nicely centred"""
    
    # first get rid of excess space
    cropped = crop_transparent_space(img)
    
    # add a slight padding back
    width, height = cropped.size
    padded_img = Image.new('RGBA', (width + padding*2, height + padding*2), (0, 0, 0, 0))
    padded_img.paste(cropped, (padding, padding), cropped)
    
    # resize but keep the proportions right (otherwise the aspect ratios may look odd)
    original_width, original_height = padded_img.size
    target_width, target_height = target_size
    
    scale = min(target_width / original_width, target_height / original_height)
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    img_resized = padded_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # centre it in a standard canvas
    final_img = Image.new('RGBA', target_size, (0, 0, 0, 0))
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    final_img.paste(img_resized, (x_offset, y_offset), img_resized)
    
    return final_img


def preprocess_clothing_image(image_path, save_path=None):
    """full pipeline: takes the raw image -> cleans and standardises the image"""
    
    # load the raw photo
    img = load_image(image_path)
    
    # get rid of background 
    img_no_bg = remove_background(img)
    
    # clean it up and make it standard size
    processed_img = center_and_resize(img_no_bg)
    
    # save it if we want to keep it
    if save_path:
        processed_img.save(save_path)
    
    return processed_img


def batch_preprocess(input_dir, output_dir):
    """process the whole folder of images, skipping if already processed (this is a more long term design choice)"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # find all images in the input folder
    image_extensions = ['.jpg', '.jpeg', '.png']
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
    
    print(f"Found {len(image_files)} images to check")
    
    processed_count = 0
    skipped_count = 0
    
    for img_file in image_files:
        # check if processed version already exists
        output_file = output_path / f"{img_file.stem}_processed.png"
        
        if output_file.exists():
            print(f"Skipping {img_file.name} - already processed")
            skipped_count += 1
        else:
            print(f"Processing {img_file.name}...")
            processed = preprocess_clothing_image(img_file, output_file)
            processed_count += 1
        
    print(f"Processed: {processed_count} new images")
    print(f"Skipped: {skipped_count} already done")