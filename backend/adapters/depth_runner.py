from __future__ import annotations

from pathlib import Path
import time

from backend.schemas import ErrorCode, Stage, ToolResult


def estimate_depth(
    image_path: str | Path,
    output_path: str | Path,
    *,
    cached_depth: str | Path | None = None,
) -> ToolResult:
    """Depth Anything boundary with an explicit procedural-layer fallback."""
    started = time.perf_counter()
    image_path = Path(image_path)
    output_path = Path(output_path)
    if not image_path.exists():
        return ToolResult(
            success=False,
            stage=Stage.DEPTH_ESTIMATED,
            elapsed_s=round(time.perf_counter() - started, 3),
            recoverable=True,
            error_code=ErrorCode.SCENE_BUILD_FAILED,
            message="Source image for depth estimation is missing",
        )

    if cached_depth is not None and Path(cached_depth).exists():
        return ToolResult(
            success=True,
            stage=Stage.DEPTH_ESTIMATED,
            artifacts={"depth": str(Path(cached_depth))},
            elapsed_s=round(time.perf_counter() - started, 3),
            fallback_used=True,
            recoverable=True,
            message="Using cached depth output until the GPU depth service is connected",
            details={"requested_output": str(output_path)},
        )

    return ToolResult(
        success=True,
        stage=Stage.DEPTH_ESTIMATED,
        artifacts={},
        elapsed_s=round(time.perf_counter() - started, 3),
        fallback_used=True,
        recoverable=True,
        message="Using procedural foreground, middle-ground and background layers",
        details={
            "requested_output": str(output_path),
            "reason": "Depth Anything GPU service is not configured",
        },
    )

