"""
Script to generate high-resolution figures and UI charts for Project Report & Research Paper.
Author: Mayur Sanjay Nakate
"""

import os
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("assets/figures", exist_ok=True)

# Set clean aesthetic styling
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#D1D5DB'
plt.rcParams['axes.linewidth'] = 0.8

# 1. Hashing Throughput Chart
fig, ax = plt.subplots(figsize=(6, 3.8), dpi=300)
algos = ['SHA-256', 'BLAKE2b', 'SHA3-256\n(Keccak)']
throughput = [799.85, 279.39, 168.80]
colors = ['#1E40AF', '#059669', '#7C3AED']

bars = ax.bar(algos, throughput, color=colors, width=0.55, edgecolor='#1E293B', linewidth=1)
for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 18, f"{yval:.1f} MB/s", ha='center', va='bottom', fontsize=9, fontweight='bold')

ax.set_ylabel('Throughput (MB / second)', fontsize=10, fontweight='bold', color='#1E293B')
ax.set_title('Cryptographic Hash Algorithm Throughput Comparison', fontsize=11, fontweight='bold', pad=14, color='#0F172A')
ax.set_ylim(0, 920)
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
fig.savefig('assets/figures/fig_hashing_throughput.png', dpi=300)
plt.close(fig)

# 2. Merkle Tree Scaling Chart
fig, ax = plt.subplots(figsize=(6, 3.8), dpi=300)
chunks = [10, 50, 100, 250, 500, 1000, 2000]
build_latency = [0.123, 0.430, 0.912, 2.155, 4.076, 8.671, 17.347]

ax.plot(chunks, build_latency, marker='o', color='#2563EB', linewidth=2, markersize=6, label='Tree Construction Time O(N)')
for x, y in zip(chunks, build_latency):
    if x in [10, 100, 500, 1000, 2000]:
        ax.annotate(f"{y:.2f} ms", (x, y), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, fontweight='bold')

ax.set_xlabel('Number of Manuscript Semantic Chunks (N)', fontsize=10, fontweight='bold', color='#1E293B')
ax.set_ylabel('Latency (milliseconds)', fontsize=10, fontweight='bold', color='#1E293B')
ax.set_title('Merkle Tree Construction Latency vs Chunk Count', fontsize=11, fontweight='bold', pad=14, color='#0F172A')
ax.grid(True, linestyle='--', alpha=0.5)
ax.set_ylim(0, 20)
plt.tight_layout()
fig.savefig('assets/figures/fig_merkle_scaling.png', dpi=300)
plt.close(fig)

# 3. Storage Savings Comparison Chart
fig, ax = plt.subplots(figsize=(6, 3.8), dpi=300)
sizes = ['100 KB', '500 KB', '2 MB', '10 MB', '50 MB']
raw_kb = [100, 500, 2048, 10240, 51200]
onchain_kb = [0.128, 0.128, 0.128, 0.128, 0.128] # 128 bytes = 0.128 KB

x = np.arange(len(sizes))
width = 0.35

ax.bar(x - width/2, raw_kb, width, label='Traditional Raw On-Chain Storage (KB)', color='#DC2626')
ax.bar(x + width/2, onchain_kb, width, label='Proposed Merkle Anchor (128 Bytes)', color='#10B981')

ax.set_yscale('log')
ax.set_ylabel('Storage Requirement in KB (Log Scale)', fontsize=10, fontweight='bold', color='#1E293B')
ax.set_title('On-Chain Storage Footprint: Raw Manuscript vs Merkle Anchor', fontsize=11, fontweight='bold', pad=14, color='#0F172A')
ax.set_xticks(x)
ax.set_xticklabels(sizes, fontweight='bold')
ax.legend(loc='upper left', fontsize=8.5)
ax.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
fig.savefig('assets/figures/fig_storage_savings.png', dpi=300)
plt.close(fig)

# 4. System Architecture Diagram
fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=300)
ax.axis('off')

# Box styles
box_kw = dict(boxstyle="round,pad=0.5", fc="#EFF6FF", ec="#3B82F6", lw=1.5)
box_storage = dict(boxstyle="round,pad=0.5", fc="#F0FDF4", ec="#10B981", lw=1.5)
box_chain = dict(boxstyle="round,pad=0.5", fc="#FEF2F2", ec="#EF4444", lw=1.5)
box_audit = dict(boxstyle="round,pad=0.5", fc="#FAF5FF", ec="#8B5CF6", lw=1.5)

