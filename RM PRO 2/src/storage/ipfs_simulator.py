"""
Decentralized Storage (IPFS Simulator) Module
Implements content-addressable storage (CID generation, chunk pinning, retrieval)
for off-chain academic manuscript preservation.
Author: Mayur Sanjay Nakate
"""

import hashlib
import json
from typing import Dict, Any, Optional, Tuple


def _b58encode(v: bytes) -> str:
    """Pure-Python implementation of Bitcoin/IPFS Base58 encoding."""
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    num = int.from_bytes(v, byteorder="big")
    chars = []
    while num > 0:
        num, rem = divmod(num, 58)
        chars.append(alphabet[rem])
    encoded = "".join(reversed(chars))
    # Count leading zero bytes
    pad_len = len(v) - len(v.lstrip(b"\x00"))
    return ("1" * pad_len) + (encoded if encoded else ("1" if pad_len > 0 else ""))


class IPFSSimulator:
    """
    Simulates an InterPlanetary File System (IPFS) content-addressable node.
    Computes deterministic multihashes (CIDv0) and stores manuscript artifacts.
    """

    def __init__(self):
        # In-memory storage table: CID -> bytes
        self._storage: Dict[str, bytes] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def generate_cid(data: bytes) -> str:
        """
        Generate an IPFS CIDv0 (base58-encoded multihash: 0x12 + 0x20 + sha256_digest).
        """
        raw_hash = hashlib.sha256(data).digest()
        # IPFS multihash prefix: 0x12 (SHA2-256 code) + 0x20 (32 bytes length)
        multihash = b"\x12\x20" + raw_hash
        return _b58encode(multihash)

    def pin_file(self, filename: str, content: bytes, mime_type: str = "text/plain") -> Tuple[str, Dict[str, Any]]:
        """
        Pin a manuscript file to content-addressable decentralized storage.
        Returns (CID, metadata).
        """
        cid = self.generate_cid(content)
        self._storage[cid] = content
        
        meta = {
            "cid": cid,
            "filename": filename,
            "size_bytes": len(content),
            "mime_type": mime_type,
            "sha256": hashlib.sha256(content).hexdigest()
        }
        self._metadata[cid] = meta
        return cid, meta

    def retrieve_file(self, cid: str) -> Optional[bytes]:
        """Retrieve raw file content by its CID."""
        return self._storage.get(cid)

    def get_metadata(self, cid: str) -> Optional[Dict[str, Any]]:
        """Get file metadata by CID."""
        return self._metadata.get(cid)

    def contains(self, cid: str) -> bool:
        """Check if CID is pinned."""
        return cid in self._storage
