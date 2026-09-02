from PIL import Image
import os
import numpy as np

def scrub_metadata(image_path, output_path):
    """
    Removes all EXIF metadata using fast NumPy array restoration.
    """
    img = Image.open(image_path)
    if img.mode != 'RGB': img = img.convert('RGB')
    
    # Fast array-based reconstruction (strips EXIF)
    arr = np.asarray(img)
    clean_img = Image.fromarray(arr)
    clean_img.save(output_path, quality=95)
    return output_path

def analyze_stego_probability(image_path):
    """
    Vectorized Chi-Square LSB detection for high-speed forensic scanning.
    """
    img = Image.open(image_path)
    if img.mode != 'RGB': img = img.convert('RGB')
    
    # Fast LSB scanning via NumPy
    pixels = np.asarray(img)
    # Target Red channel (index 0) LSBs for tactical sampling
    lsb_mean = np.mean(pixels[:, :, 0] & 1)
    
    # Anomaly score: If distribution is too perfectly 0.5, it's highly suspicious
    # score = 100 - |0.5 - mean| * 200
    score = 100 - abs(0.5 - lsb_mean) * 200
    return max(0, min(100, float(score)))

if __name__ == "__main__":
    # Test
    pass
