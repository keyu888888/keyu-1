"""Headless Blender smoke test for the Re:Dream execution environment."""

from pathlib import Path
import math
import sys

import bpy


def project_root() -> Path:
    script_path = Path(bpy.path.abspath(__file__)).resolve()
    return script_path.parents[2]


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def look_at(camera: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = mathutils.Vector(target) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    clear_scene()

    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
    cube = bpy.context.active_object
    cube.name = "REDREAM_SMOKE_CUBE"

    material = bpy.data.materials.new(name="WhiteModel")
    material.diffuse_color = (0.65, 0.72, 0.82, 1.0)
    cube.data.materials.append(material)

    bpy.ops.object.light_add(type="AREA", location=(3.0, -3.0, 4.0))
    key_light = bpy.context.active_object
    key_light.data.energy = 900
    key_light.data.shape = "DISK"
    key_light.data.size = 4.0

    bpy.ops.object.camera_add(location=(4.2, -4.2, 3.0))
    camera = bpy.context.active_object
    bpy.context.scene.camera = camera
    direction = mathutils.Vector((0.0, 0.0, 0.0)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    output_path = project_root() / "tasks" / "demo_001" / "blender" / "environment_smoke.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Blender smoke render did not produce an image")

    print(f"REDREAM_SMOKE_RENDER_OK={output_path}")


if __name__ == "__main__":
    import mathutils

    try:
        main()
    except Exception as exc:
        print(f"REDREAM_SMOKE_RENDER_FAILED={exc}", file=sys.stderr)
        raise

