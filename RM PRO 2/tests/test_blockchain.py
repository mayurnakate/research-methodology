"""
Automated Test Suite for Academic Blockchain & Time-Stamping System
Author: Mayur Sanjay Nakate
"""

import unittest
import os
import tempfile
from src.crypto.hasher import CryptoHasher
from src.crypto.merkle_tree import MerkleTree
from src.crypto.certificate import PriorityCertificateGenerator
from src.blockchain.wallet import AuthorWallet
from src.blockchain.transaction import ManuscriptTransaction
from src.blockchain.block import Block
from src.blockchain.chain import AcademicBlockchain
from src.storage.ipfs_simulator import IPFSSimulator
from src.utils.document_parser import DocumentParser


class TestCryptoAndHasher(unittest.TestCase):
    def test_sha256_hashing(self):
        text = "Blockchain Academic Integrity 2026"
        h1 = CryptoHasher.hash_string(text, "sha256")
        h2 = CryptoHasher.hash_string(text, "sha256")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_avalanche_effect(self):
        d1 = b"Original research draft text for testing."
        d2 = b"Original research craft text for testing."
        res = CryptoHasher.calculate_avalanche_effect(d1, d2)
        self.assertGreater(res["differing_bits"], 70)
        self.assertGreater(res["avalanche_percentage"], 25.0)


class TestMerkleTreeAndSelectiveDisclosure(unittest.TestCase):
    def test_merkle_tree_construction(self):
        chunks = [
            "Section 1: Abstract and Motivation",
            "Section 2: Literature Review and Background",
            "Section 3: Cryptographic Merkle Architecture",
            "Section 4: Experimental Performance Results"
        ]
        tree = MerkleTree(chunks)
        root = tree.root_hash
        self.assertIsNotNone(root)
        self.assertEqual(len(root), 64)

    def test_merkle_inclusion_proof(self):
        chunks = [f"Manuscript Paragraph #{i} detailing novel theory" for i in range(8)]
        tree = MerkleTree(chunks)
        root = tree.root_hash

        for i in range(len(chunks)):
            proof = tree.get_inclusion_proof(i)
            # Verify correct chunk with proof matches root
            self.assertTrue(MerkleTree.verify_proof(chunks[i], proof, root))
            # Verify tampered chunk fails verification
            self.assertFalse(MerkleTree.verify_proof(chunks[i] + " [TAMPERED]", proof, root))


class TestAuthorWalletAndSignatures(unittest.TestCase):
    def test_wallet_creation_and_signing(self):
        wallet = AuthorWallet(author_name="Mayur Sanjay Nakate", affiliation="Vishwakarma University")
        self.assertTrue(wallet.author_address.startswith("0x"))
        self.assertGreater(len(wallet.public_key_pem), 50)

        doc_hash = CryptoHasher.hash_string("Patent Pending Quantum Algorithm")
        signature = wallet.sign_hash(doc_hash)
        self.assertGreater(len(signature), 20)

        # Verify signature with author's public key
        self.assertTrue(AuthorWallet.verify_signature(doc_hash, signature, wallet.public_key_pem))

        # Verify signature fails if document hash is altered
        tampered_hash = CryptoHasher.hash_string("Altered Document")
        self.assertFalse(AuthorWallet.verify_signature(tampered_hash, signature, wallet.public_key_pem))


class TestDecentralizedStorage(unittest.TestCase):
    def test_ipfs_cid_pinning_and_retrieval(self):
        storage = IPFSSimulator()
        data = b"Pre-print manuscript confidential content"
        cid, meta = storage.pin_file("draft.txt", data)
        self.assertTrue(cid.startswith("Qm"))
        self.assertTrue(storage.contains(cid))
        retrieved = storage.retrieve_file(cid)
        self.assertEqual(retrieved, data)


class TestBlockchainIntegrityAndTamperDetection(unittest.TestCase):
    def test_blockchain_lifecycle(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            bc = AcademicBlockchain(persistence_file=temp_path, difficulty=1)
            self.assertEqual(len(bc.chain), 1)  # Genesis block

            wallet = AuthorWallet(author_name="Mayur Sanjay Nakate")
            doc_hash = CryptoHasher.hash_string("My First Peer-Reviewed Breakthrough")
            sig = wallet.sign_hash(doc_hash)

            tx = ManuscriptTransaction(
                manuscript_title="Novel Cryptographic Protocol",
                document_hash=doc_hash,
                merkle_root="abc123merkle",
                ipfs_cid="QmSampleCID12345",
                author_name="Mayur Sanjay Nakate",
                author_address=wallet.author_address,
                signature=sig,
                public_key_pem=wallet.public_key_pem
            )

            block, stats = bc.register_manuscript_instantly(tx)
            self.assertEqual(block.index == 1, True)
            self.assertEqual(len(bc.chain), 2)

            # Validate chain
            is_valid, errors = bc.validate_chain_integrity()
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)

            # Test finding manuscript
            found = bc.find_manuscript_by_hash(doc_hash)
            self.assertIsNotNone(found)
            self.assertEqual(found[1].manuscript_title, "Novel Cryptographic Protocol")

            # Test tampering simulation
            tamper_res = bc.simulate_tamper(1, "Hacked / Stolen Title")
            self.assertFalse(tamper_res["chain_valid_after_tamper"])
            self.assertGreater(len(tamper_res["cryptographic_errors_detected"]), 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestDocumentParser(unittest.TestCase):
    def test_chunking(self):
        text = "Paragraph one with several words here.\n\nParagraph two with more details on research.\n\nParagraph three concluding the paper."
        chunks = DocumentParser.chunk_manuscript(text, chunk_mode="paragraphs", min_chunk_words=5)
        self.assertGreaterEqual(len(chunks), 2)


if __name__ == "__main__":
    unittest.main()
