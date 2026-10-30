"""
Blockchain Ledger Manager for Academic Integrity & Priority
Manages the distributed ledger, block chaining, transaction mempool,
tamper detection, and verification queries.
Author: Mayur Sanjay Nakate
"""

import json
import os
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from src.blockchain.block import Block
from src.blockchain.transaction import ManuscriptTransaction
from src.blockchain.wallet import AuthorWallet


class AcademicBlockchain:
    """Manages the verifiable ledger for intellectual property and manuscript timestamps."""

    def __init__(self, persistence_file: Optional[str] = None, difficulty: int = 2):
        self.chain: List[Block] = []
        self.pending_transactions: List[ManuscriptTransaction] = []
        self.difficulty = difficulty
        self.persistence_file = persistence_file

        if persistence_file and os.path.exists(persistence_file) and os.path.getsize(persistence_file) > 0:
            self.load_from_disk(persistence_file)
        else:
            self.create_genesis_block()

    def create_genesis_block(self):
        """Initialize the chain with an authoritative Genesis Block."""
        genesis_tx = ManuscriptTransaction(
            manuscript_title="Genesis Block: Academic Integrity & Priority Attestation Network",
            document_hash="0000000000000000000000000000000000000000000000000000000000000000",
            merkle_root="0000000000000000000000000000000000000000000000000000000000000000",
            ipfs_cid="QmGenesisAcademicIntegrityLedgerInitialState",
            author_name="System / Governance Consensus",
            author_address="0x0000000000000000000000000000000000000000",
            signature="GENESIS_SYSTEM_SIGNATURE",
            public_key_pem="SYSTEM_GENESIS_KEY",
            affiliation="Decentralized Science (DeSci) Foundation",
            abstract_snippet="Genesis anchor initializing verifiable priority timestamping for research manuscripts."
        )
        genesis_block = Block(
            index=0,
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            difficulty=self.difficulty
        )
        genesis_block.mine_block()
        self.chain.append(genesis_block)
        if self.persistence_file:
            self.save_to_disk(self.persistence_file)

    @property
    def latest_block(self) -> Block:
        """Get the most recent block on the ledger."""
        return self.chain[-1]

    def add_transaction(self, tx: ManuscriptTransaction) -> str:
        """Add a verified manuscript registration transaction to the pending pool."""
        # Verify author digital signature if valid public key is attached
        if tx.public_key_pem and not tx.signature.startswith("GENESIS"):
            is_valid_sig = AuthorWallet.verify_signature(
                data_hash=tx.document_hash,
                signature_hex=tx.signature,
                public_key_pem=tx.public_key_pem
            )
            if not is_valid_sig:
                raise ValueError("Transaction rejected: Invalid cryptographic author signature!")

        self.pending_transactions.append(tx)
        return tx.tx_id

    def mine_pending_transactions(self, miner_address: str = "0xSystemMiner") -> Tuple[Block, Dict[str, Any]]:
        """
        Package all pending manuscript transactions into a new block and mine it.
        Returns the newly minted Block and mining stats.
        """
        if not self.pending_transactions:
            raise ValueError("No pending manuscript transactions to mine.")

        new_block = Block(
            index=len(self.chain),
            transactions=list(self.pending_transactions),
            previous_hash=self.latest_block.hash,
            difficulty=self.difficulty
        )
        mining_stats = new_block.mine_block()
        self.chain.append(new_block)
        self.pending_transactions = []

        if self.persistence_file:
            self.save_to_disk(self.persistence_file)

        return new_block, mining_stats

    def register_manuscript_instantly(self, tx: ManuscriptTransaction) -> Tuple[Block, Dict[str, Any]]:
        """Convenience method: adds transaction and mines immediate priority block."""
        self.add_transaction(tx)
        return self.mine_pending_transactions()

    def validate_chain_integrity(self) -> Tuple[bool, List[str]]:
        """
        Cryptographically validates the entire blockchain from Genesis to Head.
        Checks:
        1. Every block's previous_hash equals previous block's hash.
        2. Every block's hash matches its recalculation.
        3. Merkle root of transactions matches block contents.
        4. Proof-of-Work difficulty target is met.
        """
        errors = []
        target_prefix = "0" * self.difficulty

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            # Check 1: Chain linkage
            if current.previous_hash != prev.hash:
                errors.append(f"Block #{current.index}: previous_hash mismatch! Linked to '{current.previous_hash[:16]}...', but parent has '{prev.hash[:16]}...'")

            # Check 2: Hash recalculation
            recalc_hash = current.calculate_hash()
            if current.hash != recalc_hash:
                errors.append(f"Block #{current.index}: Corrupted block hash! Stored: '{current.hash[:16]}...', Recalculated: '{recalc_hash[:16]}...'")

            # Check 3: Merkle root of transactions
            recalc_merkle = current.calculate_transactions_merkle_root()
            if current.merkle_root != recalc_merkle:
                errors.append(f"Block #{current.index}: Corrupted transaction Merkle Root! Stored: '{current.merkle_root[:16]}...', Recalculated: '{recalc_merkle[:16]}...'")

            # Check 4: PoW difficulty
            if not current.hash.startswith(target_prefix):
                errors.append(f"Block #{current.index}: PoW difficulty requirement not met ({current.hash})")

        is_valid = len(errors) == 0
        return is_valid, errors

    def find_manuscript_by_hash(self, doc_hash: str) -> Optional[Tuple[Block, ManuscriptTransaction]]:
        """Search blockchain for a manuscript by its SHA-256 hash."""
        doc_hash_clean = doc_hash.lower().strip()
        for block in self.chain:
            for tx in block.transactions:
                if tx.document_hash.lower().strip() == doc_hash_clean or tx.merkle_root.lower().strip() == doc_hash_clean:
                    return block, tx
        return None

    def find_manuscripts_by_author(self, author_name: str) -> List[Tuple[Block, ManuscriptTransaction]]:
        """Search blockchain for all manuscripts registered by an author."""
        results = []
        name_clean = author_name.lower().strip()
        for block in self.chain:
            for tx in block.transactions:
                if name_clean in tx.author_name.lower():
                    results.append((block, tx))
        return results

    def simulate_tamper(self, block_index: int, fake_title: str) -> Dict[str, Any]:
        """
        Demonstrates the cryptographic avalanche and tamper detection.
        Modifies a transaction in the target block without mining, then audits the chain.
        """
        if block_index <= 0 or block_index >= len(self.chain):
            return {"success": False, "error": f"Invalid block index {block_index} for tampering"}

        target_block = self.chain[block_index]
        if not target_block.transactions:
            return {"success": False, "error": "Target block has no transactions"}

        original_title = target_block.transactions[0].manuscript_title
        target_block.transactions[0].manuscript_title = fake_title

        # Check chain validity now
        is_valid, errors = self.validate_chain_integrity()

        return {
            "tampered_block_index": block_index,
            "original_title": original_title,
            "tampered_title": fake_title,
            "chain_valid_after_tamper": is_valid,
            "cryptographic_errors_detected": errors
        }

    def save_to_disk(self, filepath: str):
        """Save blockchain state to JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = {
            "difficulty": self.difficulty,
            "chain_length": len(self.chain),
            "chain": [b.to_dict() for b in self.chain]
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_disk(self, filepath: str):
        """Load blockchain state from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.difficulty = data.get("difficulty", 2)
        self.chain = [Block.from_dict(b) for b in data.get("chain", [])]
