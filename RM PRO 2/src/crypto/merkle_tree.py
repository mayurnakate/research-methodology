"""
Merkle Tree Module for Granular Manuscript Provenance
Implements cryptographic Merkle Trees for chunk-level integrity and
selective disclosure proofs (Anti-Scooping Protection).
Author: Mayur Sanjay Nakate
"""

import hashlib
from typing import List, Dict, Any, Tuple, Optional


class MerkleNode:
    """Represents a node in the Merkle Tree."""
    def __init__(self, left: Optional['MerkleNode'] = None,
                 right: Optional['MerkleNode'] = None,
                 hash_val: str = "",
                 content: Optional[str] = None,
                 chunk_id: Optional[int] = None):
        self.left = left
        self.right = right
        self.hash_val = hash_val
        self.content = content  # Populated only for leaf nodes if desired
        self.chunk_id = chunk_id

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class MerkleTree:
    """
    Constructs a binary Merkle Tree from manuscript chunks.
    Allows generating cryptographic inclusion proofs for selective disclosure.
    """

    def __init__(self, chunks: List[str]):
        """Initialize and build Merkle Tree from an ordered list of text chunks."""
        self.chunks = chunks if chunks else ["EMPTY_MANUSCRIPT"]
        self.leaves: List[MerkleNode] = []
        self.levels: List[List[MerkleNode]] = []
        self.root: Optional[MerkleNode] = None
        self._build_tree()

    @staticmethod
    def hash_pair(left_hash: str, right_hash: str) -> str:
        """Combine two child hashes deterministically using SHA-256."""
        combined = (left_hash + right_hash).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    @staticmethod
    def hash_leaf(chunk_content: str) -> str:
        """Hash a single manuscript chunk using SHA-256 with leaf prefix to prevent second preimage attack."""
        # 0x00 prefix for leaves protects against second preimage attacks
        payload = b"\x00" + chunk_content.encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _build_tree(self):
        """Build the full tree level by level from leaf chunks."""
        # Step 1: Create leaf nodes
        self.leaves = [
            MerkleNode(
                hash_val=self.hash_leaf(chunk),
                content=chunk,
                chunk_id=i
            )
            for i, chunk in enumerate(self.chunks)
        ]

        current_level = self.leaves
        self.levels = [current_level]

        # Step 2: Iteratively pair and hash until root
        while len(current_level) > 1:
            next_level: List[MerkleNode] = []
            for i in range(0, len(current_level), 2):
                left_node = current_level[i]
                if i + 1 < len(current_level):
                    right_node = current_level[i + 1]
                else:
                    # Duplicate last node if odd number of leaves (standard Bitcoin / RFC 6962 pattern)
                    right_node = MerkleNode(hash_val=left_node.hash_val, chunk_id=left_node.chunk_id)

                parent_hash = self.hash_pair(left_node.hash_val, right_node.hash_val)
                parent_node = MerkleNode(left=left_node, right=right_node, hash_val=parent_hash)
                next_level.append(parent_node)

            current_level = next_level
            self.levels.append(current_level)

        self.root = current_level[0]

    @property
    def root_hash(self) -> str:
        """Return hex digest of the Merkle Root."""
        return self.root.hash_val if self.root else ""

    def get_inclusion_proof(self, chunk_index: int) -> List[Dict[str, str]]:
        """
        Generate a Merkle inclusion proof (audit path) for a specific chunk.
        Enables an author to prove a specific section/claim existed without
        revealing the remaining contents of the manuscript.
        """
        if chunk_index < 0 or chunk_index >= len(self.leaves):
            raise IndexError(f"Chunk index {chunk_index} out of range (0-{len(self.leaves)-1})")

        proof: List[Dict[str, str]] = []
        idx = chunk_index

        for level in self.levels[:-1]:
            is_right_child = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right_child else idx + 1

            if sibling_idx < len(level):
                sibling_hash = level[sibling_idx].hash_val
            else:
                # Sibling was duplicated from idx
                sibling_hash = level[idx].hash_val

            proof.append({
                "position": "left" if is_right_child else "right",
                "hash": sibling_hash
            })
            idx = idx // 2

        return proof

    @staticmethod
    def verify_proof(chunk_content: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
        """
        Cryptographically verify that a chunk belongs to the manuscript with the given Merkle Root.
        Time complexity: O(log N).
        """
        current_hash = MerkleTree.hash_leaf(chunk_content)

        for step in proof:
            sibling_hash = step["hash"]
            pos = step["position"]

            if pos == "left":
                current_hash = MerkleTree.hash_pair(sibling_hash, current_hash)
            else:
                current_hash = MerkleTree.hash_pair(current_hash, sibling_hash)

        return current_hash.lower() == expected_root.lower()

    def to_dict_tree(self) -> Dict[str, Any]:
        """Convert the tree structure to a hierarchical dictionary for visualization."""
        def serialize_node(node: Optional[MerkleNode]) -> Optional[Dict[str, Any]]:
            if not node:
                return None
            data = {
                "hash": node.hash_val[:12] + "...",
                "full_hash": node.hash_val,
                "is_leaf": node.is_leaf
            }
            if node.is_leaf:
                data["chunk_id"] = node.chunk_id
                snippet = node.content[:40] + "..." if node.content and len(node.content) > 40 else node.content
                data["snippet"] = snippet
            if node.left or node.right:
                data["children"] = []
                if node.left:
                    data["children"].append(serialize_node(node.left))
                if node.right:
                    data["children"].append(serialize_node(node.right))
            return data

        return serialize_node(self.root) or {}
