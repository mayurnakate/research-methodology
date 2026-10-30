"""
Cryptographic Hasher Module
Provides secure multi-algorithm cryptographic hashing for research manuscripts,
chunks, and metadata.
Author: Mayur Sanjay Nakate
"""

import hashlib
from typing import Dict, Any, Union


class CryptoHasher:
    """Provides cryptographic hashing and avalanche effect analysis."""

    @staticmethod
    def hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
        """Hash raw bytes using specified algorithm ('sha256', 'sha3_256', 'blake2b')."""
        algo = algorithm.lower().strip()
        if algo == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algo in ("sha3", "sha3_256"):
            return hashlib.sha3_256(data).hexdigest()
        elif algo in ("blake2", "blake2b"):
            return hashlib.blake2b(data).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}. Choose sha256, sha3_256, or blake2b.")

    @staticmethod
    def hash_string(text: str, algorithm: str = "sha256") -> str:
        """Hash a UTF-8 string."""
        return CryptoHasher.hash_bytes(text.encode("utf-8"), algorithm=algorithm)

    @staticmethod
    def hash_file_stream(file_stream, algorithm: str = "sha256", chunk_size: int = 65536) -> str:
        """Hash an entire file stream chunk-by-chunk for memory efficiency."""
        algo = algorithm.lower().strip()
        if algo == "sha256":
            hasher = hashlib.sha256()
        elif algo in ("sha3", "sha3_256"):
            hasher = hashlib.sha3_256()
        elif algo in ("blake2", "blake2b"):
            hasher = hashlib.blake2b()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        pos = file_stream.tell() if hasattr(file_stream, 'tell') else 0
        file_stream.seek(0)
        while True:
            chunk = file_stream.read(chunk_size)
            if not chunk:
                break
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            hasher.update(chunk)
        
        # Reset position
        try:
            file_stream.seek(pos)
        except Exception:
            pass

        return hasher.hexdigest()

    @staticmethod
    def calculate_avalanche_effect(original: bytes, modified: bytes) -> Dict[str, Any]:
        """
        Calculates the cryptographic avalanche effect between two byte sequences.
        Shows how a single bit change drastically alters the resulting SHA-256 digest.
        """
        hash1 = hashlib.sha256(original).hexdigest()
        hash2 = hashlib.sha256(modified).hexdigest()

        # Convert hex to binary representation
        bin1 = bin(int(hash1, 16))[2:].zfill(256)
        bin2 = bin(int(hash2, 16))[2:].zfill(256)

        diff_bits = sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
        percentage = (diff_bits / 256.0) * 100.0

        return {
            "hash_original": hash1,
            "hash_modified": hash2,
            "differing_bits": diff_bits,
            "total_bits": 256,
            "avalanche_percentage": round(percentage, 2)
        }
