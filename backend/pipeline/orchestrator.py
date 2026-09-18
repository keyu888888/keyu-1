from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from backend.adapters.blender_runner import run_blender_scene
from backend.adapters.depth_runner import estimate_depth
from backend.adapters.sam3d_runner import reconstruct_object
from backend.pipeline.compose_final import compose_final_video
from backend.schemas import SceneSpec, Stage, ToolResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def write_status(task_dir: Path, stage: str, progress: int, message: str, artifacts: dict[str, str] | None = None) -> None:
    payload = {
        "contract_version": "0.1.0",
        "job_id": task_dir.name,
        "stage": stage,
        "progress": progress,
        "message": message,
        "artifacts": artifacts or {},
        "recoverable": True,
        "next_action": None,
        "error": None,
    }
    (task_dir / "status.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pipeline(spec_path: str | Path, *, reuse_existing: bool = True) -> dict:
    started = time.perf_counter()
    spec_path = resolve_path(spec_path)
    assert spec_path is not None
    spec = SceneSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
    task_dir = PROJECT_ROOT / "tasks" / spec.job_id
    for name in ("analysis", "depth", "assets", "blender", "control", "generation", "edit", "logs"):
        (task_dir / name).mkdir(parents=True, exist_ok=True)

    steps: dict[str, dict] = {}
    write_status(task_dir, "validated", 10, "scene_spec已通过校验")

    target = spec.targets[0] if spec.targets else None
    if target is not None:
        sam_result = reconstruct_object(
            resolve_path(target.source_image),
            resolve_path(target.mask_path),
            task_dir / "assets" / f"{target.id}.glb",
            cached_asset=resolve_path(target.asset_path),
        )
        steps["reconstruction"] = sam_result.model_dump(mode="json")
        write_status(task_dir, "object_ready", 30, sam_result.message, sam_result.artifacts)

    depth_result = estimate_depth(
        resolve_path(spec.hero_image),
        task_dir / "depth" / "depth_raw.png",
        cached_depth=resolve_path(spec.background.depth_path),
    )
    steps["depth"] = depth_result.model_dump(mode="json")
    write_status(task_dir, "depth_ready", 40, depth_result.message, depth_result.artifacts)

    control_path = task_dir / "control" / "white_model.mp4"
    if reuse_existing and control_path.exists():
        blender_result = ToolResult.model_validate_json(
            (task_dir / "blender" / "tool_result.json").read_text(encoding="utf-8")
        )
        blender_result = blender_result.model_copy(
            update={
                "stage": Stage.WHITE_MODEL_RENDERED,
                "artifacts": {
                    **blender_result.artifacts,
                    "control_video": control_path.relative_to(PROJECT_ROOT).as_posix(),
                },
            }
        )
    else:
        blender_result = run_blender_scene(spec_path, render_animation=True)
    steps["blender"] = blender_result.model_dump(mode="json")
    write_status(task_dir, "white_model_ready", 70, blender_result.message, blender_result.artifacts)
    if not blender_result.success:
        raise RuntimeError(blender_result.message)

    if spec.generation.provider == "mock":
        core_video = control_path
        steps["generation"] = {
            "success": True,
            "provider": "mock",
            "message": "开发夹具直接使用白模视频代替外部生成结果",
            "artifacts": {"core_video": core_video.relative_to(PROJECT_ROOT).as_posix()},
        }
    else:
        raise RuntimeError(f"Video provider {spec.generation.provider} is not configured")
    write_status(task_dir, "core_video_ready", 82, steps["generation"]["message"], steps["generation"]["artifacts"])

    final_result = compose_final_video(
        spec.hero_image,
        core_video,
        spec.edit.output_path,
        title=spec.edit.title,
        music_path=spec.edit.music_path,
    )
    steps["compose"] = final_result.model_dump(mode="json")
    if not final_result.success:
        raise RuntimeError(final_result.message)
    write_status(task_dir, "completed", 100, final_result.message, final_result.artifacts)

    summary = {
        "success": True,
        "job_id": spec.job_id,
        "elapsed_s": round(time.perf_counter() - started, 3),
        "reuse_existing": reuse_existing,
        "steps": steps,
        "final_video": final_result.artifacts["final_video"],
    }
    (task_dir / "pipeline_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--no-reuse", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_pipeline(args.spec, reuse_existing=not args.no_reuse), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
