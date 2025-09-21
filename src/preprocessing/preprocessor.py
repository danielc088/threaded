"""
preprocessing pipeline for the uploaded clothing images (my wardrobe for now)
takes the raw jpg photos and makes them consistent for feature extraction later
"""

import cv2
from PIL import Image, ImageEnhance
import rembg as rb
import numpy as np
from pathlib import Path


def load_image(image_path):
    """load image and convert to the format such that it is all consistent to work with"""
    img = cv2.imread(str(image_path))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)


def enhance_contrast_and_brightness(img, contrast_factor=1.3, brightness_factor=1.1, saturation_factor=1.4):
    """make colours more vibrant and reduce shadow effects"""
    
    # enhance contrast first
    contrast_enhancer = ImageEnhance.Contrast(img)
    img_contrast = contrast_enhancer.enhance(contrast_factor)
    
    # boost saturation to make colours pop
    saturation_enhancer = ImageEnhance.Color(img_contrast)
    img_saturated = saturation_enhancer.enhance(saturation_factor)
    
    # then adjust brightness slightly
    brightness_enhancer = ImageEnhance.Brightness(img_saturated)
    img_enhanced = brightness_enhancer.enhance(brightness_factor)
    
    return img_enhanced


def remove_background(img):
    """apply an open source rembg library. this gets rid of that orange bedsheet (or any background really...)"""
    return rb.remove(img)


def reduce_shadows_adaptive(img_array):
    """use adaptive approach to handle shadows"""
    img_float = img_array.astype(np.float32)
    rgb = img_float[:, :, :3]
    alpha = img_float[:, :, 3]
    
    clothing_mask = alpha > 0.5
    
    if clothing_mask.any():
        # instead of global adjustment, use percentile-based normalisation
        clothing_pixels = rgb[clothing_mask]
        
        # get the 75th percentile as "normal" brightness (not shadows, not highlights)
        target_brightness = np.percentile(clothing_pixels, 75)
        
        # only boost pixels that are darker than this threshold
        dark_mask = np.mean(rgb, axis=2) < target_brightness * 0.7
        combined_mask = clothing_mask & dark_mask
        
        if combined_mask.any():
            rgb[combined_mask] *= 1.3  # modest boost only to dark areas
            rgb = np.clip(rgb, 0, 1)
    
    return np.concatenate([rgb, alpha[:, :, np.newaxis]], axis=2)


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


def preprocess_clothing_image_stages(image_path, save_bg_removed=None, save_fully_processed=None):
    """full pipeline with intermediate stages saved"""
    
    # stage 1: load and enhance the raw photo
    img = load_image(image_path)
    img_enhanced = enhance_contrast_and_brightness(img, saturation_factor=1.5)
    
    # stage 2: background removal 
    img_no_bg = remove_background(img_enhanced)
    
    # save background removed version if requested
    if save_bg_removed:
        img_no_bg.save(save_bg_removed)
    
    # stage 3: shadow reduction and full processing
    img_array = np.array(img_no_bg).astype(np.float32) / 255.0
    img_shadow_reduced = reduce_shadows_adaptive(img_array)
    img_processed = Image.fromarray((img_shadow_reduced * 255).astype(np.uint8))
    
    # final standardisation
    final_img = center_and_resize(img_processed)
    
    # save fully processed version if requested
    if save_fully_processed:
        final_img.save(save_fully_processed)
    
    return img_no_bg, final_img


def batch_preprocess(input_dir, bg_removed_dir, fully_processed_dir):
    """process the whole folder with both output stages"""
    input_path = Path(input_dir)
    bg_path = Path(bg_removed_dir)
    processed_path = Path(fully_processed_dir)
    
    # create output directories
    bg_path.mkdir(exist_ok=True)
    processed_path.mkdir(exist_ok=True)
    
    # find all images in the input folder
    image_extensions = ['.jpg', '.jpeg', '.png']
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
    
    print(f"Found {len(image_files)} images to check")
    
    processed_count = 0
    skipped_count = 0
    
    for img_file in image_files:
        # define output file paths
        bg_removed_file = bg_path / f"{img_file.stem}_bg_removed.png"
        fully_processed_file = processed_path / f"{img_file.stem}_processed.png"
        
        # check if both versions already exist
        if bg_removed_file.exists() and fully_processed_file.exists():
            print(f"Skipping {img_file.name} - already processed")
            skipped_count += 1
        else:
            print(f"Processing {img_file.name}...")
            bg_removed, fully_processed = preprocess_clothing_image_stages(
                img_file, 
                bg_removed_file, 
                fully_processed_file
            )
            processed_count += 1
    
    print(f"Processed: {processed_count} new images")
    print(f"Skipped: {skipped_count} already done")