#!/usr/bin/env python3
"""
verify_export.py — confirm an exported mesh matches its source constants.

Given a mesh and a small JSON spec of named expected dimensions (each with a
tolerance), checks watertightness and measures each feature off the mesh
itself. This catches unit errors, mirrored parts, silent boolean failures and
stale exports — the file is the ground truth, not the exporter's exit code.

Spec format (JSON):
{
  "watertight": true,
  "checks": {
    "collar OD":   {"kind": "bbox_x",  "expect": 36.0,  "tol": 0.3},
    "height":      {"kind": "bbox_z",  "expect": 11.0,  "tol": 0.2},
    "bore radius": {"kind": "section_hole_rmin", "z": 5.0,
                    "expect": 15.0, "tol": 0.15},
    "tab tips":    {"kind": "profile_rmin", "z": 0.5,
                    "expect": 11.03, "tol": 0.2},
    "channel":     {"kind": "profile_rmedian", "z": 5.0,
                    "expect": 15.0, "tol": 0.2},
    "volume":      {"kind": "volume", "expect": 21000, "tol": 2000}
  }
}

kinds: bbox_x | bbox_y | bbox_z            overall extents
       volume                              mm^3 (watertight meshes only)
       section_area                        largest loop area at z
       section_hole_rmin | section_hole_rmax   innermost hole radius at z
       profile_rmin | profile_rmedian | profile_rmax
                                           ray-cast radii about the axis at z

Radii are measured about --axis-center (default: bbox center in XY).
Exit code 0 = all pass, 1 = any failure.

Examples:
  verify_export.py out/adapter.stl spec.json
  verify_export.py out/adapter.stl spec.json --axis-center 0,0

Requires: pip install trimesh numpy scipy shapely rtree
"""

import argparse
import json
import sys

try:
    import numpy as np
    import trimesh
except ImportError as e:
    sys.exit(
        f"Missing dependency: {e.name}.\n"
        "Install with:  pip install trimesh numpy scipy shapely rtree\n"
        "(Use a venv if your system pip is externally-managed.)"
    )


def profile_radii(m, z, axis_xy, n_rays=720):
    cx, cy = axis_xy
    ang = np.linspace(0, 2 * np.pi, n_rays, endpoint=False)
    origins = np.column_stack([np.full(n_rays, cx), np.full(n_rays, cy),
                               np.full(n_rays, z)])
    dirs = np.column_stack([np.cos(ang), np.sin(ang), np.zeros(n_rays)])
    locs, idx, _ = m.ray.intersects_location(origins, dirs,
                                             multiple_hits=False)
    if not len(idx):
        return None
    return np.hypot(locs[:, 0] - cx, locs[:, 1] - cy)


def section_holes(m, z, axis_xy):
    sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is None:
        return None, None
    planar, _ = sec.to_2D()
    cx, cy = axis_xy
    best_area, holes = 0.0, []
    for poly in planar.polygons_full:
        best_area = max(best_area, poly.area)
        for ring in poly.interiors:
            pts = np.array(ring.coords)
            r = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
            holes.append((float(r.min()), float(r.max())))
    return best_area, holes


def measure(m, kind, spec, axis_xy):
    """Return measured value or (None, reason)."""
    if kind in ("bbox_x", "bbox_y", "bbox_z"):
        return float(m.extents["xyz".index(kind[-1])]), None
    if kind == "volume":
        if not m.is_watertight:
            return None, "mesh not watertight, volume unreliable"
        return float(m.volume), None
    z = spec.get("z")
    if z is None:
        return None, f"kind '{kind}' needs a 'z' height"
    if kind == "section_area":
        area, _ = section_holes(m, z, axis_xy)
        return (area, None) if area else (None, f"no section at z={z}")
    if kind in ("section_hole_rmin", "section_hole_rmax"):
        _, holes = section_holes(m, z, axis_xy)
        if not holes:
            return None, f"no hole in section at z={z}"
        inner = min(holes, key=lambda h: h[0])  # innermost hole
        return (inner[0] if kind.endswith("rmin") else inner[1]), None
    if kind in ("profile_rmin", "profile_rmedian", "profile_rmax"):
        r = profile_radii(m, z, axis_xy)
        if r is None:
            return None, f"no ray hits at z={z}"
        fn = {"profile_rmin": np.min, "profile_rmedian": np.median,
              "profile_rmax": np.max}[kind]
        return float(fn(r)), None
    return None, f"unknown kind '{kind}'"


def main():
    ap = argparse.ArgumentParser(
        description="Verify an exported mesh against expected dimensions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Spec format (JSON):")[1])
    ap.add_argument("mesh", help="exported mesh file (STL/GLB/...)")
    ap.add_argument("spec", help="JSON spec of expected dimensions")
    ap.add_argument("--axis-center", default="",
                    help="XY of the part axis as 'x,y' (default: bbox center)")
    args = ap.parse_args()

    with open(args.spec) as f:
        spec = json.load(f)

    m = trimesh.load(args.mesh, force="mesh")
    if m.is_empty:
        sys.exit(f"FAIL: {args.mesh} contains no geometry.")
    m.process(validate=True)
    m.merge_vertices()

    if args.axis_center:
        axis_xy = tuple(float(v) for v in args.axis_center.split(","))
    else:
        lo, hi = m.bounds
        axis_xy = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)

    failures = 0
    print(f"mesh: {args.mesh}")
    print(f"extents: {m.extents[0]:.2f} x {m.extents[1]:.2f} x "
          f"{m.extents[2]:.2f} mm   bodies: {m.body_count}")

    if spec.get("watertight", True):
        ok = m.is_watertight
        print(f"[{'PASS' if ok else 'FAIL'}] watertight")
        failures += 0 if ok else 1

    for name, chk in spec.get("checks", {}).items():
        val, err = measure(m, chk["kind"], chk, axis_xy)
        if val is None:
            print(f"[FAIL] {name}: could not measure ({err})")
            failures += 1
            continue
        exp, tol = chk["expect"], chk["tol"]
        ok = abs(val - exp) <= tol
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: measured {val:.3f}, "
              f"expected {exp} ± {tol} ({chk['kind']}"
              + (f" @ z={chk['z']}" if "z" in chk else "") + ")")
        failures += 0 if ok else 1

    print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
