import wave
import os
import numpy as np

class AudioEngine:
    @staticmethod
    def get_max_capacity(audio_path, decoy_mode=False):
        try:
            with wave.open(audio_path, 'rb') as wav:
                n_frames = wav.getnframes()
                total_bytes = n_frames * wav.getsampwidth() * wav.getnchannels()
                space = (total_bytes // 2) - 160
                return max(0, space // 8)
        except Exception:
            return 0

    @staticmethod
    def hide(audio_path, secret_string, output_path, decoy_bytes=None):
        song = wave.open(audio_path, mode='rb')
        params = song.getparams()
        frame_bytes = np.frombuffer(song.readframes(song.getnframes()), dtype=np.uint8).copy()
        song.close()

        def str_to_bits(s):
            if not s: return np.array([], dtype=np.uint8)
            byte_arr = np.frombuffer((s + "###END###").encode(), dtype=np.uint8)
            return np.unpackbits(byte_arr)

        real_bits = str_to_bits(secret_string)
        decoy_bits = str_to_bits(decoy_bytes) if decoy_bytes else np.array([], dtype=np.uint8)

        # High-Power Vectorized Injection
        if len(real_bits) > 0:
            count = len(real_bits)
            frame_bytes[0:count*2:2] = (frame_bytes[0:count*2:2] & 254) | real_bits
            
        if len(decoy_bits) > 0:
            count = len(decoy_bits)
            frame_bytes[1:count*2+1:2] = (frame_bytes[1:count*2+1:2] & 254) | decoy_bits

        with wave.open(output_path, 'wb') as new_audio:
            new_audio.setparams(params)
            new_audio.writeframes(frame_bytes.tobytes())

    @staticmethod
    def extract(audio_path):
        try:
            song = wave.open(audio_path, mode='rb')
            frame_bytes = np.frombuffer(song.readframes(song.getnframes()), dtype=np.uint8)
            song.close()

            bits = frame_bytes & 1
            marker = "###END###".encode()

            def reconstruct(bit_array):
                if len(bit_array) < 8: return ""
                byte_data = np.packbits(bit_array[:(len(bit_array)//8)*8]).tobytes()
                if marker in byte_data:
                    return byte_data.split(marker)[0].decode('utf-8', errors='ignore')
                return ""

            return reconstruct(bits[0::2]), reconstruct(bits[1::2])
        except Exception:
            return "", ""
