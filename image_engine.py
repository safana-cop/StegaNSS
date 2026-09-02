import cv2
import numpy as np
import os
from PIL import Image

class StegaEngine:
    @staticmethod
    def get_max_capacity(image_path, decoy_mode=False):
        img = cv2.imread(image_path)
        if img is None: return 0
        total_pixels = img.size 
        # Logical Correction: The implementation reserves 50% of bits for Decoy even if unused.
        # Each byte (pixel channel) gets 1 bit.
        # Primary gets Even indices, Decoy gets Odd indices.
        # Therefore, Primary capacity is ALWAYS total_pixels // (2 * 8) = total_pixels // 16.
        space = (total_pixels // 2) - 160 
        return max(0, space // 8)

    @staticmethod
    def hide(image_path, secret_string, output_path, decoy_bytes=None):
        img = cv2.imread(image_path)
        if img is None: raise FileNotFoundError("Carrier not found.")
        
        flat_img = img.flatten()
        
        # Vectorized bit preparation
        def str_to_bits(s):
            if not s: return np.array([], dtype=np.uint8)
            byte_arr = np.frombuffer((s + "###END###").encode(), dtype=np.uint8)
            return np.unpackbits(byte_arr)

        real_bits = str_to_bits(secret_string)
        decoy_bits = str_to_bits(decoy_bytes) if decoy_bytes else np.array([], dtype=np.uint8)

        # High-Speed Vectorized Injection
        if len(real_bits) > 0:
            count = len(real_bits)
            flat_img[0:count*2:2] = (flat_img[0:count*2:2] & 254) | real_bits
            
        if len(decoy_bits) > 0:
            count = len(decoy_bits)
            flat_img[1:count*2+1:2] = (flat_img[1:count*2+1:2] & 254) | decoy_bits

        new_img = flat_img.reshape(img.shape)
        cv2.imwrite(output_path, new_img, [cv2.IMWRITE_PNG_COMPRESSION, 1])

    @staticmethod
    def extract(image_path):
        img = cv2.imread(image_path)
        if img is None: return "", ""
        
        flat_img = img.flatten()
        all_bits = (flat_img & 1).astype(np.uint8)

        def fast_bits_to_str(bits_array):
            if len(bits_array) < 8: return ""
            # Align to 8-bit boundaries
            n = (len(bits_array) // 8) * 8
            bits_8 = bits_array[:n].reshape(-1, 8)
            # Vectorized binary to decimal conversion
            powers = np.array([128, 64, 32, 16, 8, 4, 2, 1], dtype=np.uint8)
            bytes_arr = np.packbits(bits_8)
            
            try:
                message = bytes_arr.tobytes().decode(errors='ignore')
                if "###END###" in message:
                    return message.split("###END###")[0]
            except: pass
            return ""

        return fast_bits_to_str(all_bits[0::2]), fast_bits_to_str(all_bits[1::2])
