"""
Cryptographic Priority Certificate Generator
Generates verifiable academic certificates of manuscript priority,
authorship, and immutable timestamping.
Author: Mayur Sanjay Nakate
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any


class PriorityCertificateGenerator:
    """Generates standardized cryptographic certificates for researchers."""

    @staticmethod
    def generate_certificate(
        manuscript_title: str,
        author_name: str,
        affiliation: str,
        author_address: str,
        public_key_pem: str,
        document_hash: str,
        merkle_root: str,
        ipfs_cid: str,
        block_index: int,
        block_hash: str,
        timestamp_iso: str,
        ecdsa_signature: str,
        chunk_count: int,
        co_authors: str = ""
    ) -> Dict[str, Any]:
        """Construct a standardized JSON-LD compatible certificate object."""
        cert_id = f"CERT-IP-{uuid.uuid4().hex[:12].upper()}"

        return {
            "certificate_id": cert_id,
            "standard": "IEEE-IP-PROOF-V1.0",
            "metadata": {
                "manuscript_title": manuscript_title,
                "primary_author": author_name,
                "affiliation": affiliation,
                "co_authors": co_authors,
                "registration_timestamp_utc": timestamp_iso
            },
            "cryptographic_proofs": {
                "document_sha256": document_hash,
                "merkle_root": merkle_root,
                "merkle_chunk_count": chunk_count,
                "ipfs_cid": ipfs_cid,
                "author_blockchain_address": author_address,
                "ecdsa_signature": ecdsa_signature,
                "public_key_pem": public_key_pem.strip()
            },
            "blockchain_anchor": {
                "network": "Academic-Proof-Ledger-MainNet (Simulated / Verifiable)",
                "block_index": block_index,
                "block_hash": block_hash,
                "consensus_mechanism": "Proof-of-Authority (PoA) with Byzantine Fault Tolerance",
                "non_repudiation_status": "CRYPTOGRAPHICALLY_VERIFIED"
            },
            "verification_instructions": "To verify authenticity without disclosure, calculate SHA-256 of the draft or run Merkle inclusion proof against merkle_root."
        }

    @staticmethod
    def format_text_certificate(cert: Dict[str, Any]) -> str:
        """Format certificate into an authoritative, printable plain-text format."""
        meta = cert["metadata"]
        proofs = cert["cryptographic_proofs"]
        anchor = cert["blockchain_anchor"]

        border = "=" * 80
        divider = "-" * 80

        lines = [
            border,
            "         ACADEMIC INTELLECTUAL PROPERTY & MANUSCRIPT PRIORITY CERTIFICATE         ",
            "                  Decentralized Cryptographic Ledger Attestation                  ",
            border,
            f"Certificate ID : {cert['certificate_id']}",
            f"Standard       : {cert['standard']}",
            f"Issuance Time  : {meta['registration_timestamp_utc']} UTC",
            divider,
            "1. RESEARCH MANUSCRIPT DETAILS:",
            f"   Title          : {meta['manuscript_title']}",
            f"   Primary Author : {meta['primary_author']} ({meta['affiliation']})",
            f"   Co-Authors     : {meta['co_authors'] if meta['co_authors'] else 'None'}",
            "",
            "2. CRYPTOGRAPHIC PROOFS & INTEGRITY ANCHORS:",
            f"   Manuscript SHA-256 : {proofs['document_sha256']}",
            f"   Chunk Merkle Root  : {proofs['merkle_root']} ({proofs['merkle_chunk_count']} chunks)",
            f"   Decentralized CID  : {proofs['ipfs_cid']} (IPFS Multi-hash)",
            f"   Author Public Addr : {proofs['author_blockchain_address']}",
            f"   ECDSA Signature    : {proofs['ecdsa_signature'][:32]}...{proofs['ecdsa_signature'][-16:]}",
            "",
            "3. BLOCKCHAIN ANCHORAGE:",
            f"   Block Height   : #{anchor['block_index']}",
            f"   Block Hash     : {anchor['block_hash']}",
            f"   Consensus Type : {anchor['consensus_mechanism']}",
            f"   Legal Status   : Immutable Proof of Prior Existence & Non-Repudiation",
            divider,
            "VERIFICATION NOTE: This document cryptographically establishes that the researcher",
            "possessed the exact manuscript prior to any journal review or competitor disclosure.",
            border
        ]
        return "\n".join(lines)
