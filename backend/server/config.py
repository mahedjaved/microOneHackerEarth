"""Pydantic Settings for MedRAGAssistant — all env vars validated at startup."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Required API keys ──────────────────────────────────────────
    pinecone_api_key: str
    groq_api_key: str

    # ── Prompt Injection options ──────────────────────────────────────────
    prompt_injection_detection_enabled: bool = True
    prompt_injection_confidence_threshold: float = 0.7
    prompt_injection_skip_paths: list[str] = []

    # ── PII Redaction Options ──────────────────────────────────────────
    pii_detection_enabled: bool = True
    pii_strict_mode: bool = False
    pii_redaction_enabled: bool = True
    pii_log_redactions: bool = True
    pii_redaction_mode: str = "replace"


    # ── Legacy fallback (for backward compat with existing .env files) ──
    grok_api_key: str = ""

    # ── OpenCodeZen API (fallback for Groq rate limits) ───────────
    opencodezen_api_key: str = ""
    opencodezen_base_url: str = "https://api.opencodezen.ai/v1"
    opencodezen_model: str = "nemotron"

    # ── Optional API keys (reserved for future phases) ─────────────
    google_api_key: str | None = None
    langchain_api_key: Optional[str] = None
    langsmith_api_key: str | None = None
    langsmith_tracing: bool = Field(default=True, description="Enable LangSmith tracing (default: True)")
    langsmith_project: str | None = Field(default="medrag-assistant", description="LangSmith project name (default: medrag-assistant)")

    # ── Pinecone ───────────────────────────────────────────────────
    pinecone_env: str = "us-east-1"
    pinecone_index_name: str = "medical-index"
    relaxation_time: int = 1  # seconds for readiness polls

    # ── Service URLs (Docker defaults; override for local dev) ─────
    qdrant_url: str = "http://qdrant:6333"
    database_url: str = "postgresql://postgres:postgres@postgres:5432/medrag"

    # ── Server ─────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    uploaded_docs_dir: str = "./uploaded_docs"
    medical_disclaimer: str = "This is not medical advice. Consult a healthcare professional."


     # ── Cache ─────────────────────────────────────────────────────
    cache_ttl_seconds: int = 3600
    cache_similarity_threshold: float = 0.95

     # ── GROQ_API_KEY fallback ──────────────────────────────────────
    @property
    def groq_api_key_resolved(self) -> str:
        """Return GROQ_API_KEY, falling back to the legacy GROK_API_KEY env var."""
        return self.groq_api_key or self.grok_api_key

    # ── UQ Bayesian fusion (spec 001-bayesian-evidence-fusion) ──────
    # Feature flag: when true (default), the verifier uses log-odds
    # combination; when false, falls back to the legacy mean/max path.
    # Doubles as the schema-bump switch for DoubtCertificate.
    uq_use_bayesian_fusion: bool = Field(
        default=True,
        description="Enable the new Bayesian log-odds evidence fusion in the claim verifier (spec 001-bayesian-evidence-fusion).",
    )

    # Prior probability of SUPPORTED before observing evidence. Used as
    # the starting point for log-odds updates. Default 0.5 (no prior bias).
    uq_prior: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Bayesian prior probability for SUPPORTED. Clamped to [1e-6, 1-1e-6] before log-odds.",
    )

    # Cost ratio (confident-wrong : over-abstain) for the conformal
    # quantile minimization. Default 10:1 — confidently-wrong answers
    # are penalized 10x more than unnecessary abstentions (medical-safety
    # prior).
    uq_cost_ratio: str = Field(
        default="10:1",
        description='Conformal quantile cost ratio as "N:M" (confident-wrong : over-abstain). Default 10:1.',
    )

    @property
    def uq_cost_ratio_tuple(self) -> tuple[float, float]:
        """Parse the cost ratio string into a (confident_wrong, over_abstain) tuple."""
        try:
            n, m = self.uq_cost_ratio.split(":")
            return (float(n), float(m))
        except (ValueError, AttributeError):
            return (10.0, 1.0)

# Module-level singleton — instantiated once on import.
# Imports:  from config import settings
settings = Settings()