ax.text(0.18, 0.85, "1. Research Draft Ingestion\n(TXT, MD, DOCX, LaTeX)\nExtract & Parse Text", ha="center", va="center", bbox=box_kw, fontsize=8.5, fontweight='bold')
ax.text(0.50, 0.85, "2. Semantic Chunking\nPartition into N Sections\nLeaf Hash: H(0x00 || Chunk)", ha="center", va="center", bbox=box_kw, fontsize=8.5, fontweight='bold')
ax.text(0.82, 0.85, "3. Off-Chain Storage (IPFS)\nPin Raw Manuscript File\nGenerate Content CID (Qm...)", ha="center", va="center", bbox=box_storage, fontsize=8.5, fontweight='bold')

ax.text(0.18, 0.45, "4. Binary Merkle Tree\nPairwise Hash Recursion\nExtract 32-Byte Merkle Root", ha="center", va="center", bbox=box_storage, fontsize=8.5, fontweight='bold')
ax.text(0.50, 0.45, "5. Author ECDSA Wallet\nsecp256r1 Keypair Generation\nDigital Signature Non-Repudiation", ha="center", va="center", bbox=box_chain, fontsize=8.5, fontweight='bold')
ax.text(0.82, 0.45, "6. Blockchain Consensus\nTransaction Mempool + PoW\nAnchor Priority Block", ha="center", va="center", bbox=box_chain, fontsize=8.5, fontweight='bold')

ax.text(0.50, 0.12, "7. Independent Zero-Trust Verification Portal & Selective Disclosure\nReviewers audit specific paragraphs using O(log N) inclusion proofs without reading unreleased text", ha="center", va="center", bbox=box_audit, fontsize=8.5, fontweight='bold')

# Arrows
arrow_kw = dict(arrowstyle="->", color="#475569", lw=1.5)
ax.annotate("", xy=(0.33, 0.85), xytext=(0.37, 0.85), arrowprops=arrow_kw)
ax.annotate("", xy=(0.65, 0.85), xytext=(0.69, 0.85), arrowprops=arrow_kw)
ax.annotate("", xy=(0.50, 0.73), xytext=(0.50, 0.58), arrowprops=arrow_kw)
ax.annotate("", xy=(0.32, 0.45), xytext=(0.36, 0.45), arrowprops=arrow_kw)
ax.annotate("", xy=(0.65, 0.45), xytext=(0.69, 0.45), arrowprops=arrow_kw)
ax.annotate("", xy=(0.50, 0.32), xytext=(0.50, 0.22), arrowprops=arrow_kw)

ax.set_title("Architecture & Dataflow of Academic Manuscript Time-Stamping System", fontsize=11, fontweight='bold', pad=12, color='#0F172A')
plt.tight_layout()
fig.savefig('assets/figures/fig_architecture_workflow.png', dpi=300)
plt.close(fig)

# 5. Case Study Criterion Alignment Chart
fig, ax = plt.subplots(figsize=(6.5, 4.0), dpi=300)
criteria = [
    "Root Cause", "Attack Mechanism", "Affected Systems/Data", "Timeline & Evidence",
    "Technical Response", "Immediate Corrective", "Long-term Prevention",
    "Root Cause Link", "Responsibilities", "Verification/Monitoring"
]
y = np.arange(len(criteria))
height = 0.35

analyzer_scores = [2, 0, 2, 0, 2, 0, 0, 0, 0, 1]
reader_scores = [1, 2, 2, 1, 2, 1, 0, 0, 0, 1]

ax.barh(y - height/2, analyzer_scores, height, label="Automated Analyzer Coverage (0-2)", color="#94A3B8")
ax.barh(y + height/2, reader_scores, height, label="Human Reader Rating (0=No, 1=Partial, 2=Yes)", color="#2563EB", hatch="//")

ax.set_yticks(y)
ax.set_yticklabels(criteria, fontsize=8.5)
ax.set_xlabel("Score / Rating Level", fontsize=9.5, fontweight='bold')
ax.set_title("Case Study: Automated Screening vs Independent Human Reader Judgement", fontsize=10.5, fontweight='bold', pad=12)
ax.legend(loc="lower right", fontsize=8)
ax.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()
fig.savefig('assets/figures/fig_case_study_alignment.png', dpi=300)
plt.close(fig)

print("Generated all publication and report figures in assets/figures/")
