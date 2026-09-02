import hashlib
import base64
import zlib

def encrypt_data(message: str, pin: str) -> str:
    """
    Encrypts a message string using a PIN via XOR with SHA256 key.
    Includes zlib compression for size optimization.
    Returns a Base64 encoded ciphertext string.
    """
    # 1. Compress
    compressed_data = zlib.compress(message.encode())
    
    # 2. Encrypt
    key = hashlib.sha256(pin.encode()).digest()
    encrypted_bytes = bytearray()

    for i, c in enumerate(compressed_data):
        encrypted_bytes.append(c ^ key[i % len(key)])

    return base64.b64encode(encrypted_bytes).decode()

def decrypt_data(encrypted_message: str, pin: str) -> str:
    """
    Decrypts a Base64 encoded ciphertext string using a PIN via XOR with SHA256 key.
    Includes zlib decompression for recovery.
    Returns the original message string or None if decryption fails.
    """
    try:
        key = hashlib.sha256(pin.encode()).digest()
        encrypted_bytes = base64.b64decode(encrypted_message)

        # 1. Decrypt
        decrypted_compressed = bytearray()
        for i, c in enumerate(encrypted_bytes):
            decrypted_compressed.append(c ^ key[i % len(key)])

        # 2. Decompress
        return zlib.decompress(decrypted_compressed).decode()
    except Exception:
        return None

if __name__ == "__main__":
    # Test
    msg = "Hello StegaNSS Operative!"
    pin = "1234"
    enc = encrypt_data(msg, pin)
    dec = decrypt_data(enc, pin)
    print(f"Original: {msg}")
    print(f"Encrypted (B64): {enc}")
    print(f"Decrypted: {dec}")
    assert msg == dec
