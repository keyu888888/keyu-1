"""Build and render a deterministic Re:Dream white-model scene in Blender."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from camera_templates import apply_camera_template
from safety_check import check_camera_safety


PROJECT_ROOT = SCRIPT_DIR.parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--skip-animation", action="store_true")
    parser.add_argument("--camera-template", choices=["linear_dolly", "arc_push"])
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(argv)


def resolve_project_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def create_material(name: str, color: tuple[float, float, float, float], metallic: float = 0.0):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = color
    material.metallic = metallic
    material.roughness = 0.72
    return material


def create_proxy_target() -> tuple[bpy.types.Object, list[bpy.types.Object], bool]:
    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 1.0), scale=(1.1, 0.7, 1.0))
    obj = bpy.context.active_object
    obj.name = "REDREAM_PROXY_TARGET"
    obj.data.materials.append(create_material("TargetWhite", (0.66, 0.74, 0.84, 1.0)))
    root = bpy.data.objects.new("REDREAM_TARGET_ROOT", None)
    bpy.context.collection.objects.link(root)
    obj.parent = root
    return root, [obj], True


def imported_meshes(before: set[str]) -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.name not in before and obj.type == "MESH"]


def import_target_asset(asset_path: Path | None) -> tuple[bpy.types.Object, list[bpy.types.Object], bool]:
    if asset_path is None or not asset_path.exists():
        return create_proxy_target()

    before = {obj.name for obj in bpy.context.scene.objects}
    suffix = asset_path.suffix.lower()
    if suffix in {".glb", ".gltf"}:
        bpy.ops.import_scene.gltf(filepath=str(asset_path))
    elif suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(asset_path))
    elif suffix == ".ply":
        bpy.ops.wm.ply_import(filepath=str(asset_path))
    else:
        raise ValueError(f"Unsupported asset format: {suffix}")

    meshes = imported_meshes(before)
    if not meshes:
        raise RuntimeError("Imported asset contains no mesh")

    root = bpy.data.objects.new("REDREAM_TARGET_ROOT", None)
    bpy.context.collection.objects.link(root)
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world

    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (minimum + maximum) / 2
    dimensions = maximum - minimum
    scale = 2.2 / max(dimensions.x, dimensions.y, dimensions.z, 1e-6)
    root.scale = (scale, scale, scale)
    root.location = (-center.x * scale, -center.y * scale, -minimum.z * scale)
    bpy.context.view_layer.update()
    return root, meshes, False


def create_background_layers(count: int) -> None:
    colors = [
        (0.34, 0.39, 0.46, 1.0),
        (0.24, 0.28, 0.34, 1.0),
        (0.16, 0.19, 0.24, 1.0),
    ]
    for index in range(count):
        y = 1.8 + index * 1.35
        z = 1.9 + index * 0.22
        scale = 4.2 + index * 1.0
        bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0.0, y, z), rotation=(1.5708, 0.0, 0.0))
        plane = bpy.context.active_object
        plane.name = f"REDREAM_BACKGROUND_{index + 1}"
        plane.scale = (scale, scale * 0.56, 1.0)
        plane.data.materials.append(create_material(f"Background{index + 1}", colors[index]))

    bpy.ops.mesh.primitive_plane_add(size=30.0, location=(0.0, 0.0, 0.0))
    ground = bpy.context.active_object
    ground.name = "REDREAM_GROUND"
    ground.data.materials.append(create_material("Ground", (0.12, 0.14, 0.18, 1.0)))


def create_lighting() -> None:
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.color = (0.025, 0.03, 0.04)

    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.0, 6.0))
    key = bpy.context.active_object
    key.name = "REDREAM_KEY_LIGHT"
    key.data.energy = 1100
    key.data.shape = "DISK"
    key.data.size = 5.0

    bpy.ops.object.light_add(type="AREA", location=(4.0, -1.0, 3.5))
    fill = bpy.context.active_object
    fill.name = "REDREAM_FILL_LIGHT"
    fill.data.energy = 500
    fill.data.size = 4.0


def create_path_curve(points: list[Vector]):
    curve_data = bpy.data.curves.new("REDREAM_CAMERA_PATH_DATA", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = 0.075
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, location in zip(spline.points, points):
        point.co = (*location, 1.0)
    curve = bpy.data.objects.new("REDREAM_CAMERA_PATH", curve_data)
    bpy.context.collection.objects.link(curve)
    material = create_material("PathAccent", (0.95, 0.08, 0.03, 1.0), metallic=0.0)
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = (0.95, 0.02, 0.01, 1.0)
        principled.inputs["Emission Color"].default_value = (0.95, 0.02, 0.01, 1.0)
        principled.inputs["Emission Strength"].default_value = 4.0
    curve.data.materials.append(material)
    for index, location in enumerate(points, start=1):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.16, location=location)
        marker = bpy.context.active_object
        marker.name = f"REDREAM_PATH_MARKER_{index}"
        marker.data.materials.append(material)
    return curve


def configure_render(spec: dict, task_dir: Path) -> None:
    scene = bpy.context.scene
    render = spec["render"]
    scene.render.engine = render["engine"]
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = render["width"]
    scene.render.resolution_y = render["height"]
    scene.render.resolution_percentage = 100
    scene.render.fps = render["fps"]
    scene.frame_start = 1
    scene.frame_end = round(spec["camera"]["duration_s"] * render["fps"])
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(task_dir / "blender" / "scene_preview.png")


def render_still(path: Path, frame: int) -> None:
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def render_camera_path(path: Path, main_camera, path_curve) -> None:
    scene = bpy.context.scene
    hidden_objects = [
        obj
        for obj in scene.objects
        if obj.name.startswith("REDREAM_BACKGROUND_") or obj.name == "REDREAM_GROUND"
    ]
    hidden_states = {obj.name: obj.hide_render for obj in hidden_objects}
    for obj in hidden_objects:
        obj.hide_render = True
    original_world_color = tuple(scene.world.color)
    scene.world.color = (0.015, 0.02, 0.03)
    path_center_y = (min(point.co.y for point in path_curve.data.splines[0].points) + max(point.co.y for point in path_curve.data.splines[0].points)) / 2
    view_center_y = path_center_y / 2
    bpy.ops.object.camera_add(location=(0.0, view_center_y, 12.0), rotation=(0.0, 0.0, 0.0))
    top_camera = bpy.context.active_object
    top_camera.name = "REDREAM_PATH_CAMERA"
    top_camera.data.type = "ORTHO"
    top_camera.data.ortho_scale = 15.0
    top_camera.rotation_euler = (0.0, 0.0, 0.0)
    top_camera.rotation_euler[0] = 0.0
    top_camera.rotation_euler[1] = 0.0
    top_camera.rotation_euler[2] = 0.0
    top_camera.rotation_euler = (0.0, 0.0, 0.0)
    direction = Vector((0.0, view_center_y, 0.0)) - top_camera.location
    top_camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = top_camera
    render_still(path, 1)
    scene.camera = main_camera
    for obj in scene.objects:
        if obj.name == "REDREAM_CAMERA_PATH" or obj.name.startswith("REDREAM_PATH_MARKER_"):
            obj.hide_render = True
    scene.world.color = original_world_color
    for obj in hidden_objects:
        obj.hide_render = hidden_states[obj.name]


def render_animation(output_path: Path) -> None:
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
    scene.render.ffmpeg.audio_codec = "NONE"
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(animation=True)


def main() -> None:
    started = time.perf_counter()
    args = parse_args()
    spec_path = resolve_project_path(args.spec)
    if spec_path is None or not spec_path.exists():
        raise FileNotFoundError(f"Scene spec not found: {args.spec}")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if args.camera_template:
        spec["camera"]["template"] = args.camera_template
    task_dir = PROJECT_ROOT / "tasks" / spec["job_id"]
    for name in ("blender", "control", "logs"):
        (task_dir / name).mkdir(parents=True, exist_ok=True)

    clear_scene()
    create_background_layers(spec["background"]["layer_count"])
    create_lighting()

    first_target = spec["targets"][0] if spec["targets"] else {}
    asset_path = resolve_project_path(first_target.get("asset_path"))
    target_root, target_meshes, fallback_used = import_target_asset(asset_path)

    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0.0, 0.0, 1.0))
    look_target = bpy.context.active_object
    look_target.name = "REDREAM_LOOK_TARGET"
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    camera.name = "REDREAM_MAIN_CAMERA"
    bpy.context.scene.camera = camera

    configure_render(spec, task_dir)
    points = apply_camera_template(camera, look_target, spec["camera"], bpy.context.scene.frame_end)
    path_curve = create_path_curve(points)

    frames = [1, max(2, bpy.context.scene.frame_end // 2), bpy.context.scene.frame_end]
    safety = check_camera_safety(bpy.context.scene, camera, target_meshes, frames)
    safety["fallback_used"] = fallback_used
    safety["camera_template"] = spec["camera"]["template"]
    safety_path = task_dir / "blender" / "safety_check.json"
    safety_path.write_text(json.dumps(safety, ensure_ascii=False, indent=2), encoding="utf-8")

    check_dir = task_dir / "blender" / "checks"
    check_dir.mkdir(parents=True, exist_ok=True)
    for label, frame in zip(("first", "middle", "last"), frames):
        render_still(check_dir / f"{label}.png", frame)
    render_still(task_dir / "blender" / "scene_preview.png", frames[1])
    render_camera_path(task_dir / "blender" / "camera_path.png", camera, path_curve)

    scene_path = task_dir / "blender" / "scene.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(scene_path))
    control_path = task_dir / "control" / "white_model.mp4"
    if not args.skip_animation:
        render_animation(control_path)

    result = {
        "contract_version": "0.1.0",
        "success": bool(safety["passed"]),
        "stage": "white_model_rendered" if not args.skip_animation else "scene_built",
        "artifacts": {
            "scene": str(scene_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "scene_preview": str((task_dir / "blender" / "scene_preview.png").relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "camera_path": str((task_dir / "blender" / "camera_path.png").relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "safety_check": str(safety_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        },
        "elapsed_s": round(time.perf_counter() - started, 3),
        "fallback_used": fallback_used,
        "recoverable": True,
        "error_code": None if safety["passed"] else "E405_CAMERA_UNSAFE",
        "message": "白模场景已生成" if safety["passed"] else "镜头安全检查未通过",
        "details": safety,
    }
    if not args.skip_animation:
        result["artifacts"]["control_video"] = str(control_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    result_path = task_dir / "blender" / "tool_result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REDREAM_RESULT={result_path}")
    if not safety["passed"]:
        raise SystemExit(5)


if __name__ == "__main__":
    main()
