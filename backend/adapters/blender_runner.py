from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time

from backend.schemas import ErrorCode, Stage, ToolResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def find_blender() -> Path:
    candidates = list((PROJECT_ROOT / "tools" / "blender").glob("**/blender.exe"))
    if not candidates:
        raise FileNotFoundError("Blender executable not found under tools/blender")
    return candidates[0]


def run_blender_scene(spec_path: str | Path, *, render_animation: bool = True) -> ToolResult:
    started = time.perf_counter()
    spec_path = Path(spec_path)
    if not spec_path.is_absolute():
        spec_path = PROJECT_ROOT / spec_path
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    result_path = PROJECT_ROOT / "tasks" / spec["job_id"] / "blender" / "tool_result.json"
    result_path.unlink(missing_ok=True)
    command = [
        str(find_blender()),
        "-b",
        "--python",
        str(PROJECT_ROOT / "backend" / "blender_scripts" / "build_scene.py"),
        "--",
        "--spec",
        str(spec_path),
    ]
    if not render_animation:
        command.append("--skip-animation")
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=900,
    )
    if result_path.exists():
        return ToolResult.model_validate_json(result_path.read_text(encoding="utf-8"))
    return ToolResult(
        success=False,
        stage=Stage.SCENE_BUILT,
        elapsed_s=round(time.perf_counter() - started, 3),
        fallback_used=False,
        recoverable=True,
        error_code=ErrorCode.SCENE_BUILD_FAILED,
        message="Blender did not produce a tool result",
        details={
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-2000:],
            "stderr_tail": completed.stderr[-2000:],
        },
    )
