from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Stage(StrEnum):
    OBJECT_RECONSTRUCTED = "object_reconstructed"
    DEPTH_ESTIMATED = "depth_estimated"
    SCENE_BUILT = "scene_built"
    WHITE_MODEL_RENDERED = "white_model_rendered"
    CORE_VIDEO_GENERATED = "core_video_generated"
    FINAL_VIDEO_COMPOSED = "final_video_composed"


class ErrorCode(StrEnum):
    MASK_INVALID = "E401_MASK_INVALID"
    SAM3D_FAILED = "E402_SAM3D_FAILED"
    ASSET_IMPORT_FAILED = "E403_ASSET_IMPORT_FAILED"
    SCENE_BUILD_FAILED = "E404_SCENE_BUILD_FAILED"
    CAMERA_UNSAFE = "E405_CAMERA_UNSAFE"
    RENDER_FAILED = "E406_RENDER_FAILED"
    VIDEO_API_FAILED = "E407_VIDEO_API_FAILED"
    COMPOSE_FAILED = "E408_COMPOSE_FAILED"


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str = "0.1.0"
    success: bool
    stage: Stage
    artifacts: dict[str, str] = Field(default_factory=dict)
    elapsed_s: float = Field(ge=0)
    fallback_used: bool = False
    recoverable: bool = True
    error_code: ErrorCode | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)

