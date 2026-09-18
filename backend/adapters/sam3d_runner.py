from __future__ import annotations

from pathlib import Path
import time

from backend.schemas import ErrorCode, Stage, ToolResult


def reconstruct_object(
    image_path: str | Path,
    mask_path: str | Path | None,
    output_path: str | Path,
    *,
    cached_asset: str | Path | None = None,
) -> ToolResult:
    """SAM 3D boundary.

    GPU inference is intentionally unavailable in the Windows web environment.
    Until the Linux service is connected, a verified cached asset may be returned.
    """
    started = time.perf_counter()
    image_path = Path(image_path)
    mask_path = Path(mask_path) if mask_path is not None else None
    output_path = Path(output_path)
    if not image_path.exists() or mask_path is None or not mask_path.exists():
        return ToolResult(
            success=False,
            stage=Stage.OBJECT_RECONSTRUCTED,
            elapsed_s=round(time.perf_counter() - started, 3),
            recoverable=True,
            error_code=ErrorCode.MASK_INVALID,
            message="Source image or mask is missing",
        )

    if cached_asset is not None and Path(cached_asset).exists():
        return ToolResult(
            success=True,
            stage=Stage.OBJECT_RECONSTRUCTED,
            artifacts={"asset": str(Path(cached_asset))},
            elapsed_s=round(time.perf_counter() - started, 3),
            fallback_used=True,
            recoverable=True,
            message="Using a verified cached SAM 3D asset until the GPU service is connected",
            details={"requested_output": str(output_path)},
        )

    return ToolResult(
        success=False,
        stage=Stage.OBJECT_RECONSTRUCTED,
        elapsed_s=round(time.perf_counter() - started, 3),
        recoverable=True,
        error_code=ErrorCode.SAM3D_FAILED,
        message="SAM 3D Linux GPU service is not configured",
        details={"requested_output": str(output_path)},
    )
