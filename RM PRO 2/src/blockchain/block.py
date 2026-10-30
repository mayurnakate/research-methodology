"""
Block Data Structure for Academic Ledger
Implements cryptographically chained blocks with Proof-of-Work / Proof-of-Authority consensus.
Author: Mayur Sanjay Nakate
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.blockchain.transaction import ManuscriptTransaction


class Block:
    """Represents an immutable block on the research provenance blockchain."""

    def __init__(
        self,
        index: int,
        transactions: List[ManuscriptTransaction],
        previous_hash: str,
        timestamp: Optional[str] = None,
        nonce: int = 0,
        difficulty: int = 2,
        block_hash: Optional[str] = None
    ):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.nonce = nonce
        self.difficulty = difficulty
        self.merkle_root = self.calculate_transactions_merkle_root()
        self.hash = block_hash or self.calculate_hash()

    def calculate_transactions_merkle_root(self) -> str:
        """Calculate Merkle root of transactions contained in this block."""
        if not self.transactions:
            return hashlib.sha256(b"EMPTY_BLOCK").hexdigest()

        tx_hashes = [tx.calculate_hash() for tx in self.transactions]
        current_layer = tx_hashes

        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                h1 = current_layer[i]
                h2 = current_layer[i + 1] if i + 1 < len(current_layer) else h1
                combined = hashlib.sha256((h1 + h2).encode("utf-8")).hexdigest()
                next_layer.append(combined)
            current_layer = next_layer

        return current_layer[0]

    def calculate_hash(self) -> str:
        """
        Compute block SHA-256 hash using header fields.
        H = SHA256(index + timestamp + previous_hash + merkle_root + nonce)
        """
        header = f"{self.index}:{self.timestamp}:{self.previous_hash}:{self.merkle_root}:{self.nonce}"
        return hashlib.sha256(header.encode("utf-8")).hexdigest()

    def mine_block(self, difficulty: Optional[int] = None) -> Dict[str, Any]:
        """
        Mine block using Proof-of-Work to satisfy difficulty target (leading zeros).
        Returns mining metrics (elapsed time, hashes tried).
        """
        if difficulty is not None:
            self.difficulty = difficulty

        target_prefix = "0" * self.difficulty
        start_time = time.time()
        hashes_calculated = 0

        while not self.hash.startswith(target_prefix):
            self.nonce += 1
            self.hash = self.calculate_hash()
            hashes_calculated += 1

        elapsed = time.time() - start_time
        return {
            "elapsed_seconds": round(elapsed, 4),
            "hashes_calculated": hashes_calculated,
            "hashrate_hps": round(hashes_calculated / max(elapsed, 0.0001), 2),
            "final_hash": self.hash,
            "nonce": self.nonce
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize block to dictionary."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "hash": self.hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Block':
        """Reconstruct block from dictionary."""
        txs = [ManuscriptTransaction.from_dict(t) for t in data.get("transactions", [])]
        return cls(
            index=data["index"],
            transactions=txs,
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            nonce=data.get("nonce", 0),
            difficulty=data.get("difficulty", 2),
            block_hash=data.get("hash")
        )
