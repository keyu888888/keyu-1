"""Rule-based Blender camera safety checks for the 10-day demo."""

from __future__ import annotations

from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def _world_bbox_points(objects) -> list[Vector]:
    points: list[Vector] = []
    for obj in objects:
        if obj.type != "MESH" or not obj.visible_get():
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    return points


def check_camera_safety(scene, camera, target_objects, frames: list[int]) -> dict:
    points = _world_bbox_points(target_objects)
    if not points:
        return {
            "passed": False,
            "reason": "target_has_no_mesh",
            "frames": [],
        }

    frame_results = []
    passed = True
    for frame in frames:
        scene.frame_set(frame)
        projected = [world_to_camera_view(scene, camera, point) for point in points]
        xs = [point.x for point in projected if point.z > 0]
        ys = [point.y for point in projected if point.z > 0]
        if not xs or not ys:
            in_frame = False
            bounds = None
        else:
            bounds = {
                "min_x": min(xs),
                "max_x": max(xs),
                "min_y": min(ys),
                "max_y": max(ys),
            }
            in_frame = (
                bounds["min_x"] >= 0.03
                and bounds["max_x"] <= 0.97
                and bounds["min_y"] >= 0.03
                and bounds["max_y"] <= 0.97
            )
        passed = passed and in_frame
        frame_results.append({"frame": frame, "in_frame": in_frame, "bounds": bounds})

    return {
        "passed": passed,
        "reason": None if passed else "target_outside_safe_frame",
        "frames": frame_results,
    }

