"""Deterministic camera templates used by the Blender runtime."""

from __future__ import annotations

import math

from mathutils import Vector


SUPPORTED_TEMPLATES = {"linear_dolly", "arc_push"}


def _insert_location(camera, frame: int, location: Vector) -> None:
    camera.location = location
    camera.keyframe_insert(data_path="location", frame=frame)


def _linearize_location_keys(camera) -> None:
    if camera.animation_data is None or camera.animation_data.action is None:
        return
    for curve in camera.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.easing = "EASE_IN_OUT"


def apply_camera_template(camera, target, spec: dict, frame_end: int) -> list[Vector]:
    template = spec["template"]
    if template not in SUPPORTED_TEMPLATES:
        raise ValueError(f"Unsupported camera template: {template}")

    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.name = "REDREAM_TRACK_TARGET"
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"

    target_height = 1.0
    if template == "linear_dolly":
        start = Vector((0.0, -6.8, 2.7))
        end = Vector((0.0, -6.0, 2.7))
        points = [start, end]
    else:
        angle = math.radians(min(float(spec.get("angle_deg", 8.0)), 12.0))
        start_radius = 6.8
        end_radius = start_radius * (1.0 - min(float(spec.get("travel_ratio", 0.08)), 0.12))
        start = Vector((-math.sin(angle / 2) * start_radius, -math.cos(angle / 2) * start_radius, 2.7))
        middle_radius = (start_radius + end_radius) / 2
        middle = Vector((0.0, -middle_radius, 2.55))
        end = Vector((math.sin(angle / 2) * end_radius, -math.cos(angle / 2) * end_radius, 2.4))
        points = [start, middle, end]

    camera.data.lens = 52
    target.location = (0.0, 0.0, target_height)
    if len(points) == 2:
        _insert_location(camera, 1, points[0])
        _insert_location(camera, frame_end, points[1])
    else:
        _insert_location(camera, 1, points[0])
        _insert_location(camera, max(2, frame_end // 2), points[1])
        _insert_location(camera, frame_end, points[2])
    _linearize_location_keys(camera)
    return points
