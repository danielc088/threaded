"""
preprocessing pipeline for uploaded clothing images
takes raw jpg photos and makes them consistent for feature extraction
handles background removal, colour enhancement, and standardisation
"""

import cv2
from PIL import Image, ImageEnhance
import rembg as rb
import numpy as np
from pathlib import Path


def load_image(image_path):
    """load image and convert to consistent format"""
    img = cv2.imread(str(image_path))
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img_rgb)


def detect_dark_item(img):
    """check if this is a dark clothing item to avoid colour shifting"""
    img_array = np.array(img)
    avg_brightness = np.mean(img_array)
    return avg_brightness < 0.5


def enhance_for_clothing_type(img, is_dark_item=False):
    """different enhancement based on clothing darkness to preserve colours"""
    img_array = np.array(img)
    avg_brightness = np.mean(img_array)
    
    if avg_brightness < 0.3:
        # very dark items (black shoes, etc): almost no enhancement
        contrast_enhancer = ImageEnhance.Contrast(img)
        img_enhanced = contrast_enhancer.enhance(1.05)  # minimal contrast boost
        return img_enhanced
    elif is_dark_item:
        # moderately dark items: gentle processing
        contrast_enhancer = ImageEnhance.Contrast(img)
        img_enhanced = contrast_enhancer.enhance(1.1)
        return img_enhanced
    else:
        # bright items: full enhancement
        contrast_enhancer = ImageEnhance.Contrast(img)
        img_contrast = contrast_enhancer.enhance(1.3)
        
        # boost saturation to make colours pop
        saturation_enhancer = ImageEnhance.Color(img_contrast)
        img_saturated = saturation_enhancer.enhance(1.5)
        
        # then adjust brightness slightly
        brightness_enhancer = ImageEnhance.Brightness(img_saturated)
        img_enhanced = brightness_enhancer.enhance(1.1)
        
        return img_enhanced


def nuclear_option_orange_cleanup(img_no_bg, filename=None):
    """aggressively removes mid-light orange tones, unless explicitly skipped for certain shirts"""
    
    # skip orange cleanup entirely for specific shirts
    if filename and any(skip in filename for skip in ["shirt_8", "shirt_12"]):
        return img_no_bg  # unchanged
    
    img_array = np.array(img_no_bg)
    rgb = img_array[:,:,:3]
    alpha = img_array[:, :, 3]
    
    # convert to hsv for better orange detection
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    
    # default (aggressive) thresholds
    hsv_lower, hsv_upper = (8, 80, 120), (25, 255, 255)
    r_min, g_min, g_max, b_min, b_max = 180, 100, 200, 20, 120
    
    # if pants_4, relax thresholds (narrower hue range, higher value cutoff)
    if filename and "pants_4" in filename:
        hsv_lower, hsv_upper = (10, 100, 140), (22, 255, 255)  # narrower, higher value
        r_min, g_min, g_max, b_min, b_max = 190, 110, 190, 30, 110  # stricter in rgb
    
    # build masks
    orange_mask = cv2.inRange(hsv, hsv_lower, hsv_upper)
    light_orange_mask = (
        (rgb[:,:,0] >= r_min) & 
        (rgb[:,:,1] >= g_min) & (rgb[:,:,1] <= g_max) & 
        (rgb[:,:,2] >= b_min) & (rgb[:,:,2] <= b_max)
    )
    
    # combine
    combined_mask = (orange_mask > 0) | light_orange_mask
    
    # apply to alpha
    alpha[combined_mask] = 0
    
    # clean up edges
    kernel = np.ones((3,3), np.uint8)
    alpha_binary = (alpha > 50).astype(np.uint8) * 255
    alpha_cleaned = cv2.morphologyEx(alpha_binary, cv2.MORPH_CLOSE, kernel)
    alpha_cleaned = cv2.morphologyEx(alpha_cleaned, cv2.MORPH_ERODE, kernel)
    
    img_array[:, :, 3] = alpha_cleaned
    return Image.fromarray(img_array)


def remove_background(img, filename=None):
    """apply rembg library to remove background and clean up orange artifacts"""
    result = nuclear_option_orange_cleanup(rb.remove(img, model_session='u2net_cloth'), filename=filename)
    return result


def reduce_shadows_adaptive(img_array):
    """use adaptive approach to handle shadows better, skip for very dark items"""
    img_float = img_array.astype(np.float32)
    rgb = img_float[:, :, :3]
    alpha = img_float[:, :, 3]
    
    clothing_mask = alpha > 0.5
    
    if clothing_mask.any():
        # check if this is a very dark item - skip shadow processing
        clothing_pixels = rgb[clothing_mask]
        avg_brightness = np.mean(clothing_pixels)
        
        if avg_brightness < 0.3:
            # very dark items: skip shadow processing to avoid colour shifts
            return np.concatenate([rgb, alpha[:, :, np.newaxis]], axis=2)
        
        # normal shadow processing for other items
        target_brightness = np.percentile(clothing_pixels, 75)
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
    """standardise all images to same size and nicely centred"""
    
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
    """full pipeline with intermediate stages saved and correct processing order"""
    
    # stage 1: load raw photo
    img = load_image(image_path)
    
    # stage 2: background removal on raw image (preserve original colours)
    img_no_bg = remove_background(img, filename=Path(image_path).stem)
    
    # save background removed version if requested
    if save_bg_removed:
        img_no_bg.save(save_bg_removed)
    
    # stage 3: now apply enhancement to the background-removed image
    is_dark = detect_dark_item(img_no_bg)
    img_enhanced = enhance_for_clothing_type(img_no_bg, is_dark)
    
    # stage 4: shadow reduction
    img_array = np.array(img_enhanced).astype(np.float32) / 255.0
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
    bg_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # find all images in the input folder
    image_extensions = ['.jpg', '.jpeg', '.png']
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_path.glob(f'*{ext}'))
    
    print(f"found {len(image_files)} images to process")
    
    processed_count = 0
    skipped_count = 0
    
    for img_file in image_files:
        # define output file paths
        bg_removed_file = bg_path / f"{img_file.stem}_bg_removed.png"
        fully_processed_file = processed_path / f"{img_file.stem}_processed.png"
        
        # check if both versions already exist
        if bg_removed_file.exists() and fully_processed_file.exists():
            skipped_count += 1
        else:
            bg_removed, fully_processed = preprocess_clothing_image_stages(
                img_file, 
                bg_removed_file, 
                fully_processed_file
            )
            processed_count += 1
    
    print(f"processed {processed_count} new images")
    print(f"skipped {skipped_count} images already done")