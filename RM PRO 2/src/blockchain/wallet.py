"""
Cryptographic Wallet and Author Identity Module
Provides ECDSA key generation, manuscript signing, and signature verification.
Author: Mayur Sanjay Nakate
"""

import hashlib
import json
from typing import Tuple, Dict, Any
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend


class AuthorWallet:
    """Manages author cryptographic identity, ECDSA keypairs, and signing operations."""

    def __init__(self, private_key_pem: str = None, author_name: str = "Mayur Sanjay Nakate", affiliation: str = "Vishwakarma University"):
        self.author_name = author_name
        self.affiliation = affiliation
        
        if private_key_pem:
            self._private_key = serialization.load_pem_private_key(
                private_key_pem.encode("utf-8"),
                password=None,
                backend=default_backend()
            )
        else:
            # Generate new SECP256R1 ECDSA keypair
            self._private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        self._public_key = self._private_key.public_key()

    @property
    def public_key_pem(self) -> str:
        """Export public key in PEM format."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

    @property
    def private_key_pem(self) -> str:
        """Export private key in PEM format (confidential to author)."""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

    @property
    def author_address(self) -> str:
        """
        Derive deterministic author blockchain address from public key hash.
        Format: 0x<40-char hex string>
        """
        der_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return "0x" + hashlib.sha256(der_bytes).hexdigest()[:40]

    def sign_hash(self, data_hash: str) -> str:
        """
        Sign a 32-byte hex digest using author's ECDSA private key.
        Returns hexadecimal signature string.
        """
        digest_bytes = bytes.fromhex(data_hash) if len(data_hash) == 64 else data_hash.encode("utf-8")
        signature = self._private_key.sign(
            digest_bytes,
            ec.ECDSA(hashes.SHA256())
        )
        return signature.hex()

    @staticmethod
    def verify_signature(data_hash: str, signature_hex: str, public_key_pem: str) -> bool:
        """
        Verify that a signature was created by the owner of public_key_pem for data_hash.
        Enforces cryptographic non-repudiation.
        """
        try:
            pub_key = serialization.load_pem_public_key(
                public_key_pem.encode("utf-8"),
                backend=default_backend()
            )
            sig_bytes = bytes.fromhex(signature_hex)
            digest_bytes = bytes.fromhex(data_hash) if len(data_hash) == 64 else data_hash.encode("utf-8")
            pub_key.verify(sig_bytes, digest_bytes, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    def export_identity_card(self) -> Dict[str, Any]:
        """Export author identity metadata for academic verifiable credentials."""
        return {
            "author_name": self.author_name,
            "affiliation": self.affiliation,
            "blockchain_address": self.author_address,
            "public_key_pem": self.public_key_pem
        }
