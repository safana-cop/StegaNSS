import cv2
import os
import numpy as np

class VideoEngine:
    @staticmethod
    def get_max_capacity(video_path, decoy_mode=False):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): return 0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        # Total storage units (bytes across all frames and channels)
        total_bytes = w * h * 3 * frames
        # Half for Primary, Half for Decoy
        # subtract header/footer buffer
        space = (total_bytes // 2) - 2000 
        return max(0, space // 8)

    @staticmethod
    def hide(video_path, secret_string, output_path, decoy_bytes=None, target_height=None):
        """
        Hides primary and decoy secrets across all frames of a video using LSB.
        Supports optional resolution scaling to reduce lossless file footprint.
        """
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        # ---------------------------------------------------------
        # OPTIMIZATION: Resolution Scaling
        # ---------------------------------------------------------
        if target_height and target_height < height:
            scale = target_height / height
            width = int(width * scale)
            height = target_height
            width = width if width % 2 == 0 else width - 1

        fourcc = cv2.VideoWriter_fourcc(*'FFV1') 
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        def str_to_bits(s):
            if not s: return np.array([], dtype=np.uint8)
            byte_arr = np.frombuffer((s + "###END###").encode(), dtype=np.uint8)
            return np.unpackbits(byte_arr)

        real_bits = str_to_bits(secret_string)
        decoy_bits = str_to_bits(decoy_bytes) if decoy_bytes else np.array([], dtype=np.uint8)

        idx_real = 0
        idx_decoy = 0

        while True:
            ret, frame = cap.read()
            if not ret: break

            if target_height:
                frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

            if idx_real < len(real_bits) or idx_decoy < len(decoy_bits):
                flat = frame.ravel()
                
                if idx_real < len(real_bits):
                    remaining_real = len(real_bits) - idx_real
                    available_even = (len(flat) + 1) // 2
                    consume_real = min(remaining_real, available_even)
                    flat[0:consume_real*2:2] = (flat[0:consume_real*2:2] & 254) | real_bits[idx_real:idx_real+consume_real]
                    idx_real += consume_real

                if idx_decoy < len(decoy_bits):
                    remaining_decoy = len(decoy_bits) - idx_decoy
                    available_odd = len(flat) // 2
                    consume_decoy = min(remaining_decoy, available_odd)
                    flat[1:consume_decoy*2+1:2] = (flat[1:consume_decoy*2+1:2] & 254) | decoy_bits[idx_decoy:idx_decoy+consume_decoy]
                    idx_decoy += consume_decoy

            out.write(frame)

        cap.release()
        out.release()

    @staticmethod
    def extract(video_path):
        cap = cv2.VideoCapture(video_path)
        primary_buffer = bytearray()
        decoy_buffer = bytearray()
        
        found_primary = False
        found_decoy = False
        primary_msg = ""
        decoy_msg = ""
        marker = "###END###".encode()

        while True:
            ret, frame = cap.read()
            if not ret: break
            
            flat = frame.ravel()
            bits = (flat & 1).astype(np.uint8)
            
            # High-Speed Vectorized Bit Collection
            if not found_primary:
                # Pack bits from current frame and append to buffer
                even_bits = bits[0::2]
                packed = np.packbits(even_bits)
                primary_buffer.extend(packed.tobytes())
                if marker in primary_buffer:
                    found_primary = True
                    primary_msg = primary_buffer.split(marker)[0].decode('utf-8', errors='ignore')
            
            if not found_decoy:
                odd_bits = bits[1::2]
                packed = np.packbits(odd_bits)
                decoy_buffer.extend(packed.tobytes())
                if marker in decoy_buffer:
                    found_decoy = True
                    decoy_msg = decoy_buffer.split(marker)[0].decode('utf-8', errors='ignore')
            
            if found_primary and found_decoy: break
        
        cap.release()
        return primary_msg, decoy_msg
