"""Request schemas for /v1/analyze."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeOptions(BaseModel):
    """Tuning knobs the client can pass to /v1/analyze."""

    max_clauses: int = Field(200, ge=1, le=500)
    include_top_k: int = Field(3, ge=1, le=10)


class AnalyzeRequest(BaseModel):
    """JSON body for /v1/analyze in text mode.

    Binary mode (PDF upload) uses multipart/form-data and is handled directly
    in the route handler, not via this model.
    """

    input_type: Literal["text"] = "text"
    text: str = Field(..., min_length=1)
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)
