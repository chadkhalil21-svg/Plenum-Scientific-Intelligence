"""Original parametric design model in editable OpenSCAD, optional STL export.

This is an aesthetic/mechanical geometry fixture, not a structurally safe
building, engineered aircraft part, load-bearing component or manufacturable
approved product. Input parameters are bounded and never interpolated as code.
"""
from pathlib import Path
from math import isfinite
import json
import subprocess


def validate_panel(width=180, height=110, thickness=6, hole_diameter=5):
    values=(width,height,thickness,hole_diameter)
    if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not isfinite(x)
           for x in values):
        raise ValueError("Finite numerical CAD dimensions required")
    if not (80<=width<=300 and 60<=height<=250 and 3<=thickness<=18
            and 2<=hole_diameter<=12):
        raise ValueError("Dimensions outside reviewed design limits")
    if hole_diameter>=min(width,height)/8:
        raise ValueError("Holes too large for bounding geometry")
    return tuple(float(x) for x in values)


def parametric_panel(width=180,height=110,thickness=6,hole_diameter=5):
    width,height,thickness,hole=validate_panel(width,height,thickness,hole_diameter)
    margin=18.0
    # Eight regularly spaced fastener holes; no presumption of structural use.
    points=[(margin+i*(width-2*margin)/3, y)
            for i in range(4) for y in (margin,height-margin)]
    holes="\n".join(
        f"  translate([{x:.4f},{y:.4f},-1]) cylinder(d={hole:.4f}, h={thickness+2:.4f}, $fn=48);"
        for x,y in points
    )
    return f"""// Plenum original parametric geometric sample; units: mm
// Reference only. No finite element, material, fatigue, fastener or safety checks.
width = {width:.4f};
height = {height:.4f};
thickness = {thickness:.4f};
difference() {{
  cube([width, height, thickness], center=false);
{holes}
}}
"""


def create_design(folder,width=180,height=110,thickness=6,hole_diameter=5,
                  render=False):
    dims=validate_panel(width,height,thickness,hole_diameter)
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    scad=folder/"plenum_original_panel.scad"
    scad.write_text(parametric_panel(*dims),encoding="utf-8")
    stl=folder/"plenum_original_panel.stl"
    mesh_ok=False
    if render:
        try:
            subprocess.run(["openscad","-o",str(stl),str(scad)],
                           capture_output=True,text=True,
                           check=True,timeout=100)
        except (OSError,subprocess.SubprocessError) as exc:
            raise RuntimeError("Approved OpenSCAD mesh export failed") from None
        mesh_ok=stl.is_file() and stl.stat().st_size>1000
        if not mesh_ok:
            raise RuntimeError("OpenSCAD mesh missing or undersized")
    report={
        "schema":"plenum-original-parametric-design-v1",
        "author":"Plenum procedural geometry",
        "dimension_units":"mm",
        "dimensions":{"width":dims[0],"height":dims[1],
                      "thickness":dims[2],"hole_diameter":dims[3]},
        "mounting_holes":8,
        "source_scad":str(scad),
        "stl_mesh":str(stl) if mesh_ok else None,
        "mesh_export_verified":mesh_ok,
        "novel_design_or_patentability_verified":False,
        "structural_strength_or_safety_validated":False,
        "manufacturing_tolerances_verified":False,
        "professional_engineering_approval":False,
        "human_review_required_before_manufacture":True,
    }
    return report
