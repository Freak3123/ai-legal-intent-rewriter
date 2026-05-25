"""Pipeline modules. Each one is a stub; replace progressively across phases 2-3.

Pipeline order:
  ingest  → segment  → classify  → ner  → rewrite  → risk
"""

from app.pipeline import classify, ingest, ner, rewrite, risk, segment

__all__ = ["classify", "ingest", "ner", "rewrite", "risk", "segment"]
