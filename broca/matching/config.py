from __future__ import annotations

import os
from pydantic import BaseModel


class MatcherConfig(BaseModel):
    # Core
    enabled: bool = os.getenv("BROCA_MATCHER_ENABLED", "true").lower() == "true"
    cache_size: int = int(os.getenv("BROCA_MATCHER_CACHE_SIZE", "20000"))
    max_text_chars: int = int(os.getenv("BROCA_MATCHER_MAX_TEXT_CHARS", "20000"))

    # Text thresholds
    text_threshold: float = float(os.getenv("BROCA_MATCHER_TEXT_THRESHOLD", "0.82"))
    contradiction_threshold: float = float(os.getenv("BROCA_MATCHER_CONTRADICTION_THRESHOLD", "0.70"))

    # Field-aware matching
    # These keys are always treated as strict/hard constraints (no fuzzy/semantic matching).
    hard_keys_csv: str = os.getenv("BROCA_MATCHER_HARD_KEYS", "type,namespace,tags")
    # Per-field thresholds for text-like keys, format: "text:0.82,description:0.75"
    field_thresholds_csv: str = os.getenv("BROCA_MATCHER_FIELD_THRESHOLDS", "")

    # Backend toggles (all local; missing deps simply disable the backend)
    enable_regex_module: bool = os.getenv("BROCA_MATCHER_ENABLE_REGEX_MODULE", "true").lower() == "true"
    enable_rapidfuzz: bool = os.getenv("BROCA_MATCHER_ENABLE_RAPIDFUZZ", "true").lower() == "true"
    enable_flashtext: bool = os.getenv("BROCA_MATCHER_ENABLE_FLASHTEXT", "true").lower() == "true"
    enable_ahocorasick: bool = os.getenv("BROCA_MATCHER_ENABLE_AHOCORASICK", "true").lower() == "true"
    enable_simhash: bool = os.getenv("BROCA_MATCHER_ENABLE_SIMHASH", "true").lower() == "true"
    enable_datasketch_minhash: bool = os.getenv("BROCA_MATCHER_ENABLE_DATASKETCH", "true").lower() == "true"

    # ML-ish local similarity
    enable_hashing_tfidf: bool = os.getenv("BROCA_MATCHER_ENABLE_HASHING_TFIDF", "true").lower() == "true"
    hashing_tfidf_ngram_max: int = int(os.getenv("BROCA_MATCHER_HASHING_TFIDF_NGRAM_MAX", "2"))
    hashing_tfidf_n_features: int = int(os.getenv("BROCA_MATCHER_HASHING_TFIDF_N_FEATURES", str(2**18)))

    # Embeddings (optional local model)
    enable_sentence_transformers: bool = os.getenv("BROCA_MATCHER_ENABLE_SENTENCE_TRANSFORMERS", "false").lower() == "true"
    sentence_transformer_model: str = os.getenv("BROCA_MATCHER_SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
    embedding_cache_size: int = int(os.getenv("BROCA_MATCHER_EMBED_CACHE_SIZE", "10000"))

    # ANN prefiltering (FAISS) for ranking many candidates quickly
    enable_faiss: bool = os.getenv("BROCA_MATCHER_ENABLE_FAISS", "true").lower() == "true"
    ann_index_cache_size: int = int(os.getenv("BROCA_MATCHER_ANN_INDEX_CACHE_SIZE", "32"))
    ann_min_candidates: int = int(os.getenv("BROCA_MATCHER_ANN_MIN_CANDIDATES", "32"))
    ann_top_k: int = int(os.getenv("BROCA_MATCHER_ANN_TOP_K", "25"))
