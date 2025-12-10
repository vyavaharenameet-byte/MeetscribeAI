# summarize.py
"""
TextRank-like summarizer + simple action-item extractor.

Provides:
  - summarize_text(text, num_sentences=5) -> (summary_text, minutes_struct)
minutes_struct is a dict: {"items": [{"text": "..."} , ...]}
"""

import re
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import sent_tokenize

# Basic action-item patterns (very simple heuristic)
ACTION_PATTERNS = [
    r"\bwill\b", r"\bshall\b", r"\bto\s+do\b", r"\baction\b", r"\bdeadline\b",
    r"\bdue\b", r"\bby\s+[A-Za-z0-9]+\b", r"\bassign(ed)?\b", r"\bcomplete\b",
    r"\bdeliver\b", r"\bsubmit\b", r"\bprepare\b", r"\bshare\b", r"\bsend\b"
]


def _clean_sentence(s):
    return s.strip().replace("\n", " ").strip()


def _extract_action_items(sentences):
    items = []
    for s in sentences:
        lower = s.lower()
        for pat in ACTION_PATTERNS:
            if re.search(pat, lower):
                items.append({"text": _clean_sentence(s)})
                break
    return items


def _build_similarity_matrix(sentences):
    # Use TF-IDF on sentences (strip very short sentences)
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vectorizer.fit_transform(sentences)
    except ValueError:
        # Happens if sentences are empty or too few tokens
        return np.zeros((len(sentences), len(sentences)))

    if tfidf.shape[0] == 0:
        return np.zeros((len(sentences), len(sentences)))

    sim_matrix = cosine_similarity(tfidf)
    # remove self-similarity
    np.fill_diagonal(sim_matrix, 0)
    return sim_matrix


def _rank_sentences_by_textrank(sentences, top_n=5):
    if not sentences:
        return []

    if len(sentences) <= top_n:
        # not enough sentences — return all
        return list(range(len(sentences)))

    sim_matrix = _build_similarity_matrix(sentences)
    # If matrix is all zeros (e.g., one-sentence or very short), fallback to first sentences
    if not np.any(sim_matrix):
        return list(range(min(top_n, len(sentences))))

    # Build graph and run PageRank
    try:
        graph = nx.from_numpy_array(sim_matrix)
        scores = nx.pagerank(graph)
    except Exception:
        # fallback: sum of similarities
        scores = {i: float(sim_matrix[i].sum()) for i in range(len(sentences))}

    # sort sentence indices by score desc
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_indices = [idx for idx, score in ranked[:top_n]]
    return top_indices


def summarize_text(text: str, num_sentences: int = 5):
    """
    Main entrypoint used by your API.

    Returns: (summary_string, minutes_struct)
      minutes_struct = {"items": [{"text": ...}, ...]}
    """
    if not text or not text.strip():
        return ("", {"items": []})

    # 1) Split to sentences
    raw_sents = sent_tokenize(text)
    sentences = [_clean_sentence(s) for s in raw_sents if s.strip()]

    if len(sentences) == 0:
        return ("", {"items": []})

    # 2) Get top sentence indices via TextRank-style ranking
    top_idx = _rank_sentences_by_textrank(sentences, top_n=min(num_sentences, len(sentences)))

    # 3) Keep original order of selected sentences for readability
    top_idx_sorted = sorted(top_idx)
    summary_sentences = [sentences[i] for i in top_idx_sorted]
    summary_text = " ".join(summary_sentences)

    # 4) Extract action items heuristically from full text and from top sentences
    # First, look for explicit action-indicating sentences in the whole document
    action_items = _extract_action_items(sentences)
    # If none found, try extracting from the top summary sentences
    if not action_items:
        action_items = _extract_action_items(summary_sentences)

    minutes_struct = {"items": action_items}

    return (summary_text, minutes_struct)
