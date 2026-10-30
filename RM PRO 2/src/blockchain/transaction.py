"""
Transaction Module for Academic Manuscript Registration
Defines the transaction data structure for timestamping intellectual property on-chain.
Author: Mayur Sanjay Nakate
"""

import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class ManuscriptTransaction:
    """
    Represents an on-chain registration event for a research manuscript draft.
    """

    def __init__(
        self,
        manuscript_title: str,
        document_hash: str,
        merkle_root: str,
        ipfs_cid: str,
        author_name: str,
        author_address: str,
        signature: str,
        public_key_pem: str,
        co_authors: str = "",
        affiliation: str = "Vishwakarma University",
        abstract_snippet: str = "",
        timestamp: Optional[str] = None,
        tx_id: Optional[str] = None
    ):
        self.tx_id = tx_id or f"TX-{uuid.uuid4().hex[:16]}"
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.manuscript_title = manuscript_title
        self.document_hash = document_hash
        self.merkle_root = merkle_root
        self.ipfs_cid = ipfs_cid
        self.author_name = author_name
        self.author_address = author_address
        self.signature = signature
        self.public_key_pem = public_key_pem
        self.co_authors = co_authors
        self.affiliation = affiliation
        self.abstract_snippet = abstract_snippet

    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to serializable dictionary."""
        return {
            "tx_id": self.tx_id,
            "timestamp": self.timestamp,
            "manuscript_title": self.manuscript_title,
            "document_hash": self.document_hash,
            "merkle_root": self.merkle_root,
            "ipfs_cid": self.ipfs_cid,
            "author_name": self.author_name,
            "author_address": self.author_address,
            "signature": self.signature,
            "public_key_pem": self.public_key_pem,
            "co_authors": self.co_authors,
            "affiliation": self.affiliation,
            "abstract_snippet": self.abstract_snippet
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ManuscriptTransaction':
        """Reconstruct transaction from dictionary."""
        return cls(
            manuscript_title=data["manuscript_title"],
            document_hash=data["document_hash"],
            merkle_root=data["merkle_root"],
            ipfs_cid=data["ipfs_cid"],
            author_name=data["author_name"],
            author_address=data["author_address"],
            signature=data["signature"],
            public_key_pem=data["public_key_pem"],
            co_authors=data.get("co_authors", ""),
            affiliation=data.get("affiliation", ""),
            abstract_snippet=data.get("abstract_snippet", ""),
            timestamp=data.get("timestamp"),
            tx_id=data.get("tx_id")
        )

    def calculate_hash(self) -> str:
        """Deterministic hash of the transaction payload."""
        tx_dict = self.to_dict()
        # Exclude tx_id itself from payload to ensure idempotence
        payload = json.dumps({k: v for k, v in tx_dict.items() if k != "tx_id"}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
