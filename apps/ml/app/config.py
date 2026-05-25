"""Configuration for the ML service.

All model version pins live here — bumping a model means changing one line and
restarting the Space. No service redeploy needed.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelVersions(BaseSettings):
    """Pinned Hugging Face Hub model IDs.

    A pin containing "/" is treated as an HF repo ID and loaded via the
    transformers library. Any other value (e.g. "tfidf-logreg-v1") falls back
    to the local sklearn pickle / template implementation.
    """

    classifier: str = "freak3123/legal-bert-cuad-v1"
    rewriter: str = "freak3123/flan-t5-simplify-v1"
    ner_version: str = "spacy-entityruler-v1"


class Settings(BaseSettings):
    """Runtime settings, loaded from env vars or .env."""

    # Auth — leave blank in dev to skip Bearer-token check
    ml_service_token: str = ""

    # Hugging Face Hub access (only needed for private models)
    hf_token: str = ""

    # CORS — comma-separated origins
    cors_allowed_origins: str = "http://localhost:3000"

    # Limits
    max_text_length: int = 2_000_000  # ~2 MB of text
    max_clause_length: int = 5_000  # cap per-clause text
    max_clauses: int = 200
    max_pdf_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    # Logging
    log_level: str = "INFO"

    # Pipeline thresholds
    short_notice_days_threshold: int = 7  # flag termination clauses with notice ≤ N days
    high_risk_score_threshold: float = 0.7
    medium_risk_score_threshold: float = 0.4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


# Singletons used throughout the app
settings = Settings()
model_versions = ModelVersions()
