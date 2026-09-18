from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TargetSpec(StrictModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    label: str
    priority: int = Field(default=1, ge=1, le=3)
    representation: Literal["sam3d", "image_card", "proxy"]
    source_image: str
    mask_path: str | None = None
    asset_path: str | None = None
    reason: str = ""
    position_uv: tuple[float, float] = (0.5, 0.5)


class BackgroundSpec(StrictModel):
    method: Literal["depth_layers", "single_card"]
    layer_count: int = Field(ge=1, le=3)
    depth_path: str | None = None
    layer_paths: list[str] = Field(default_factory=list, max_length=3)


class CameraSpec(StrictModel):
    template: Literal["linear_dolly", "arc_push"]
    duration_s: float = Field(ge=4, le=6)
    angle_deg: float = Field(ge=0, le=12)
    travel_ratio: float = Field(ge=0.01, le=0.12)
    fallback: list[Literal["linear_dolly", "arc_push", "two_d_motion"]]


class RenderSpec(StrictModel):
    width: Literal[1280] = 1280
    height: Literal[720] = 720
    fps: Literal[24] = 24
    engine: Literal["BLENDER_EEVEE_NEXT"] = "BLENDER_EEVEE_NEXT"


class GenerationSpec(StrictModel):
    provider: Literal["h3", "seedance", "mock"]
    prompt: str
    allow_cached_success: bool = True
    max_retries: int = Field(default=1, ge=0, le=2)


class EditSpec(StrictModel):
    duration_s: float = Field(ge=20, le=25)
    title: str = Field(max_length=80)
    music_path: str | None = None
    output_path: str


class SceneSpec(StrictModel):
    contract_version: Literal["0.1.0"]
    job_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    hero_image: str
    hero_reason: str = ""
    scene_type: str = "unknown"
    quality_score: float = Field(default=0.0, ge=0, le=1)
    reconstruction_budget: int = Field(ge=0, le=1)
    targets: list[TargetSpec] = Field(max_length=3)
    background: BackgroundSpec
    camera: CameraSpec
    render: RenderSpec
    generation: GenerationSpec
    edit: EditSpec
    style: str = "cinematic_warm"
    music_mood: str = "healing"
    risk_notes: list[str] = Field(default_factory=list)

