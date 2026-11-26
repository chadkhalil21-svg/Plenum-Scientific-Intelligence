"""Bounded original procedural scientific concept renderer using Blender.

Invoke only through an approved local Blender executable and the fixed script
below. Input is data, never an arbitrary .blend file, Python, URL, or plugin.
The resulting illustration is a concept render, not measured science.
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import sys


def vector(value, lo, hi):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("Expected a three-vector")
    if any(type(v) not in (int, float) or not lo <= v <= hi
           or (type(v) is float and not math.isfinite(v)) for v in value):
        raise ValueError("Vector outside bounded scientific visualization scope")
    return tuple(value)


def validate(data):
    if not isinstance(data, dict) or set(data) != {"schema", "concept", "objects"}:
        raise ValueError("Invalid concept scene")
    if data["schema"] != "plenum-concept-geometry-v1" or data["concept"] is not True:
        raise ValueError("Original concept visualization only")
    objects = data["objects"]
    if not isinstance(objects, list) or not 1 <= len(objects) <= 16:
        raise ValueError("Require 1–16 bounded geometry objects")
    for item in objects:
        if not isinstance(item, dict) or set(item) != {"shape", "position", "size", "color"}:
            raise ValueError("Only allowlisted primitive data")
        if item["shape"] not in ("cube", "sphere"):
            raise ValueError("Unsupported primitive")
        vector(item["position"], -3, 3)
        vector(item["size"], 0.08, 2)
        vector(item["color"], 0, 1)
    return objects


def render(source, output):
    # Trusted development fixture or owner-local concept only.
    if os.getenv("GITHUB_ACTIONS") == "true":
        if os.getenv("PLENUM_PUBLIC_GEOMETRY_FIXTURE") != "confirmed":
            raise PermissionError("Only the public development fixture is allowed")
    elif os.getenv("PLENUM_OWNER_LOCAL_MEDIA") != "authorized":
        raise PermissionError("Owner local media runtime authorization required")
    source, output = Path(source), Path(output)
    if source.is_symlink() or output.is_symlink() or output.exists():
        raise ValueError("No symlinks or overwrite")
    if not source.is_file() or not 0 < source.stat().st_size <= 20000:
        raise ValueError("Invalid local scene data")
    if source.suffix != ".json" or output.suffix != ".png":
        raise ValueError("Only JSON to PNG")
    if source.resolve().parent != output.resolve().parent:
        raise ValueError("Output must remain in scene workspace")
    data = json.loads(source.read_text())
    objects = validate(data)
    import bpy
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.resolution_x = 512
    scene.render.resolution_y = 320
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output.resolve())
    world = bpy.data.worlds.new("Original concept background")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.15, 0.18, 0.25, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    for i, item in enumerate(objects):
        if item["shape"] == "cube":
            bpy.ops.mesh.primitive_cube_add(size=1, location=item["position"])
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, radius=0.5,
                                                 location=item["position"])
        obj = bpy.context.object
        obj.name = f"Concept primitive {i+1}"
        obj.scale = item["size"]
        mat = bpy.data.materials.new(f"Original material {i+1}")
        mat.diffuse_color = (*item["color"], 1)
        mat.use_nodes = True
        mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (*item["color"], 1)
        obj.data.materials.append(mat)
    bpy.ops.object.camera_add(location=(8, -10, 7))
    camera = bpy.context.object
    camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10
    scene.camera = camera
    for location, power in [((4, -4, 6), 1200), ((-4, 3, 5), 900)]:
        bpy.ops.object.light_add(type="AREA", location=location)
        lamp = bpy.context.object
        lamp.rotation_euler = (-lamp.location).to_track_quat("-Z", "Y").to_euler()
        lamp.data.energy = power
        lamp.data.shape = "DISK"
        lamp.data.size = 5
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size < 1000:
        raise RuntimeError("No accepted concept render")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    if len(args) != 2:
        raise SystemExit("Usage: blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python SCRIPT -- SCENE.json OUTPUT.png")
    render(*args)
